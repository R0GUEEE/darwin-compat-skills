// qemu-ops fixture: freestanding aarch64 "kernel" for `-M virt`.
// Writes a banner to the PL011 UART at 0x09000000, then parks forever.
// No firmware, no kernel, no rootfs: boots in ~0.3 s under TCG and gives
// automation a deterministic first byte to wait for.
    .section .text
    .global _start
_start:
    ldr x1, =0x09000000          // PL011 data register
    adr x2, msg
1:  ldrb w3, [x2], #1
    cbz w3, 2f
    strb w3, [x1]
    b 1b
2:  wfe
    b 2b
msg:
    .asciz "qemu-ops: hello from aarch64 virt\n"
    .p2align 3
