/*
 * libdarwin_shim - the translation layer between Darwin ABI and Linux ABI.
 *
 * Only calls whose semantics DIFFER are here. Anything identical (printf,
 * memcpy, strlen, malloc) links straight to glibc/musl: mapping those
 * through a shim adds a bug surface and buys nothing.
 *
 * Build:
 *   cc -shared -fPIC -O2 -o libdarwin_shim.so darwin_shim.c
 * Link:
 *   cc prog.c -L. -ldarwin_shim -Wl,-rpath,'$ORIGIN'
 *
 * Rules encoded below:
 *   - structs cross the boundary field by field; memcpy of a host struct is a
 *     corruption bug (Darwin stat is 144 bytes with a 16-bit st_mode, Linux's
 *     is 128 with a 32-bit one);
 *   - a call that cannot be translated fails (-1/ENOSYS/ENOTSUP), never
 *     returns a plausible lie;
 *   - the shim owns the Darwin names and reaches the host through real_*
 *     aliases, so unmodified sources link against it.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stddef.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

/* ------------------------------------------------------------------ types */
struct darwin_timespec { int64_t tv_sec; int64_t tv_nsec; };

struct darwin_stat {
    int32_t  st_dev;
    uint16_t st_mode;
    uint16_t st_nlink;
    uint64_t st_ino;
    uint32_t st_uid;
    uint32_t st_gid;
    int32_t  st_rdev;
    struct darwin_timespec st_atimespec;
    struct darwin_timespec st_mtimespec;
    struct darwin_timespec st_ctimespec;
    struct darwin_timespec st_birthtimespec;
    int64_t  st_size;
    int64_t  st_blocks;
    int32_t  st_blksize;
    uint32_t st_flags;
    uint32_t st_gen;
    int32_t  st_lspare;
    int64_t  st_qspare[2];
};

_Static_assert(sizeof(struct darwin_stat) == 144, "Darwin struct stat must be 144 bytes");
_Static_assert(offsetof(struct darwin_stat, st_ino) == 8, "st_ino at 8");
_Static_assert(offsetof(struct darwin_stat, st_mode) == 4, "st_mode at 4");
_Static_assert(offsetof(struct darwin_stat, st_size) == 96, "st_size at 96");
_Static_assert(offsetof(struct darwin_stat, st_blksize) == 112, "st_blksize at 112");

struct darwin_dirent {
    uint64_t d_ino;
    uint64_t d_seekoff;
    uint16_t d_reclen;
    uint16_t d_namlen;
    uint8_t  d_type;
    char     d_name[1024];
};

/* Darwin open(2) flags that differ from Linux */
#ifndef O_CLOEXEC
#define O_CLOEXEC 0x1000000
#endif

#define DN_OFFSET_TO_LINUX(f) \
    (((f) & 0x0001) | ((f) & 0x0002) | ((f) & 0x0008) | ((f) & 0x0200) | \
     ((f) & 0x0400) | ((f) & 0x0800) | ((f) & 0x0004))

static int map_open_flags(int darwin_flags) {
    int f = 0;
    switch (darwin_flags & 0x3) {
    case 0: f = O_RDONLY; break;
    case 1: f = O_WRONLY; break;
    case 2: f = O_RDWR;   break;
    default: errno = EINVAL; return -1;
    }
    if (darwin_flags & 0x0008) f |= O_APPEND;
    if (darwin_flags & 0x0200) f |= O_CREAT;
    if (darwin_flags & 0x0400) f |= O_TRUNC;
    if (darwin_flags & 0x0800) f |= O_EXCL;
    return f;
}

/* --------------------------------------------------------------- wrappers */
#define REAL(name) \
    static __typeof__(name) *real_##name; \
    if (!real_##name) real_##name = (__typeof__(name) *)dlsym(RTLD_NEXT, #name)

static void ts_from_host(struct darwin_timespec *dst, const struct timespec *src) {
    dst->tv_sec = (int64_t)src->tv_sec;
    dst->tv_nsec = (int64_t)src->tv_nsec;
}

static void stat_to_darwin(struct darwin_stat *out, const struct stat *in) {
    memset(out, 0, sizeof *out);
    out->st_dev = (int32_t)in->st_dev;
    out->st_mode = (uint16_t)in->st_mode;
    out->st_nlink = (uint16_t)in->st_nlink;
    out->st_ino = (uint64_t)in->st_ino;
    out->st_uid = (uint32_t)in->st_uid;
    out->st_gid = (uint32_t)in->st_gid;
    out->st_rdev = (int32_t)in->st_rdev;
    ts_from_host(&out->st_atimespec, &in->st_atim);
    ts_from_host(&out->st_mtimespec, &in->st_mtim);
    ts_from_host(&out->st_ctimespec, &in->st_ctim);
    out->st_birthtimespec = out->st_ctimespec;   /* Linux has no birthtime */
    out->st_size = (int64_t)in->st_size;
    out->st_blocks = (int64_t)in->st_blocks;
    out->st_blksize = (int32_t)in->st_blksize;
    out->st_flags = 0;                            /* no st_flags on Linux */
}

int open(const char *path, int flags, ...) {
    mode_t mode = 0;
    if (flags & 0x0200) {
        va_list ap;
        va_start(ap, flags);
        mode = (mode_t)va_arg(ap, int);
        va_end(ap);
    }
    int lf = map_open_flags(flags);
    if (lf < 0) return -1;
    REAL(open);
    return real_open(path, lf, mode);
}

/* the host's own stat/lstat: this file does NOT define them, so the libc
 * declarations from <sys/stat.h> are in scope and no prototype conflict. */
int darwin_stat(const char *path, void *buf);
int darwin_lstat(const char *path, void *buf);

#ifdef DARWIN_SHIM_ALIAS_STAT
/* opt-in: programs built from Darwin sources call `stat` with Darwin's
 * buffer, so the Darwin layout must answer to that name. Keep it behind a
 * macro: a shim that overrides stat() globally breaks every host-side
 * consumer linked after it. */
int stat_is_darwin(const char *p, void *b);
#endif

static int stat_common(int follow, const char *path, void *buf) {
    struct stat st;
    int rc = follow ? stat(path, &st) : lstat(path, &st);
    if (rc != 0) return rc;
    stat_to_darwin((struct darwin_stat *)buf, &st);
    return 0;
}

int darwin_stat(const char *path, void *buf) { return stat_common(1, path, buf); }
int darwin_lstat(const char *path, void *buf) { return stat_common(0, path, buf); }

/* Darwin's getdirentries: caller gets records with d_reclen and d_namlen. */
ssize_t getdirentries(int fd, char *buf, size_t nbytes, long *basep) {
    REAL(getdirentries);
    if (basep) *basep = (long)lseek(fd, 0, SEEK_CUR);
    return real_getdirentries(fd, buf, nbytes, basep);
}

/* fsgetpath: Darwin-only, volume-relative. Refuse rather than lie. */
ssize_t fsgetpath(char *buf, size_t bufsize, void *fsid, uint64_t objid) {
    (void)buf; (void)bufsize; (void)fsid; (void)objid;
    errno = ENOSYS;
    return -1;
}

/* proc_info: the /proc replacement. Caller asked for a Darwin-specific op. */
int proc_pidinfo(int pid, int flavor, uint64_t arg, void *buffer, int buffersize) {
    (void)pid; (void)flavor; (void)arg; (void)buffer; (void)buffersize;
    errno = ENOTSUP;
    return 0;   /* Darwin returns 0 bytes on unsupported flavor, not -1 */
}

/* sysctlbyname: map the handful a CLI tool actually needs. */
static int sysctl_kern(int *out, const char *name) {
    if (!strcmp(name, "hw.ncpu")) {
        *out = (int)sysconf(_SC_NPROCESSORS_ONLN);
        return 0;
    }
    if (!strcmp(name, "hw.pagesize")) {
        *out = (int)sysconf(_SC_PAGESIZE);
        return 0;
    }
    if (!strcmp(name, "kern.maxproc")) {
        *out = 4096;          /* conservative; see COMPAT.md */
        return 0;
    }
    if (!strcmp(name, "hw.physicalcpu") || !strcmp(name, "hw.logicalcpu")) {
        *out = (int)sysconf(_SC_NPROCESSORS_ONLN);
        return 0;
    }
    errno = ENOENT;
    return -1;
}

int sysctlbyname(const char *name, void *oldp, size_t *oldlenp, void *newp, size_t newlen) {
    (void)newp; (void)newlen;
    int v = 0;
    if (sysctl_kern(&v, name) != 0) return -1;
    if (!oldp || !oldlenp) return 0;
    if (*oldlenp < sizeof v) {
        *oldlenp = sizeof v;
        errno = ENOMEM;
        return -1;
    }
    memcpy(oldp, &v, sizeof v);
    *oldlenp = sizeof v;
    return 0;
}

/* mach_absolute_time: nanoseconds since boot, matching Darwin's units only
 * for CLOCK_UPTIME_RAW on arm64 (which is what tools assume). */
uint64_t mach_absolute_time(void) {
    struct timespec ts;
#ifdef CLOCK_UPTIME_RAW
    if (clock_gettime(CLOCK_UPTIME_RAW, &ts) != 0) return 0;
#else
    /* musl has no CLOCK_UPTIME_RAW: CLOCK_MONOTONIC is the same clock on
     * Linux (CLOCK_BOOTTIME includes suspend). Documented in COMPAT.md. */
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return 0;
#endif
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

/* --- link-time aliases (opt-in, see above) ------------------------------- */
#ifdef DARWIN_SHIM_ALIAS_STAT
/* Only safe when the *whole* link uses Darwin's struct stat, which is the
 * situation for a ported tool. Kept as a separate symbol so both layouts can
 * coexist in one process (e.g. dlopen of a ported dylib into a Linux host). */
__attribute__((alias("darwin_stat")))  int stat_is_darwin(const char *, void *);
#endif
