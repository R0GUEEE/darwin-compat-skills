# QMP recipes

All examples assume `qmp = unix:/tmp/vm.qmp,server,nowait` and a client that
has read the greeting and sent `qmp_capabilities`.

## Handshake (python)

```python
import json, socket
s = socket.socket(socket.AF_UNIX); s.connect('/tmp/vm.qmp')
f = s.makefile('rwb', buffering=0)
json.loads(f.readline())                       # {"QMP": {"version": ...}}
f.write(b'{"execute":"qmp_capabilities"}\n')
json.loads(f.readline())                       # {"return": {}}
def cmd(c):
    f.write((json.dumps(c) + '\n').encode())
    while True:
        d = json.loads(f.readline())
        if 'return' in d or 'error' in d:
            return d
```

`qvm.py` in `scripts/` is exactly this plus argument plumbing.

## Common tasks

| task | command | reply shape |
|---|---|---|
| is it running | `{"execute":"query-status"}` | `{"return":{"status":"running","running":true}}` |
| stop / start | `{"execute":"stop"}` / `{"execute":"cont"}` | `{"return":{}}` |
| reboot | `{"execute":"system_reset"}` | returns at once |
| power off | `{"execute":"quit"}` | connection drops after |
| CPUs | `{"execute":"query-cpus-fast"}` | list with `thread-id`, `cpu-index` |
| blocks | `{"execute":"query-block"}` | devices, `inserted.file`, `ro` |
| dirty bitmap | `{"execute":"query-blockstats"}` | per-device stats |
| balloon | `{"execute":"balloon","arguments":{"value":<bytes>}}` | needs a balloon device |
| save snapshot | `{"execute":"blockdev-snapshot-internal-sync",...}` | needs qcow2 |
| migrate to file | `{"execute":"migrate","arguments":{"uri":"file:/tmp/m"}}` | then poll `query-migrate` |

## Escape hatch: HMP

Anything QMP does not expose is reachable with
`{"execute":"human-monitor-command","arguments":{"command-line":"..."}}`:

```
info registers          -> full CPU state as text
x /16xb 0x40080000      -> memory dump (b = byte, x = hex)
info mtree              -> address space map (why a device is not where you think)
info block              -> block backends and their images
info chardev            -> serial/console wiring (is your log actually attached?)
log in_asm,-exec        -> trace to the -D logfile (huge; filter first)
```

`info chardev` is the fastest way to confirm a `-serial file:` is really
attached after a silent boot.

## GDB stub specifics (AArch64)

* QEMU exposes the stop before `main`, `pc = 0x0` if you attached with `-S`
  and no kernel; with `-kernel` the pc is the kernel entry (0x40080000 for
  `virt`).
* `info registers` / `x/4i $pc` work; `stepi` is slow (TCG single-step) but
  correct.
* Do not send `vCont` by hand unless you also handle the `+` ack framing -
  the reply is `T05thread:01;` with the ack prefix optional. `qvm.py regs`
  locates the packet with `rfind(b'$')` for that reason.
* `-gdb tcp::1234` binds on all interfaces; for a local-only session use
  `-gdb unix:/tmp/vm.gdb,server,nowait` and `target remote /tmp/vm.gdb`.

## Error shapes worth recognising

| reply | meaning |
|---|---|
| `{"error":{"class":"GenericError","desc":"..."}}` | command ran, refused |
| connection closed right after `quit` | normal |
| timeout on first command | you skipped `qmp_capabilities` |
| `CommandNotFound` | this QEMU build lacks the command; check `query-commands` |

`{"execute":"query-commands"}` is the authoritative capability list for the
running binary - read it once per session rather than assuming.
