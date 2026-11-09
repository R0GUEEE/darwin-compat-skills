# Darwin vs Linux ABI, field by field

Derived with `abi_probe.py --sdk iPhoneOS16.5.sdk --target arm64-apple-ios14`
(see `darwin-porting/scripts/abi_probe.py`). Regenerate for any SDK:

```bash
python3 abi_probe.py --sdk /path/Foo.sdk --json > abi.json
```

## Scalar types (arm64 Darwin)

| type | Darwin | Linux aarch64 | consequence if assumed equal |
|---|---|---|---|
| `mode_t` | **2 bytes** | 4 | every field after `st_mode` shifts |
| `dev_t` | 4 | 8 | `st_dev`/`st_rdev` truncate or misalign |
| `ino_t` | 8 | 8 | - |
| `nlink_t` | 2 | 8 | |
| `off_t` | 8 | 8 | |
| `blkcnt_t` | 8 | 8 | |
| `blksize_t` | 4 | 4 | |
| `sigset_t` | **4** | 128 | signals silently not masked |
| `pthread_t` | **8 (pointer)** | 8 (pointer) | compare by value works, copying does not |
| `clock_t` | 8 | 8 | |
| `time_t` | 8 | 8 | |

## struct stat (Darwin, 64-bit inode variant, size 144)

| offset | field | width |
|---|---|---|
| 0 | `st_dev` | 4 |
| 4 | `st_mode` | 2 |
| 6 | `st_nlink` | 2 |
| 8 | `st_ino` | 8 |
| 16 | `st_uid` | 4 |
| 20 | `st_gid` | 4 |
| 24 | `st_rdev` | 4 |
| 32 | `st_atimespec` | 16 |
| 48 | `st_mtimespec` | 16 |
| 64 | `st_ctimespec` | 16 |
| 80 | `st_birthtimespec` | 16 |
| 96 | `st_size` | 8 |
| 104 | `st_blocks` | 8 |
| 112 | `st_blksize` | 4 |
| 116 | `st_flags` | 4 |
| 120 | `st_gen` | 4 |
| 124 | `st_lspare` | 4 |
| 128 | `st_qspare[2]` | 16 |

Linux aarch64 `struct stat` is 128 bytes with `st_mode` at 16 and `st_ino` at
8 — the layouts are not interchangeable in either direction. `st_flags` and
`st_birthtimespec` have no Linux equivalent; the shim writes 0 / mirrors ctime.

## struct dirent (Darwin, size 1048)

| offset | field | width | note |
|---|---|---|---|
| 0 | `d_ino` | 8 | |
| 8 | `d_seekoff` | 8 | cookie for `seekdir`, not present on Linux |
| 16 | `d_reclen` | 2 | record length including padding for `d_name` |
| 18 | `d_namlen` | 2 | name length, no NUL counted |
| 20 | `d_type` | 1 | DT_* values differ in numbering |
| 21 | `d_name[1024]` | | record padded so the next `d_reclen` is 8-aligned |

Linux `getdents64` gives `d_ino, d_off, d_reclen, d_type, d_name[NUL]` - you
must re-pack, and `d_reclen` must be 8-aligned to keep `d_ino` (a 64-bit
value) aligned on the next record. That alignment is the classic corruption.

## signal, termios, sockets

* `struct sigaction`: Darwin 16 bytes (handler @0, mask @8, flags @12); Linux
  has a 4-byte handler, a 128-byte mask and `sa_restorer`. Copy field by
  field; the mask alone is 32x larger.
* `struct termios`: Darwin 72 (cc[20]), Linux 44 or 60 depending on arch.
  ioctl payloads (`TCGETS`) therefore cannot be passed through, and Darwin's
  `VMIN/VTIME` indices differ from Linux's.
* `struct sockaddr_storage`: 128 on both. Socket options and `SO_*` values are
  mostly shared, but `TCP_NODELAY`-adjacent options and `NSLookupResults`
  differ; verify per option.

## sysctl MIB (from XNU bsd/sys/sysctl.h)

| name | MIB | mapped to |
|---|---|---|
| `kern.maxproc` | [1, 6] | fixed conservative constant, documented |
| `kern.boottime` | [1, 21] | `/proc/stat` btime |
| `kern.procargs2` | [1, 49] | `/proc/<pid>/cmdline` + `environ` |
| `hw.ncpu` | [6, 3] | `sysconf(_SC_NPROCESSORS_ONLN)` |
| `hw.physmem` | [6, 5] | `/proc/meminfo MemTotal` |
| `hw.memsize` | [6, 24] | same as physmem |
| `hw.pagesize` | [6, 7] | `sysconf(_SC_PAGESIZE)` |

Everything not in that table returns ENOENT from the shim. A missing entry in
the table is visible in `COMPAT.md`; a silently wrong value is not.
