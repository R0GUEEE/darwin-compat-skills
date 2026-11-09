# iSH sandbox quirks that look like parser bugs

Everything here was reproducible on this device (CPython 3.12.16,
aarch64-musl, kernel reports 4.20.69-ish). Two skills depend on it:
`darwin-compat-layer` and `darwin-porting`. Read this before spending an hour
on a decoder that "must be wrong".

## 1. `read()` with a length that ends on a 32K boundary zeroes the tail

```python
f = open(path, 'rb'); f.seek(32764); f.read(12)
# b'\x00\x00\x00\x00' + the 8 real bytes   <- first 4 lost
f.seek(32768); f.read(6)                   # correct
os.pread(fd, 6, 32768)                     # correct
```
Consequence: any code that reads a struct/table "exactly to the end" of a read
can silently get zeros. Mitigation: read whole files through `mmap`
(`saferead.read_image`), never `read()` of struct-sized lengths.

## 2. Slicing and `struct.unpack_from` can disagree with `od` - and each other

Observed on a 49944-byte object file: for two 4-byte words inside a header,
`d[o:o+4]`, `struct.unpack_from('<I', d, o)` and an mmap of the same file all
returned one value; `od -An -tx1` showed another (the correct one, per
`llvm-objdump`). The pattern is stable per file and per offset, identical in a
fresh process, and *differs between files with identical content*: a `shutil`
copy of the file read correctly at every offset where the original did not.

Rules that follow:
* verify a buffer against the file (`saferead.verify`) before a long parse;
* when a value looks impossible, get a second opinion from `od` and from
  `llvm-objdump`, and prefer the tool's answer;
* never reason "it read differently across runs, so it is nondeterministic" -
  the failing offsets are deterministic per file.

## 3. Recursive byte-walkers can silently skip a branch

A recursive descent over `bytes` with `if tl == 0: ... return` inside
`while p < len(d)` was seen to skip the terminal branch entirely - no
exception, no output, `walk()` just returned - while an iterative worklist
over the same bytes decoded correctly, and the same recursive code sometimes
worked. Do not trust a single decoder run: decode with two implementations,
or decode iteratively and cross-check against `llvm-objdump`.

## 4. The allocator fails transiently

`MemoryError` from module imports, `libcrypto.so.3: Out of memory` from
`od`/`tail`, `symbol not found` from coreutils - then it works again on the
next command. Check headroom (`sandbox.py`), retry, never conclude a tool is
broken from one OOM. A stray `find /` can consume the whole 4 GB.

## 5. Tool notes

* `llvm-objdump --macho --exports-trie|--bind|--lazy-bind|--chained-fixups`
  is the ground truth; `llvm-otool` prints the same load commands.
* `ld64.lld` here does not implement `-bind_at_load` (warns and ignores).
* A synthesized stub dylib does **not** produce lazy bind entries; only a real
  `libSystem.B.dylib` (an SDK or a dyld cache) does.
* clang/lld can emit real Darwin Mach-O for arm64 and x86_64 from the
  sandbox; `file` and `llvm-objdump` confirm it. Use them instead of
  hand-written fixtures.
* `svc #0x80` is Darwin's syscall trap, `svc #0` is Linux's; a converted
  binary must rewrite them (the converter does, and reports the count).
* Mach-O preserves `__PAGEZERO` at 0, so a converted image wants the low 4 GB.
  Expect `p_align` congruence problems when the loader honours `p_align`; the
  converter emits 2^16 for this reason.
