#!/usr/bin/env python3
"""gen_sysctl.py - MIB tables for a Darwin compatibility layer.

Darwin userspace says "kern.proc.pid", "hw.ncpu", "hw.memsize". Those become
MIB arrays (CTL_KERN, KERN_PROC, KERN_PROC_PID, pid). The numbers live in
exactly one place: XNU `bsd/sys/sysctl.h` - and the whole block is wrapped in
`#ifdef SYSCTL_DEF_ENABLED`, which is why naive scrapers find nothing.

    python3 gen_sysctl.py --sysctl-h $XNU/bsd/sys/sysctl.h --check kern.proc.pid,hw.ncpu
    python3 gen_sysctl.py --sysctl-h ... --c > sysctl_gen.h
    python3 gen_sysctl.py --sysctl-h ... --json > sysctl.json

Each namespace block is delimited by its own comment:
    /* CTL_KERN identifiers */ ... until the next `/*! ... */` divider.
"""
import argparse, json, re, sys

TOP = re.compile(r'^#define\s+CTL_([A-Z_]+)\s+(\d+)')
NUMBERED = re.compile(r'^#define\s+([A-Z][A-Z0-9_]*)\s+(\d+)\s*(?:/\*\s*(.*?)\s*\*/)?')
BLOCK = re.compile(r'^\s*(?:/\*|\*)\s*(?:CTL_)?([A-Z_]+) identifiers\s*(?:\*/)?\s*$')


def parse(path):
    ns, out = None, {}
    for raw in open(path):
        line = raw.strip()
        m = BLOCK.search(line)
        if m:
            ns = m.group(1)
            out.setdefault(ns, {})
            continue
        t = TOP.match(line)
        if t:
            out.setdefault('TOP', {})['CTL_' + t.group(1)] = {'num': int(t.group(2)), 'comment': ''}
            continue
        if ns is None:
            continue
        n = NUMBERED.match(line)
        if n:
            # keep the namespace's own prefix only (KERN_*, HW_*, ...); other
            # prefixes inside a block belong to nested sub-namespaces and would
            # otherwise collide in a flat enum
            name = n.group(1)
            pref = NS_PREFIX.get(ns, '')
            if pref and not name.startswith(pref):
                continue
            out[ns][name] = {'num': int(n.group(2)), 'comment': (n.group(3) or '')[:60]}
    return out


NAMES = {'KERN': 'kern', 'HW': 'hw', 'VM': 'vm', 'VFS': 'vfs', 'NET': 'net',
         'MACHDEP': 'machdep', 'USER': 'user', 'DEBUG': 'debug'}


def resolve(table, spec):
    """'kern.proc.pid' -> [CTL_KERN, KERN_PROC, KERN_PROC_PID] or None."""
    ns, _, rest = spec.partition('.')
    upper = ns.upper()
    entry = table.get(upper, {})
    mib = [table.get('TOP', {}).get('CTL_' + upper, {}).get('num')]
    cur = rest
    while cur:
        head, _, tail = cur.partition('.')
        cand = head.upper()
        direct = entry.get(cand) or entry.get((NS_PREFIX.get(upper, upper) + cand) if cur is rest else cand)
        if direct is None:
            return None
        mib.append(direct['num'])
        cur = tail
    return mib


NS_PREFIX = {'KERN': 'KERN_', 'HW': 'HW_', 'VM': 'VM_', 'VFS': 'VFS_', 'NET': 'NET_',
             'MACHDEP': 'MACH_', 'USER': 'USER_', 'DEBUG': 'DBG_'}


def to_c(table):
    L = ['/* generated from XNU bsd/sys/sysctl.h */']
    for ns, entries in sorted(table.items()):
        if ns == 'TOP':
            continue
        if not entries:
            continue          # an empty enum is a compile error, not a no-op
        L += ['', 'enum dnt_sysctl_%s {' % NAMES.get(ns, ns.lower())]
        for name, v in sorted(entries.items(), key=lambda kv: kv[1]['num']):
            L.append('    DNT_%s = %d,   /* %s */' % (name, v['num'], v['comment'][:44]))
        L.append('};')
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sysctl-h', required=True)
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--c', action='store_true')
    ap.add_argument('--check', help='comma separated: kern.proc.pid,hw.ncpu')
    a = ap.parse_args()
    table = parse(a.sysctl_h)
    if a.check:
        for spec in a.check.split(','):
            mib = resolve_any(table, spec)
            print('%-26s %s' % (spec, mib if mib else 'NOT FOUND'))
        return 0
    if a.c:
        print(to_c(table))
    else:
        json.dump(table, sys.stdout, indent=1, sort_keys=True)
    return 0


def resolve_any(table, spec):
    """Resolve regardless of how the header names the constant."""
    ns, _, rest = spec.partition('.')
    upper = ns.upper()
    top = table.get('TOP', {}).get('CTL_' + upper, {}).get('num')
    if top is None:
        return None
    mib = [top]
    parts = rest.split('.') if rest else []
    entries = table.get(upper, {})
    for i, part in enumerate(parts):
        want = (NS_PREFIX.get(upper, '') + part).upper()
        hit = entries.get(want) or entries.get(part.upper())
        if hit is None:
            return None
        mib.append(hit['num'])
    return mib


if __name__ == '__main__':
    sys.exit(main())
