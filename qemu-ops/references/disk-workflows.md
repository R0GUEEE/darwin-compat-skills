# Disk workflows

## Formats that matter here

`qemu-img --help` lists the full set; these are the ones with a reason to
exist on a phone:

| format | use |
|---|---|
| `raw` | maximum speed, sparse files are the host's problem; 1:1 with a block device |
| `qcow2` | snapshots, backing files, compression; the default for anything you edit |
| `vmdk` / `vdi` / `vpc` | exporting to VMware / VirtualBox / Hyper-V |
| `dmg` | **reading** macOS disk images (a Darwin-tooling must) |

## Create

```bash
qemu-img create -f qcow2 -o cluster_size=16384,preallocation=metadata d.qcow2 8G
qemu-img create -f qcow2 -b base.qcow2 -F qcow2 overlay.qcow2
```

* `cluster_size` 16384 matches a 16K page host and keeps clusters aligned to
  what the guest filesystem expects.
* `preallocation=metadata` allocates the L2 tables (a few hundred KiB) so the
  first write does not stall; `full` would allocate everything.
* `-b` + `-F` (backing format) is mandatory in modern QEMU; omitting `-F` is
  refused rather than sniffed.

## Snapshots

```bash
qemu-img snapshot -c before-upgrade d.qcow2
qemu-img snapshot -l d.qcow2
qemu-img snapshot -a before-upgrade d.qcow2
qemu-img snapshot -d before-upgrade d.qcow2
```

Internal snapshots live in the qcow2 file and need the VM stopped for
`qemu-img`. For a running VM use QMP (`blockdev-snapshot-internal-sync`) or
`savevm` via HMP. External snapshots (`-drive ...,snapshot=on`, or a new
overlay) are cheaper and let the base stay read-only.

## Convert

```bash
qemu-img convert -f raw -O qcow2 -c big.raw big.qcow2       # compress
qemu-img convert -f qcow2 -O raw d.qcow2 d.raw              # expand
qemu-img convert -f dmg -O raw installer.dmg disk.raw       # read a DMG
qemu-img convert -O vmdk -o subformat=streamOptimized d.qcow2 d.vmdk
```

`-c` on a sparse image is the difference between 900 MB and 50 KB. Converting
a DMG gives you the raw HFS/APFS *filesystem*, not the installer's payload -
`7z`/`hdiutil` semantics differ, and APFS containers need `apfs-fuse` or a
Darwin tool.

## Inspect and repair

```bash
qemu-img info d.qcow2          # virtual vs disk size, backing file, snapshots
qemu-img check d.qcow2         # leaks, refcount errors; -r leaks repairs
qemu-img map d.qcow2           # which guest offsets are allocated
qemu-img amend -o compatible=1.1 d.qcow2
```

`qemu-img map` is how you prove a "compressed copy" is actually sparse:
`allocate != length` means holes survived.

## Resize

```bash
qemu-img resize d.qcow2 +2G        # grow (shrink needs --shrink, dangerous)
```

Growing the image does not grow the guest filesystem; that needs `resize2fs`
in the guest (ext4) or `xfs_growfs`. Do the image first, filesystem second,
and keep a snapshot before shrinking.

## Attach and share

```bash
# in a guest
qemu-system-aarch64 ... -drive file=d.qcow2,if=virtio,format=qcow2,cache=writeback
# read-only share for a second tool
qemu-nbd --read-only -t -p 10809 d.qcow2 &
# macOS host: hdiutil attach nbd://localhost:10809
```

No `/dev/nbd*` inside iSH, so `qemu-nbd` here is server-mode only. Attach from
a host that has the module.

## Habits

* `-snapshot` for anything experimental; the image stays pristine.
* One overlay per experiment, base never mounted read-write.
* `qemu-img check` after any unclean kill - the guest can be fine and the image
  not.
