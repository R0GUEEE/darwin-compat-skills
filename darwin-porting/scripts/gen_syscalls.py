#!/usr/bin/env python3
"""gen_syscalls.py - generate a Darwin syscall table from XNU's syscalls.master.

syscalls.master is the single source of truth: bsd/sys/syscall.h is generated
at build time and is NOT in the source tree (a GET of it 404s on every tag).

    python3 gen_syscalls.py --master syscalls.master --format c    > syscalls_gen.h
    python3 gen_syscalls.py --master syscalls.master --format json > syscalls.json
    python3 gen_syscalls.py --master syscalls.master --check 6,244,520

Facts encoded here (verified on xnu-11215.41.3 and xnu-12377.121.6):
  * ONE numbering for every architecture. arm64 has no private syscall space.
  * numbers are sparse; a hole means "never assigned", not "removed".
    The highest number grows over time (557 in 11215, same in 12377).
  * the same number CAN appear twice (557 = coalition_policy_get | enosys),
    usually under the same #if. A C enum built naively will not compile;
    one symbol per NUMBER, extra names kept as aliases.
  * the `#else` branch of every guard holds the real fallback (often
    `nosys`) or the same semantic call with different ABI. Track both and
    mark which branch you picked, or a backend will answer a bogus EBADF.
  * Files column: only entries with H or ALL belong in a generated header.
  * Dispatch table order for a aarch64 backend: the authoritative order for
    kernel-internal numbers is NOT this file; for userspace ABI this is.
"""
import argparse, json, re, sys

ENTRY = re.compile(r'^(\d+)\s+(\S+)\s+(\S+)\s+\{\s*(.*?)\s*\}\s*(.*)$')
NAME = re.compile(r'(\w+)\s*\(')
ARGS = re.compile(r'\((.*)\)')
NOISE = re.compile(r'NO_SYSCALL_STUB|COMPAT_INTEGRITY_INVERTED')
COND = re.compile(r'^#\s*(if|ifdef|ifndef|else|elif|endif)\b\s*(.*)$')


def parse(master_text):
    """-> list of entries (raw, both branches) sorted by number."""
    out = []
    stack = []       # list of [cond, branch_state]
    for lineno, raw in enumerate(master_text.splitlines(), 1):
        line = raw.rstrip()
        c = COND.match(line)
        if c:
            kind, rest = c.group(1), c.group(2)
            expr = rest.split('/*')[0].split('//')[0].strip()
            if kind in ('if', 'ifdef', 'ifndef'):
                stack.append({'cond': expr, 'taken': 'true', 'else': False})
            elif kind == 'else':
                if stack:
                    stack[-1]['taken'] = 'false'
                    stack[-1]['else'] = True
            elif kind == 'endif':
                if stack:
                    stack.pop()
            continue
        if not line or line.startswith(';') or line.startswith('#'):
            continue
        m = ENTRY.match(line)
        if not m:
            continue
        num, audit, files, decl, comment = m.groups()
        nm = NAME.search(decl)
        if not nm:
            continue
        args = ARGS.search(decl)
        guard = ''
        if stack:
            guard = ' && '.join(
                (g['cond'] if g['taken'] == 'true' else '!(%s)' % g['cond']) for g in stack)
        header = ('H' in files) or files.upper() == 'ALL'
        if 'P' in files and 'H' not in files and files.upper() != 'ALL':
            header = False
        out.append({
            'num': int(num), 'audit': audit, 'files': files,
            'name': nm.group(1),
            'args': NOISE.sub('', args.group(1) if args else '').strip(),
            'decl': decl, 'comment': comment.strip(),
            'guard': guard, 'header': header, 'line': lineno,
        })
    out.sort(key=lambda e: (e['num'], e['line']))
    return out


def dedupe(entries):
    seen, out = {}, []
    for e in entries:
        key = e['num']
        if key in seen:
            seen[key]['aliases'].append({'name': e['name'], 'guard': e['guard']})
            continue
        e['aliases'] = []
        seen[key] = e
        out.append(e)
    return out


def unique_names(entries):
    """nosys appears 90 times and enosys 13 times; the C enum needs one symbol
    per NUMBER with a unique identifier. First occurrence keeps the plain name,
    later ones get _<num>. Names must not collide across entries either."""
    used, out = {}, []
    for e in entries:
        nm = e['name'].upper()
        if nm in used:
            nick = '%s_%d' % (nm, e['num'])
            if nick in used:
                nick += '_alias'
            e2 = dict(e, cname=nick)
            used[nick] = True
        else:
            e2 = dict(e, cname=nm)
            used[nm] = True
        out.append(e2)
    return out


def to_c(entries, maxnum, tag):
    entries = unique_names(entries)
    L = ['/* syscalls_gen.h - generated from xnu %s bsd/kern/syscalls.master. Do not edit. */' % tag,
         '#ifndef DNT_SYSCALLS_GEN_H', '#define DNT_SYSCALLS_GEN_H', '',
         '#define DNT_SYSCALL_MAX %d' % maxnum, '', 'enum dnt_syscall {']
    for e in entries:
        cond = e['guard']
        if cond:
            L.append('#if %s' % cond)
        alias = ''
        if e['aliases']:
            alias = '  /* also: %s */' % ', '.join(a['name'] for a in e['aliases'])
        L.append('    DNT_SYS_%s = %d,%s' % (e['cname'], e['num'], alias))
        if cond:
            L.append('#else')
            L.append('    DNT_SYS_%s_DISABLED = %d,' % (e['cname'], e['num']))
            L.append('#endif')
    by = {e['num']: e['name'] for e in entries}
    L += ['};', '', '/* one name per number; aliases are comments only */',
          'static const char *const dnt_syscall_names[DNT_SYSCALL_MAX + 1] = {']
    for n in range(maxnum + 1):
        L.append('    [%d] = %s,' % (n, '"%s"' % by[n] if n in by else 'NULL'))
    L += ['};', '', '#endif /* DNT_SYSCALLS_GEN_H */']
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--master', required=True)
    ap.add_argument('--format', choices=['json', 'c', 'names'], default='json')
    ap.add_argument('--tag', default='unknown')
    ap.add_argument('--check', help='comma-separated numbers to resolve')
    a = ap.parse_args()
    raw = parse(open(a.master).read())
    uniq = dedupe(raw)
    maxnum = max((e['num'] for e in raw), default=0)

    if a.check:
        for n in [int(x) for x in a.check.split(',')]:
            hits = [e for e in raw if e['num'] == n]
            if not hits:
                print('%4d  UNASSIGNED' % n)
            for h in hits:
                print('%4d  %-28s (%-40s) guard=%s' % (n, h['name'], h['args'] or '-', h['guard'] or '-'))
        return 0

    if a.format == 'c':
        sys.stdout.write(to_c(uniq, maxnum, a.tag))
    elif a.format == 'names':
        for e in raw:
            print('%d\t%s' % (e['num'], e['name']))
    else:
        json.dump({'max': maxnum, 'entries': len(raw), 'unique': len(uniq),
                   'tag': a.tag, 'syscalls': raw}, sys.stdout, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
