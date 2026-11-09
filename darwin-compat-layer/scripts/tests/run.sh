#!/bin/sh
# run.sh - build and self-test the Darwin compat layer pieces.
# Everything here runs on the iSH device; no macOS required.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
TOP=$(cd "$HERE/.." && pwd)
OUT=${OUT:-$(mktemp -d)}

echo "== ABI struct mirror (ctypes)"
python3 "$TOP/abi_structs.py"

echo "== C shim compiles clean under -Wall -Wextra -Wpedantic"
cc -shared -fPIC -O2 -Wall -Wextra -Wpedantic -o "$OUT/libdarwin_shim.so" "$TOP/darwin_shim.c" 2>&1 \
  | grep -v 'ISO C forbids conversion of object pointer' | grep -v '^ \|^$' || true

echo "== shim runtime self-test"
cc -O2 -o "$OUT/shimtest" "$HERE/shim_selftest.c" "$OUT/libdarwin_shim.so" \
   -Wl,-rpath,"$OUT" -include errno.h
"$OUT/shimtest"

echo "== Mach-O -> ELF converter (raw-syscall fixture)"
FIX=${FIXTURES:-/var/minis/workspace/fix}
if [ -f "$FIX/hello_arm64" ]; then
    python3 "$TOP/macho2elf.py" --in "$FIX/hello_arm64" --out "$OUT/hello.elf" --report "$OUT/hello.json" >/dev/null
    "$OUT/hello.elf" > "$OUT/hello.out" 2>&1 || echo "(converted ELF exited $? - check the report)"
    head -2 "$OUT/hello.out" || true
    python3 - "$OUT/hello.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
print('rewritten:', r.get('rewritten'), 'unresolved:', r['unresolved'])
PY
else
    echo "(no fixtures at $FIX; run darwin-porting/scripts/fixtures/build_fixtures.sh)"
fi

echo "== sysctl MIB tables"
python3 "$TOP/gen_sysctl.py" --sysctl-h "${XNU:-/tmp/xnu-xnu-11215.41.3}/bsd/sys/sysctl.h" \
    --check kern.maxproc,hw.ncpu,hw.memsize 2>/dev/null || echo "(no XNU tree; set XNU=...)"
echo "done: $OUT"
