#!/bin/sh
# Build the QEMU fixtures in this directory. Requires: clang (or as), ld, qemu-img.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$HERE/out}
mkdir -p "$OUT"

clang --target=aarch64-none-elf -c "$HERE/hello_kernel.s" -o "$OUT/hello_kernel.o"
ld -T "$HERE/link.ld" -nostdlib -o "$OUT/hello_kernel.elf" "$OUT/hello_kernel.o"
qemu-img create -f qcow2 "$OUT/base.qcow2" 32M >/dev/null
qemu-img snapshot -c clean "$OUT/base.qcow2"
printf 'boot=1\n' > "$OUT/boot.txt"
printf 'reboot 3\n' > "$OUT/reset_cmds.txt"
echo "built: $OUT/hello_kernel.elf $OUT/base.qcow2"
qemu-img info "$OUT/base.qcow2" | head -3
