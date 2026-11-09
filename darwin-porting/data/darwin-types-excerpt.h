/* vendored: xnu-11215.41.3 bsd/sys/_types.h + related, concatenated for reference only (APSL-2.0) */

/* ---- sys/_types.h ---- */
#ifndef _SYS__TYPES_H_
#define _SYS__TYPES_H_
#include <sys/cdefs.h>
#include <machine/_types.h>
#if defined(KERNEL)
#ifdef XNU_KERNEL_PRIVATE
#endif
#define USE_CLANG_TYPES 0
#else
#if defined(__has_feature) && __has_feature(modules)
#define USE_CLANG_TYPES 1
#else
#define USE_CLANG_TYPES 0
#endif
#endif
#if USE_CLANG_TYPES
#include <sys/_types/_null.h>
#endif
#if USE_CLANG_TYPES
#define __DARWIN_NULL NULL
#elif defined(__cplusplus)
#ifdef __GNUG__
#define __DARWIN_NULL __null
#else /* ! __GNUG__ */
#ifdef __LP64__
#define __DARWIN_NULL (0L)
#else /* !__LP64__ */
#define __DARWIN_NULL 0
#endif /* __LP64__ */
#endif /* __GNUG__ */
#else /* ! __cplusplus */
#define __DARWIN_NULL ((void *)0)
#endif
#if !defined(DRIVERKIT)
typedef __int64_t       __darwin_blkcnt_t;      /* total blocks */
typedef __int32_t       __darwin_blksize_t;     /* preferred block size */
typedef __int32_t       __darwin_dev_t;         /* dev_t */
typedef unsigned int    __darwin_fsblkcnt_t;    /* Used by statvfs and fstatvfs */
typedef unsigned int    __darwin_fsfilcnt_t;    /* Used by statvfs and fstatvfs */
typedef __uint32_t      __darwin_gid_t;         /* [???] process and group IDs */
typedef __uint32_t      __darwin_id_t;          /* [XSI] pid_t, uid_t, or gid_t*/
typedef __uint64_t      __darwin_ino64_t;       /* [???] Used for 64 bit inodes */
#if __DARWIN_64_BIT_INO_T
typedef __darwin_ino64_t __darwin_ino_t;        /* [???] Used for inodes */
#else /* !__DARWIN_64_BIT_INO_T */
typedef __uint32_t      __darwin_ino_t;         /* [???] Used for inodes */
#endif /* __DARWIN_64_BIT_INO_T */
typedef __darwin_natural_t __darwin_mach_port_name_t; /* Used by mach */
typedef __darwin_mach_port_name_t __darwin_mach_port_t; /* Used by mach */
typedef __uint16_t      __darwin_mode_t;        /* [???] Some file attributes */
typedef __int64_t       __darwin_off_t;         /* [???] Used for file sizes */
typedef __int32_t       __darwin_pid_t;         /* [???] process and group IDs */
typedef __uint32_t      __darwin_sigset_t;      /* [???] signal set */
typedef __int32_t       __darwin_suseconds_t;   /* [???] microseconds */
typedef __uint32_t      __darwin_uid_t;         /* [???] user IDs */
typedef __uint32_t      __darwin_useconds_t;    /* [???] microseconds */
#endif /* !defined(DRIVERKIT) */
typedef unsigned char   __darwin_uuid_t[16];
typedef char    __darwin_uuid_string_t[37];
#undef USE_CLANG_TYPES
#if !defined(KERNEL) && !defined(DRIVERKIT)
#include <sys/_pthread/_pthread_types.h>
#endif /* !defined(KERNEL) && !defined(DRIVERKIT) */
#if defined(__GNUC__) && (__GNUC__ == 3 && __GNUC_MINOR__ >= 5 || __GNUC__ > 3)
#define __offsetof(type, field) __builtin_offsetof(type, field)
#else /* !(gcc >= 3.5) */
#define __offsetof(type, field) ((size_t)(&((type *)0)->field))
#endif /* (gcc >= 3.5) */
#ifdef KERNEL
#include <sys/_types/_offsetof.h>
#endif /* KERNEL */
#endif  /* _SYS__TYPES_H_ */

/* ---- sys/_types/_mode_t.h ---- */
#ifndef _MODE_T
#define _MODE_T
#include <sys/_types.h> /* __darwin_mode_t */
typedef __darwin_mode_t         mode_t;
#endif  /* _MODE_T */

/* ---- sys/_types/_dev_t.h ---- */
#ifndef _DEV_T
#define _DEV_T
#include <sys/_types.h> /* __darwin_dev_t */
typedef __darwin_dev_t        dev_t;    /* device number */
#endif  /* _DEV_T */

/* ---- sys/_types/_ino_t.h ---- */
#ifndef _INO_T
#define _INO_T
#include <sys/_types.h> /* __darwin_ino_t */
typedef __darwin_ino_t          ino_t;          /* inode number */
#endif  /* _INO_T */

/* ---- sys/_types/_blkcnt_t.h ---- */
#ifndef _BLKCNT_T
#define _BLKCNT_T
#include <sys/_types.h> /* __darwin_blkcnt_t */
typedef __darwin_blkcnt_t        blkcnt_t;
#endif  /* _BLKCNT_T */

/* ---- sys/_types/_blksize_t.h ---- */
#ifndef _BLKSIZE_T
#define _BLKSIZE_T
#include <sys/_types.h> /* __darwin_blksize_t */
typedef __darwin_blksize_t        blksize_t;
#endif  /* _BLKSIZE_T */

/* ---- sys/_types/_off_t.h ---- */
#ifndef _OFF_T
#define _OFF_T
#include <sys/_types.h> /* __darwin_off_t */
typedef __darwin_off_t          off_t;
#endif  /* _OFF_T */

/* ---- sys/stat.h ---- */
#ifndef _SYS_STAT_H_
#define _SYS_STAT_H_
#include <sys/_types.h>
#include <sys/cdefs.h>
#ifdef KERNEL
#include <machine/types.h>
#else /* !KERNEL */
#include <Availability.h>
#endif /* KERNEL */
#include <sys/_types/_timespec.h>
#ifdef KERNEL
#include <sys/_types/_user64_timespec.h>
#include <sys/_types/_user32_timespec.h>
#endif /* KERNEL */
#include <sys/_types/_blkcnt_t.h>
#include <sys/_types/_blksize_t.h>
#include <sys/_types/_dev_t.h>                  /* device number */
#include <sys/_types/_ino_t.h>
#if !defined(_POSIX_C_SOURCE) || defined(_DARWIN_C_SOURCE)
#include <sys/_types/_ino64_t.h>
#endif /* !defined(_POSIX_C_SOURCE) || defined(_DARWIN_C_SOURCE) */
#include <sys/_types/_mode_t.h>
#include <sys/_types/_nlink_t.h>
#include <sys/_types/_uid_t.h>
#include <sys/_types/_gid_t.h>
#include <sys/_types/_off_t.h>
#include <sys/_types/_time_t.h>
#if !defined(_POSIX_C_SOURCE) || defined(_DARWIN_C_SOURCE)
struct ostat {
	__uint16_t      st_dev;         /* inode's device */
	ino_t           st_ino;         /* inode's number */
	mode_t          st_mode;        /* inode protection mode */
	nlink_t         st_nlink;       /* number of hard links */
	__uint16_t      st_uid;         /* user ID of the file's owner */
	__uint16_t      st_gid;         /* group ID of the file's group */
	__uint16_t      st_rdev;        /* device type */
	__int32_t       st_size;        /* file size, in bytes */
	struct  timespec st_atimespec;  /* time of last access */
	struct  timespec st_mtimespec;  /* time of last data modification */
	struct  timespec st_ctimespec;  /* time of last file status change */
	__int32_t       st_blksize;     /* optimal blocksize for I/O */
	__int32_t       st_blocks;      /* blocks allocated for file */
	__uint32_t      st_flags;       /* user defined flags for file */
	__uint32_t      st_gen;         /* file generation number */
};
#define __DARWIN_STRUCT_STAT64_TIMES \
	struct timespec st_atimespec;           /* time of last access */ \
	struct timespec st_mtimespec;           /* time of last data modification */ \
	struct timespec st_ctimespec;           /* time of last status change */ \
	struct timespec st_birthtimespec;       /* time of file creation(birth) */
#else /* (_POSIX_C_SOURCE && !_DARWIN_C_SOURCE) */
#define __DARWIN_STRUCT_STAT64_TIMES \
	time_t		st_atime;               /* [XSI] Time of last access */ \
	long		st_atimensec;           /* nsec of last access */ \
	time_t		st_mtime;               /* [XSI] Last data modification time */ \
	long		st_mtimensec;           /* last data modification nsec */ \
	time_t		st_ctime;               /* [XSI] Time of last status change */ \
	long		st_ctimensec;           /* nsec of last status change */ \
	time_t		st_birthtime;           /*  File creation time(birth)  */ \
	long		st_birthtimensec;       /* nsec of File creation time */
#endif /* (!_POSIX_C_SOURCE || _DARWIN_C_SOURCE) */
#define __DARWIN_STRUCT_STAT64 { \
	dev_t		st_dev;                 /* [XSI] ID of device containing file */ \
	mode_t		st_mode;                /* [XSI] Mode of file (see below) */ \
	nlink_t		st_nlink;               /* [XSI] Number of hard links */ \
	__darwin_ino64_t st_ino;                /* [XSI] File serial number */ \
	uid_t		st_uid;                 /* [XSI] User ID of the file */ \
	gid_t		st_gid;                 /* [XSI] Group ID of the file */ \
	dev_t		st_rdev;                /* [XSI] Device ID */ \
	__DARWIN_STRUCT_STAT64_TIMES \
	off_t		st_size;                /* [XSI] file size, in bytes */ \
	blkcnt_t	st_blocks;              /* [XSI] blocks allocated for file */ \
	blksize_t	st_blksize;             /* [XSI] optimal blocksize for I/O */ \
	__uint32_t	st_flags;               /* user defined flags for file */ \
	__uint32_t	st_gen;                 /* file generation number */ \
	__int32_t	st_lspare;              /* RESERVED: DO NOT USE! */ \
	__int64_t	st_qspare[2];           /* RESERVED: DO NOT USE! */ \
}
#if __DARWIN_64_BIT_INO_T
struct stat __DARWIN_STRUCT_STAT64;
#else /* !__DARWIN_64_BIT_INO_T */
struct stat {
	dev_t           st_dev;         /* [XSI] ID of device containing file */
	ino_t           st_ino;         /* [XSI] File serial number */
	mode_t          st_mode;        /* [XSI] Mode of file (see below) */
	nlink_t         st_nlink;       /* [XSI] Number of hard links */
	uid_t           st_uid;         /* [XSI] User ID of the file */
	gid_t           st_gid;         /* [XSI] Group ID of the file */
