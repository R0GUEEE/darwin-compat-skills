# Porting checklist

## ABI baseline (arm64 Darwin, iPhoneOS 16.5 SDK)

Derived with `abi_probe.py` from the SDK headers - not from memory. Regenerate
for another SDK and diff:

```bash
python3 scripts/abi_probe.py --sdk /opt/sdks-src/iPhoneOS16.5.sdk --json > abi.json
```

| item | size | notes |
|---|---|---|
| `struct stat` | 144 | `st_ino` @8, `st_mode` @4, `st_size` @96, `st_blksize` @112, `st_flags` @116 |
| `mode_t` | **2** | 16-bit. Assuming 4 shifts every field after `st_mode` |
| `dev_t` | 4 | `ino_t` 8, `blkcnt_t` 8, `blksize_t` 4, `off_t` 8 |
| `struct dirent` | 1048 | `d_ino` @0, `d_seekoff` @8, `d_namlen` @18, `d_type` @20 |
| `struct sigaction` | 16 | handler @0, mask @8; no `sa_restorer`, no `sa_sigaction` union at 0 |
| `struct timeval` / `timespec` | 16 | |
| `struct termios` | 72 | Linux differs (44 on aarch64) - do not memcpy |
| `struct sigset_t` | 4 | Linux is 128 bytes |
| `pthread_t` | 8 | a pointer, not a small integer |
| `struct sockaddr_storage` | 128 | same as Linux |

Anything that crosses the ABI (stat, dirent, ioctl payloads, pthread handles)
must be translated field by field. `memcpy` of a host struct is the single most
common source of "works until someone reads a file" bugs.

`d_namlen` is a 16-bit length; Linux's `d_reclen` / NUL-terminated `d_name`
does not translate, so `getdirentries` output must be re-packed with
`d_reclen = align(24 + namlen + 1)` to whatever the consumer expects.

## Call map and its acceptance test

| Darwin | Linux | test that proves it |
|---|---|---|
| `kqueue`/`kevent` | epoll (+ libkqueue) | file + socket + timer in one loop |
| `FSEvents` | inotify | rename inside watched dir |
| `IOKit` | libudev | enumerate + hotplug |
| `libproc` (`proc_pidinfo`) | `/proc/<pid>/*` | task list matches ps |
| `sysctlbyname` | `/proc/sys`, `sysconf` | hw.ncpu, hw.memsize |
| `mach_absolute_time` | `clock_gettime(CLOCK_UPTIME_RAW)` | monotonic across suspend policy stated |
| `os_log` | syslog/journald | message appears with correct level |
| `launchctl` | systemd unit / dbus | start, stop, restart |
| `Security.framework` | OpenSSL/GnuTLS | keychain item round-trip |
| `dispatch_*` | pthread pool + libdispatch | queue serialization under load |
| `getdirentries` | `getdents64` | ordering + reclen packing |
| `posix_spawn` | `posix_spawn` | env/arg passing, exit code |

## Exit criteria

1. Every mapped syscall has a test named in `COMPAT.md`.
2. `--help`, `--version`, exit codes, stderr text identical to the reference
   capture (record them in `tests/golden/`).
3. Filesystem semantics tested on the target's own layout (`/private/var`
   vs `/var`, case-insensitivity where relevant).
4. No `memcpy` between ABI structs (grep for it in review).
5. Tests run under ASan/UBSan where the platform allows.
6. `docs/DEVIATIONS.md` lists every difference, including "not implemented".

## Failure modes seen in practice

* **Link address used as mapped address.** Keep `link_base` (file offsets,
  `mach_header` addresses) and `image_base` (runtime) as separate values.
  Mixing them makes every PC-relative access land somewhere plausible but
  wrong.
* **`__PAGEZERO` rejected as impossible.** vmaddr 0, vmsize 4 GB, filesize 0.
  Skip it, never validate it as geometry.
* **Guest pointers unregistered** → EFAULT on every write. Loader must
  register each mapped region before code runs.
* **std fds as invalid handles** → `write(1, ...)` returns EBADF from the host.
* **`exit` through a host hook** → process dies before you can report the code
  or free the image. Handle it in the interpreter.
* **Fuzzing with a roomy buffer.** Fuzz with the buffer sized to exactly
  `max_mapped`; that is what surfaced 2^63 allocations, unsigned underflow in
  bounds checks, and segment ranges larger than the file.
