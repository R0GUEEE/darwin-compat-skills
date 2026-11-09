#!/usr/bin/env python3
"""qvm.py - drive a QEMU instance from the iSH shell over QMP + GDB.

Why QMP and not `expect`: every control surface here is a socket or a file.
stdin is not a reliable control channel when the shell starts QEMU in the
background, but `-qmp unix:...` and `-gdb tcp::...` are.

    python3 qvm.py start --name vm1 --machine virt --cpu cortex-a57 \
        --kernel k.elf --serial-log vm1.log --qmp /tmp/vm1.qmp [--gdb 1234]
    python3 qvm.py status  --qmp /tmp/vm1.qmp
    python3 qvm.py hmp     --qmp /tmp/vm1.qmp --cmd "info registers"
    python3 qvm.py mem     --qmp /tmp/vm1.qmp --addr 0x40080000 --len 32
    python3 qvm.py regs    --gdb 1234                 # full GDB register dump
    python3 qvm.py wait    --log vm1.log --for "hello" --timeout 20
    python3 qvm.py reset   --qmp /tmp/vm1.qmp
    python3 qvm.py quit    --qmp /tmp/vm1.qmp

Notes from this device:
  * `-serial stdio` does not work when stdin is a pipe and the only writer is
    this shell: QEMU sees EOF, then nothing. Use `-serial file:PATH` (or
    `-chardev stdio,id=c,logfile=PATH -serial chardev:c`) and watch the file.
  * a headless `virt` boot reaches first UART output in ~0.3 s under TCG; a
    real distro kernel takes minutes. Always wait on output, never on sleep.
  * `human-monitor-command` is the escape hatch for anything QMP does not
    expose; it needs no extra protocol.
"""
import argparse, json, os, socket, subprocess, sys, time


CHILD = None


def qmp_connect(path, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.startswith('/') and os.path.exists(path):
            break
        time.sleep(0.05)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect(path)
    f = s.makefile('rwb', buffering=0)
    greeting = json.loads(f.readline())
    f.write(b'{"execute":"qmp_capabilities"}\n')
    while True:
        d = json.loads(f.readline())
        if 'return' in d or 'error' in d:
            break
    return s, f, greeting


def qmp_cmd(f, obj):
    f.write((json.dumps(obj) + '\n').encode())
    while True:
        line = f.readline()
        if not line:
            raise SystemExit('qvm: QMP connection closed')
        d = json.loads(line)
        if 'return' in d or 'error' in d:
            return d


def hmp(f, command):
    r = qmp_cmd(f, {'execute': 'human-monitor-command',
                    'arguments': {'command-line': command}})
    return r.get('return', '') if 'return' in r else str(r)


# ------------------------------------------------------------------ actions
def cmd_start(a):
    sock = a.qmp
    if sock.startswith('/') and os.path.exists(sock):
        os.remove(sock)
    argv = ['qemu-system-' + a.machine.split('-')[0] if False else a.binary,
            '-M', a.machine, '-cpu', a.cpu, '-display', 'none', '-monitor', 'none',
            '-qmp', 'unix:%s,server,nowait' % sock]
    if a.kernel:
        argv += ['-kernel', a.kernel]
    if a.append:
        argv += ['-append', a.append]
    if a.serial_log:
        argv += ['-serial', 'file:' + a.serial_log]
    for d in a.drive or []:
        argv += ['-drive', d]
    for n in a.netdev or []:
        argv += ['-netdev', n]
    for d in a.device or []:
        argv += ['-device', d]
    if a.memory:
        argv += ['-m', a.memory]
    if a.smp:
        argv += ['-smp', str(a.smp)]
    if a.gdb:
        argv += ['-gdb', 'tcp::%d' % a.gdb]
    if a.snapshot:
        argv += ['-snapshot']
    if a.paused:
        argv += ['-S']
    log = open(a.log, 'ab') if a.log else subprocess.DEVNULL
    p = subprocess.Popen(argv, stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                         start_new_session=True)
    global CHILD
    CHILD = p
    # wait for QMP so the caller can act immediately
    s, f, greet = qmp_connect(sock, a.timeout)
    print(json.dumps({'pid': p.pid, 'qmp': sock,
                      'qemu': greet['QMP']['version']['qemu'],
                      'argv': argv}, indent=1))
    return 0


def with_qmp(a, fn):
    s, f, _ = qmp_connect(a.qmp)
    try:
        return fn(f)
    finally:
        s.close()


def cmd_status(a):
    def fn(f):
        st = qmp_cmd(f, {'execute': 'query-status'})
        out = {'qemu_status': st.get('return')}
        for key, q in (('cpus', 'query-cpus-fast'), ('block', 'query-block')):
            r = qmp_cmd(f, {'execute': q})
            if 'return' in r:
                out[key] = r['return']
        print(json.dumps(out, indent=1))
    return with_qmp(a, fn)


def cmd_hmp(a):
    print(with_qmp(a, lambda f: hmp(f, a.cmd)), end='')


def cmd_mem(a):
    print(with_qmp(a, lambda f: hmp(f, 'x /%db %#x' % (a.len, a.addr))), end='')


def cmd_reset(a):
    print(with_qmp(a, lambda f: qmp_cmd(f, {'execute': 'system_reset'})))


def cmd_quit(a):
    try:
        print(with_qmp(a, lambda f: qmp_cmd(f, {'execute': 'quit'})))
    except (ConnectionError, OSError, SystemExit) as e:
        print('qvm: instance gone (%s)' % e)


def cmd_wait(a):
    """Stream new bytes of a guest log until a marker appears (or any output).

    Waiting on the file is the only reliable synchronisation with QEMU from a
    shell: stdin is not a control channel once QEMU is backgrounded, and a
    sleep-based wait either flakes or wastes minutes on a slow TCG boot.
    """
    deadline = time.time() + a.timeout
    seen = 0
    buf = ''
    while time.time() < deadline:
        try:
            with open(a.log, 'rb') as fh:
                fh.seek(seen)
                chunk = fh.read()
                seen += len(chunk)
        except OSError:
            chunk = b''
        if chunk:
            text = chunk.decode('utf-8', 'replace')
            sys.stdout.write(text)
            sys.stdout.flush()
            buf = (buf + text)[-round(a.match_len * 4):] if a.match else ''
            if not a.match:
                return 0
            if a.match in buf:
                return 0
        time.sleep(0.1)
    sys.stderr.write('qvm: timeout after %.0fs waiting for %r in %s\n'
                     % (a.timeout, a.match, a.log))
    return 2


def _tail(path, needle):
    try:
        return open(path, 'r', errors='replace').read()[-4096:]
    except OSError:
        return ''


def cmd_regs(a):
    """Full register file through the GDB stub; AArch64 order from gdb."""
    s = socket.create_connection(('127.0.0.1', a.gdb), timeout=5)

    def xmit(pkt):
        body = pkt.encode() if isinstance(pkt, str) else pkt
        s.sendall(b'$' + body + b'#' + ('%02x' % (sum(body) & 0xff)).encode())
        buf = b''
        while b'#' not in buf or len(buf) - buf.index(b'#') < 3:
            buf += s.recv(65536)
        return buf.strip()

    # interrupting a running target: ^C then read the stop reply
    s.sendall(b'\x03')
    time.sleep(0.2)
    s.settimeout(0.5)
    try:
        s.recv(4096)          # stop reply (T05...), may already be buffered
    except socket.timeout:
        pass
    s.settimeout(10)
    r = xmit(b'g')
    # GDB replies are `+$payload#xx`; the ack prefix is optional and often
    # absent, so locate the packet instead of assuming byte 0 is `$`.
    start = r.rfind(b'$')
    end = r.rfind(b'#')
    body = r[start + 1:end].decode()
    words = [int(body[i:i + 8], 16) for i in range(0, len(body) - 7, 8)]
    # gdbserver order for aarch64: x0-x30, sp, pc, cpsr  (little endian words)
    names = ['x%d' % i for i in range(31)] + ['sp', 'pc', 'cpsr']
    print(json.dumps({names[i]: hex(w) for i, w in enumerate(words[:34])}, indent=1))
    s.close()
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='c', required=True)

    st = sub.add_parser('start')
    st.add_argument('--binary', default='qemu-system-aarch64')
    st.add_argument('--machine', default='virt')
    st.add_argument('--cpu', default='cortex-a57')
    st.add_argument('--kernel')
    st.add_argument('--append')
    st.add_argument('--serial-log')
    st.add_argument('--drive', action='append')
    st.add_argument('--netdev', action='append')
    st.add_argument('--device', action='append')
    st.add_argument('--memory')
    st.add_argument('--smp', type=int)
    st.add_argument('--gdb', type=int)
    st.add_argument('--qmp', default='/tmp/qvm.qmp')
    st.add_argument('--log', default='/tmp/qvm.qemu.log')
    st.add_argument('--snapshot', action='store_true')
    st.add_argument('--paused', action='store_true')
    st.add_argument('--timeout', type=float, default=10)
    st.set_defaults(fn=cmd_start)

    rp = sub.add_parser('resume')      # start with --paused, then release it
    rp.add_argument('--qmp', required=True)
    rp.set_defaults(fn=lambda a: (print(with_qmp(a, lambda f: qmp_cmd(f, {'execute': 'cont'}))), 0)[1])

    for name, fn in (('status', cmd_status), ('reset', cmd_reset), ('quit', cmd_quit)):
        sp = sub.add_parser(name)
        sp.add_argument('--qmp', required=True)
        sp.set_defaults(fn=fn)

    h = sub.add_parser('hmp')
    h.add_argument('--qmp', required=True)
    h.add_argument('--cmd', required=True)
    h.set_defaults(fn=cmd_hmp)

    m = sub.add_parser('mem')
    m.add_argument('--qmp', required=True)
    m.add_argument('--addr', type=lambda x: int(x, 0), required=True)
    m.add_argument('--len', type=int, default=16)
    m.set_defaults(fn=cmd_mem)

    w = sub.add_parser('wait')
    w.add_argument('--log', required=True)
    w.add_argument('--for', dest='match')
    w.add_argument('--timeout', type=float, default=30)
    w.set_defaults(fn=cmd_wait)
    w.add_argument('--match-len', dest='match_len', type=int, default=256)

    g = sub.add_parser('regs')
    g.add_argument('--gdb', type=int, required=True)
    g.set_defaults(fn=cmd_regs)

    a = p.parse_args()
    r = a.fn(a)
    sys.exit(r if isinstance(r, int) else 0)


if __name__ == '__main__':
    main()
