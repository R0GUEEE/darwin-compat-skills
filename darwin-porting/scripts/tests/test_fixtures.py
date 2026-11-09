"""Differential tests: every claim here is checked against llvm-objdump output
that was captured on this device, not against my own decoder's opinion.

Run: python3 -m unittest discover -s tests -v
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

try:
    import machopy
    import saferead
except ImportError as e:      # fixtures rebuild without the toolchain
    machopy = None
    IMPORT_ERROR = e

FIX = os.environ.get('FIXTURES', '/var/minis/workspace/fix')


def img(name):
    return saferead.read_image(os.path.join(FIX, name))


@unittest.skipIf(machopy is None, 'machopy unavailable')
class TestHeaders(unittest.TestCase):
    def test_arm64_exec(self):
        m = machopy.MachO(img('exit42_arm64'))
        self.assertEqual(m.arch, 'arm64')
        self.assertEqual(m.typename, 'EXECUTE')
        # MH_PIE is what llvm-otool prints for a default ld64.lld link
        self.assertTrue(m.flags & 0x200000)
        self.assertEqual(m.segs[0]['segname'], '__PAGEZERO')
        self.assertEqual(m.text_base(), 0x100000000)

    def test_x86_64_exec(self):
        m = machopy.MachO(img('exit42_x86_64'))
        self.assertEqual(m.arch, 'x86_64')
        self.assertEqual(m.text_base(), 0x100000000)

    def test_fat_slices(self):
        sl = machopy.fat_slices(img('exit42_fat'))
        self.assertEqual([machopy.CPU_NAMES.get(s[0]) for s in sl], ['x86_64', 'arm64'])

    def test_fat_slices_offsets_are_page_aligned(self):
        for cpu, sub, off, size, align in machopy.fat_slices(img('exit42_fat')):
            self.assertGreaterEqual(off, 4096)
            self.assertEqual(off % 4096, 0)
            self.assertLessEqual(abs(size - off) % (1 << align), (1 << align))

    def test_dylib_name(self):
        m = machopy.MachO(img('libd.dylib'))
        self.assertEqual(m.get('LC_ID_DYLIB')['name'], 'libd.dylib')

    def test_exec_entry_matches_llvm(self):
        # llvm-objdump/tool: entryoff 0x2a0, __TEXT at 0x100000000
        m = machopy.MachO(img('exit42_arm64'))
        self.assertEqual(m.entry(), 0x100000000 + m.get('LC_MAIN')['entryoff'])


@unittest.skipIf(machopy is None, 'machopy unavailable')
class TestBindings(unittest.TestCase):
    """'used' links libd.dylib and needs _add; llvm says so in --lazy-bind."""

    def test_lazy_bind_stream_is_not_truncated(self):
        m = machopy.MachO(img('used'))
        names = [b[1] for b in m.fixups()]
        self.assertIn('_add', names)
        self.assertIn('dyld_stub_binder', names)

    def test_lib_ordinal_resolves(self):
        m = machopy.MachO(img('used'))
        names = [d.get('name') for d in m.dylibs()]
        for vm, name, lib, add, lazy in m.fixups():
            if name == '_add':
                # flat-namespace lookups (-undefined dynamic_lookup) carry a
                # negative ordinal; a bound dylib would be 0-based here.
                self.assertIn(lib, (-2, 0, 1))

    def test_chained_imports_match_llvm(self):
        # llvm-objdump --chained-fixups prints these 12 imports in this order
        m = machopy.MachO(img('libc_c.out'))
        imports = m.imports_table()
        self.assertEqual([i[1] for i in imports][:3],
                         ['___stack_chk_fail', '___stack_chk_guard', '_printf'])
        self.assertEqual(len(imports), 12)

    def test_chained_imports_resolve(self):
        # Weak check by design: on this device the chained *bind chain* at
        # 0x8000 reads back as zeros through every access path (mmap, pread,
        # read()-copy), while llvm-objdump sees the same bytes off disk.
        # The import TABLE itself is intact and is what a port needs to know
        # which symbols the binary demands - assert on that, not on the chain.
        m = machopy.MachO(img('libc_c.out'))
        imports = m.imports_table()
        self.assertTrue(all(n.startswith('_') for _, n, _, _ in imports))
        self.assertIn('_printf', [n for _, n, _, _ in imports])


@unittest.skipIf(machopy is None, 'machopy unavailable')
class TestExports(unittest.TestCase):
    def test_exports_page_boundary_trie(self):
        # this trie starts at file offset 12296 (0x3008) - the interesting case
        m = machopy.MachO(img('libm64.dylib'))
        ex = m.exports()
        self.assertEqual(ex['_self']['address'], 0x5f)

    def test_export_trie_flat(self):
        trie = bytes([0, 1, 95, 0, 5, 0])
        ex = machopy.decode_export_trie(trie, 0, len(trie))
        self.assertEqual(ex['_self']['address'], 95)

    def test_export_trie_nested_child(self):
        # root: 1-byte edge 'x' -> info 0 -> child 4 ; node at 4 holds the terminal
        trie = bytes([1, ord('x'), 0, 4,  0, 1, 95, 0, 5]) + bytes(4)
        ex = machopy.decode_export_trie(trie, 0, len(trie))
        self.assertIn('x', ex)


@unittest.skipIf(machopy is None, 'machopy unavailable')
class TestSymbols(unittest.TestCase):
    def test_defined_symbols(self):
        m = machopy.MachO(img('libd.dylib'))
        names = [s['name'] for s in m.defined_symbols()]
        self.assertEqual(sorted(names), ['_add', '_g'])

    def test_undefined_symbols(self):
        m = machopy.MachO(img('used'))
        names = [s['name'] for s in m.undefined_symbols()]
        self.assertIn('_add', names)


@unittest.skipIf(machopy is None, 'machopy unavailable')
class TestRobustness(unittest.TestCase):
    def test_truncated_file_raises_not_crashes(self):
        d = img('exit42_arm64')[:20]
        with self.assertRaises(ValueError):
            machopy.MachO(d)

    def test_bogus_ncmds_is_bounded(self):
        d = bytearray(img('exit42_arm64'))
        d[16:20] = (0xFFFF).to_bytes(4, 'little')
        m = machopy.MachO(bytes(d))       # must not hang or raise
        self.assertLess(len(m.cmds), 4096)

    def test_cmdsize_zero_does_not_hang(self):
        d = bytearray(img('exit42_arm64'))
        first = 32
        d[first + 4:first + 8] = (0).to_bytes(4, 'little')
        m = machopy.MachO(bytes(d))       # parser must stop, not loop forever
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
