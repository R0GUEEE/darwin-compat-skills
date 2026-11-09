#!/bin/sh
# Build real Darwin binaries with the LLVM tools already in the iSH sandbox.
# Everything here is ground truth: a loader tested only against hand-made blobs
# will happily accept garbage.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$HERE/out}
mkdir -p "$OUT"

for pair in "arm64:macos11:hello_arm64" "arm64:macos11:exit42_arm64"; do
    arch=${pair%%:*}; rest=${pair#*:}; plat=${rest%%:*}; src=${rest##*:}
    clang --target=${arch}-apple-${plat} -c "$HERE/$src.s" -o "$OUT/$src.o"
    ld64.lld -arch "$arch" -platform_version macos 11.0 11.0 -e _start \
        "$OUT/$src.o" -o "$OUT/$src"
    echo "built $OUT/$src"
done

# x86_64 variant: exercises the other cputype in the same loader path
clang --target=x86_64-apple-macos11 -c "$HERE/exit42_x86_64.s" -o "$OUT/exit42_x86_64.o"
ld64.lld -arch x86_64 -platform_version macos 11.0 11.0 -e _start \
    "$OUT/exit42_x86_64.o" -o "$OUT/exit42_x86_64"
echo "built $OUT/exit42_x86_64"

# a dylib + an exe that imports from it: the only way to exercise bind opcodes
clang --target=arm64-apple-macos11 -fPIC -c "$HERE/libd.c" -o "$OUT/libd.o"
ld64.lld -arch arm64 -platform_version macos 11.0 11.0 -dylib \
    -install_name libd.dylib "$OUT/libd.o" -o "$OUT/libd.dylib"
clang --target=arm64-apple-macos11 -fPIC -c "$HERE/used.c" -o "$OUT/used.o"
ld64.lld -arch arm64 -platform_version macos 11.0 11.0 -e _start \
    -undefined dynamic_lookup "$OUT/used.o" "$OUT/libd.dylib" -o "$OUT/used"
echo "built $OUT/libd.dylib + $OUT/used"

# universal binary: lipo equivalent, free with llvm-lipo
llvm-lipo -create "$OUT/exit42_arm64" "$OUT/exit42_x86_64" -output "$OUT/exit42_fat"
echo "built $OUT/exit42_fat"

for f in "$OUT"/*; do
    case "$f" in *.o|*.s|*.c) continue;; esac
    printf '%-24s ' "$(basename "$f")"
    file "$f"
done
