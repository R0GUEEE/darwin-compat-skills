---
name: darwin-compat-layer
version: 1.0.0
description: Run Darwin/macOS/iOS binaries on Linux - decide between a shim (source port), a Mach-O->ELF conversion, and a full loader, then build the ABI translation layer (stat/dirent/sigaction/sysctl), the syscall dispatch table, and a loader that maps an image the way dyld does. Use for "run this mac binary on Linux", "compatibility layer", "Darwin ABI shim", "syscall dispatch", "map Mach-O image", or any Darwin-on-Linux/Windows runtime work.
triggers: compatibility layer, run mac binary on linux, Darwin ABI, syscall dispatch, Mach-O loader, shim
---

# Darwin compatibility layer

Three layers, cheapest first. Do not start at the bottom.

| Layer | What it buys | What breaks |
|---|---|---|
| **shim** (`libdarwin_shim.so`) | recompiled Darwin source runs unchanged | link-time only; needs source or an object |
| **convert** (`macho2elf.py`) | a Mach-O image becomes an ELF | no dyld: no dylibs, no lazy binding, no ObjC |
| **loader** (`dnt`) | a Mach-O image runs *as* Mach-O, real dyld semantics | a runtime to write and debug, per-arch |

Rule that decides it: **if the binary imports from libSystem and needs lazy
binding, only the loader works.** `ld64.lld` will not emit a lazy bind entry
for an undefined symbol against a synthesized stub dylib (verified:
`lazy_bind_size == 0`), so a converted ELF has no way to resolve `printf` at
runtime unless you substitute symbols before conversion.

## 1. Shim: ABI translation, the part that silently corrupts

`scripts/darwin_shim.c` + `scripts/abi_structs.py`. Only the asymmetric calls
are there - same-behaviour libc (printf, memcpy, strlen) links straight to the
host and should not be shimmed.

```bash
cd /var/minis/skills/darwin-compat-layer
sh scripts/tests/run.sh          # builds, runs ABI + shim + converter checks
```

Numbers the shim encodes (derived from the SDK with `abi_probe.py`, not from
memory): `struct stat` is 144 bytes, `st_ino`@8, **`st_mode`@4 and 16-bit**,
`st_size`@96, `st_blksize`@112; `struct dirent` is 1048 bytes with
`d_seekoff`@8 and a 16-bit `d_namlen`@18; `sigset_t` is 4 bytes (Linux: 128);
`termios` 72; `pthread_t` 8.

Never `memcpy` one ABI's struct into the other. Translate field by field, and
let the compiler enforce the layout: the shim carries `_Static_assert` on
every offset that matters as well as `sizeof`.

Calls that must return ENOSYS rather than a plausible lie: `fsgetpath`,
`proc_pidinfo` flavors you do not implement, `terminate_with_payload`.

## 2. Convert: Mach-O -> ELF

```bash
python3 scripts/macho2elf.py --in tool --out tool.elf --report r.json
python3 scripts/macho2elf.py --in lib.dylib --out lib.so --kind so
```

What the converter does: parses with `machopy` (from `darwin-porting`), lays
segments out at their Mach-O vaddrs, rewrites `svc #0x80` to `svc #0`, zeroes
the Mach-O header word, and emits `PT_LOAD`s plus a real `.dynsym/.dynstr/
.hash` so `dlopen` works. `--report` lists resolved and unresolved imports -
read it before blaming the converter.

Two loader facts this encodes:
* a `PT_DYNAMIC` with only `DT_NULL` makes the **dynamic loader segfault**
  (dlopen reads `DT_STRTAB`/`DT_SYMTAB` unconditionally) - emit the real
  tables or none;
* `p_align` must be congruent with (`p_offset mod p_align == p_vaddr mod
  p_align`). Mach-O links `__TEXT` at 0x100000000 with fileoff 0; declaring
  `p_align` 0x1000 there loads the file at the wrong in-page offset and the
  first instruction fetched is garbage. `/bin/ld` uses 2^16 for exactly this
  reason.

## 3. Loader: the dyld work

Only worth it when you need dynamic binaries. The invariants, each one a bug
in a from-scratch implementation:

1. `__PAGEZERO` (vmaddr 0, vmsize 4 GB, filesize 0) is normal - skip it, do
   not validate it as geometry.
2. Keep **link base** (addresses in the file) and **image base** (runtime)
   separate. Map at the link address or refuse: the interpreter dereferences
   guest addresses as native pointers, so a silent slide corrupts everything.
3. Register guest memory regions *before* running code, or every pointer
   argument comes back EFAULT.
4. Give std fds real host handles, or `write(1, ...)` returns EBADF.
5. Handle `exit()` in the interpreter, never through a host exit hook - on
   Windows that is `ExitProcess` and your process dies inside the syscall.
6. A Darwin syscall returns **two** things: `x0` value and the carry flag.
   `read() == 2` and `ENOTDIR == 2` are indistinguishable from the value.
7. Weak binds count: `LC_DYLD_INFO.weak_bind` carries imports too. Ignoring
   it makes a dynamic binary report zero fixups.
8. Fuzz with a buffer sized to exactly `max_mapped`. A roomy buffer hides
   the bugs that matter: 2^63 allocations from a corrupt vmaddr, unsigned
   underflow turning bounds checks into no-ops, spans larger than the file.

## 4. Building the syscall surface

`gen_syscalls.py` (in `darwin-porting`) emits the numbered table from
`syscalls.master`; implement handlers against that table, not against memory.
`getcwd` and `isatty` are **not** Darwin syscalls (libSystem uses
`fcntl(F_GETPATH)` and `ioctl`). Grep the master before adding a handler.

`gen_sysctl.py` emits the MIB numbers (`kern.maxproc` = [1,6], `hw.ncpu` =
[6,3], `hw.memsize` = [6,24]) from XNU's `sysctl.h`, including the
`#ifdef SYSCTL_DEF_ENABLED` block that naive scrapers miss.

## 5. Where this does not go

* ObjC/Swift apps: the runtime, Foundation and CoreFoundation are out of scope
  for all three layers. Use Darling on a real x86 host.
* iOS apps: AMFI/FairPlay, entitlements, the dyld shared cache - not a compat
  layer problem, a device problem.
* GPU/window system: Metal and AppKit have no shim worth writing.

## 6. Deliverable contract

Ship the shim or loader, `docs/COMPAT.md` (one line per translated call,
naming the test that proves it), `docs/DEVIATIONS.md`, and the report from
the converter or loader's `--report`. State which binaries actually ran.

## References

- `references/abi-differences.md` - field-by-field Darwin vs Linux tables
- `references/loader-checklist.md` - dyld semantics as acceptance tests
- `references/sandbox-quirks.md` - why every parser here reads via
  `saferead` and verifies with `llvm-objdump`
- `../darwin-porting/` - `machopy`, `saferead`, `abi_probe`, `gen_syscalls`
