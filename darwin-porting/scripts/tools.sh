#!/bin/sh
# tools.sh - the reverse-engineering toolkit that actually exists in this
# sandbox, and what each one is for. Run each line as-is; they are tested here.
#
# Install once (iSH/Alpine):
#   apk add ripgrep llvm llvm-otool clang lld llvm-lipo binutils file \
#           py3-capstone capstone qemu-x86_64 strace python3
#
# Rule: if a binary or tool comes from a *real* toolchain, test against it.
# Synthetic fixtures hide loader bugs (see references/macho-internals.md).

set -e
F=${1:?usage: tools.sh <macho-file>}

echo "== identity"
file "$F"

echo "== header (llvm-otool)"
llvm-otool -hv "$F"

echo "== load commands (every one, resolved)"
llvm-otool -l "$F" | sed -n '1,120p'

echo "== universal slices"
llvm-lipo -info "$F" 2>/dev/null || echo "(thin)"

echo "== dylibs and rpaths"
llvm-objdump --macho --dylibs-used "$F" 2>/dev/null || true
llvm-objdump --macho --private-headers "$F" 2>/dev/null | grep -A2 -E 'LC_RPATH|LC_LOAD_DYLIB|LC_ID_DYLIB' || true

echo "== symbols (defined + undefined)"
llvm-nm --arch all -m "$F" 2>/dev/null | head -80   # if llvm-nm is absent: llvm-objdump --syms
llvm-objdump --macho --syms "$F" 2>/dev/null | head -60

echo "== exports trie (the truth for what this binary offers)"
llvm-objdump --macho --exports-trie "$F" 2>/dev/null || true

echo "== bind table (what it needs, and from which dylib ordinal)"
llvm-objdump --macho --bind "$F" 2>/dev/null || true
llvm-objdump --macho --lazy-bind "$F" 2>/dev/null || true
llvm-objdump --macho --weak-bind "$F" 2>/dev/null || true
llvm-objdump --macho --rebase "$F" 2>/dev/null || true

echo "== code signature slots"
llvm-objdump --macho --code-signature "$F" 2>/dev/null | head -40 || echo "(none)"

echo "== disassembly (arm64 shown; will disassemble any slice present)"
llvm-objdump --macho -d --no-show-raw-insn "$F" 2>/dev/null | head -120

echo "== strings worth grepping (paths, SQL, XML, versions)"
strings -a -n 6 "$F" | head -100

echo "== grep patterns that pay off across a whole binary"
# filesystem paths, defaults domains, entitlements, xpc services
for pat in '/usr/|/private/|/var/|/etc/' 'com\.apple\.' 'XPC_|NSXPC|xpc_' \
           'NS[A-Z][A-Za-z]+Domain|preferences' 'CFBundle|Info\.plist'; do
    echo "--- $pat"
    strings -a "$F" | rg -N --no-filename -e "$pat" | head -8 || true
done

echo "== entropy sweep: encrypted / packed sections"
# a FairPlay-encrypted iOS binary shows an LC_ENCRYPTION_INFO with cryptid=1
llvm-otool -l "$F" | rg -A4 'LC_ENCRYPTION_INFO' || echo "(not encrypted)"

echo "== capstone: decode a range (replace start/size)"
cat <<'NOTE'
python3 - "$F" <<'PY'
import sys, capstone
from machopy import MachO           # from the skill's scripts dir
m = MachO(open(sys.argv[1], 'rb').read())
sect = m.section('__text')
code = m.data[sect['offset']:sect['offset'] + 64]
md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
for ins in md.disasm(code, sect['addr']):
    print('%#x  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))
PY
NOTE
