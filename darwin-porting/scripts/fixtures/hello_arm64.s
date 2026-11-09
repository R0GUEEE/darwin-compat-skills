# Minimal Darwin arm64 executable: no libSystem, raw syscalls.
#   x0 = fd, x1 = buf, x2 = len, x16 = syscall number, svc #0x80
#   4 = write, 1 = exit.  Build:
#   clang --target=arm64-apple-macos11 -c hello_arm64.s
#   ld64.lld -arch arm64 -platform_version macos 11.0 11.0 -e _start hello_arm64.o -o hello_arm64
    .globl _start
    .text
_start:
    mov x0, #1
    adr x1, msg
    mov x2, #15
    mov x16, #4
    svc #0x80
    mov x0, #0
    mov x16, #1
    svc #0x80
msg:
    .ascii "hello, darwin\n\n\n"
