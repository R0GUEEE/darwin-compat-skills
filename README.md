# Darwin on Linux — three skills

Reverse-engineering Darwin tooling, running Darwin binaries on Linux, and
operating QEMU. Every numbered claim below was executed on an iPhone running
Minis' iSH sandbox (Alpine, aarch64, QEMU 9.1.2, clang 19, CPython 3.12) during
the build; anything that was not executed is marked **untested** and says why.

```
darwin-porting/        reverse engineer Darwin tools, rebuild them for Linux
darwin-compat-layer/   run Darwin binaries on Linux: shim / convert / loader
qemu-ops/              drive QEMU: user & system mode, QMP, disks, qtests
```

Install by copying the directories into `/var/minis/skills/`. The skills are
self-contained; `darwin-compat-layer` and `qemu-ops` reuse scripts from
`darwin-porting`, so keep the three side by side.

---

## darwin-porting

Objective: turn a Darwin binary or Apple source tree into a tested Linux
artefact.

```bash
S=darwin-porting/scripts
python3 $S/mcmd.py info /path/tool            # header, segments, dylibs, rpath
python3 $S/mcmd.py imports /path/tool         # what it needs, from which dylib
python3 $S/mcmd.py exports /path/tool         # export trie
sh $S/tools.sh /path/tool                     # full llvm sweep + strings + sigs

python3 $S/gen_syscalls.py --master $S/../data/syscalls.master --format c > syscalls_gen.h
python3 $S/gen_syscalls.py --master ... --check 5,6,244,520

python3 $S/abi_probe.py --sdk /opt/sdks-src/iPhoneOS16.5.sdk --json
```

**Tested**
- `machopy.py` parses arm64/x86_64 Mach-O, fat binaries, dylibs and
  SDK-linked executables; exports, symbols, classic binds, lazy binds and
  chained fixups agree with `llvm-objdump --macho`.
- `gen_syscalls.py` produces a header that compiles clean with
  `-Wall -Wextra`; the name table covers `[0..557]`.
- `abi_probe.py` derives the Darwin struct ABI from headers by compiling
  probes and reading `mov w0,#imm` back. Verified values: `struct stat` 144 B
  (`st_ino`@8, `st_mode`@4 as **u16**, `st_size`@96), `struct dirent` 1048 B,
  `sigset_t` 4 B, `termios` 72 B, `mode_t` 2 B.
- `scripts/tests/test_fixtures.py`: 18 differential tests, all passing.

**Bugs the fixtures caught** — `__PAGEZERO` rejected as invalid geometry;
link address used as mapped address; lazy-bind `DONE` ending the whole stream;
`dyld_chained_starts_in_segment` offsets mis-parsed (page_size is u16).

---

## darwin-compat-layer

Objective: make Darwin binaries run on Linux without a Mac.

```bash
sh darwin-compat-layer/scripts/tests/run.sh          # everything below
cc -shared -fPIC -O2 darwin-compat-layer/scripts/darwin_shim.c -o libdarwin_shim.so
python3 darwin-compat-layer/scripts/macho2elf.py --in tool --out tool.elf --report r.json
```

**Tested**
- `darwin_shim.c` compiles with `-Wall -Wextra -Wpedantic` and passes a
  runtime self-test: `darwin_stat` returns a 144-byte Darwin `struct stat`
  with the right offsets, `sysctlbyname("hw.ncpu")` works, unknown names
  return `ENOENT`, `fsgetpath` returns `ENOSYS` rather than a plausible lie.
- `abi_structs.py` proves the same layout with ctypes asserts.
- `macho2elf.py` rewrites `svc #0x80` → `svc #0` (count reported), zeroes the
  Mach-O header word, and emits `.dynsym/.dynstr/.hash` so `dlopen` loads a
  converted dylib and `dlsym` finds its exports.
- `gen_sysctl.py` produces compiling MIB enums from XNU `sysctl.h`.

**Untested / limits**
- A converted *executable* faults on the iSH kernel: Mach-O keeps
  `__PAGEZERO` at 0, so the image wants the low 4 GB, which the kernel's
  ELF loader does not honour. Documented in `scripts/macho2elf.py` and the
  skill; the fix is a loader, not a converter.
- No ObjC/Swift/CF coverage — out of scope for all three layers.

---

## qemu-ops

```bash
Q=qemu-ops/scripts/qvm.py
python3 $Q start --kernel fw.elf --serial-log vm.log --qmp /tmp/vm.qmp --gdb 1234
python3 $Q wait --log vm.log --for "login:" --timeout 120
python3 $Q hmp   --qmp /tmp/vm.qmp --cmd "info registers"
python3 $Q regs  --gdb 1234
python3 $Q quit  --qmp /tmp/vm.qmp
sh qemu-ops/scripts/selftest.sh
```

**Tested**
- `qvm.py` start/status/hmp/mem/resume/wait/regs/quit against
  `qemu-system-aarch64` 9.1.2; QMP over a unix socket, GDB stub register dump
  from a `-S` start, serial captured via `-serial file:` (stdin is not a
  control channel — `-serial stdio` receives nothing from a piped shell).
- Measured TCG throughput: ~2.3M guest instructions/s (64K×2048 iterations =
  117 s). Headless `virt` machine reaches its first UART byte in 0.3 s.
- `qemu-img` create/snapshot/convert/check flows; `-c` compression on a sparse
  raw image.
- `gdb` 15.2 on this device speaks aarch64 to QEMU's stub and auto-detects the
  stop.

**Untested**
- `qtest.py` needs a configured QEMU build with qos-test; none was built here.
- Booting a real distro (minutes at ~2.3M instr/s) was not attempted; the
  freestanding fixture is the fast path.

---

## iSH quirks these skills encode

1. `read()` whose length lands exactly on a 32K boundary can zero its tail —
   read images through `mmap` (`saferead.read_image`).
2. `bytes` slicing and `struct.unpack_from` have disagreed with `od` on
   specific offsets; verify a buffer before a long parse.
3. Recursive byte-walkers can silently skip a branch; decode iteratively and
   cross-check with `llvm-objdump`.
4. The allocator fails transiently (`MemoryError`, `libcrypto.so.3: Out of
   memory`); retry before believing a tool is broken.

Details: `darwin-compat-layer/references/sandbox-quirks.md`.
