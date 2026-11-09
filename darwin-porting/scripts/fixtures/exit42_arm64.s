# exits 42 - the smallest useful conformance test for a loader/interpreter.
    .globl _start
    .text
_start:
    mov x0, #42
    mov x16, #1
    svc #0x80
