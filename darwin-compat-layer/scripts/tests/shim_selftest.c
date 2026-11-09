#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/stat.h>

/* Darwin ABI mirror, same layout the shim writes */
struct darwin_timespec { int64_t tv_sec, tv_nsec; };
struct darwin_stat {
    int32_t st_dev; uint16_t st_mode; uint16_t st_nlink; uint64_t st_ino;
    uint32_t st_uid; uint32_t st_gid; int32_t st_rdev;
    struct darwin_timespec at, mt, ct, bt;
    int64_t st_size, st_blocks; int32_t st_blksize; uint32_t st_flags, st_gen;
    int32_t st_lspare; int64_t st_qspare[2];
};
int darwin_stat(const char *p, void *b);
int darwin_lstat(const char *p, void *b);
int sysctlbyname(const char *n, void *o, size_t *ol, void *np, size_t nl);
uint64_t mach_absolute_time(void);
ssize_t fsgetpath(char *b, size_t s, void *f, uint64_t o);

int main(void) {
    struct darwin_stat ds;
    if (darwin_stat("/etc/hostname", &ds) != 0) { perror("darwin_stat"); return 1; }
    printf("size=%lld mode=%o ino=%llu blksize=%d (struct %zu)\n",
           (long long)ds.st_size, ds.st_mode, (unsigned long long)ds.st_ino,
           ds.st_blksize, sizeof ds);
    int ncpu = 0; size_t len = sizeof ncpu;
    if (sysctlbyname("hw.ncpu", &ncpu, &len, 0, 0) == 0) printf("hw.ncpu=%d\n", ncpu);
    if (sysctlbyname("hw.nope", &ncpu, &len, 0, 0) != 0) printf("hw.nope -> ENOENT as expected\n");
    printf("mach_absolute_time=%llu\n", (unsigned long long)mach_absolute_time());
    char buf[64];
    printf("fsgetpath -> %zd errno=%s\n", fsgetpath(buf, sizeof buf, 0, 0), strerror(errno));
    return 0;
}
