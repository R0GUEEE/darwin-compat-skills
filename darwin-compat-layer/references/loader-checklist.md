# Loader acceptance checklist

Each item is a test with a binary that proves it. A loader without these is a
parser with a PC.

## Fixtures you can build here

```bash
sh /var/minis/skills/darwin-porting/scripts/fixtures/build_fixtures.sh /tmp/fix
```

| fixture | proves |
|---|---|
| `hello_arm64` | raw `svc #0x80` write + exit, no libSystem |
| `exit42_arm64` / `exit42_x86_64` | second architecture, exit code plumbing |
| `exit42_fat` | universal binary slice selection |
| `libd.dylib` + `used` | dylib import, lazy stubs, ordinal resolution |
| `libc_c.out` (needs an SDK) | chained fixups, real libSystem import table |

## dyld semantics as tests

1. **Image placement.** `__TEXT` at its link address (0x100000000 for a
   default arm64 link), or refuse with an error naming the address. A silent
   slide must fail a test, not produce a hang.
2. **`__PAGEZERO` skipped**, not mapped, not validated. A loader that rejects
   it rejects every real Darwin executable.
3. **Segments mapped with Mach-O permissions**: `__TEXT` r-x, `__DATA` rw-,
   `__LINKEDIT` r--. W^X violations on newer kernels present as SIGBUS on
   first write to `__DATA`.
4. **Entry** = `__TEXT.vmaddr + LC_MAIN.entryoff`. For `LC_UNIXTHREAD`, take
   the PC from the thread state instead.
5. **Std fds** are the host's 0/1/2. `write(1, "x", 1)` must reach your
   terminal, not return EBADF.
6. **Guest pointer registration.** Every mapped range is addressable through
   the syscall layer; a write to a registered range succeeds, one past the end
   returns EFAULT (test both).
7. **Exit in the interpreter.** `exit(42)` from guest code returns 42 to the
   host *and* frees the image. On Windows, running it through `ExitProcess`
   kills the test harness.
8. **Two-value syscall return.** `read()` returning 2 must not be reported as
   an error; `open` of a missing file must report ENOENT, not fd 2.
9. **Weak binds decoded.** A binary with only weak imports must still show
   them (`LC_DYLD_INFO.weak_bind`).
10. **Lazy binding.** With real `libSystem.B.dylib` present, the first call to
    an imported function resolves through `dyld_stub_binder`; without it, the
    loader must say "cannot resolve _printf" and exit non-zero - not crash.
11. **Bounds established once at parse.** Reject impossible geometry (segment
    below base, span > file size, vmaddr 2^63) before mapping anything.
12. **Fuzz with `max_mapped` sized buffers.** The real allocation size is the
    fuzzer's buffer size; a roomy buffer makes every bug invisible.

## Failure signatures and their causes

| symptom | usual cause |
|---|---|
| SIGBUS on first store | `__DATA` mapped read-only |
| SIGILL at entry | wrong `p_align` congruence, or fileoffset/vaddr mix-up |
| every read/write EFAULT | guest ranges not registered |
| `write(1,...)` EBADF | std fds not wired to host handles |
| fixes apply at wild addresses | link base used as image base |
| zero fixups, no error | `LC_DYLD_INFO.weak_bind` ignored, or a 1-based
  `seg_info_offset` walked as 0-based |
| hangs after `exit(0)` | exit routed to the host hook |
| `read()==2` treated as error | failure inferred from the value instead of
  the carry flag |

## Exit criteria for claiming "runs Darwin binaries"

* `hello_arm64`, `exit42_arm64`, `exit42_x86_64`, `exit42_fat` all run with
  the documented output/exit code.
* `used` either resolves `_add` from the loaded dylib or fails by name.
* One binary linked against the SDK prints something and exits 0.
* All of the above asserted in CI, not by hand.
