# Mach-O internals for porters

Everything here was verified against `llvm-objdump --macho` on real
clang/ld64.lld output, and against binaries linked with the iPhoneOS 16.5 SDK.
Where "correct" and "plausible" disagreed, the field values below are the ones
the tools print.

## 1. Header and pack

```
offset  size  field
0       4     magic   0xfeedface (32) / 0xfeedfacf (64), LE
4       4     cputype 0x0100000c arm64, 0x01000007 x86_64
8       4     cpusubtype
12      4     filetype 2 EXECUTE, 6 DYLIB, 8 BUNDLE, 0xb KEXT
16      4     ncmds
20      4     sizeofcmds   load commands live in [hdrsize, hdrsize+sizeofcmds)
24      4     flags  bit21 (0x200000) = PIE - clang/lld set it by default
28      4     reserved (64-bit only)
```
Magic tells you endianness and width. A "universal" file starts with
`0xcafebabe` BE, whose next word is the slice COUNT - that same magic is Java
class format, so sanity-check the count (<= 64) before trusting it.
Fat64 (`0xcafebabf`) uses 32-byte slice records instead of 20.

## 2. Load commands that matter

| cmd | why | offsets that cost people hours |
|---|---|---|
| LC_SEGMENT_64 | memory layout | section array at `+72`, 80 bytes/record |
| LC_MAIN | entry | `entryoff` is relative to `__TEXT.vmaddr` |
| LC_LOAD_DYLIB et al | deps | name is `lc_str` (offset from cmd start), ordinal = order of appearance |
| LC_ID_DYLIB | install name | same layout as LOAD_DYLIB |
| LC_RPATH | dyld search | `@executable_path/`, `@loader_path/`, `@rpath/` |
| LC_SYMTAB | nlist | strx is relative to `stroff` |
| LC_DYSYMTAB | indirect syms | 18 u32 fields; `indirectsymoff` at field 12 |
| LC_DYLD_INFO_ONLY | classic binds | 5 (off,size) pairs: rebase, bind, weak, lazy, export |
| LC_DYLD_EXPORTS_TRIE | modern exports | supersedes DI['export'] |
| LC_DYLD_CHAINED_FIXUPS | modern binds | see below |
| LC_CODE_SIGNATURE | signature | `dataoff` is the superblob |
| LC_FUNCTION_STARTS | debug/stack walk | ULEB deltas from `text_base` |

### Section records (LC_SEGMENT_64)
`sectname[16] segname[16] addr u64 size u64 offset u32 align u32 reloff u32
nreloc u32 flags u32 reserved1 u32 reserved2 u32 reserved3 u32`
`offset == 0` means the section has no file bytes (zerofill). Flags
0x80000400 = pure instructions, 0x80000408 = self-modifying stubs.

## 3. Export trie (`LC_DYLD_EXPORTS_TRIE` or `DI.export`)

```
node:
  terminalSize u8; if 0 -> terminal record, else read that many bytes of edge name
  edge: name[terminalSize] uleb flags; flags != 0 -> terminal, else uleb childOffset
terminal record after flags:
  if flags & 0x08 (REEXPORT): uleb libraryOrdinal, then C string (import name)
  else:                      uleb address; flags&3==3 -> more uleb resolver; flags&0x10 -> stub
```
* The first node is reached at offset 0 and almost always holds the self
  terminal: bytes `00 01 5f 00 05` = terminalSize 0, flags 1, address 0x5f.
* Child offsets are relative to the START of the trie, not to the node.
* Node size is bounded by `size`; a child offset beyond it is corruption and
  must stop the walk, not wrap.

## 4. Classic bind opcodes (`LC_DYLD_INFO*.bind / lazy_bind`)

```
0x00 DONE         0x10 SET_DYLIB_ORDINAL_IMM    0x20 SET_DYLIB_ORDINAL_ULEB
0x30 SET_DYLIB_SPECIAL_IMM   0x40 SET_SYMBOL_TRAILING_FLAGS_IMM
0x50 SET_TYPE_IMM 0x60 SET_ADDEND_SLEB          0x70 SET_SEGMENT_AND_OFFSET_ULEB
0x80 ADD_ADDR_ULEB 0x90 DO_BIND 0xA0 DO_BIND_ADD_ADDR_ULEB
0xB0 DO_BIND_ADD_ADDR_IMM_SCALED  0xC0 DO_BIND_ULEB_TIMES_SKIPPING_ULEB
```
* `DONE` in the **bind** stream ends the table.
* `DONE` in the **lazy_bind** stream ends one ENTRY only; dyld re-enters for
  the next stub. Stopping the whole stream there loses every imported
  function that comes after the first stub - llvm-objdump shows two lazy
  entries for a binary with two stubs, and a one-entry parser looks correct.
* Ordinals are 1-based here (1 = first LC_LOAD_DYLIB), negative/special for
  flat namespace (0xFF area). Report them 0-based or clearly marked.

## 5. Chained fixups (`LC_DYLD_CHAINED_FIXUPS`)

```
fixups_header: version u32, starts_offset u32, imports_offset u32,
               symbols_offset u32, imports_count u32, imports_format u32,
               symbols_format u32                       (7 x u32 = 28 bytes)
starts:        seg_count u32, seg_info_offset[seg_count] u32   (0 = no fixups)
seg_info:      size u32, page_size u16, pointer_format u16,
               segment_offset u64, max_valid_pointer u32, page_count u16,
               page_start[page_count] u16
```
Two traps, both silent:

1. `page_size` is **u16** and `pointer_format` is the **u16 after it**. Reading
   both as u32 shifts `segment_offset` and everything after it by two bytes;
   the page starts then look like nonsense and you produce zero fixups with no
   error.
2. `seg_info_offset[i]` belongs to segment *i* of the segment list, 0-based.
   dyld code indexes it as `[seg-1]` because segment 0 (`__PAGEZERO`) never has
   fixups; copying that 1-based form and skipping `idx==0` loses segment 1
   (usually `__TEXT`) and reports an empty bind list.

Pointer formats worth implementing first: 2 `PTR_64` and 6 `PTR_64_OFFSET`
(next bits 0..11, bind bit 62, ordinal bits 24..31), 1 and 9 for arm64e
(next bits 0..10, ordinal 51..58 / 48..71). `0x7FF`/`0xFFF` in the next field
means "stride 8/4", not "end".

The import table itself is inside `LINKEDIT` and its `name_offset` is relative
to `symbols_offset`. It is the fastest way to learn **which symbols** a binary
needs - a good first pass even before the bind chain decodes correctly.

## 6. Code signature (for `ldid`-style rewriting)

```
superblob: magic 0xfade0cc0, length u32, count u32, index[count]{type u32, offset u32}
type 0            = CodeDirectory
CD:      magic 0xfade0c02, length, version, flags, hashOffset, identOffset,
         nSpecialSlots, nCodeSlots, codeLimit, hashSize u8, hashType u8,
         platform u8, pageSizeLog2 u8, spare2, scatterOffset, teamOffset ...
```
`pageSizeLog2` is 12 for most clang output; hashes cover `codeLimit` bytes in
`1 << pageSizeLog2` chunks. Ad-hoc signing after patching = write a new CD with
the new `codeLimit`, re-hash, fix `LC_CODE_SIGNATURE.dataoff/datasize`, and
zero the old signature bytes. Anything that runs under AMFI will also want the
`CS_ADHOC` flag (0x2) and no entitlement blob.

## 7. Fat slicing

`lipo -create` only pads each slice to its alignment; it does not deduplicate.
When repacking, keep `align` from the original records and pad with zeros -
dyld validates `offset % (1 << align) == 0`.

## 8. ARM64 details that surprise

* `svc #0x80` is the Darwin syscall trap; `svc #0` is Linux ABI. A binary
  built for the wrong target traps here and looks "unsupported".
* Syscall number goes in `x16`, not `x8`. x0-x5 arguments, x0 result,
  carry flag (see the dispatch layer skill for the two-value return).
* On x86_64 Darwin the number is OR-ed with `0x2000000`.
