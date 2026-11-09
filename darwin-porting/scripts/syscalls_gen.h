/* syscalls_gen.h - generated from xnu xnu-12377.121.6 bsd/kern/syscalls.master. Do not edit. */
#ifndef DNT_SYSCALLS_GEN_H
#define DNT_SYSCALLS_GEN_H

#define DNT_SYSCALL_MAX 557

enum dnt_syscall {
    DNT_SYS_NOSYS = 0,
    DNT_SYS_EXIT = 1,
    DNT_SYS_FORK = 2,
    DNT_SYS_READ = 3,
    DNT_SYS_WRITE = 4,
    DNT_SYS_OPEN = 5,
    DNT_SYS_SYS_CLOSE = 6,
    DNT_SYS_WAIT4 = 7,
    DNT_SYS_ENOSYS = 8,
    DNT_SYS_LINK = 9,
    DNT_SYS_UNLINK = 10,
    DNT_SYS_ENOSYS_11 = 11,
    DNT_SYS_SYS_CHDIR = 12,
    DNT_SYS_SYS_FCHDIR = 13,
    DNT_SYS_MKNOD = 14,
    DNT_SYS_CHMOD = 15,
    DNT_SYS_CHOWN = 16,
    DNT_SYS_ENOSYS_17 = 17,
    DNT_SYS_GETFSSTAT = 18,
    DNT_SYS_ENOSYS_19 = 19,
    DNT_SYS_GETPID = 20,
    DNT_SYS_ENOSYS_21 = 21,
    DNT_SYS_ENOSYS_22 = 22,
    DNT_SYS_SETUID = 23,
    DNT_SYS_GETUID = 24,
    DNT_SYS_GETEUID = 25,
    DNT_SYS_PTRACE = 26,
#if SOCKETS
    DNT_SYS_RECVMSG = 27,  /* also: nosys */
#else
    DNT_SYS_RECVMSG_DISABLED = 27,
#endif
#if SOCKETS
    DNT_SYS_SENDMSG = 28,  /* also: nosys */
#else
    DNT_SYS_SENDMSG_DISABLED = 28,
#endif
#if SOCKETS
    DNT_SYS_RECVFROM = 29,  /* also: nosys */
#else
    DNT_SYS_RECVFROM_DISABLED = 29,
#endif
#if SOCKETS
    DNT_SYS_ACCEPT = 30,  /* also: nosys */
#else
    DNT_SYS_ACCEPT_DISABLED = 30,
#endif
#if SOCKETS
    DNT_SYS_GETPEERNAME = 31,  /* also: nosys */
#else
    DNT_SYS_GETPEERNAME_DISABLED = 31,
#endif
#if SOCKETS
    DNT_SYS_GETSOCKNAME = 32,  /* also: nosys */
#else
    DNT_SYS_GETSOCKNAME_DISABLED = 32,
#endif
    DNT_SYS_ACCESS = 33,
    DNT_SYS_CHFLAGS = 34,
    DNT_SYS_FCHFLAGS = 35,
    DNT_SYS_SYNC = 36,
    DNT_SYS_KILL = 37,
    DNT_SYS_SYS_CROSSARCH_TRAP = 38,
    DNT_SYS_GETPPID = 39,
    DNT_SYS_NOSYS_40 = 40,
    DNT_SYS_SYS_DUP = 41,
    DNT_SYS_PIPE = 42,
    DNT_SYS_GETEGID = 43,
    DNT_SYS_NOSYS_44 = 44,
    DNT_SYS_NOSYS_45 = 45,
    DNT_SYS_SIGACTION = 46,
    DNT_SYS_GETGID = 47,
    DNT_SYS_SIGPROCMASK = 48,
    DNT_SYS_GETLOGIN = 49,
    DNT_SYS_SETLOGIN = 50,
    DNT_SYS_ACCT = 51,
    DNT_SYS_SIGPENDING = 52,
    DNT_SYS_SIGALTSTACK = 53,
    DNT_SYS_IOCTL = 54,
    DNT_SYS_REBOOT = 55,
    DNT_SYS_REVOKE = 56,
    DNT_SYS_SYMLINK = 57,
    DNT_SYS_READLINK = 58,
    DNT_SYS_EXECVE = 59,
    DNT_SYS_UMASK = 60,
    DNT_SYS_CHROOT = 61,
    DNT_SYS_NOSYS_62 = 62,
    DNT_SYS_NOSYS_63 = 63,
    DNT_SYS_NOSYS_64 = 64,
    DNT_SYS_MSYNC = 65,
#if CONFIG_VFORK
    DNT_SYS_VFORK = 66,  /* also: nosys */
#else
    DNT_SYS_VFORK_DISABLED = 66,
#endif
    DNT_SYS_OSLOG_COPROC_REG = 67,
    DNT_SYS_OSLOG_COPROC = 68,
    DNT_SYS_NOSYS_69 = 69,
    DNT_SYS_NOSYS_70 = 70,
    DNT_SYS_NOSYS_71 = 71,
    DNT_SYS_NOSYS_72 = 72,
    DNT_SYS_MUNMAP = 73,
    DNT_SYS_MPROTECT = 74,
    DNT_SYS_MADVISE = 75,
    DNT_SYS_NOSYS_76 = 76,
    DNT_SYS_NOSYS_77 = 77,
    DNT_SYS_MINCORE = 78,
    DNT_SYS_GETGROUPS = 79,
    DNT_SYS_SETGROUPS = 80,
    DNT_SYS_GETPGRP = 81,
    DNT_SYS_SETPGID = 82,
    DNT_SYS_SETITIMER = 83,
    DNT_SYS_NOSYS_84 = 84,
    DNT_SYS_SWAPON = 85,
    DNT_SYS_GETITIMER = 86,
    DNT_SYS_NOSYS_87 = 87,
    DNT_SYS_NOSYS_88 = 88,
    DNT_SYS_SYS_GETDTABLESIZE = 89,
    DNT_SYS_SYS_DUP2 = 90,
    DNT_SYS_NOSYS_91 = 91,
    DNT_SYS_SYS_FCNTL = 92,
    DNT_SYS_SELECT = 93,
    DNT_SYS_NOSYS_94 = 94,
    DNT_SYS_FSYNC = 95,
    DNT_SYS_SETPRIORITY = 96,
#if SOCKETS
    DNT_SYS_SOCKET = 97,  /* also: nosys */
#else
    DNT_SYS_SOCKET_DISABLED = 97,
#endif
#if SOCKETS
    DNT_SYS_CONNECT = 98,  /* also: nosys */
#else
    DNT_SYS_CONNECT_DISABLED = 98,
#endif
    DNT_SYS_NOSYS_99 = 99,
    DNT_SYS_GETPRIORITY = 100,
    DNT_SYS_NOSYS_101 = 101,
    DNT_SYS_NOSYS_102 = 102,
    DNT_SYS_NOSYS_103 = 103,
#if SOCKETS
    DNT_SYS_BIND = 104,  /* also: nosys */
#else
    DNT_SYS_BIND_DISABLED = 104,
#endif
#if SOCKETS
    DNT_SYS_SETSOCKOPT = 105,  /* also: nosys */
#else
    DNT_SYS_SETSOCKOPT_DISABLED = 105,
#endif
#if SOCKETS
    DNT_SYS_LISTEN = 106,  /* also: nosys */
#else
    DNT_SYS_LISTEN_DISABLED = 106,
#endif
    DNT_SYS_NOSYS_107 = 107,
    DNT_SYS_NOSYS_108 = 108,
    DNT_SYS_NOSYS_109 = 109,
    DNT_SYS_NOSYS_110 = 110,
    DNT_SYS_SIGSUSPEND = 111,
    DNT_SYS_NOSYS_112 = 112,
#if SOCKETS
    DNT_SYS_NOSYS_113 = 113,  /* also: nosys */
#else
    DNT_SYS_NOSYS_113_DISABLED = 113,
#endif
#if SOCKETS
    DNT_SYS_NOSYS_114 = 114,  /* also: nosys */
#else
    DNT_SYS_NOSYS_114_DISABLED = 114,
#endif
    DNT_SYS_NOSYS_115 = 115,
    DNT_SYS_GETTIMEOFDAY = 116,
    DNT_SYS_GETRUSAGE = 117,
#if SOCKETS
    DNT_SYS_GETSOCKOPT = 118,  /* also: nosys */
#else
    DNT_SYS_GETSOCKOPT_DISABLED = 118,
#endif
    DNT_SYS_NOSYS_119 = 119,
    DNT_SYS_READV = 120,
    DNT_SYS_WRITEV = 121,
    DNT_SYS_SETTIMEOFDAY = 122,
    DNT_SYS_FCHOWN = 123,
    DNT_SYS_FCHMOD = 124,
    DNT_SYS_NOSYS_125 = 125,
    DNT_SYS_SETREUID = 126,
    DNT_SYS_SETREGID = 127,
    DNT_SYS_RENAME = 128,
    DNT_SYS_NOSYS_129 = 129,
    DNT_SYS_NOSYS_130 = 130,
    DNT_SYS_SYS_FLOCK = 131,
    DNT_SYS_MKFIFO = 132,
#if SOCKETS
    DNT_SYS_SENDTO = 133,  /* also: nosys */
#else
    DNT_SYS_SENDTO_DISABLED = 133,
#endif
#if SOCKETS
    DNT_SYS_SHUTDOWN = 134,  /* also: nosys */
#else
    DNT_SYS_SHUTDOWN_DISABLED = 134,
#endif
#if SOCKETS
    DNT_SYS_SOCKETPAIR = 135,  /* also: nosys */
#else
    DNT_SYS_SOCKETPAIR_DISABLED = 135,
#endif
    DNT_SYS_MKDIR = 136,
    DNT_SYS_RMDIR = 137,
    DNT_SYS_UTIMES = 138,
    DNT_SYS_FUTIMES = 139,
    DNT_SYS_ADJTIME = 140,
    DNT_SYS_NOSYS_141 = 141,
    DNT_SYS_GETHOSTUUID = 142,
    DNT_SYS_NOSYS_143 = 143,
    DNT_SYS_NOSYS_144 = 144,
    DNT_SYS_NOSYS_145 = 145,
    DNT_SYS_NOSYS_146 = 146,
    DNT_SYS_SETSID = 147,
    DNT_SYS_NOSYS_148 = 148,
    DNT_SYS_NOSYS_149 = 149,
    DNT_SYS_NOSYS_150 = 150,
    DNT_SYS_GETPGID = 151,
    DNT_SYS_SETPRIVEXEC = 152,
    DNT_SYS_PREAD = 153,
    DNT_SYS_PWRITE = 154,
#if NFSSERVER
    DNT_SYS_NFSSVC = 155,  /* also: nosys */
#else
    DNT_SYS_NFSSVC_DISABLED = 155,
#endif
    DNT_SYS_NOSYS_156 = 156,
    DNT_SYS_STATFS = 157,
    DNT_SYS_FSTATFS = 158,
    DNT_SYS_UNMOUNT = 159,
    DNT_SYS_NOSYS_160 = 160,
#if NFSSERVER
    DNT_SYS_GETFH = 161,  /* also: nosys */
#else
    DNT_SYS_GETFH_DISABLED = 161,
#endif
    DNT_SYS_NOSYS_162 = 162,
    DNT_SYS_NOSYS_163 = 163,
    DNT_SYS_FUNMOUNT = 164,
    DNT_SYS_QUOTACTL = 165,
    DNT_SYS_NOSYS_166 = 166,
    DNT_SYS_MOUNT = 167,
    DNT_SYS_NOSYS_168 = 168,
    DNT_SYS_CSOPS = 169,
    DNT_SYS_CSOPS_AUDITTOKEN = 170,
    DNT_SYS_NOSYS_171 = 171,
    DNT_SYS_NOSYS_172 = 172,
    DNT_SYS_WAITID = 173,
    DNT_SYS_NOSYS_174 = 174,
    DNT_SYS_NOSYS_175 = 175,
    DNT_SYS_NOSYS_176 = 176,
    DNT_SYS_KDEBUG_TYPEFILTER = 177,
    DNT_SYS_KDEBUG_TRACE_STRING = 178,
    DNT_SYS_KDEBUG_TRACE64 = 179,
    DNT_SYS_KDEBUG_TRACE = 180,
    DNT_SYS_SETGID = 181,
    DNT_SYS_SETEGID = 182,
    DNT_SYS_SETEUID = 183,
    DNT_SYS_SIGRETURN = 184,
    DNT_SYS_SYS_PANIC_WITH_DATA = 185,
    DNT_SYS_THREAD_SELFCOUNTS = 186,
    DNT_SYS_FDATASYNC = 187,
    DNT_SYS_STAT = 188,
    DNT_SYS_SYS_FSTAT = 189,
    DNT_SYS_LSTAT = 190,
    DNT_SYS_PATHCONF = 191,
    DNT_SYS_SYS_FPATHCONF = 192,
    DNT_SYS_NOSYS_193 = 193,
    DNT_SYS_GETRLIMIT = 194,
    DNT_SYS_SETRLIMIT = 195,
    DNT_SYS_GETDIRENTRIES = 196,
    DNT_SYS_MMAP = 197,
    DNT_SYS_NOSYS_198 = 198,
    DNT_SYS_LSEEK = 199,
    DNT_SYS_TRUNCATE = 200,
    DNT_SYS_FTRUNCATE = 201,
    DNT_SYS_SYSCTL = 202,
    DNT_SYS_MLOCK = 203,
    DNT_SYS_MUNLOCK = 204,
    DNT_SYS_UNDELETE = 205,
    DNT_SYS_NOSYS_206 = 206,
    DNT_SYS_NOSYS_207 = 207,
    DNT_SYS_NOSYS_208 = 208,
    DNT_SYS_NOSYS_209 = 209,
    DNT_SYS_NOSYS_210 = 210,
    DNT_SYS_NOSYS_211 = 211,
    DNT_SYS_NOSYS_212 = 212,
    DNT_SYS_NOSYS_213 = 213,
    DNT_SYS_NOSYS_214 = 214,
    DNT_SYS_NOSYS_215 = 215,
    DNT_SYS_OPEN_DPROTECTED_NP = 216,
    DNT_SYS_FSGETPATH_EXT = 217,
    DNT_SYS_OPENAT_DPROTECTED_NP = 218,
    DNT_SYS_NOSYS_219 = 219,
    DNT_SYS_GETATTRLIST = 220,
    DNT_SYS_SETATTRLIST = 221,
    DNT_SYS_GETDIRENTRIESATTR = 222,
    DNT_SYS_EXCHANGEDATA = 223,
    DNT_SYS_NOSYS_224 = 224,
    DNT_SYS_SEARCHFS = 225,
    DNT_SYS_DELETE = 226,
    DNT_SYS_COPYFILE = 227,
    DNT_SYS_FGETATTRLIST = 228,
    DNT_SYS_FSETATTRLIST = 229,
    DNT_SYS_POLL = 230,
    DNT_SYS_NOSYS_231 = 231,
    DNT_SYS_NOSYS_232 = 232,
    DNT_SYS_NOSYS_233 = 233,
    DNT_SYS_GETXATTR = 234,
    DNT_SYS_FGETXATTR = 235,
    DNT_SYS_SETXATTR = 236,
    DNT_SYS_FSETXATTR = 237,
    DNT_SYS_REMOVEXATTR = 238,
    DNT_SYS_FREMOVEXATTR = 239,
    DNT_SYS_LISTXATTR = 240,
    DNT_SYS_FLISTXATTR = 241,
    DNT_SYS_FSCTL = 242,
    DNT_SYS_INITGROUPS = 243,
    DNT_SYS_POSIX_SPAWN = 244,
    DNT_SYS_FFSCTL = 245,
    DNT_SYS_NOSYS_246 = 246,
    DNT_SYS_NOSYS_247 = 247,
#if NFSSERVER
    DNT_SYS_FHOPEN = 248,  /* also: nosys */
#else
    DNT_SYS_FHOPEN_DISABLED = 248,
#endif
    DNT_SYS_NOSYS_249 = 249,
    DNT_SYS_MINHERIT = 250,
#if SYSV_SEM
    DNT_SYS_SEMSYS = 251,  /* also: nosys */
#else
    DNT_SYS_SEMSYS_DISABLED = 251,
#endif
#if SYSV_MSG
    DNT_SYS_MSGSYS = 252,  /* also: nosys */
#else
    DNT_SYS_MSGSYS_DISABLED = 252,
#endif
#if SYSV_SHM
    DNT_SYS_SHMSYS = 253,  /* also: nosys */
#else
    DNT_SYS_SHMSYS_DISABLED = 253,
#endif
#if SYSV_SEM
    DNT_SYS_SEMCTL = 254,  /* also: nosys */
#else
    DNT_SYS_SEMCTL_DISABLED = 254,
#endif
#if SYSV_SEM
    DNT_SYS_SEMGET = 255,  /* also: nosys */
#else
    DNT_SYS_SEMGET_DISABLED = 255,
#endif
#if SYSV_SEM
    DNT_SYS_SEMOP = 256,  /* also: nosys */
#else
    DNT_SYS_SEMOP_DISABLED = 256,
#endif
#if SYSV_SEM
    DNT_SYS_NOSYS_257 = 257,  /* also: nosys */
#else
    DNT_SYS_NOSYS_257_DISABLED = 257,
#endif
#if SYSV_MSG
    DNT_SYS_MSGCTL = 258,  /* also: nosys */
#else
    DNT_SYS_MSGCTL_DISABLED = 258,
#endif
#if SYSV_MSG
    DNT_SYS_MSGGET = 259,  /* also: nosys */
#else
    DNT_SYS_MSGGET_DISABLED = 259,
#endif
#if SYSV_MSG
    DNT_SYS_MSGSND = 260,  /* also: nosys */
#else
    DNT_SYS_MSGSND_DISABLED = 260,
#endif
#if SYSV_MSG
    DNT_SYS_MSGRCV = 261,  /* also: nosys */
#else
    DNT_SYS_MSGRCV_DISABLED = 261,
#endif
#if SYSV_SHM
    DNT_SYS_SHMAT = 262,  /* also: nosys */
#else
    DNT_SYS_SHMAT_DISABLED = 262,
#endif
#if SYSV_SHM
    DNT_SYS_SHMCTL = 263,  /* also: nosys */
#else
    DNT_SYS_SHMCTL_DISABLED = 263,
#endif
#if SYSV_SHM
    DNT_SYS_SHMDT = 264,  /* also: nosys */
#else
    DNT_SYS_SHMDT_DISABLED = 264,
#endif
#if SYSV_SHM
    DNT_SYS_SHMGET = 265,  /* also: nosys */
#else
    DNT_SYS_SHMGET_DISABLED = 265,
#endif
    DNT_SYS_SHM_OPEN = 266,
    DNT_SYS_SHM_UNLINK = 267,
    DNT_SYS_SEM_OPEN = 268,
    DNT_SYS_SEM_CLOSE = 269,
    DNT_SYS_SEM_UNLINK = 270,
    DNT_SYS_SEM_WAIT = 271,
    DNT_SYS_SEM_TRYWAIT = 272,
    DNT_SYS_SEM_POST = 273,
    DNT_SYS_SYS_SYSCTLBYNAME = 274,
    DNT_SYS_ENOSYS_275 = 275,
    DNT_SYS_ENOSYS_276 = 276,
    DNT_SYS_OPEN_EXTENDED = 277,
    DNT_SYS_UMASK_EXTENDED = 278,
    DNT_SYS_STAT_EXTENDED = 279,
    DNT_SYS_LSTAT_EXTENDED = 280,
    DNT_SYS_SYS_FSTAT_EXTENDED = 281,
    DNT_SYS_CHMOD_EXTENDED = 282,
    DNT_SYS_FCHMOD_EXTENDED = 283,
    DNT_SYS_ACCESS_EXTENDED = 284,
    DNT_SYS_SYS_SETTID = 285,
    DNT_SYS_GETTID = 286,
    DNT_SYS_SETSGROUPS = 287,
    DNT_SYS_GETSGROUPS = 288,
    DNT_SYS_SETWGROUPS = 289,
    DNT_SYS_GETWGROUPS = 290,
    DNT_SYS_MKFIFO_EXTENDED = 291,
    DNT_SYS_MKDIR_EXTENDED = 292,
#if CONFIG_EXT_RESOLVER
    DNT_SYS_IDENTITYSVC = 293,  /* also: nosys */
#else
    DNT_SYS_IDENTITYSVC_DISABLED = 293,
#endif
    DNT_SYS_SHARED_REGION_CHECK_NP = 294,
    DNT_SYS_NOSYS_295 = 295,
    DNT_SYS_VM_PRESSURE_MONITOR = 296,
#if PSYNCH
    DNT_SYS_PSYNCH_RW_LONGRDLOCK = 297,  /* also: nosys */
#else
    DNT_SYS_PSYNCH_RW_LONGRDLOCK_DISABLED = 297,
#endif
#if PSYNCH
    DNT_SYS_PSYNCH_RW_YIELDWRLOCK = 298,  /* also: nosys */
#else
    DNT_SYS_PSYNCH_RW_YIELDWRLOCK_DISABLED = 298,
#endif
#if PSYNCH
    DNT_SYS_PSYNCH_RW_DOWNGRADE = 299,  /* also: enosys */
#else
    DNT_SYS_PSYNCH_RW_DOWNGRADE_DISABLED = 299,
#endif
#if PSYNCH
    DNT_SYS_PSYNCH_RW_UPGRADE = 300,  /* also: enosys */
#else
    DNT_SYS_PSYNCH_RW_UPGRADE_DISABLED = 300,
#endif
#if PSYNCH
    DNT_SYS_PSYNCH_MUTEXWAIT = 301,  /* also: nosys */
#else
    DNT_SYS_PSYNCH_MUTEXWAIT_DISABLED = 301,
#endif
#if PSYNCH
    DNT_SYS_PSYNCH_MUTEXDROP = 302,  /* also: nosys */
#else
    DNT_SYS_PSYNCH_MUTEXDROP_DISABLED = 302,
#endif
#if PSYNCH
    DNT_SYS_PSYNCH_CVBROAD = 303,  /* also: nosys */
#else
    DNT_SYS_PSYNCH_CVBROAD_DISABLED = 303,
#endif
#if PSYNCH
    DNT_SYS_PSYNCH_CVSIGNAL = 304,  /* also: nosys */
#else
    DNT_SYS_PSYNCH_CVSIGNAL_DISABLED = 304,
#endif
#if PSYNCH
    DNT_SYS_PSYNCH_CVWAIT = 305,  /* also: nosys */
#else
    DNT_SYS_PSYNCH_CVWAIT_DISABLED = 305,
#endif
#if PSYNCH
    DNT_SYS_PSYNCH_RW_RDLOCK = 306,  /* also: nosys */
#else
    DNT_SYS_PSYNCH_RW_RDLOCK_DISABLED = 306,
#endif
#if PSYNCH
    DNT_SYS_PSYNCH_RW_WRLOCK = 307,  /* also: nosys */
#else
    DNT_SYS_PSYNCH_RW_WRLOCK_DISABLED = 307,
#endif
#if PSYNCH
    DNT_SYS_PSYNCH_RW_UNLOCK = 308,  /* also: nosys */
#else
    DNT_SYS_PSYNCH_RW_UNLOCK_DISABLED = 308,
#endif
#if PSYNCH
    DNT_SYS_PSYNCH_RW_UNLOCK2 = 309,  /* also: nosys */
#else
    DNT_SYS_PSYNCH_RW_UNLOCK2_DISABLED = 309,
#endif
    DNT_SYS_GETSID = 310,
    DNT_SYS_SYS_SETTID_WITH_PID = 311,
#if PSYNCH
    DNT_SYS_PSYNCH_CVCLRPREPOST = 312,  /* also: nosys */
#else
    DNT_SYS_PSYNCH_CVCLRPREPOST_DISABLED = 312,
#endif
    DNT_SYS_AIO_FSYNC = 313,
    DNT_SYS_AIO_RETURN = 314,
    DNT_SYS_AIO_SUSPEND = 315,
    DNT_SYS_AIO_CANCEL = 316,
    DNT_SYS_AIO_ERROR = 317,
    DNT_SYS_AIO_READ = 318,
    DNT_SYS_AIO_WRITE = 319,
    DNT_SYS_LIO_LISTIO = 320,
    DNT_SYS_NOSYS_321 = 321,
    DNT_SYS_IOPOLICYSYS = 322,
    DNT_SYS_PROCESS_POLICY = 323,
    DNT_SYS_MLOCKALL = 324,
    DNT_SYS_MUNLOCKALL = 325,
    DNT_SYS_NOSYS_326 = 326,
    DNT_SYS_ISSETUGID = 327,
    DNT_SYS___PTHREAD_KILL = 328,
    DNT_SYS___PTHREAD_SIGMASK = 329,
    DNT_SYS___SIGWAIT = 330,
    DNT_SYS___DISABLE_THREADSIGNAL = 331,
    DNT_SYS___PTHREAD_MARKCANCEL = 332,
    DNT_SYS___PTHREAD_CANCELED = 333,
    DNT_SYS___SEMWAIT_SIGNAL = 334,
    DNT_SYS_NOSYS_335 = 335,
    DNT_SYS_PROC_INFO = 336,
#if SENDFILE
    DNT_SYS_SENDFILE = 337,  /* also: nosys */
#else
    DNT_SYS_SENDFILE_DISABLED = 337,
#endif
    DNT_SYS_STAT64 = 338,
    DNT_SYS_SYS_FSTAT64 = 339,
    DNT_SYS_LSTAT64 = 340,
    DNT_SYS_STAT64_EXTENDED = 341,
    DNT_SYS_LSTAT64_EXTENDED = 342,
    DNT_SYS_SYS_FSTAT64_EXTENDED = 343,
    DNT_SYS_GETDIRENTRIES64 = 344,
    DNT_SYS_STATFS64 = 345,
    DNT_SYS_FSTATFS64 = 346,
    DNT_SYS_GETFSSTAT64 = 347,
    DNT_SYS___PTHREAD_CHDIR = 348,
    DNT_SYS___PTHREAD_FCHDIR = 349,
    DNT_SYS_AUDIT = 350,
    DNT_SYS_AUDITON = 351,
    DNT_SYS_NOSYS_352 = 352,
    DNT_SYS_GETAUID = 353,
    DNT_SYS_SETAUID = 354,
    DNT_SYS_NOSYS_355 = 355,
    DNT_SYS_NOSYS_356 = 356,
    DNT_SYS_GETAUDIT_ADDR = 357,
    DNT_SYS_SETAUDIT_ADDR = 358,
    DNT_SYS_AUDITCTL = 359,
    DNT_SYS_BSDTHREAD_CREATE = 360,
    DNT_SYS_BSDTHREAD_TERMINATE = 361,
    DNT_SYS_KQUEUE = 362,
    DNT_SYS_KEVENT = 363,
    DNT_SYS_LCHOWN = 364,
    DNT_SYS_NOSYS_365 = 365,
    DNT_SYS_BSDTHREAD_REGISTER = 366,
    DNT_SYS_WORKQ_OPEN = 367,
    DNT_SYS_WORKQ_KERNRETURN = 368,
    DNT_SYS_KEVENT64 = 369,
    DNT_SYS_NOSYS_370 = 370,
    DNT_SYS_NOSYS_371 = 371,
    DNT_SYS_THREAD_SELFID = 372,
    DNT_SYS_LEDGER = 373,
    DNT_SYS_KEVENT_QOS = 374,
    DNT_SYS_KEVENT_ID = 375,
    DNT_SYS_NOSYS_376 = 376,
    DNT_SYS_NOSYS_377 = 377,
    DNT_SYS_NOSYS_378 = 378,
    DNT_SYS_NOSYS_379 = 379,
    DNT_SYS___MAC_EXECVE = 380,
#if CONFIG_MACF
    DNT_SYS___MAC_SYSCALL = 381,  /* also: enosys */
#else
    DNT_SYS___MAC_SYSCALL_DISABLED = 381,
#endif
#if CONFIG_MACF
    DNT_SYS___MAC_GET_FILE = 382,  /* also: nosys */
#else
    DNT_SYS___MAC_GET_FILE_DISABLED = 382,
#endif
#if CONFIG_MACF
    DNT_SYS___MAC_SET_FILE = 383,  /* also: nosys */
#else
    DNT_SYS___MAC_SET_FILE_DISABLED = 383,
#endif
#if CONFIG_MACF
    DNT_SYS___MAC_GET_LINK = 384,  /* also: nosys */
#else
    DNT_SYS___MAC_GET_LINK_DISABLED = 384,
#endif
#if CONFIG_MACF
    DNT_SYS___MAC_SET_LINK = 385,  /* also: nosys */
#else
    DNT_SYS___MAC_SET_LINK_DISABLED = 385,
#endif
#if CONFIG_MACF
    DNT_SYS___MAC_GET_PROC = 386,  /* also: nosys */
#else
    DNT_SYS___MAC_GET_PROC_DISABLED = 386,
#endif
#if CONFIG_MACF
    DNT_SYS___MAC_SET_PROC = 387,  /* also: nosys */
#else
    DNT_SYS___MAC_SET_PROC_DISABLED = 387,
#endif
#if CONFIG_MACF
    DNT_SYS___MAC_GET_FD = 388,  /* also: nosys */
#else
    DNT_SYS___MAC_GET_FD_DISABLED = 388,
#endif
#if CONFIG_MACF
    DNT_SYS___MAC_SET_FD = 389,  /* also: nosys */
#else
    DNT_SYS___MAC_SET_FD_DISABLED = 389,
#endif
#if CONFIG_MACF
    DNT_SYS___MAC_GET_PID = 390,  /* also: nosys */
#else
    DNT_SYS___MAC_GET_PID_DISABLED = 390,
#endif
    DNT_SYS_ENOSYS_391 = 391,
    DNT_SYS_ENOSYS_392 = 392,
    DNT_SYS_ENOSYS_393 = 393,
    DNT_SYS_PSELECT = 394,
    DNT_SYS_PSELECT_NOCANCEL = 395,
    DNT_SYS_READ_NOCANCEL = 396,
    DNT_SYS_WRITE_NOCANCEL = 397,
    DNT_SYS_OPEN_NOCANCEL = 398,
    DNT_SYS_SYS_CLOSE_NOCANCEL = 399,
    DNT_SYS_WAIT4_NOCANCEL = 400,
#if SOCKETS
    DNT_SYS_RECVMSG_NOCANCEL = 401,  /* also: nosys */
#else
    DNT_SYS_RECVMSG_NOCANCEL_DISABLED = 401,
#endif
#if SOCKETS
    DNT_SYS_SENDMSG_NOCANCEL = 402,  /* also: nosys */
#else
    DNT_SYS_SENDMSG_NOCANCEL_DISABLED = 402,
#endif
#if SOCKETS
    DNT_SYS_RECVFROM_NOCANCEL = 403,  /* also: nosys */
#else
    DNT_SYS_RECVFROM_NOCANCEL_DISABLED = 403,
#endif
#if SOCKETS
    DNT_SYS_ACCEPT_NOCANCEL = 404,  /* also: nosys */
#else
    DNT_SYS_ACCEPT_NOCANCEL_DISABLED = 404,
#endif
    DNT_SYS_MSYNC_NOCANCEL = 405,
    DNT_SYS_SYS_FCNTL_NOCANCEL = 406,
    DNT_SYS_SELECT_NOCANCEL = 407,
    DNT_SYS_FSYNC_NOCANCEL = 408,
#if SOCKETS
    DNT_SYS_CONNECT_NOCANCEL = 409,  /* also: nosys */
#else
    DNT_SYS_CONNECT_NOCANCEL_DISABLED = 409,
#endif
    DNT_SYS_SIGSUSPEND_NOCANCEL = 410,
    DNT_SYS_READV_NOCANCEL = 411,
    DNT_SYS_WRITEV_NOCANCEL = 412,
#if SOCKETS
    DNT_SYS_SENDTO_NOCANCEL = 413,  /* also: nosys */
#else
    DNT_SYS_SENDTO_NOCANCEL_DISABLED = 413,
#endif
    DNT_SYS_PREAD_NOCANCEL = 414,
    DNT_SYS_PWRITE_NOCANCEL = 415,
    DNT_SYS_WAITID_NOCANCEL = 416,
    DNT_SYS_POLL_NOCANCEL = 417,
#if SYSV_MSG
    DNT_SYS_MSGSND_NOCANCEL = 418,  /* also: nosys */
#else
    DNT_SYS_MSGSND_NOCANCEL_DISABLED = 418,
#endif
#if SYSV_MSG
    DNT_SYS_MSGRCV_NOCANCEL = 419,  /* also: nosys */
#else
    DNT_SYS_MSGRCV_NOCANCEL_DISABLED = 419,
#endif
    DNT_SYS_SEM_WAIT_NOCANCEL = 420,
    DNT_SYS_AIO_SUSPEND_NOCANCEL = 421,
    DNT_SYS___SIGWAIT_NOCANCEL = 422,
    DNT_SYS___SEMWAIT_SIGNAL_NOCANCEL = 423,
    DNT_SYS___MAC_MOUNT = 424,
#if CONFIG_MACF
    DNT_SYS___MAC_GET_MOUNT = 425,  /* also: nosys */
#else
    DNT_SYS___MAC_GET_MOUNT_DISABLED = 425,
#endif
    DNT_SYS___MAC_GETFSSTAT = 426,
    DNT_SYS_FSGETPATH = 427,
    DNT_SYS_AUDIT_SESSION_SELF = 428,
    DNT_SYS_AUDIT_SESSION_JOIN = 429,
    DNT_SYS_SYS_FILEPORT_MAKEPORT = 430,
    DNT_SYS_SYS_FILEPORT_MAKEFD = 431,
    DNT_SYS_AUDIT_SESSION_PORT = 432,
    DNT_SYS_PID_SUSPEND = 433,
    DNT_SYS_PID_RESUME = 434,
#if CONFIG_EMBEDDED
    DNT_SYS_PID_HIBERNATE = 435,  /* also: nosys */
#else
    DNT_SYS_PID_HIBERNATE_DISABLED = 435,
#endif
#if SOCKETS
    DNT_SYS_PID_SHUTDOWN_SOCKETS = 436,  /* also: nosys */
#else
    DNT_SYS_PID_SHUTDOWN_SOCKETS_DISABLED = 436,
#endif
    DNT_SYS_NOSYS_437 = 437,
    DNT_SYS_NOSYS_438 = 438,
    DNT_SYS_KAS_INFO = 439,
#if CONFIG_MEMORYSTATUS
    DNT_SYS_MEMORYSTATUS_CONTROL = 440,  /* also: nosys */
#else
    DNT_SYS_MEMORYSTATUS_CONTROL_DISABLED = 440,
#endif
    DNT_SYS_GUARDED_OPEN_NP = 441,
    DNT_SYS_GUARDED_CLOSE_NP = 442,
    DNT_SYS_GUARDED_KQUEUE_NP = 443,
    DNT_SYS_CHANGE_FDGUARD_NP = 444,
    DNT_SYS_USRCTL = 445,
    DNT_SYS_PROC_RLIMIT_CONTROL = 446,
#if SOCKETS
    DNT_SYS_CONNECTX = 447,  /* also: nosys */
#else
    DNT_SYS_CONNECTX_DISABLED = 447,
#endif
#if SOCKETS
    DNT_SYS_DISCONNECTX = 448,  /* also: nosys */
#else
    DNT_SYS_DISCONNECTX_DISABLED = 448,
#endif
#if SOCKETS
    DNT_SYS_PEELOFF = 449,  /* also: nosys */
#else
    DNT_SYS_PEELOFF_DISABLED = 449,
#endif
#if SOCKETS
    DNT_SYS_SOCKET_DELEGATE = 450,  /* also: nosys */
#else
    DNT_SYS_SOCKET_DELEGATE_DISABLED = 450,
#endif
    DNT_SYS_TELEMETRY = 451,
#if CONFIG_PROC_UUID_POLICY
    DNT_SYS_PROC_UUID_POLICY = 452,  /* also: nosys */
#else
    DNT_SYS_PROC_UUID_POLICY_DISABLED = 452,
#endif
#if CONFIG_MEMORYSTATUS
    DNT_SYS_MEMORYSTATUS_GET_LEVEL = 453,  /* also: nosys */
#else
    DNT_SYS_MEMORYSTATUS_GET_LEVEL_DISABLED = 453,
#endif
    DNT_SYS_SYSTEM_OVERRIDE = 454,
    DNT_SYS_VFS_PURGE = 455,
    DNT_SYS_SFI_CTL = 456,
    DNT_SYS_SFI_PIDCTL = 457,
#if CONFIG_COALITIONS
    DNT_SYS_COALITION = 458,  /* also: enosys */
#else
    DNT_SYS_COALITION_DISABLED = 458,
#endif
#if CONFIG_COALITIONS
    DNT_SYS_COALITION_INFO = 459,  /* also: enosys */
#else
    DNT_SYS_COALITION_INFO_DISABLED = 459,
#endif
#if NECP
    DNT_SYS_NECP_MATCH_POLICY = 460,  /* also: nosys */
#else
    DNT_SYS_NECP_MATCH_POLICY_DISABLED = 460,
#endif
    DNT_SYS_GETATTRLISTBULK = 461,
    DNT_SYS_CLONEFILEAT = 462,
    DNT_SYS_OPENAT = 463,
    DNT_SYS_OPENAT_NOCANCEL = 464,
    DNT_SYS_RENAMEAT = 465,
    DNT_SYS_FACCESSAT = 466,
    DNT_SYS_FCHMODAT = 467,
    DNT_SYS_FCHOWNAT = 468,
    DNT_SYS_FSTATAT = 469,
    DNT_SYS_FSTATAT64 = 470,
    DNT_SYS_LINKAT = 471,
    DNT_SYS_UNLINKAT = 472,
    DNT_SYS_READLINKAT = 473,
    DNT_SYS_SYMLINKAT = 474,
    DNT_SYS_MKDIRAT = 475,
    DNT_SYS_GETATTRLISTAT = 476,
    DNT_SYS_PROC_TRACE_LOG = 477,
    DNT_SYS_BSDTHREAD_CTL = 478,
    DNT_SYS_OPENBYID_NP = 479,
#if SOCKETS
    DNT_SYS_RECVMSG_X = 480,  /* also: nosys */
#else
    DNT_SYS_RECVMSG_X_DISABLED = 480,
#endif
#if SOCKETS
    DNT_SYS_SENDMSG_X = 481,  /* also: nosys */
#else
    DNT_SYS_SENDMSG_X_DISABLED = 481,
#endif
    DNT_SYS_THREAD_SELFUSAGE = 482,
#if CONFIG_CSR
    DNT_SYS_CSRCTL = 483,  /* also: enosys */
#else
    DNT_SYS_CSRCTL_DISABLED = 483,
#endif
    DNT_SYS_GUARDED_OPEN_DPROTECTED_NP = 484,
    DNT_SYS_GUARDED_WRITE_NP = 485,
    DNT_SYS_GUARDED_PWRITE_NP = 486,
    DNT_SYS_GUARDED_WRITEV_NP = 487,
    DNT_SYS_RENAMEATX_NP = 488,
#if CONFIG_CODE_DECRYPTION
    DNT_SYS_MREMAP_ENCRYPTED = 489,  /* also: enosys */
#else
    DNT_SYS_MREMAP_ENCRYPTED_DISABLED = 489,
#endif
#if NETWORKING
    DNT_SYS_NETAGENT_TRIGGER = 490,  /* also: nosys */
#else
    DNT_SYS_NETAGENT_TRIGGER_DISABLED = 490,
#endif
    DNT_SYS_STACK_SNAPSHOT_WITH_CONFIG = 491,
#if CONFIG_TELEMETRY
    DNT_SYS_MICROSTACKSHOT = 492,  /* also: enosys */
#else
    DNT_SYS_MICROSTACKSHOT_DISABLED = 492,
#endif
#if PGO
    DNT_SYS_GRAB_PGO_DATA = 493,  /* also: enosys */
#else
    DNT_SYS_GRAB_PGO_DATA_DISABLED = 493,
#endif
#if CONFIG_PERSONAS
    DNT_SYS_PERSONA = 494,  /* also: enosys */
#else
    DNT_SYS_PERSONA_DISABLED = 494,
#endif
    DNT_SYS_ENOSYS_495 = 495,
    DNT_SYS_MACH_EVENTLINK_SIGNAL = 496,
    DNT_SYS_MACH_EVENTLINK_WAIT_UNTIL = 497,
    DNT_SYS_MACH_EVENTLINK_SIGNAL_WAIT_UNTIL = 498,
    DNT_SYS_WORK_INTERVAL_CTL = 499,
    DNT_SYS_GETENTROPY = 500,
#if NECP
    DNT_SYS_NECP_OPEN = 501,  /* also: enosys */
#else
    DNT_SYS_NECP_OPEN_DISABLED = 501,
#endif
#if NECP
    DNT_SYS_NECP_CLIENT_ACTION = 502,  /* also: enosys */
#else
    DNT_SYS_NECP_CLIENT_ACTION_DISABLED = 502,
#endif
#if SKYWALK
    DNT_SYS___NEXUS_OPEN = 503,  /* also: enosys */
#else
    DNT_SYS___NEXUS_OPEN_DISABLED = 503,
#endif
#if SKYWALK
    DNT_SYS___NEXUS_REGISTER = 504,  /* also: enosys */
#else
    DNT_SYS___NEXUS_REGISTER_DISABLED = 504,
#endif
#if SKYWALK
    DNT_SYS___NEXUS_DEREGISTER = 505,  /* also: enosys */
#else
    DNT_SYS___NEXUS_DEREGISTER_DISABLED = 505,
#endif
#if SKYWALK
    DNT_SYS___NEXUS_CREATE = 506,  /* also: enosys */
#else
    DNT_SYS___NEXUS_CREATE_DISABLED = 506,
#endif
#if SKYWALK
    DNT_SYS___NEXUS_DESTROY = 507,  /* also: enosys */
#else
    DNT_SYS___NEXUS_DESTROY_DISABLED = 507,
#endif
#if SKYWALK
    DNT_SYS___NEXUS_GET_OPT = 508,  /* also: enosys */
#else
    DNT_SYS___NEXUS_GET_OPT_DISABLED = 508,
#endif
#if SKYWALK
    DNT_SYS___NEXUS_SET_OPT = 509,  /* also: enosys */
#else
    DNT_SYS___NEXUS_SET_OPT_DISABLED = 509,
#endif
#if SKYWALK
    DNT_SYS___CHANNEL_OPEN = 510,  /* also: enosys */
#else
    DNT_SYS___CHANNEL_OPEN_DISABLED = 510,
#endif
#if SKYWALK
    DNT_SYS___CHANNEL_GET_INFO = 511,  /* also: enosys */
#else
    DNT_SYS___CHANNEL_GET_INFO_DISABLED = 511,
#endif
#if SKYWALK
    DNT_SYS___CHANNEL_SYNC = 512,  /* also: enosys */
#else
    DNT_SYS___CHANNEL_SYNC_DISABLED = 512,
#endif
#if SKYWALK
    DNT_SYS___CHANNEL_GET_OPT = 513,  /* also: enosys */
#else
    DNT_SYS___CHANNEL_GET_OPT_DISABLED = 513,
#endif
#if SKYWALK
    DNT_SYS___CHANNEL_SET_OPT = 514,  /* also: enosys */
#else
    DNT_SYS___CHANNEL_SET_OPT_DISABLED = 514,
#endif
    DNT_SYS_SYS_ULOCK_WAIT = 515,
    DNT_SYS_SYS_ULOCK_WAKE = 516,
    DNT_SYS_FCLONEFILEAT = 517,
    DNT_SYS_FS_SNAPSHOT = 518,
    DNT_SYS_ENOSYS_519 = 519,
    DNT_SYS_TERMINATE_WITH_PAYLOAD = 520,
    DNT_SYS_ABORT_WITH_PAYLOAD = 521,
#if NECP
    DNT_SYS_NECP_SESSION_OPEN = 522,  /* also: enosys */
#else
    DNT_SYS_NECP_SESSION_OPEN_DISABLED = 522,
#endif
#if NECP
    DNT_SYS_NECP_SESSION_ACTION = 523,  /* also: enosys */
#else
    DNT_SYS_NECP_SESSION_ACTION_DISABLED = 523,
#endif
    DNT_SYS_SETATTRLISTAT = 524,
    DNT_SYS_NET_QOS_GUIDELINE = 525,
    DNT_SYS_FMOUNT = 526,
    DNT_SYS_NTP_ADJTIME = 527,
    DNT_SYS_NTP_GETTIME = 528,
    DNT_SYS_OS_FAULT_WITH_PAYLOAD = 529,
    DNT_SYS_KQUEUE_WORKLOOP_CTL = 530,
    DNT_SYS___MACH_BRIDGE_REMOTE_TIME = 531,
#if CONFIG_COALITIONS
    DNT_SYS_COALITION_LEDGER = 532,  /* also: enosys */
#else
    DNT_SYS_COALITION_LEDGER_DISABLED = 532,
#endif
    DNT_SYS_LOG_DATA = 533,
    DNT_SYS_MEMORYSTATUS_AVAILABLE_MEMORY = 534,
    DNT_SYS_OBJC_BP_ASSIST_CFG_NP = 535,
    DNT_SYS_SHARED_REGION_MAP_AND_SLIDE_2_NP = 536,
    DNT_SYS_PIVOT_ROOT = 537,
    DNT_SYS_TASK_INSPECT_FOR_PID = 538,
    DNT_SYS_TASK_READ_FOR_PID = 539,
    DNT_SYS_SYS_PREADV = 540,
    DNT_SYS_SYS_PWRITEV = 541,
    DNT_SYS_SYS_PREADV_NOCANCEL = 542,
    DNT_SYS_SYS_PWRITEV_NOCANCEL = 543,
    DNT_SYS_SYS_ULOCK_WAIT2 = 544,
    DNT_SYS_PROC_INFO_EXTENDED_ID = 545,
#if SOCKETS
    DNT_SYS_TRACKER_ACTION = 546,  /* also: nosys */
#else
    DNT_SYS_TRACKER_ACTION_DISABLED = 546,
#endif
    DNT_SYS_DEBUG_SYSCALL_REJECT = 547,
    DNT_SYS_SYS_DEBUG_SYSCALL_REJECT_CONFIG = 548,
    DNT_SYS_GRAFTDMG = 549,
    DNT_SYS_MAP_WITH_LINKING_NP = 550,
    DNT_SYS_FREADLINK = 551,
    DNT_SYS_SYS_RECORD_SYSTEM_EVENT = 552,
    DNT_SYS_MKFIFOAT = 553,
    DNT_SYS_MKNODAT = 554,
    DNT_SYS_UNGRAFTDMG = 555,
#if CONFIG_COALITIONS
    DNT_SYS_SYS_COALITION_POLICY_SET = 556,  /* also: enosys */
#else
    DNT_SYS_SYS_COALITION_POLICY_SET_DISABLED = 556,
#endif
#if CONFIG_COALITIONS
    DNT_SYS_SYS_COALITION_POLICY_GET = 557,  /* also: enosys */
#else
    DNT_SYS_SYS_COALITION_POLICY_GET_DISABLED = 557,
#endif
};

/* one name per number; aliases are comments only */
static const char *const dnt_syscall_names[DNT_SYSCALL_MAX + 1] = {
    [0] = "nosys",
    [1] = "exit",
    [2] = "fork",
    [3] = "read",
    [4] = "write",
    [5] = "open",
    [6] = "sys_close",
    [7] = "wait4",
    [8] = "enosys",
    [9] = "link",
    [10] = "unlink",
    [11] = "enosys",
    [12] = "sys_chdir",
    [13] = "sys_fchdir",
    [14] = "mknod",
    [15] = "chmod",
    [16] = "chown",
    [17] = "enosys",
    [18] = "getfsstat",
    [19] = "enosys",
    [20] = "getpid",
    [21] = "enosys",
    [22] = "enosys",
    [23] = "setuid",
    [24] = "getuid",
    [25] = "geteuid",
    [26] = "ptrace",
    [27] = "recvmsg",
    [28] = "sendmsg",
    [29] = "recvfrom",
    [30] = "accept",
    [31] = "getpeername",
    [32] = "getsockname",
    [33] = "access",
    [34] = "chflags",
    [35] = "fchflags",
    [36] = "sync",
    [37] = "kill",
    [38] = "sys_crossarch_trap",
    [39] = "getppid",
    [40] = "nosys",
    [41] = "sys_dup",
    [42] = "pipe",
    [43] = "getegid",
    [44] = "nosys",
    [45] = "nosys",
    [46] = "sigaction",
    [47] = "getgid",
    [48] = "sigprocmask",
    [49] = "getlogin",
    [50] = "setlogin",
    [51] = "acct",
    [52] = "sigpending",
    [53] = "sigaltstack",
    [54] = "ioctl",
    [55] = "reboot",
    [56] = "revoke",
    [57] = "symlink",
    [58] = "readlink",
    [59] = "execve",
    [60] = "umask",
    [61] = "chroot",
    [62] = "nosys",
    [63] = "nosys",
    [64] = "nosys",
    [65] = "msync",
    [66] = "vfork",
    [67] = "oslog_coproc_reg",
    [68] = "oslog_coproc",
    [69] = "nosys",
    [70] = "nosys",
    [71] = "nosys",
    [72] = "nosys",
    [73] = "munmap",
    [74] = "mprotect",
    [75] = "madvise",
    [76] = "nosys",
    [77] = "nosys",
    [78] = "mincore",
    [79] = "getgroups",
    [80] = "setgroups",
    [81] = "getpgrp",
    [82] = "setpgid",
    [83] = "setitimer",
    [84] = "nosys",
    [85] = "swapon",
    [86] = "getitimer",
    [87] = "nosys",
    [88] = "nosys",
    [89] = "sys_getdtablesize",
    [90] = "sys_dup2",
    [91] = "nosys",
    [92] = "sys_fcntl",
    [93] = "select",
    [94] = "nosys",
    [95] = "fsync",
    [96] = "setpriority",
    [97] = "socket",
    [98] = "connect",
    [99] = "nosys",
    [100] = "getpriority",
    [101] = "nosys",
    [102] = "nosys",
    [103] = "nosys",
    [104] = "bind",
    [105] = "setsockopt",
    [106] = "listen",
    [107] = "nosys",
    [108] = "nosys",
    [109] = "nosys",
    [110] = "nosys",
    [111] = "sigsuspend",
    [112] = "nosys",
    [113] = "nosys",
    [114] = "nosys",
    [115] = "nosys",
    [116] = "gettimeofday",
    [117] = "getrusage",
    [118] = "getsockopt",
    [119] = "nosys",
    [120] = "readv",
    [121] = "writev",
    [122] = "settimeofday",
    [123] = "fchown",
    [124] = "fchmod",
    [125] = "nosys",
    [126] = "setreuid",
    [127] = "setregid",
    [128] = "rename",
    [129] = "nosys",
    [130] = "nosys",
    [131] = "sys_flock",
    [132] = "mkfifo",
    [133] = "sendto",
    [134] = "shutdown",
    [135] = "socketpair",
    [136] = "mkdir",
    [137] = "rmdir",
    [138] = "utimes",
    [139] = "futimes",
    [140] = "adjtime",
    [141] = "nosys",
    [142] = "gethostuuid",
    [143] = "nosys",
    [144] = "nosys",
    [145] = "nosys",
    [146] = "nosys",
    [147] = "setsid",
    [148] = "nosys",
    [149] = "nosys",
    [150] = "nosys",
    [151] = "getpgid",
    [152] = "setprivexec",
    [153] = "pread",
    [154] = "pwrite",
    [155] = "nfssvc",
    [156] = "nosys",
    [157] = "statfs",
    [158] = "fstatfs",
    [159] = "unmount",
    [160] = "nosys",
    [161] = "getfh",
    [162] = "nosys",
    [163] = "nosys",
    [164] = "funmount",
    [165] = "quotactl",
    [166] = "nosys",
    [167] = "mount",
    [168] = "nosys",
    [169] = "csops",
    [170] = "csops_audittoken",
    [171] = "nosys",
    [172] = "nosys",
    [173] = "waitid",
    [174] = "nosys",
    [175] = "nosys",
    [176] = "nosys",
    [177] = "kdebug_typefilter",
    [178] = "kdebug_trace_string",
    [179] = "kdebug_trace64",
    [180] = "kdebug_trace",
    [181] = "setgid",
    [182] = "setegid",
    [183] = "seteuid",
    [184] = "sigreturn",
    [185] = "sys_panic_with_data",
    [186] = "thread_selfcounts",
    [187] = "fdatasync",
    [188] = "stat",
    [189] = "sys_fstat",
    [190] = "lstat",
    [191] = "pathconf",
    [192] = "sys_fpathconf",
    [193] = "nosys",
    [194] = "getrlimit",
    [195] = "setrlimit",
    [196] = "getdirentries",
    [197] = "mmap",
    [198] = "nosys",
    [199] = "lseek",
    [200] = "truncate",
    [201] = "ftruncate",
    [202] = "sysctl",
    [203] = "mlock",
    [204] = "munlock",
    [205] = "undelete",
    [206] = "nosys",
    [207] = "nosys",
    [208] = "nosys",
    [209] = "nosys",
    [210] = "nosys",
    [211] = "nosys",
    [212] = "nosys",
    [213] = "nosys",
    [214] = "nosys",
    [215] = "nosys",
    [216] = "open_dprotected_np",
    [217] = "fsgetpath_ext",
    [218] = "openat_dprotected_np",
    [219] = "nosys",
    [220] = "getattrlist",
    [221] = "setattrlist",
    [222] = "getdirentriesattr",
    [223] = "exchangedata",
    [224] = "nosys",
    [225] = "searchfs",
    [226] = "delete",
    [227] = "copyfile",
    [228] = "fgetattrlist",
    [229] = "fsetattrlist",
    [230] = "poll",
    [231] = "nosys",
    [232] = "nosys",
    [233] = "nosys",
    [234] = "getxattr",
    [235] = "fgetxattr",
    [236] = "setxattr",
    [237] = "fsetxattr",
    [238] = "removexattr",
    [239] = "fremovexattr",
    [240] = "listxattr",
    [241] = "flistxattr",
    [242] = "fsctl",
    [243] = "initgroups",
    [244] = "posix_spawn",
    [245] = "ffsctl",
    [246] = "nosys",
    [247] = "nosys",
    [248] = "fhopen",
    [249] = "nosys",
    [250] = "minherit",
    [251] = "semsys",
    [252] = "msgsys",
    [253] = "shmsys",
    [254] = "semctl",
    [255] = "semget",
    [256] = "semop",
    [257] = "nosys",
    [258] = "msgctl",
    [259] = "msgget",
    [260] = "msgsnd",
    [261] = "msgrcv",
    [262] = "shmat",
    [263] = "shmctl",
    [264] = "shmdt",
    [265] = "shmget",
    [266] = "shm_open",
    [267] = "shm_unlink",
    [268] = "sem_open",
    [269] = "sem_close",
    [270] = "sem_unlink",
    [271] = "sem_wait",
    [272] = "sem_trywait",
    [273] = "sem_post",
    [274] = "sys_sysctlbyname",
    [275] = "enosys",
    [276] = "enosys",
    [277] = "open_extended",
    [278] = "umask_extended",
    [279] = "stat_extended",
    [280] = "lstat_extended",
    [281] = "sys_fstat_extended",
    [282] = "chmod_extended",
    [283] = "fchmod_extended",
    [284] = "access_extended",
    [285] = "sys_settid",
    [286] = "gettid",
    [287] = "setsgroups",
    [288] = "getsgroups",
    [289] = "setwgroups",
    [290] = "getwgroups",
    [291] = "mkfifo_extended",
    [292] = "mkdir_extended",
    [293] = "identitysvc",
    [294] = "shared_region_check_np",
    [295] = "nosys",
    [296] = "vm_pressure_monitor",
    [297] = "psynch_rw_longrdlock",
    [298] = "psynch_rw_yieldwrlock",
    [299] = "psynch_rw_downgrade",
    [300] = "psynch_rw_upgrade",
    [301] = "psynch_mutexwait",
    [302] = "psynch_mutexdrop",
    [303] = "psynch_cvbroad",
    [304] = "psynch_cvsignal",
    [305] = "psynch_cvwait",
    [306] = "psynch_rw_rdlock",
    [307] = "psynch_rw_wrlock",
    [308] = "psynch_rw_unlock",
    [309] = "psynch_rw_unlock2",
    [310] = "getsid",
    [311] = "sys_settid_with_pid",
    [312] = "psynch_cvclrprepost",
    [313] = "aio_fsync",
    [314] = "aio_return",
    [315] = "aio_suspend",
    [316] = "aio_cancel",
    [317] = "aio_error",
    [318] = "aio_read",
    [319] = "aio_write",
    [320] = "lio_listio",
    [321] = "nosys",
    [322] = "iopolicysys",
    [323] = "process_policy",
    [324] = "mlockall",
    [325] = "munlockall",
    [326] = "nosys",
    [327] = "issetugid",
    [328] = "__pthread_kill",
    [329] = "__pthread_sigmask",
    [330] = "__sigwait",
    [331] = "__disable_threadsignal",
    [332] = "__pthread_markcancel",
    [333] = "__pthread_canceled",
    [334] = "__semwait_signal",
    [335] = "nosys",
    [336] = "proc_info",
    [337] = "sendfile",
    [338] = "stat64",
    [339] = "sys_fstat64",
    [340] = "lstat64",
    [341] = "stat64_extended",
    [342] = "lstat64_extended",
    [343] = "sys_fstat64_extended",
    [344] = "getdirentries64",
    [345] = "statfs64",
    [346] = "fstatfs64",
    [347] = "getfsstat64",
    [348] = "__pthread_chdir",
    [349] = "__pthread_fchdir",
    [350] = "audit",
    [351] = "auditon",
    [352] = "nosys",
    [353] = "getauid",
    [354] = "setauid",
    [355] = "nosys",
    [356] = "nosys",
    [357] = "getaudit_addr",
    [358] = "setaudit_addr",
    [359] = "auditctl",
    [360] = "bsdthread_create",
    [361] = "bsdthread_terminate",
    [362] = "kqueue",
    [363] = "kevent",
    [364] = "lchown",
    [365] = "nosys",
    [366] = "bsdthread_register",
    [367] = "workq_open",
    [368] = "workq_kernreturn",
    [369] = "kevent64",
    [370] = "nosys",
    [371] = "nosys",
    [372] = "thread_selfid",
    [373] = "ledger",
    [374] = "kevent_qos",
    [375] = "kevent_id",
    [376] = "nosys",
    [377] = "nosys",
    [378] = "nosys",
    [379] = "nosys",
    [380] = "__mac_execve",
    [381] = "__mac_syscall",
    [382] = "__mac_get_file",
    [383] = "__mac_set_file",
    [384] = "__mac_get_link",
    [385] = "__mac_set_link",
    [386] = "__mac_get_proc",
    [387] = "__mac_set_proc",
    [388] = "__mac_get_fd",
    [389] = "__mac_set_fd",
    [390] = "__mac_get_pid",
    [391] = "enosys",
    [392] = "enosys",
    [393] = "enosys",
    [394] = "pselect",
    [395] = "pselect_nocancel",
    [396] = "read_nocancel",
    [397] = "write_nocancel",
    [398] = "open_nocancel",
    [399] = "sys_close_nocancel",
    [400] = "wait4_nocancel",
    [401] = "recvmsg_nocancel",
    [402] = "sendmsg_nocancel",
    [403] = "recvfrom_nocancel",
    [404] = "accept_nocancel",
    [405] = "msync_nocancel",
    [406] = "sys_fcntl_nocancel",
    [407] = "select_nocancel",
    [408] = "fsync_nocancel",
    [409] = "connect_nocancel",
    [410] = "sigsuspend_nocancel",
    [411] = "readv_nocancel",
    [412] = "writev_nocancel",
    [413] = "sendto_nocancel",
    [414] = "pread_nocancel",
    [415] = "pwrite_nocancel",
    [416] = "waitid_nocancel",
    [417] = "poll_nocancel",
    [418] = "msgsnd_nocancel",
    [419] = "msgrcv_nocancel",
    [420] = "sem_wait_nocancel",
    [421] = "aio_suspend_nocancel",
    [422] = "__sigwait_nocancel",
    [423] = "__semwait_signal_nocancel",
    [424] = "__mac_mount",
    [425] = "__mac_get_mount",
    [426] = "__mac_getfsstat",
    [427] = "fsgetpath",
    [428] = "audit_session_self",
    [429] = "audit_session_join",
    [430] = "sys_fileport_makeport",
    [431] = "sys_fileport_makefd",
    [432] = "audit_session_port",
    [433] = "pid_suspend",
    [434] = "pid_resume",
    [435] = "pid_hibernate",
    [436] = "pid_shutdown_sockets",
    [437] = "nosys",
    [438] = "nosys",
    [439] = "kas_info",
    [440] = "memorystatus_control",
    [441] = "guarded_open_np",
    [442] = "guarded_close_np",
    [443] = "guarded_kqueue_np",
    [444] = "change_fdguard_np",
    [445] = "usrctl",
    [446] = "proc_rlimit_control",
    [447] = "connectx",
    [448] = "disconnectx",
    [449] = "peeloff",
    [450] = "socket_delegate",
    [451] = "telemetry",
    [452] = "proc_uuid_policy",
    [453] = "memorystatus_get_level",
    [454] = "system_override",
    [455] = "vfs_purge",
    [456] = "sfi_ctl",
    [457] = "sfi_pidctl",
    [458] = "coalition",
    [459] = "coalition_info",
    [460] = "necp_match_policy",
    [461] = "getattrlistbulk",
    [462] = "clonefileat",
    [463] = "openat",
    [464] = "openat_nocancel",
    [465] = "renameat",
    [466] = "faccessat",
    [467] = "fchmodat",
    [468] = "fchownat",
    [469] = "fstatat",
    [470] = "fstatat64",
    [471] = "linkat",
    [472] = "unlinkat",
    [473] = "readlinkat",
    [474] = "symlinkat",
    [475] = "mkdirat",
    [476] = "getattrlistat",
    [477] = "proc_trace_log",
    [478] = "bsdthread_ctl",
    [479] = "openbyid_np",
    [480] = "recvmsg_x",
    [481] = "sendmsg_x",
    [482] = "thread_selfusage",
    [483] = "csrctl",
    [484] = "guarded_open_dprotected_np",
    [485] = "guarded_write_np",
    [486] = "guarded_pwrite_np",
    [487] = "guarded_writev_np",
    [488] = "renameatx_np",
    [489] = "mremap_encrypted",
    [490] = "netagent_trigger",
    [491] = "stack_snapshot_with_config",
    [492] = "microstackshot",
    [493] = "grab_pgo_data",
    [494] = "persona",
    [495] = "enosys",
    [496] = "mach_eventlink_signal",
    [497] = "mach_eventlink_wait_until",
    [498] = "mach_eventlink_signal_wait_until",
    [499] = "work_interval_ctl",
    [500] = "getentropy",
    [501] = "necp_open",
    [502] = "necp_client_action",
    [503] = "__nexus_open",
    [504] = "__nexus_register",
    [505] = "__nexus_deregister",
    [506] = "__nexus_create",
    [507] = "__nexus_destroy",
    [508] = "__nexus_get_opt",
    [509] = "__nexus_set_opt",
    [510] = "__channel_open",
    [511] = "__channel_get_info",
    [512] = "__channel_sync",
    [513] = "__channel_get_opt",
    [514] = "__channel_set_opt",
    [515] = "sys_ulock_wait",
    [516] = "sys_ulock_wake",
    [517] = "fclonefileat",
    [518] = "fs_snapshot",
    [519] = "enosys",
    [520] = "terminate_with_payload",
    [521] = "abort_with_payload",
    [522] = "necp_session_open",
    [523] = "necp_session_action",
    [524] = "setattrlistat",
    [525] = "net_qos_guideline",
    [526] = "fmount",
    [527] = "ntp_adjtime",
    [528] = "ntp_gettime",
    [529] = "os_fault_with_payload",
    [530] = "kqueue_workloop_ctl",
    [531] = "__mach_bridge_remote_time",
    [532] = "coalition_ledger",
    [533] = "log_data",
    [534] = "memorystatus_available_memory",
    [535] = "objc_bp_assist_cfg_np",
    [536] = "shared_region_map_and_slide_2_np",
    [537] = "pivot_root",
    [538] = "task_inspect_for_pid",
    [539] = "task_read_for_pid",
    [540] = "sys_preadv",
    [541] = "sys_pwritev",
    [542] = "sys_preadv_nocancel",
    [543] = "sys_pwritev_nocancel",
    [544] = "sys_ulock_wait2",
    [545] = "proc_info_extended_id",
    [546] = "tracker_action",
    [547] = "debug_syscall_reject",
    [548] = "sys_debug_syscall_reject_config",
    [549] = "graftdmg",
    [550] = "map_with_linking_np",
    [551] = "freadlink",
    [552] = "sys_record_system_event",
    [553] = "mkfifoat",
    [554] = "mknodat",
    [555] = "ungraftdmg",
    [556] = "sys_coalition_policy_set",
    [557] = "sys_coalition_policy_get",
};

#endif /* DNT_SYSCALLS_GEN_H */