# x86_64 Darwin exit(42).  Syscall = 0x2000000 | number, rax = number, rdi = arg.
    .globl _start
    .text
_start:
    movl $0x2000001, %eax
    movl $42, %edi
    syscall
