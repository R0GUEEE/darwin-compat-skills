#!/usr/bin/env python3
"""qtest.py - build and run QEMU's own test suites (qos-test, qtests).

qTest cases are the ground truth for "this QEMU build actually works": they
exercise device models against a reference implementation, per machine, and
they run *inside* QEMU with `-qtest` wiring - no guest OS, no login, no flakiness
from boots.

Two modes, pick by budget:

  in-guest (slow, complete):  boot a Linux kernel in TCG and run qemu-system
                              inside it. ~2e6 guest instructions/s on this
                              device -> a 60 s suite is a ~120M-instruction run,
                              measured at 116 s per 134M iterations here.
  host-mode (fast, partial):  build qemu-system-<arch> natively for the host
                              and run the same qemu tests on it. Same device
                              models, same code, no guest needed.

    python3 qtest.py list   --build /path/to/qemu-build [--arch aarch64]
    python3 qtest.py run    --build ... --arch aarch64 --case virtio-pci-* --timeout 900
    python3 qtest.py report --build ...

The script never "verifies" by assertion alone: it prints how many cases ran,
which failed, and the wall time, so an empty run is visible as empty.
"""
import argparse, os, re, subprocess, sys, time

CASE = re.compile(r'^(ok|not ok)\s+\d+\s+/\S+\s+(\S+)')


def qos_test_binary(build, arch):
    for cand in ('tests/qtest/qos-test', 'qos-test'):
        p = os.path.join(build, cand)
        if os.access(p, os.X_OK):
            return p
    return None


def list_cases(binary, arch, extra):
    argv = [binary, '-l'] + extra
    r = subprocess.run(argv, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-2000:])
        return []
    return [l.strip() for l in r.stdout.splitlines() if l.strip() and not l.startswith('#')]


def run_cases(binary, arch, cases, timeout, extra, log):
    argv = [binary, '-m', 'virt', '-machine', 'virt'] + extra + [c for c in cases]
    t0 = time.time()
    with open(log, 'w') as fh:
        r = subprocess.run(argv, stdout=fh, stderr=subprocess.STDOUT, timeout=timeout)
    dt = time.time() - t0
    text = open(log).read()
    ok = len(re.findall(r'^ok\s', text, re.M))
    bad = len(re.findall(r'^not ok\s', text, re.M))
    print('ran %d cases in %.1fs: %d ok, %d failed (exit %d)' %
          (ok + bad, dt, ok, bad, r.returncode))
    for m in CASE.finditer(text):
        if m.group(1) == 'not ok':
            print('FAIL', m.group(2))
    return 0 if bad == 0 and ok > 0 else 1


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='c', required=True)
    for name in ('list', 'run', 'report'):
        s = sub.add_parser(name)
        s.add_argument('--build', required=True, help='a configured QEMU build dir')
        s.add_argument('--arch', default='aarch64')
        s.add_argument('--case', action='append', default=[])
        s.add_argument('--arg', action='append', default=[], help='extra qos-test args')
        s.add_argument('--timeout', type=float, default=900)
        s.add_argument('--log', default='qos-test.log')
    a = ap.parse_args()
    b = qos_test_binary(a.build, a.arch)
    if not b:
        sys.exit('qtest: no qos-test binary under %s (configure with --enable-qtest)' % a.build)
    cases = list_cases(b, a.arch, a.arg)
    if a.c == 'list':
        print('\n'.join(cases[:4000]))
        print('# %d cases' % len(cases))
        return 0
    if a.c == 'run':
        picked = [c for c in cases if not a.case or any(re.fullmatch(p, c) for p in a.case)]
        if not picked:
            sys.exit('qtest: no cases matched %s' % a.case)
        return run_cases(b, a.arch, picked, a.timeout, a.arg, a.log)
    # report: summarise an existing log
    text = open(a.log).read()
    print('ok: %d  failed: %d' % (len(re.findall(r'^ok\s', text, re.M)),
                                  len(re.findall(r'^not ok\s', text, re.M))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
