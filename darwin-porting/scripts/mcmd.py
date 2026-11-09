#!/usr/bin/env python3
"""mcmd.py - otool/lipo/install_name_tool equivalents that work on Linux.

    python3 mcmd.py info   FILE        # header, segments, dylibs, rpaths, sig
    python3 mcmd.py deps   FILE        # LC_LOAD_DYLIB table
    python3 mcmd.py exports FILE       # export trie (what it offers)
    python3 mcmd.py undef  FILE        # undefined symbols
    python3 mcmd.py imports FILE       # fixup/import table (what it needs)
    python3 mcmd.py symtab FILE        # all nlist entries
    python3 mcmd.py slices FILE        # universal slices + cpu types
    python3 mcmd.py sections FILE

Comparison commands, in order of trust: llvm-objdump --macho, llvm-otool,
this tool. When they disagree, believe llvm and find out why.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import machopy
from saferead import read_image, verify


def images(path):
    d = read_image(path)
    bad = verify(d, path)
    if bad:
        sys.stderr.write('mcmd: warning: buffer diverges from disk at %s\n' % bad)
    sl = machopy.fat_slices(d)
    if sl:
        return [(machopy.CPU_NAMES.get(c, hex(c)), machopy.MachO(d, off)) for c, cs, off, sz, al in sl]
    return [(machopy.CPU_NAMES.get(machopy.MachO(d).cputype), machopy.MachO(d))]


def cmd_info(a):
    out = []
    for arch, m in images(a.file):
        out.append({
            'file': a.file, 'arch': arch, 'type': m.typename, 'bits': m.bits,
            'cpu': hex(m.cputype), 'subtype': hex(m.cpusub), 'uuid': m.uuid(),
            'platform': m.platform_name(), 'minos': m.minos(),
            'flags': hex(m.flags), 'pie': bool(m.flags & 0x200000),
            'entry': hex(m.entry()) if m.entry() else None,
            'encrypted': m.is_encrypted(),
            'signature': m.code_signature() is not None,
            'segments': [{'name': s['segname'], 'vmaddr': hex(s['vmaddr']),
                          'fileoff': s['fileoff'], 'filesize': s['filesize'],
                          'sections': [x['sect'] for x in s.get('sections', [])]}
                         for s in m.segs],
            'dylibs': [x.get('name') for x in m.dylibs()],
            'rpaths': [x['path'] for x in m.get_all('LC_RPATH')],
            'install_name': (m.get('LC_ID_DYLIB') or {}).get('name'),
        })
    print(json.dumps(out[0] if len(out) == 1 else out, indent=1))


def cmd_deps(a):
    for arch, m in images(a.file):
        for lib in m.dylibs():
            print('%-8s %-10s %s' % (arch, lib.get('kind'), lib.get('name')))


def cmd_exports(a):
    for arch, m in images(a.file):
        for name, e in sorted(m.exports().items()):
            if 'reexport' in e:
                print('%-8s %-44s reexport %s' % (arch, name, e['reexport']))
            else:
                tag = '' if e.get('kind') == 'regular' else ' [' + e.get('kind', '') + ']'
                print('%-8s %-44s %#x%s' % (arch, name, e.get('address', 0), tag))


def cmd_undef(a):
    for arch, m in images(a.file):
        for s in m.undefined_symbols():
            print('%s %s' % (arch, s['name']))


def cmd_imports(a):
    for arch, m in images(a.file):
        libs = [x.get('name') for x in m.dylibs()]
        for lib, name, add, weak in m.imports_table():
            if lib < 0:
                src = 'flat'
            elif lib < len(libs):
                src = '%s [%d]' % (libs[lib], lib + 1)
            else:
                src = 'lib%d?' % (lib + 1)
            print('%-8s %-44s %s%s' % (arch, name, src, ' (weak)' if weak else ''))


def cmd_symtab(a):
    for arch, m in images(a.file):
        for s in m.symbols():
            print('%-8s %-48s %-6s %#x' % (arch, s['name'], s['kind'], s['value']))


def cmd_slices(a):
    d = read_image(a.file)
    sl = machopy.fat_slices(d)
    if not sl:
        m = machopy.MachO(d)
        print('thin %s (magic %#x)' % (m.arch, machopy.u32(d, 0)))
        return
    for c, cs, off, sz, al in sl:
        print('%-10s cpusub=%#x off=%d size=%d align=2^%d' % (machopy.CPU_NAMES.get(c, hex(c)), cs, off, sz, al))


def cmd_sections(a):
    for arch, m in images(a.file):
        for s in m.sections:
            print('%-8s %-12s %-18s addr=%#x size=%#x off=%#x flags=%#x' %
                  (arch, s['seg'], s['sect'], s['addr'], s['size'], s['offset'], s['flags']))


def main():
    p = argparse.ArgumentParser(prog='mcmd', description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='c', required=True)
    for name, fn in (('info', cmd_info), ('deps', cmd_deps), ('exports', cmd_exports),
                     ('undef', cmd_undef), ('imports', cmd_imports), ('symtab', cmd_symtab),
                     ('slices', cmd_slices), ('sections', cmd_sections)):
        s = sub.add_parser(name)
        s.add_argument('file')
        s.set_defaults(fn=fn)
    a = p.parse_args()
    try:
        a.fn(a)
    except (OSError, ValueError, EOFError) as e:
        sys.exit('mcmd: %s: %s' % (a.file, e))


if __name__ == '__main__':
    main()
