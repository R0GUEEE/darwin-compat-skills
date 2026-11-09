---
name: darwin-porting
version: 2.0.0
description: Reverse engineer Darwin/macOS/iOS command-line tools and rebuild working Linux (or Windows) equivalents - Mach-O parsing, dyld internals (export trie, bind opcodes, chained fixups), XNU syscall table generation, and the dispatch-layer traps that come with it. Use for any "port tool X from macOS", "what does this Darwin binary call", "decode this Mach-O", "which syscall is N", "reimplement otool/lipo" request.
triggers: Mach-O, otool, dyld, syscall table, Darwin utility, port from macOS, binary analysis
---

# Darwin utility porting lab

Goal is a **compiled, tested artefact** - a Linux binary, a library, or a
shim - not a report. Choose the route on evidence, not preference:

| Route | Pick when | Cost |
|---|---|---|
| source port | Apple OSS source exists (`apple-oss-distributions/*`) | days, honest |
| clean-room reimplementation | behaviour is observable, format is documented | days, honest |
| compatibility layer | many binaries, one ABI (`darwin-compat-layer` skill) | weeks |
| Darling / container | user wants the real tool, not a clone | a host VM |

A binary alone never implies its source. Reading Apple's `.tbd` stubs and dyld
output tells you the **ABI**; it does not tell you the **algorithm**.

## 1. Inventory before you touch code

```bash
S=/var/minis/skills/darwin-porting/scripts
sh $S/tools.sh /path/to/tool            # headers, exports, binds, strings, sigs
python3 $S/mcmd.py info   tool          # same, structured (JSON)
python3 $S/mcmd.py deps   tool          # which dylibs, which rpath
python3 $S/mcmd.py exports tool
python3 $S/mcmd.py fixups  tool         # what it imports, from where
```

Read the dependency list as a difficulty score. Each `libSystem` call is a
Linux libc call; each `CoreFoundation`, `Security`, `IOKit`, `libdispatch`,
`libxpc`, `libproc` call is a bespoke port; each `_OBJC_CLASS_$_` is a rewrite.

## 2. Decode the Mach-O properly

`machopy.py` is the reader; `saferead.py` is the I/O layer. Use them together -
**never** `open().read()`:

```python
import sys; sys.path.insert(0, '/var/minis/skills/darwin-porting/scripts')
from saferead import read_image, verify
import machopy

d = read_image(path)                 # mmap-backed copy
assert not verify(d, path)           # bytes agree with a fresh mmap
m = machopy.MachO(d)                 # thin file
for cpu, sub, off, size, align in machopy.fat_slices(d):
    m = machopy.MachO(d, off)        # each universal slice
m.exports()        # {name: {address|reexport, kind, weak}}   export trie
m.fixups()         # [(vmaddr, name, 0-based lib idx, addend, lazy)]
m.imports_table()  # import-table order (chained fixups or opcode streams)
m.symbols()        # nlist, decoded, with kind
m.dylibs()         # LC_LOAD_DYLIB / weak / reexport / lazy
```

Load-command offsets that bite everyone: `LC_SEGMENT_64` sections start at
`cmdsize`-independent `+72` with 80-byte records; `dyld_chained_starts_in_segment`
has `page_size: u16` at `+4` and `page_format: u16` at `+6` (**not** u32/u32 -
that mistake pushes every later field two bytes and yields zero fixups);
`LC_SYMTAB` string offsets are relative to `stroff`, not to the symbol.

## 3. Recover the syscall surface

`bsd/sys/syscall.h` is generated at build time and is *not* in the XNU tree -
fetching it 404s on every tag. Generate it from the master file instead:

```bash
curl -sSL -o syscalls.master \
  https://raw.githubusercontent.com/apple-oss-distributions/xnu/xnu-12377.121.6/bsd/kern/syscalls.master

python3 $S/gen_syscalls.py --master syscalls.master --format c --tag xnu-12377 > syscalls_gen.h
python3 $S/gen_syscalls.py --master syscalls.master --check 5,6,244,520
```

The generated header compiles clean under `-Wall -Wextra` and gives you a
`[0..557]` name table plus one enum symbol per number. Facts it encodes:
numbers are one namespace for every architecture, sparse, and *some numbers
carry two names* (`557` = `coalition_policy_get` | `enosys`); `nosys` appears
90 times. Dedupe by number or the enum will not compile.

## 4. Port the code

1. One portability header (`dnt_port.h`), two backends (POSIX, Win32), no
   `#ifdef` inside the algorithm. That split is why the same VFS code could be
   tested on Linux and verified on a Windows runner.
2. Map APIs, and test the mapping - not the claim.
   `kqueue`→epoll, `FSEvents`→inotify, `IOKit`→libudev, `mach_absolute_time`→
   `clock_gettime(CLOCK_UPTIME_RAW)`, `os_log`→syslog, `libproc`→`/proc`,
   `sysctlbyname`→`sysconf`/sysfs.
3. Preserve observable surface: flags, exit codes, stderr text, config paths.
   Write those down in `docs/DEVIATIONS.md` as you change them.
4. Darwin returns **two** things from a syscall: `x0` result and the carry
   flag. Never infer failure from a value (`read()==2` vs `ENOTDIR==2`).
5. `exit()` must terminate in the interpreter, not through a host hook - on
   Windows a host `ExitProcess` kills your process before you can report the
   guest's code or free its image.

## 5. Prove it with real binaries

Synthetic fixtures hide loader bugs. Build Darwin binaries with the LLVM tools
already here and test against their *llvm-objdump* output:

```bash
sh $S/fixtures/build_fixtures.sh /tmp/fix    # arm64 + x86_64 + fat + dylib
llvm-objdump --macho --exports-trie /tmp/fix/used
llvm-objdump --macho --lazy-bind   /tmp/fix/used
FIXTURES=/tmp/fix python3 -m unittest discover -s $S/tests -v
```

Bugs that only real output exposed: `__PAGEZERO` rejected as "segment below
base"; link address used as mapped address (every PC-relative access off);
exec `exit()` routed through the host; std fds as invalid handles; guest
pointers rejected for want of a registered memory region; and the lazy-bind
`DONE` opcode, which terminates one *entry*, not the stream.

## 6. Deliverable

Ship: the working code, `docs/COMPAT.md` (call-by-call mapping with test
names), `docs/DEVIATIONS.md`, build command, and test output. State plainly
what ran and what did not - an unverified "should work" is a lie with a
deadline.

## References

- `references/macho-internals.md` - structures, offsets, traps
- `references/xnu-syscalls.md` - numbering, guards, ABI notes
- `references/porting-checklist.md` - per-subsystem map + acceptance tests
- `../sandbox-quirks.md` (in `darwin-compat-layer`) - why every parser here
  reads through `saferead`
- https://github.com/apple-oss-distributions
- https://github.com/llvm/llvm-project/tree/main/llvm/include/llvm/BinaryFormat/MachO.h
