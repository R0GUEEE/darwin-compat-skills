#!/usr/bin/env python3
"""abi_probe.py - derive the Darwin struct ABI from the SDK headers, by compiling.

Offsets and sizes are NOT guesswork: they are whatever the target's own headers
say, read out of the compiled object. This is how you settle questions like
"is mode_t 16 bits", "does struct dirent carry a 64-bit d_seekoff", "how big is
sigset_t" without trusting memory or a web page.

    python3 abi_probe.py --sdk /opt/sdks-src/iPhoneOS16.5.sdk --target arm64-apple-ios14
    python3 abi_probe.py --sdk /path/to/MacOSX.sdk --target x86_64-apple-macos11

How it works: one function per field returning sizeof/offsetof, compiled with
the SDK's own headers, then each function's `mov w0, #imm` / `mov x0, #imm`
is read back from the disassembly. No execution on the host is required, so
this works for arm64 targets from an x86 or arm64 Linux box alike.

Gotchas that cost time:
  * clang's `sizeof(mode_t)` is `w0` (32-bit) - a negative test result shows
    up as `mvn w0, #0` on current clang; absent that, 0 is a real offset.
  * optimised code (>= -O1) folds every probe into a constant, which is what
    we want; at -O0 the accesses leak into memory and the pattern breaks.
  * function symbols are `_abi_N` on Darwin Mach-O, `abi_N` on ELF. Accept both.
"""
import argparse, os, re, subprocess, sys, tempfile

HEADERS = r'''
#include <stddef.h>
#include <sys/stat.h>
#include <sys/dirent.h>
#include <dirent.h>
#include <signal.h>
#include <sys/resource.h>
#include <sys/time.h>
#include <termios.h>
#include <sys/socket.h>
#include <pthread.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <sched.h>
#include <poll.h>
'''

# (type, field) - field None means "sizeof the type"
FIELDS = [
    ('struct stat', None), ('struct stat', 'st_dev'), ('struct stat', 'st_ino'),
    ('struct stat', 'st_mode'), ('struct stat', 'st_nlink'), ('struct stat', 'st_uid'),
    ('struct stat', 'st_rdev'), ('struct stat', 'st_atimespec'), ('struct stat', 'st_size'),
    ('struct stat', 'st_blocks'), ('struct stat', 'st_blksize'), ('struct stat', 'st_flags'),
    ('struct dirent', None), ('struct dirent', 'd_ino'), ('struct dirent', 'd_namlen'),
    ('struct dirent', 'd_type'), ('struct dirent', 'd_seekoff'),
    ('struct sigaction', None), ('struct sigaction', 'sa_handler'), ('struct sigaction', 'sa_mask'),
    ('struct rlimit', None), ('struct timeval', None), ('struct timespec', None),
    ('struct termios', None), ('struct sockaddr', None), ('struct sockaddr_storage', None),
    ('struct pollfd', None), ('struct sched_param', None),
    ('sigset_t', None), ('pthread_t', None), ('off_t', None), ('mode_t', None),
    ('dev_t', None), ('ino_t', None), ('blkcnt_t', None), ('blksize_t', None),
]


def emit(path):
    body = []
    names = []
    for i, (t, f) in enumerate(FIELDS):
        if f is None:
            body.append('size_t abi_%d(void) { return sizeof(%s); }' % (i, t))
            names.append('%s.size' % t)
        else:
            body.append('size_t abi_%d(void) { return offsetof(%s, %s); }' % (i, t, f))
            names.append('%s.%s' % (t, f))
    with open(path, 'w') as fh:
        fh.write(HEADERS + '\n' + '\n'.join(body) + '\n')
    return names


def compile_obj(sdk, target, src, obj):
    cmd = ['clang', '--target=' + target, '-O1', '-c', src, '-o', obj]
    if sdk:
        cmd[1:1] = ['-isysroot', sdk]
    subprocess.run(cmd, check=True)


def read_back(obj):
    dis = subprocess.run(['llvm-objdump', '-d', '--no-show-raw-insn', obj],
                         capture_output=True, text=True).stdout
    out, cur = {}, None
    for line in dis.splitlines():
        m = re.search(r'<[_]?(abi_\d+|ltmp\d+)>:', line)
        if m:
            tok = m.group(1)
            cur = int(tok[4:]) if tok.startswith('abi_') else 0
            continue
        if cur is None or cur in out:
            continue
        m = re.search(r'\bmov(?:z)?\s+([wx]0),\s*#(0x[0-9a-f]+|-?\d+)', line)
        if m:
            out[cur] = int(m.group(2), 0) & 0xFFFFFFFF
            continue
        if re.search(r'\bmvn\s+w0,\s*#0', line):
            out[cur] = -1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sdk', default=os.environ.get('SDK'), help='path to Foo.sdk')
    ap.add_argument('--target', default='arm64-apple-ios14')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    if not a.sdk:
        sys.exit('abi_probe: --sdk (or $SDK) is required; try /opt/sdks-src/*.sdk')

    tmp = tempfile.mkdtemp(prefix='abiprobe.')
    src, obj = os.path.join(tmp, 'p.c'), os.path.join(tmp, 'p.o')
    names = emit(src)
    compile_obj(a.sdk, a.target, src, obj)
    got = read_back(obj)
    missing = [names[i] for i in range(len(names)) if i not in got]
    if missing:
        sys.stderr.write('abi_probe: no constant found for %s\n' % ', '.join(missing[:5]))

    if a.json:
        import json
        print(json.dumps({names[i]: got[i] for i in sorted(got)}, indent=1))
    else:
        print('# %s (%s)' % (a.sdk, a.target))
        for i in sorted(got):
            print('%-34s %s' % (names[i], got[i] if got[i] != -1 else 'N/A'))


if __name__ == '__main__':
    main()
