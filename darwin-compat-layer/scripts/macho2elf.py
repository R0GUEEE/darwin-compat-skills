#!/usr/bin/env python3
"""macho2elf.py - re-lay a Darwin arm64/x86_64 Mach-O image as a Linux ELF.

    python3 macho2elf.py --in hello_arm64 --out hello.elf --kind exe
    python3 macho2elf.py --in libd.dylib  --out libd.so  --kind so --report r.json

What it does, in order:
  1. parse with machopy (segments, sections, exports, imports)
  2. place every PT_LOAD at a 16K-aligned address derived from its Mach-O
     vmaddr, relative to the Mach-O __TEXT base (so PC-relative code is intact)
  3. map binds through a libc name table; unresolved imports are listed
  4. write ELF64 with correct e_machine, e_flags, phdr alignment

Limit of the approach, stated once: Mach-O preserves `__PAGEZERO` at 0, so the
image wants the low 4 GB. Linux still gives your image whatever it wants above
the mmap base; code that only uses PC-relative addressing survives, code that
dereferences absolute Mach-O vaddrs (gOT slots filled by dyld) does not.
That is the reason a compat layer needs a loader, not just a converter -
see `dnt` in the SKILL for what the loader side looks like.
"""
import argparse, json, os, struct, sys

for _p in (os.environ.get('MACHOTOOLS', ''),
           '/var/minis/skills/darwin-porting/scripts',
           os.path.dirname(os.path.abspath(__file__))):
    if _p and os.path.isdir(_p):
        sys.path.insert(0, _p)

import machopy
from saferead import read_image

EM = {'arm64': 183, 'x86_64': 62, 'i386': 3, 'arm': 40}
LIBC = {'_printf': 'printf', '_puts': 'puts', '_fprintf': 'fprintf', '_strlen': 'strlen',
        '_memcpy': 'memcpy', '_memset': 'memset', '_malloc': 'malloc', '_free': 'free',
        '_open': 'open', '_close': 'close', '_read': 'read', '_write': 'write', '_stat': 'stat',
        '_getenv': 'getenv', '_perror': 'perror', '_exit': 'exit', '_abort': 'abort',
        '__stack_chk_fail': '__stack_chk_fail', 'dyld_stub_binder': None}


def align(v, a):
    return (v + a - 1) & ~(a - 1)


# Darwin `svc #0x80` is 0xd4000801; Linux AArch64 `svc #0` is 0xd4000001.
# Rewriting them is what makes raw-syscall binaries runnable at all; for code
# that goes through libSystem this is a no-op (no svc in the image).
SVC_DARWIN = b'\x01\x10\x00\xd4'
SVC_LINUX = b'\x01\x00\x00\xd4'


def rewrite_svc(blob, rep):
    n = blob.count(SVC_DARWIN)
    if n:
        rep.setdefault('rewritten', {})['svc_0x80'] = n
    return blob.replace(SVC_DARWIN, SVC_LINUX)


def demote_unusable_headers(blob, arch, rep):
    """Keep everything *after* the old Mach-O header bytes.

    Mach-O puts its load commands in the first page(s) of __TEXT, and the
    header word (0xfeedfacf) is an instruction no AArch64 will execute. Zeroing
    the region up to the first section's file offset leaves the non-zero path
    intact (execution starts at the entry, not at file offset 0) and makes the
    image look like plain padding to every disassembler.
    """
    if arch != 'arm64':
        return blob
    if len(blob) >= 4 and blob[:4] == b'\xcf\xfa\xed\xfe':
        rep.setdefault('rewritten', {})['mach_header_zeroed'] = True
        return b'\0' * 32 + blob[32:]
    return blob


def convert(path, out, kind, report_path=None):
    rep = {'segments': [], 'exports': [], 'resolved': [], 'unresolved': [], 'warnings': []}
    d = read_image(path)
    sl = machopy.fat_slices(d)
    m = None
    if sl:
        host = 'arm64' if os.uname().machine == 'aarch64' else 'x86_64'
        for cpu, cs, off, sz, al in sl:
            if machopy.CPU_NAMES.get(cpu) == host:
                m = machopy.MachO(d, off)
                break
        if m is None:
            m = machopy.MachO(d, sl[0][2])
            rep['warnings'].append('host arch missing; used first slice')
    else:
        m = machopy.MachO(d)
    if m.bits != 64:
        raise SystemExit('macho2elf: 32-bit images are out of scope')

    text = m.text_base()
    loads = []
    for s in m.segs:
        if s['segname'] == '__PAGEZERO' or s['filesize'] == 0:
            continue
        data = d[s['fileoff']:s['fileoff'] + s['filesize']]
        vaddr = align(text + (s['vmaddr'] - text), 0x4000)
        loads.append({'name': s['segname'], 'vaddr': vaddr, 'data': data, 'prot': s['initprot']})
        rep['segments'].append({'name': s['segname'], 'vaddr': hex(vaddr),
                                'size': len(data), 'prot': s['initprot']})
    if not loads:
        raise SystemExit('macho2elf: no loadable segments')

    rep['exports'] = sorted(m.exports())
    for name in sorted(m.external_names()):
        v = LIBC.get(name, False)
        if v is False:
            rep['unresolved'].append(name)
        elif v:
            rep['resolved'].append([name, v])

    # --- ELF writer ---
    # A DT_NULL-only PT_DYNAMIC is enough for the kernel, but dlopen needs a
    # real linker view: .dynsym must contain global symbols or `dlsym` finds
    # nothing, and the dynamic section must point at hash/strtab/symtab.
    # Symbols are named WITHOUT the Mach-O leading underscore (`_add` -> `add`),
    # which is what Objective-C-free Mach-O C code means and what dlsym callers
    # expect.
    def sym_name(n):
        return n[1:] if n.startswith('_') and n != '_self' else n

    exports = sorted(sym_name(n) for n in m.exports() if n != '_self')
    strtab = bytearray(b'\0')
    offs = {}
    for n in exports:
        offs[n] = len(strtab)
        strtab += n.encode() + b'\0'

    nph = len(loads) + 1
    cur = align(64 + nph * 56, 0x1000)
    phdrs, blobs = [], []
    for L in loads:
        cur = align(cur, 0x1000)
        fileoff = cur
        raw = bytes(L['data'])
        if m.arch == 'arm64':
            raw = rewrite_svc(raw, rep)
            raw = demote_unusable_headers(raw, m.arch, rep)
        blob = raw + b'\0' * (align(len(raw), 0x1000) - len(raw))
        # p_align must match the congruence of offset and vaddr. Mach-O links
        # __TEXT at 0x100000000 with fileoff 0, i.e. mod 0x10000; declaring
        # 0x1000 makes the kernel map the file at the wrong in-page offset and
        # the first instruction fetched is garbage. /bin/ld emits 2^16 for the
        # same reason - copy that.
        phdrs.append(struct.pack(
            '<IIQQQQQQ', 1,
            4 | (2 if L['prot'] & 2 else 0) | (1 if L['prot'] & 1 else 0),
            fileoff, L['vaddr'], L['vaddr'], len(blob), len(blob), 0x10000))
        blobs.append((fileoff, blob))
        cur += len(blob)

    # dynsym: 1 null + N exports, each STB_GLOBAL/STT_FUNC/STV_DEFAULT
    dynsym = struct.pack('<IBBHQQ', 0, 0, 0, 0, 0, 0)
    symvals = {}
    for n in exports:
        v = None
        e = m.exports().get('_' + n) or m.exports().get(n)
        if e and 'address' in e:
            v = text + e['address']
        symvals[n] = v
        dynsym += struct.pack('<IBBHQQ', offs[n], 0x12, 0, 0, v or 0, 0)

    def section(blob, name):
        nonlocal cur
        cur = align(cur, 16)
        fo = cur
        blobs_extra.append((fo, blob))
        cur += len(blob)
        return fo

    blobs_extra = []
    strtab_off = section(bytes(strtab), '.dynstr')
    symtab_off = section(dynsym, '.dynsym')
    # ELF64 hash table (SysV): nbucket, nchain, buckets..., chains...
    n = len(exports) + 1
    nbucket = max(1, n)
    buckets = [0] * nbucket
    chains = [0] * n

    def elf_hash(name):
        h = 0
        for c in name.encode():
            h = ((h << 4) + c) & 0xFFFFFFFF
            g = h & 0xF0000000
            if g:
                h ^= g >> 24
            h &= ~g
        return h

    for i, nm in enumerate(exports, start=1):
        b = elf_hash(nm) % nbucket
        chains[i] = buckets[b]
        buckets[b] = i
    hashtab = struct.pack('<II', nbucket, n) + struct.pack('<%dI' % nbucket, *buckets) \
        + struct.pack('<%dI' % n, *chains)
    hash_off = section(hashtab, '.hash')

    dyn_vaddr_base = loads[-1]['vaddr'] + align(len(loads[-1]['data']), 0x1000) + 0x2000
    dyn = [
        (5, strtab_off + 0),          # DT_STRTAB  (patched to vaddr below)
        (6, symtab_off + 0),          # DT_SYMTAB
        (4, hash_off + 0),            # DT_HASH
        (10, len(strtab)),            # DT_STRSZ
        (11, 24),                     # DT_SYMENT
        (0, 0),
    ]
    def dyn_vaddr(fo):
        # extras live in a synthetic page after the last PT_LOAD
        return dyn_vaddr_base + fo
    dynbytes = b''.join(struct.pack('<qQ', t, v) if t != 0 else struct.pack('<qQ', 0, 0)
                        for t, v in [(5, dyn_vaddr(strtab_off)), (6, dyn_vaddr(symtab_off)),
                                     (4, dyn_vaddr(hash_off)), (10, len(strtab)),
                                     (11, 24), (0, 0)])
    cur = align(cur, 0x1000)
    dyn_off = cur
    blobs_extra.append((dyn_off, dynbytes))
    cur += len(dynbytes)
    phdrs.append(struct.pack('<IIQQQQQQ', 2, 6, dyn_off, dyn_vaddr(dyn_off) + 0x10000 - 0x10000,
                             dyn_vaddr_base, len(dynbytes), len(dynbytes), 8))
    phdrs.append(struct.pack('<IIQQQQQQ', 1, 6, dyn_off, dyn_vaddr(dyn_off),
                             dyn_vaddr(dyn_off), len(dynbytes), len(dynbytes), 0x1000))
    # keep the count consistent with what we emit
    nph = len(phdrs)
    blobs += blobs_extra

    entry = text + (m.entry() - text if m.entry() else 0)
    ehdr = struct.pack('<16sHHIQQQIHHHHHH',
                       b'\x7fELF\x02\x01\x01' + b'\0' * 9,
                       2 if kind == 'exe' else 3,
                       EM.get(m.arch, 183), 1, entry,
                       64, 64, 0, 64, 56, nph, 64, 0, 0)

    total = max([64 + nph * 56] + [fo + len(b) for fo, b in blobs])
    total = align(total, 0x1000)
    img = bytearray(total)
    img[0:64] = ehdr
    ph = b''.join(phdrs)
    img[64:64 + len(ph)] = ph
    for fo, b in blobs:
        img[fo:fo + len(b)] = b
    open(out, 'wb').write(img)
    os.chmod(out, 0o755)
    rep['symbols'] = symvals

    rep['output'] = {'file': out, 'size': len(img), 'entry': hex(entry),
                     'arch': m.arch, 'machine': EM.get(m.arch), 'kind': kind}
    if report_path:
        open(report_path, 'w').write(json.dumps(rep, indent=1))
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--kind', choices=['exe', 'so'], default='exe')
    ap.add_argument('--report')
    a = ap.parse_args()
    rep = convert(a.inp, a.out, a.kind, a.report)
    print(json.dumps({k: rep[k] for k in ('output', 'warnings', 'unresolved')}, indent=1))


if __name__ == '__main__':
    main()
