---
name: qemu-ops
version: 1.0.0
description: Manage QEMU on this device and elsewhere - pick the right emulator (qemu-user vs qemu-system), drive a running instance over QMP/GDB instead of stdin, build and snapshot qcow2 images, run QEMU's own qtest suites, and work around the TCG speed and sandbox limits of iSH. Use for any QEMU, qemu-img, qcow2, qemu-system-aarch64, qemu-user, QMP, gdb-stub or qtest request.
triggers: qemu, qcow2, qemu-img, qemu-system, qemu-user, QMP, qtest, VM
---

# QEMU operations

## 1. Which emulator, and what it costs here

| Need | Tool | Cost on this device |
|---|---|---|
| run one Linux binary of another arch | `qemu-<arch>` (user mode) | startup ~0.4 s, I/O-bound work barely slower |
| run firmware / kernel / whole OS | `qemu-system-<arch>` | TCG only: measured **~2.3M guest instructions/s** (134M loop iterations in 117 s) |
| create / convert / snapshot disks | `qemu-img` | native, fast |
| serve a disk over NBD | `qemu-nbd` | native; no `/dev/nbd*` here, so remote clients only |

Installed: `qemu-x86_64`, `qemu-aarch64` (user), `qemu-system-aarch64`,
`qemu-img`, `qemu-nbd`. More with `apk add qemu-system-x86_64
qemu-system-arm qemu-system-riscv64`.

No KVM on iSH - `-accel help` lists kvm but `/dev/kvm` does not exist. Plan for
TCG. A headless `virt` machine reaches its first UART byte in ~0.3 s; a real
distro userspace boot is minutes.

**Calibration** (cortex-a57, `-M virt`, headless, 2-instruction loop):
64K×256 iterations 4.5-5.7 s, 64K×1024 58 s, 64K×2048 117 s. Estimate any
guest workload as `seconds ≈ guest_instructions / 2.3e6` before promising a
result.

## 2. Control it over QMP, not stdin

`-serial stdio` is unreliable once QEMU is backgrounded with a piped stdin
(QEMU sees EOF; the guest console gets nothing). Everything a script needs is a
socket or a file:

```bash
Q=/var/minis/skills/qemu-ops/scripts/qvm.py
python3 $Q start --machine virt --cpu cortex-a57 --kernel k.elf \
        --serial-log vm.log --qmp /tmp/vm.qmp --gdb 1234 --log /tmp/vm.boot.log
python3 $Q wait   --log vm.log --for "login:" --timeout 120
python3 $Q hmp    --qmp /tmp/vm.qmp --cmd "info registers"
python3 $Q mem    --qmp /tmp/vm.qmp --addr 0x40080000 --len 8
python3 $Q status --qmp /tmp/vm.qmp
python3 $Q resume --qmp /tmp/vm.qmp          # release a --paused start
python3 $Q quit   --qmp /tmp/vm.qmp
```

`--paused` (`-S`) + the GDB stub gives a VM stopped before instruction 0.
`gdb` here does handle aarch64 (`show architecture` → `auto (currently
"aarch64")`); `target remote :1234`, `file k.elf`, `break *addr`,
`continue`, `info registers`, `x/4i $pc` all work, and gdb detects the stop
itself - no `vCont` handshake needed.

QMP mechanics that cost time:
* read the greeting, send `qmp_capabilities`, and only then will anything
  else answer;
* `human-monitor-command` is the escape hatch for everything outside the QMP
  schema (`info registers`, `x /8xb ADDR`, `info mtree`);
* `system_reset` returns immediately - re-`query-status` to confirm.

## 3. Disks: build once, snapshot, then throw away

```bash
qemu-img create -f qcow2 -o cluster_size=16384,preallocation=metadata d.qcow2 8G
qemu-img snapshot -c clean d.qcow2
qemu-img snapshot -l d.qcow2
qemu-img snapshot -a clean d.qcow2
qemu-img check d.qcow2
qemu-img convert -c -f raw -O qcow2 big.raw big.qcow2     # -c compresses
```

* `qemu-img rebase -b base.qcow2 child.qcow2` needs `-F qcow2`; it refuses to
  sniff a backing format (security fix), and says so plainly.
* Run throwaway guests with `-snapshot`; no write reaches the image, so a
  crashed boot cannot poison a reusable base.
* `-O qcow2 -c` on a mostly-empty raw image yields tens of KB, not gigabytes.

## 4. Networking and sharing

`-netdev user` (slirp) is the only backend needing no privileges here;
`hostfwd` publishes a guest port:

```bash
-netdev user,id=n0,hostfwd=tcp::10022-:22 -device virtio-net-device,netdev=n0
```

`tap` needs `CAP_NET_ADMIN` and a host bridge (not available in iSH); use
slirp, or `-netdev socket` for two QEMU instances talking to each other. 9p
(`-virtfs local,path=DIR,mount_tag=host`) shares a directory without rebuilding
an image; the guest kernel needs `9pnet_virtio`.

## 5. Test with QEMU's own suites

qTest cases check device models against a reference - the cheapest proof that a
build or machine configuration is sane.

```bash
python3 scripts/qtest.py list --build /path/qemu-build
python3 scripts/qtest.py run  --build /path/qemu-build --case 'virtio-pci-*' --timeout 900
python3 scripts/qtest.py report --build /path/qemu-build
```

In-guest route (qemu-system boots Linux, runs qos-test) is honest but slow:
budget tens of minutes at ~2.3M instr/s. Host-mode route (native
`qemu-system-aarch64` + its qos-test) exercises the same device models without
TCG and is the fast path.

## 6. Fixtures and self-check

```bash
sh scripts/fixtures/build_fixtures.sh /tmp/qfix
python3 scripts/qvm.py start --kernel /tmp/qfix/hello_kernel.elf \
        --serial-log /tmp/qfix/out.log --qmp /tmp/qfix.qmp
python3 scripts/qvm.py wait --log /tmp/qfix/out.log --for hello --timeout 10
```

`qemu-ops: hello from aarch64 virt` means emulator, QMP and the serial path all
work. Everything else builds on that check; if it fails, nothing else is
worth debugging until it passes.

## References

- `references/qmp-recipes.md` - commands per task, with reply shapes
- `references/disk-workflows.md` - images, snapshots, conversion, resizing
- `references/performance.md` - TCG measurements and what is worth tuning
