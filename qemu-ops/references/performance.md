# Performance on this device

Measurements taken on the iSH sandbox (aarch64 host, QEMU 9.1.2, TCG only,
no `/dev/kvm`). Every number below was produced here; re-measure before
quoting them for a different device.

## Baseline

| workload | wall time |
|---|---|
| `qemu-aarch64 /bin/true` (user mode) | 0.42 s |
| `-M virt` + freestanding kernel to first UART byte | 0.3–1.4 s |
| loop, 64K×256 iterations | 4.5–5.7 s |
| loop, 64K×1024 iterations | 57.9 s |
| loop, 64K×2048 iterations | 116.9 s |
| `qemu-img convert -c` a 512 KiB raw image | < 0.2 s |
| `qemu-img create` + snapshot | < 0.1 s |

Derived throughput: ~2.3M guest instructions/s, i.e. ~0.43 µs per instruction.
The first-boot numbers are dominated by QEMU start-up (page table build, ELF
load, chardev open) - a 65K-iteration loop finishes faster than a 2-second
sleep.

## What actually helps

1. **Do less in the guest.** Every second of guest CPU is ~2.3M instructions.
   A 60-second userspace test is a 140M-instruction run (measured).
2. **`-M virt` and virtio only.** Emulated PCI IDE/SATA and e1000 are 5–20×
   more expensive per I/O than virtio-blk / virtio-net.
3. **Headless**: `-display none -monitor none`. A graphical console costs 5+ %
   even when nothing draws.
4. **`-serial file:`** instead of stdio: no pty, no echo loop, and the log is
   what your wait logic reads anyway.
5. **Cache the guest kernel page tables** (`-cpu max` vs `cortex-a57` changes
   nothing measurable here; TCG does not model the MMU differently).
6. **Batch I/O in the guest**: one 4 MiB write beats 1024 4 KiB writes by a
   wide margin because each syscall crosses the TCG boundary.

## What does not help

* `-accel tcg,thread=multi`, `-icount auto`, `-accel tcg,thread=single`: all
  three measured >180 s on a workload the default finished in 58 s. On a
  single-core-limited host, multi-threaded TCG's synchronisation cost
  dominates; do not "tune" with these without measuring.
* More RAM: 16 MiB vs 128 MiB on the same loop moved 5.7 s → 4.5 s, i.e.
  noise, except when the guest actually needs the memory.
* `-m 2G` when 256 MiB suffices: larger guest RAM slows every TCG TLB flush.

## Estimating a job

```
seconds ≈ guest_instructions / 2.3e6
```

A distro boot is on the order of 1e9 instructions → ~7 minutes minimum, before
the distro's own services. Anything that "should finish in a minute" on a real
machine is a ten-minute job here; say so up front rather than after the
timeout.

## Keeping the host alive

* Run guests with `timeout` and `-snapshot`.
* Close QMP connections; a leaked socket holds the VNC/console chardevs.
* Watch memory: QEMU reserves guest RAM eagerly. `free -m` before a 2 GiB VM
  on a 4 GiB device; the sandbox OOM-killer kills the largest process (QEMU)
  without a usable message.
* `-D /tmp/qemu-trace.log` only with a narrow `-d` filter; full `in_asm` on a
  boot produces hundreds of MB.
