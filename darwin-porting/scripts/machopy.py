"""machopy - Mach-O reader/writer for Linux hosts. Pure stdlib, no page-size
assumptions, safe on 16K-page kernels and on iSH.

Verified against llvm-objdump on real clang/ld64.lld output and on binaries
linked against the iPhoneOS SDK (see tests/ and fixtures/).

The three iSH traps this file is built around:
  * a read() whose length ends on a 16K boundary can return a zeroed tail;
  * slicing and indexing the same buffer can disagree on some offsets;
  * recursive walks over bytes can misread the first byte of a child frame.
So: take the image from one mmap copy, bounds-check every read, and decode
trie/opcode streams with a work queue instead of recursion.

API
    from saferead import read_image
    m = machopy.MachO(read_image(path))     # thin or one slice
    machopy.MachO(d, off)                   # a specific fat slice
    machopy.fat_slices(d)                   # [(cpu, subtype, off, size, align)]
    m.exports(); m.fixups(); m.imports_table(); m.symbols()
    m.dylibs(); m.segs; m.sections; m.get('LC_...')
"""
import struct

try:
    from saferead import read_u32 as read_u32_at   # bounds-checked, slice-based
except ImportError:                                   # standalone use
    def read_u32_at(dd, o):
        if o < 0 or o + 4 > len(dd):
            raise EOFError('u32 out of bounds at %d' % o)
        return (dd[o] | (dd[o + 1] << 8) | (dd[o + 2] << 16) | (dd[o + 3] << 24))

MH_MAGIC, MH_MAGIC_64 = 0xfeedface, 0xfeedfacf
FAT_MAGIC, FAT_MAGIC_64 = 0xcafebabe, 0xcafebabf

LC_SEGMENT, LC_SEGMENT_64 = 0x1, 0x19
LC_SYMTAB, LC_DYSYMTAB = 0x2, 0xb
LC_ID_DYLIB, LC_LOAD_DYLIB = 0xd, 0xc
LC_REEXPORT_DYLIB, LC_LOAD_WEAK_DYLIB, LC_LAZY_LOAD_DYLIB = 0x8000001f, 0x80000018, 0x80000003
LC_LOAD_DYLINKER, LC_RPATH, LC_MAIN = 0xe, 0x8000001c, 0x80000028
LC_DYLD_INFO, LC_DYLD_INFO_ONLY = 0x22, 0x80000022
LC_DYLD_EXPORTS_TRIE, LC_DYLD_CHAINED_FIXUPS = 0x80000033, 0x80000034
LC_CODE_SIGNATURE, LC_FUNCTION_STARTS, LC_DATA_IN_CODE = 0x1d, 0x26, 0x29
LC_BUILD_VERSION, LC_VERSION_MIN_MACOSX, LC_VERSION_MIN_IPHONEOS = 0x32, 0x24, 0x25
LC_UUID, LC_SOURCE_VERSION, LC_ENCRYPTION_INFO, LC_ENCRYPTION_INFO_64 = 0x1b, 0x2a, 0x21, 0x2c
LC_LINKER_OPTION = 0x80000023

LC_NAMES = {
    LC_SEGMENT: 'LC_SEGMENT', LC_SEGMENT_64: 'LC_SEGMENT_64', LC_SYMTAB: 'LC_SYMTAB',
    LC_DYSYMTAB: 'LC_DYSYMTAB', LC_ID_DYLIB: 'LC_ID_DYLIB', LC_LOAD_DYLIB: 'LC_LOAD_DYLIB',
    LC_REEXPORT_DYLIB: 'LC_REEXPORT_DYLIB', LC_LOAD_WEAK_DYLIB: 'LC_LOAD_WEAK_DYLIB',
    LC_LAZY_LOAD_DYLIB: 'LC_LAZY_LOAD_DYLIB', LC_LOAD_DYLINKER: 'LC_LOAD_DYLINKER',
    LC_RPATH: 'LC_RPATH', LC_MAIN: 'LC_MAIN', LC_DYLD_INFO: 'LC_DYLD_INFO',
    LC_DYLD_INFO_ONLY: 'LC_DYLD_INFO_ONLY', LC_DYLD_EXPORTS_TRIE: 'LC_DYLD_EXPORTS_TRIE',
    LC_DYLD_CHAINED_FIXUPS: 'LC_DYLD_CHAINED_FIXUPS', LC_CODE_SIGNATURE: 'LC_CODE_SIGNATURE',
    LC_FUNCTION_STARTS: 'LC_FUNCTION_STARTS', LC_DATA_IN_CODE: 'LC_DATA_IN_CODE',
    LC_BUILD_VERSION: 'LC_BUILD_VERSION', LC_VERSION_MIN_MACOSX: 'LC_VERSION_MIN_MACOSX',
    LC_VERSION_MIN_IPHONEOS: 'LC_VERSION_MIN_IPHONEOS', LC_UUID: 'LC_UUID',
    LC_SOURCE_VERSION: 'LC_SOURCE_VERSION', LC_ENCRYPTION_INFO: 'LC_ENCRYPTION_INFO',
    LC_ENCRYPTION_INFO_64: 'LC_ENCRYPTION_INFO_64', LC_LINKER_OPTION: 'LC_LINKER_OPTION',
}

CPU_NAMES = {0x01000007: 'x86_64', 0x0100000c: 'arm64', 0x0100000c | 0x02000000: 'arm64_32',
             7: 'i386', 12: 'arm', 0x01000000: 'ppc64', 18: 'ppc'}
FTYPE_NAMES = {1: 'OBJECT', 2: 'EXECUTE', 4: 'CORE', 6: 'DYLIB', 7: 'DYLINKER',
               8: 'BUNDLE', 9: 'DSYM', 0xb: 'KEXT_BUNDLE', 5: 'PRELOAD'}
PLATFORM_NAMES = {1: 'macOS', 2: 'iOS', 3: 'tvOS', 4: 'watchOS', 5: 'bridgeOS',
                  6: 'macCatalyst', 7: 'iOS-simulator', 8: 'tvOS-simulator',
                  9: 'watchOS-simulator', 10: 'DriverKit', 11: 'visionOS', 12: 'visionOS-simulator'}

N_STAB, N_PEXT, N_TYPE, N_EXT = 0xe0, 0x10, 0x0e, 0x01
N_UNDF, N_ABS, N_SECT, N_PBUD, N_INDR = 0x0, 0x2, 0xe, 0xc, 0xa


def u32(d, o):
    if o < 0 or o + 4 > len(d):
        raise EOFError('u32 out of bounds at %d (len %d)' % (o, len(d)))
    b = d[o:o + 4]
    if len(b) != 4:
        raise EOFError('short slice at %d' % o)
    # int.from_bytes on the slice: struct.unpack_from and slicing disagree on
    # some offsets under iSH (see references/sandbox-quirks.md)
    return b[0] | (b[1] << 8) | (b[2] << 16) | (b[3] << 24)


def u64(d, o):
    if o < 0 or o + 8 > len(d):
        raise EOFError('u64 out of bounds at %d (len %d)' % (o, len(d)))
    b = d[o:o + 8]
    if len(b) != 8:
        raise EOFError('short slice at %d' % o)
    return int.from_bytes(b, 'little')


def i32(d, o):
    v = u32(d, o)
    return v - (1 << 32) if v & 0x80000000 else v


def u16(d, o):
    if o < 0 or o + 2 > len(d):
        raise EOFError('u16 out of bounds at %d (len %d)' % (o, len(d)))
    b = d[o:o + 2]
    return b[0] | (b[1] << 8)


def cstr(d, o):
    if o < 0 or o >= len(d):
        return ''
    e = d.find(b'\0', o)
    if e < 0:
        e = len(d)
    return d[o:e].decode('utf-8', 'replace')


def uleb(d, p):
    r = s = 0
    while True:
        if p >= len(d):
            raise EOFError('uleb past end at %d' % p)
        b = d[p]; p += 1
        r |= (b & 0x7f) << s
        s += 7
        if not b & 0x80:
            return r, p


def sleb(d, p):
    r = s = 0
    while True:
        if p >= len(d):
            raise EOFError('sleb past end at %d' % p)
        b = d[p]; p += 1
        r |= (b & 0x7f) << s
        s += 7
        if not b & 0x80:
            if b & 0x40:
                r -= 1 << s
            return r, p


def fat_slices(d):
    if len(d) < 8:
        return []
    m = struct.unpack_from('>I', d, 0)[0]
    if m == FAT_MAGIC:
        n = struct.unpack_from('>I', d, 4)[0]
        if n == 0 or n > 64:
            return []
        out = []
        for i in range(n):
            o = 8 + i * 20
            if o + 20 > len(d):
                return []
            c, cs, off, sz, al = struct.unpack_from('>iiIII', d, o)
            out.append((c, cs, off, sz, al))
        return out
    if m == FAT_MAGIC_64:
        n = struct.unpack_from('>I', d, 4)[0]
        if n == 0 or n > 64:
            return []
        out = []
        for i in range(n):
            o = 8 + i * 32
            if o + 32 > len(d):
                return []
            c, cs, off, sz, al, _ = struct.unpack_from('>iiQQII', d, o)
            out.append((c, cs, off, sz, al))
        return out
    return []


class MachO:
    def __init__(self, data, off=0):
        self.data = data
        self.off = off
        if off + 28 > len(data):
            raise ValueError('file too short for a Mach-O header')
        magic = u32(data, off)
        if magic == MH_MAGIC_64:
            self.bits = 64
        elif magic == MH_MAGIC:
            self.bits = 32
        else:
            raise ValueError('not Mach-O (magic %#x)' % magic)
        self.cputype = u32(data, off + 4)
        self.cpusub = u32(data, off + 8)
        self.filetype = u32(data, off + 12)
        self.ncmds = u32(data, off + 16)
        self.sizeofcmds = u32(data, off + 20)
        self.flags = u32(data, off + 24)
        if self.bits == 64 and off + 32 <= len(data):
            self.reserved = u32(data, off + 28)
        self.hdrsize = 32 if self.bits == 64 else 28
        self.cmds = []
        self.segs = []
        self.sections = []
        self._parse()

    # ---- header ----
    @property
    def arch(self):
        return CPU_NAMES.get(self.cputype, 'cpu%#x' % self.cputype)

    @property
    def typename(self):
        return FTYPE_NAMES.get(self.filetype, str(self.filetype))

    def _parse(self):
        d = self.data
        o = self.off + self.hdrsize
        end = min(len(d), self.off + self.hdrsize + self.sizeofcmds)
        for _ in range(self.ncmds):
            if o + 8 > end:
                break
            cmd, cs = u32(d, o), u32(d, o + 4)
            if cs < 8 or o + cs > end:
                break
            e = {'cmd': LC_NAMES.get(cmd, 'LC_%#x' % cmd), 'cmdval': cmd, 'cmdsize': cs, 'off': o}
            try:
                self._one(e, cmd, o, cs)
            except (EOFError, struct.error, UnicodeDecodeError):
                e['truncated'] = True
            self.cmds.append(e)
            o += cs

    def _one(self, e, cmd, o, cs):
        d, b = self.data, self.bits == 64
        if cmd == LC_SEGMENT_64:
            e.update(segname=cstr(d, o + 8), vmaddr=u64(d, o + 24), vmsize=u64(d, o + 32),
                     fileoff=u64(d, o + 40), filesize=u64(d, o + 48),
                     maxprot=u32(d, o + 56), initprot=u32(d, o + 60), nsects=u32(d, o + 64))
            secs = []
            for i in range(e['nsects']):
                sb = o + 72 + 80 * i
                if sb + 80 > o + cs:
                    break
                s = {'sect': cstr(d, sb), 'seg': cstr(d, sb + 16), 'addr': u64(d, sb + 32),
                     'size': u64(d, sb + 40), 'offset': u32(d, sb + 48), 'align': u32(d, sb + 52),
                     'reloff': u32(d, sb + 56), 'nreloc': u32(d, sb + 60), 'flags': u32(d, sb + 64),
                     'res1': u32(d, sb + 68), 'res2': u32(d, sb + 72)}
                secs.append(s)
                self.sections.append(s)
            e['sections'] = secs
            self.segs.append(e)
        elif cmd == LC_SEGMENT:
            e.update(segname=cstr(d, o + 8), vmaddr=u32(d, o + 24), vmsize=u32(d, o + 28),
                     fileoff=u32(d, o + 32), filesize=u32(d, o + 36),
                     maxprot=u32(d, o + 40), initprot=u32(d, o + 44), nsects=u32(d, o + 48))
            secs = []
            for i in range(e['nsects']):
                sb = o + 56 + 68 * i
                if sb + 68 > o + cs:
                    break
                s = {'sect': cstr(d, sb), 'seg': cstr(d, sb + 16), 'addr': u32(d, sb + 32),
                     'size': u32(d, sb + 36), 'offset': u32(d, sb + 40), 'align': u32(d, sb + 44),
                     'reloff': u32(d, sb + 48), 'nreloc': u32(d, sb + 52), 'flags': u32(d, sb + 56),
                     'res1': u32(d, sb + 60), 'res2': u32(d, sb + 64)}
                secs.append(s)
                self.sections.append(s)
            e['sections'] = secs
            self.segs.append(e)
        elif cmd in (LC_LOAD_DYLIB, LC_LOAD_WEAK_DYLIB, LC_REEXPORT_DYLIB, LC_LAZY_LOAD_DYLIB):
            no = u32(d, o + 8)
            if no < cs:
                e['name'] = cstr(d, o + no)
            e['cur'] = (u32(d, o + 24), u32(d, o + 28)) if cs >= 32 else (0, 0)
            e['compat'] = (u32(d, o + 16), u32(d, o + 20)) if cs >= 32 else (0, 0)
            e['kind'] = {LC_LOAD_DYLIB: 'load', LC_LOAD_WEAK_DYLIB: 'weak',
                         LC_REEXPORT_DYLIB: 'reexport', LC_LAZY_LOAD_DYLIB: 'lazy'}[cmd]
        elif cmd == LC_ID_DYLIB:
            no = u32(d, o + 8)
            if no < cs:
                e['name'] = cstr(d, o + no)
        elif cmd == LC_LOAD_DYLINKER:
            no = u32(d, o + 8)
            e['name'] = cstr(d, o + no) if no < cs else '/usr/lib/dyld'
        elif cmd == LC_RPATH:
            no = u32(d, o + 8)
            e['path'] = cstr(d, o + no) if no < cs else ''
        elif cmd == LC_LINKER_OPTION:
            n = u32(d, o + 8)
            paths, p = [], o + 12
            for _ in range(n):
                if p >= o + cs:
                    break
                s = cstr(d, p)
                paths.append(s)
                p += len(s.encode('utf-8', 'replace')) + 1
            e['options'] = paths
        elif cmd == LC_MAIN:
            e['entryoff'] = u64(d, o + 8)
            e['stacksize'] = u64(d, o + 16)
        elif cmd in (LC_DYLD_INFO, LC_DYLD_INFO_ONLY):
            f = struct.unpack_from('<10I', d, o + 8)
            e.update(rebase=(f[0], f[1]), bind=(f[2], f[3]), weak=(f[4], f[5]),
                     lazy=(f[6], f[7]), export=(f[8], f[9]))
        elif cmd in (LC_DYLD_EXPORTS_TRIE, LC_DYLD_CHAINED_FIXUPS, LC_CODE_SIGNATURE,
                     LC_FUNCTION_STARTS, LC_DATA_IN_CODE):
            e['dataoff'], e['datasize'] = u32(d, o + 8), u32(d, o + 12)
        elif cmd == LC_SYMTAB:
            e.update(symoff=u32(d, o + 8), nsyms=u32(d, o + 12),
                     stroff=u32(d, o + 16), strsize=u32(d, o + 20))
        elif cmd == LC_DYSYMTAB:
            e['fields'] = struct.unpack_from('<18I', d, o + 8)
        elif cmd == LC_BUILD_VERSION:
            e.update(platform=u32(d, o + 8), minos=u32(d, o + 12), sdk=u32(d, o + 16))
            n = u32(d, o + 20)
            tools = []
            for i in range(min(n, 16)):
                tb = o + 24 + i * 8
                if tb + 8 > o + cs:
                    break
                tools.append({'tool': u32(d, tb), 'version': u32(d, tb + 4)})
            e['tools'] = tools
        elif cmd in (LC_VERSION_MIN_MACOSX, LC_VERSION_MIN_IPHONEOS):
            e['minos'], e['sdk'] = u32(d, o + 8), u32(d, o + 12)
            e['platform'] = 1 if cmd == LC_VERSION_MIN_MACOSX else 2
        elif cmd == LC_UUID:
            e['uuid'] = d[o + 8:o + 24].hex()
        elif cmd == LC_SOURCE_VERSION:
            e['version'] = u64(d, o + 8)
        elif cmd in (LC_ENCRYPTION_INFO, LC_ENCRYPTION_INFO_64):
            e.update(cryptoff=u32(d, o + 8), cryptsize=u32(d, o + 12), cryptid=u32(d, o + 16))

    # ---- helpers ----
    def get(self, name, default=None):
        for c in self.cmds:
            if c['cmd'] == name:
                return c
        return default

    def get_all(self, name):
        return [c for c in self.cmds if c['cmd'] == name]

    def seg(self, name):
        for s in self.segs:
            if s['segname'] == name:
                return s
        return None

    def text_base(self):
        t = self.seg('__TEXT')
        return t['vmaddr'] if t else 0

    def vm2file(self, addr):
        for s in self.segs:
            if s['vmaddr'] <= addr < s['vmaddr'] + s['vmsize'] and s['filesize']:
                delta = addr - s['vmaddr']
                if delta < s['filesize']:
                    return self.off + s['fileoff'] + delta
        return None

    def section(self, sect, seg=None):
        for s in self.sections:
            if s['sect'] == sect and (seg is None or s['seg'] == seg):
                return s
        return None

    def section_bytes(self, sect, seg=None):
        s = self.section(sect, seg)
        if not s or not s['offset']:
            return b''
        o = self.off + s['offset']
        return self.data[o:o + s['size']]

    def dylibs(self):
        return [c for c in self.cmds if c['cmd'] in (
            'LC_LOAD_DYLIB', 'LC_LOAD_WEAK_DYLIB', 'LC_REEXPORT_DYLIB', 'LC_LAZY_LOAD_DYLIB')]

    def entry(self):
        m = self.get('LC_MAIN')
        if m:
            return self.text_base() + m['entryoff']
        lc = self.get('LC_UNIXTHREAD') or self.get('LC_THREAD')
        return None

    def code_signature(self):
        c = self.get('LC_CODE_SIGNATURE')
        return (c['dataoff'], c['datasize']) if c else None

    def is_encrypted(self):
        c = self.get('LC_ENCRYPTION_INFO_64') or self.get('LC_ENCRYPTION_INFO')
        return bool(c and c.get('cryptid'))

    def uuid(self):
        u = self.get('LC_UUID')
        return u['uuid'] if u else None

    def platform_name(self):
        b = self.get('LC_BUILD_VERSION')
        if not b:
            return None
        return PLATFORM_NAMES.get(b['platform'], str(b['platform']))

    def minos(self):
        b = self.get('LC_BUILD_VERSION')
        if not b:
            return None
        v = b['minos']
        return '%d.%d.%d' % (v >> 16, (v >> 8) & 0xff, v & 0xff)

    # ---- symbols ----
    def symbols(self):
        st = self.get('LC_SYMTAB')
        if not st:
            return []
        d = self.data
        out = []
        n = 16 if self.bits == 64 else 12
        base = self.off
        if st['symoff'] + st['nsyms'] * n > len(d):
            raise EOFError('symtab past end of file')
        for i in range(st['nsyms']):
            o = base + st['symoff'] + i * n
            if self.bits == 64:
                strx, typ, sect, desc, val = struct.unpack_from('<IBBHQ', d, o)
            else:
                strx, typ, sect, desc, val = struct.unpack_from('<IBBhI', d, o)
            so = base + st['stroff'] + strx
            name = cstr(d, so) if strx else ''
            out.append({'name': name, 'type': typ, 'sect': sect, 'desc': desc,
                        'value': val, 'external': bool(typ & N_EXT),
                        'kind': {N_UNDF: 'undef', N_ABS: 'abs', N_SECT: 'sect',
                                 N_PBUD: 'pbud', N_INDR: 'indr'}.get(typ & N_TYPE, 'other')
                        if not (typ & N_STAB) else 'stab'})
        return out

    def undefined_symbols(self):
        return [s for s in self.symbols() if s['kind'] == 'undef' and s['external']]

    def defined_symbols(self):
        return [s for s in self.symbols() if s['kind'] == 'sect' and s['external']]

    def indirect_symbols(self):
        """(__TEXT,__stubs)->symbol indexes via LC_DYSYMTAB indirectsymoff"""
        ds = self.get('LC_DYSYMTAB')
        st = self.get('LC_SYMTAB')
        if not ds or not st:
            return []
        f = ds['fields']
        indoff, nind = f[12], f[13]
        if not indoff or not nind:
            return []
        syms = self.symbols()
        out = []
        for i in range(nind):
            idx = u32(self.data, self.off + indoff + 4 * i)
            out.append(syms[idx]['name'] if idx < len(syms) else None)
        return out

    # ---- fixups ----
    def fixups(self):
        """Normalized bindings: [(where_vmaddr, name, dylib_ordinal, addend, lazy)]
        Includes the lazy-bind stubs, which is where most imported *functions*
        live on older toolchains; a dependency-only view that skips them
        under-reports what the binary needs.
        """
        ch = self.get('LC_DYLD_CHAINED_FIXUPS')
        di = self.get('LC_DYLD_INFO_ONLY') or self.get('LC_DYLD_INFO')
        if ch:
            return parse_chained(self.data, self.off + ch['dataoff'], self.segs, self.dylibs())[0]
        out = []
        if di:
            for key, lazy in (('bind', False), ('lazy', True)):
                off, size = di[key]
                if size:
                    out += parse_opcode_binds(self.data, self.off + off, size, self.segs, lazy=lazy)
        return out

    def exports(self):
        t = self.get('LC_DYLD_EXPORTS_TRIE')
        di = self.get('LC_DYLD_INFO_ONLY') or self.get('LC_DYLD_INFO')
        if t and t['datasize']:
            off, size = t['dataoff'], t['datasize']
        elif di and di['export'][1]:
            off, size = di['export']
        else:
            return {}
        return decode_export_trie(self.data, self.off + off, size)

    def imports_table(self):
        """[(lib_ordinal, name, addend, weak)] from chained fixups or the
        opcode streams, in import-table order."""
        ch = self.get('LC_DYLD_CHAINED_FIXUPS')
        if ch:
            return parse_chained(self.data, self.off + ch['dataoff'], self.segs, self.dylibs())[1]
        out, seen = [], set()
        for vm, name, lib, add, lazy in self.fixups():
            key = (lib, name)
            if key not in seen:
                seen.add(key)
                out.append((lib, name, add, lazy))
        return out

    def external_names(self):
        """Names this binary needs from its dependencies (exports + undefined)."""
        names = set(s['name'] for s in self.undefined_symbols() if s['name'])
        names |= set(b[1] for b in self.fixups() if b[1])
        return names


EXPORT_KIND = {0: 'regular', 1: 'thread_local', 2: 'absolute', 3: 'resolver'}
EXPORT_FLAG_REEXPORT, EXPORT_FLAG_STUB_RESOLVER, EXPORT_FLAG_WEAK = 0x08, 0x10, 0x04


def decode_export_trie(d, base, size):
    """{name: {'kind', 'address'|'reexport'|'resolver', 'weak'}}"""
    end = min(len(d), base + size)
    out = {}
    seen = set()

    def entry(name, info, p):
        kind = info & 0x03
        e = {'flags': info, 'weak': bool(info & EXPORT_FLAG_WEAK)}
        if not (info & 0x08):
            e['kind'] = 'absolute' if kind == 2 else ('resolver' if kind == 3 else 'regular')
        if info & EXPORT_FLAG_REEXPORT:
            lib, p = uleb(d, p)
            e['reexport'] = (lib, cstr(d, p))
            return
        addr, p = uleb(d, p)
        e['address'] = addr
        if kind == 3:
            res, p = uleb(d, p)
            e['resolver'] = res
        if info & EXPORT_FLAG_STUB_RESOLVER:
            stub, p = uleb(d, p)
            e['stub'] = stub
        out[name or '_self'] = e

    def walk(node, prefix, depth):
        if node in seen or depth > 128:
            return
        seen.add(node)
        p = base + node
        while p < end:
            tl = d[p]; p += 1
            if tl == 0:
                info, p = uleb(d, p)
                entry(prefix, info, p)
                return
            if p + tl >= end:
                return
            name = d[p:p + tl].decode('utf-8', 'replace'); p += tl
            info, p = uleb(d, p)
            if info:
                entry(prefix + name, info, p)
                continue
            child, p = uleb(d, p)
            walk(child, prefix + name, depth + 1)

    walk(0, '', 0)
    return out


BIND_KINDS = {0: 'pointer', 1: 'text_abs32', 2: 'text_pcrel32', 3: 'text_addend'}


def parse_opcode_binds(d, base, size, segs, lazy=False):
    out, p, end = [], base, min(len(d), base + size)
    seg, off, lib, name, kind, addend = 0, 0, 0, '', 0, 0
    while p < end:
        b = d[p]; p += 1
        op, imm = b & 0xF0, b & 0x0F
        if op == 0x00:
            # DONE. In the bind stream it terminates the table. In the LAZY
            # stream it terminates only the current entry: dyld re-enters the
            # stream for the next stub, so keep going (verified against
            # llvm-objdump --lazy-bind: two entries = two stubs).
            if not lazy:
                break
            addend = 0
            continue
        if op == 0x10:
            lib = imm
        elif op == 0x20:
            lib, p = uleb(d, p)
        elif op == 0x30:
            lib = imm - 16 if imm else 0
        elif op == 0x40:
            weak = bool(imm & 1); kind = (imm >> 3) & 1
            name = cstr(d, p)
            p += len(name.encode('utf-8', 'replace')) + 1
        elif op == 0x50:
            kind = imm
        elif op == 0x60:
            addend, p = sleb(d, p)
        elif op == 0x70:
            seg = imm
            off, p = uleb(d, p)
        elif op == 0x80:
            v, p = uleb(d, p); off += v
        elif op in (0x90, 0xA0, 0xB0):
            if seg < len(segs):
                out.append((segs[seg]["vmaddr"] + off, name, (lib - 1 if lib > 0 else 0xFF00 | lib), addend, lazy))
            if op == 0x90:
                off += 8
            elif op == 0xA0:
                v, p = uleb(d, p); off += 8 + v
            else:
                off += 8 + imm * 8
        elif op == 0xC0:
            count, p = uleb(d, p)
            skip, p = uleb(d, p)
            for _ in range(count):
                if seg < len(segs):
                    out.append((segs[seg]["vmaddr"] + off, name, (lib - 1 if lib > 0 else 0xFF00 | lib), addend, lazy))
                off += 8 + skip
        elif op == 0xD0:
            break
        else:
            break
    return out




def parse_chained(d, base, segs, dylibs):
    """dyld_chained_fixups_header -> (binds, imports).

    binds:   [(vmaddr_in_segment, name, lib_ordinal, addend, weak)]
    imports: [(lib_ordinal, name, addend, weak)]  (import-table order)

    Layout, verified against `llvm-objdump --macho --chained-fixups`:
      header  : version, starts_offset, imports_offset, symbols_offset,
                imports_count, imports_format, symbols_format   (7 x u32)
      starts  : seg_count(u32), seg_info_offset[seg_count](u32)
                0 = segment has no fixups
      seg_info: size(u32), page_size(u16!), pointer_format(u16),
                segment_offset(u64), max_valid_pointer(u32), page_count(u16),
                page_start[page_count](u16)
    Version-1 implementations had page_size as u32 / format as u16 and every
    offset after it was shifted - that silently produced zero fixups.
    """
    if base + 28 > len(d):
        return [], []
    version, starts_off, imports_off, symbols_off, imports_count, ifmt, sfmt = \
        struct.unpack_from('<7I', d, base)
    sym_base = base + symbols_off
    imports = []
    for i in range(imports_count):
        try:
            if ifmt == 1:      # DYLD_CHAINED_IMPORT
                raw = struct.unpack_from('<I', d, base + imports_off + 4 * i)[0]
                imports.append((raw & 0xff, cstr(d, sym_base + (raw >> 9)), 0, bool((raw >> 8) & 1)))
            elif ifmt == 2:    # DYLD_CHAINED_IMPORT_ADDEND
                lib = struct.unpack_from('<I', d, base + imports_off + 8 * i)[0]
                add = struct.unpack_from('<i', d, base + imports_off + 8 * i + 4)[0]
                imports.append((lib & 0xff, cstr(d, sym_base + (lib >> 9)), add, False))
            elif ifmt == 3:    # DYLD_CHAINED_IMPORT_ADDEND64
                lo = u64(d, base + imports_off + 16 * i)
                add = u64(d, base + imports_off + 16 * i + 8)
                imports.append((lo & 0xffff, cstr(d, sym_base + (lo >> 32)), add, bool((lo >> 16) & 1)))
            else:
                break
        except (EOFError, struct.error):
            break

    binds = []
    so = base + starts_off
    try:
        seg_count = read_u32_at(d, so + 4)
        info_offs = [u32(d, so + 8 + 4 * i) for i in range(seg_count)]
    except (EOFError, struct.error):
        return binds, imports

    for seg_idx, info_off in enumerate(info_offs):
        # Off-by-one trap: seg_info_offset[i] belongs to segment i in the file,
        # but dyld indexes it as [seg-1]. Walking it as a 0-based array skips
        # the first segment and lands one segment late for every other one,
        # which yields an empty bind list and no error at all.
        if info_off == 0 or seg_idx >= len(segs):
            continue
        s = so + info_off
        try:
            page_size = u16(d, s + 4)
            fmt = u16(d, s + 6)
            seg_off = u64(d, s + 8)
            page_count = u16(d, s + 20)
            starts = [u16(d, s + 22 + 2 * j) for j in range(page_count)]
        except (EOFError, struct.error):
            continue
        seg = segs[seg_idx]
        seg_base = seg['vmaddr']
        for pnum, st in enumerate(starts):
            if st & 0x8000:
                # 0x8000 = no fixups on this page; 0xFFFF = multi-start, skip
                continue
            ptr = seg_off + pnum * page_size + st
            steps = 0
            while ptr and ptr < len(d) and steps < 1 << 16:
                steps += 1
                raw = u64(d, ptr)
                nxt, is_bind, ordinal, add = decode_chained_ptr(fmt, raw)
                if is_bind and 0 < ordinal <= len(imports):
                    _, nm, base_add, weak = imports[ordinal - 1]
                    # chained ordinals are 1-based (1 = first LC_LOAD_DYLIB)
                    binds.append((seg_base + ptr, nm, ordinal - 1,
                                  (base_add + add) if add is not None else base_add, weak))
                if not nxt:
                    break
                ptr += nxt
    return binds, imports


CHAINED_STRIDE = {1: 4, 2: 8, 3: 8, 4: 4, 5: 8, 6: 8, 7: 8, 8: 8, 9: 8, 12: 8}


def decode_chained_ptr(fmt, raw):
    """-> (next, is_bind, ordinal, addend) for the common pointer formats."""
    if fmt == 2:           # DYLD_CHAINED_PTR_64 (x86_64 no-auth, arm64)
        nxt = raw & 0xFFF
        if not nxt or nxt == 0xFFF:      # 0xFFF = "next 4-byte stride" marker
            nxt = 4 if nxt == 0xFFF else 0
        if (raw >> 62) & 1:
            return nxt, True, (raw >> 24) & 0xFF, 0
        return nxt, False, 0, None
    if fmt == 6:           # DYLD_CHAINED_PTR_64_OFFSET
        nxt = raw & 0xFFF
        nxt = 4 if nxt == 0xFFF else nxt
        if (raw >> 62) & 1:
            return nxt, True, (raw >> 24) & 0xFF, 0
        return nxt, False, 0, None
    if fmt == 1:           # DYLD_CHAINED_PTR_ARM64E (unauth userspace)
        nxt = raw & 0x7FF
        if not nxt or nxt == 0x7FF:
            nxt = 8 if nxt == 0x7FF else 0
        if (raw >> 62) & 1:
            return nxt, True, (raw >> 51) & 0xFF, 0
        return nxt, False, 0, None
    if fmt == 9:           # DYLD_CHAINED_PTR_ARM64E_USERLAND24
        nxt = raw & 0x7FF
        nxt = 8 if nxt == 0x7FF else nxt
        if (raw >> 62) & 1:
            return nxt, True, (raw >> 48) & 0xFFFFFF, 0
        return nxt, False, 0, None
    if fmt in (3, 4):
        return (raw & 0xFFF) or 0, bool(raw >> 63), (raw >> 32) & 0xFF, None
    if fmt == 5:           # DYLD_CHAINED_PTR_32
        nxt = raw & 0x3F
        nxt = 4 if nxt == 0x3F else nxt
        if (raw >> 31) & 1:
            return nxt, True, (raw >> 26) & 0xF, 0
        return nxt, False, 0, None
    if fmt == 12:          # DYLD_CHAINED_PTR_ARM64E_SHARED_CACHE
        nxt = raw & 0x7FF
        nxt = 8 if nxt == 0x7FF else nxt
        return nxt, bool(raw >> 62), (raw >> 48) & 0xFFFFFF, 0
    return 0, False, 0, None

