#!/bin/sh
# selftest.sh - prove the QEMU stack works on this device, in under a minute.
# Each step names what it proved; a silent pass is not a pass.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
Q="$HERE/qvm.py"
OUT=${OUT:-$(mktemp -d)}
FIX=${FIX:-/tmp/qfix}

echo "== versions"
qemu-img --version | head -1
qemu-aarch64 --version | head -1
qemu-system-aarch64 --version | head -1

echo "== fixtures"
[ -f "$FIX/hello_kernel.elf" ] || sh "$HERE/fixtures/build_fixtures.sh" "$FIX" >/dev/null

echo "== user-mode emulator"
qemu-aarch64 /bin/echo qemu-user-ok

echo "== disk tooling"
qemu-img create -f qcow2 "$OUT/t.qcow2" 16M >/dev/null
qemu-img snapshot -c s1 "$OUT/t.qcow2" >/dev/null
qemu-img snapshot -a s1 "$OUT/t.qcow2" >/dev/null
qemu-img check "$OUT/t.qcow2" | grep -q "No errors" && echo "qcow2 snapshot+check ok"

echo "== system emulator + QMP"
rm -f "$OUT/vm.log" "$OUT/vm.qmp"
python3 "$Q" start --kernel "$FIX/hello_kernel.elf" --serial-log "$OUT/vm.log" \
        --qmp "$OUT/vm.qmp" --log "$OUT/qemu.log" >/dev/null
python3 "$Q" wait --log "$OUT/vm.log" --for "hello from aarch64" --timeout 20
python3 "$Q" hmp --qmp "$OUT/vm.qmp" --cmd "info cpus" | head -1
python3 "$Q" mem --qmp "$OUT/vm.qmp" --addr 0x40080000 --len 4
python3 "$Q" quit --qmp "$OUT/vm.qmp" >/dev/null
echo "system emulator + QMP ok"

echo "== gdb stub"
rm -f "$OUT/vm2.qmp"
python3 "$Q" start --kernel "$FIX/hello_kernel.elf" --serial-log "$OUT/vm2.log" \
        --qmp "$OUT/vm2.qmp" --gdb 12399 --paused --log "$OUT/qemu2.log" >/dev/null
python3 "$Q" regs --gdb 12399 | python3 -c 'import json,sys; d=json.load(sys.stdin); print("regs ok, pc=%s" % d["pc"])'
python3 "$Q" resume --qmp "$OUT/vm2.qmp" >/dev/null
python3 "$Q" quit --qmp "$OUT/vm2.qmp" >/dev/null

echo "all checks passed ($OUT)"
