"""saferead.py - file reads that survive the iSH page-cache and interpreter quirks.

Two independent hazards observed on this device (CPython 3.12 / aarch64 iSH):

1. `read()` returning a zeroed tail.
   A single read(2) whose LENGTH lands exactly on a 16K (or 32K) boundary can
   come back with its tail zeroed. A struct at the end of that read decodes as
   zeros; a trie or table looks truncated; nothing raises.

2. Slicing and indexing the same buffer disagreeing.
   On specific files and offsets, `d[a:b]` returned bytes from a DIFFERENT
   offset than `d[a]`/`d[b-1]`, while `struct.unpack_from(d, a)` and an mmap
   of the same file agreed with each other and with `od`. A parser that mixes
   `d[p:p+n]` (names) with `d[p]` (tags) can therefore walk two different
   copies of the file, which shows up as an impossible walk: a tag byte read
   as 0, a child offset pointing past the end of a table that is not there.

The rule that survives both: take the image from ONE source (mmap - the
kernel's copy), slice it exactly ONCE into bytes, then treat that bytes object
as immutable and bounds-check every read before it executes. Do not mix
read()/pread()/slicing/indexing in one parser.

    from saferead import read_image, verify
    d = read_image(path)
    assert not verify(d, path)          # bytes match a fresh mmap
    u32 = read_u32(d, off)              # bounds-checked, no struct.unpack_from
"""
import os, mmap, struct

CHUNK = 1 << 20


def read_image(path):
    """Whole file as bytes, copied out of an mmap (immune to both quirks)."""
    fd = os.open(path, os.O_RDONLY)
    try:
        size = os.fstat(fd).st_size
        if size == 0:
            return b''
        mm = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
        try:
            return bytes(mm[:])
        finally:
            mm.close()
    finally:
        os.close(fd)


def read_range(path, off, size):
    fd = os.open(path, os.O_RDONLY)
    try:
        mm = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
        try:
            return mm[off:off + size]
        finally:
            mm.close()
    finally:
        os.close(fd)


def verify(d, path, probes=8):
    """Spot-check d against a fresh mmap. Returns mismatched offsets."""
    n = len(d)
    if n == 0:
        return []
    bad = []
    fd = os.open(path, os.O_RDONLY)
    mm = None
    try:
        mm = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
        step = max(1, n // (probes + 1))
        offs = list(range(0, max(0, n - 16), step))[:probes]
        if n >= 16:
            offs.append(n - 16)
        for off in offs:
            if d[off:off + 16] != mm[off:off + 16]:
                bad.append(off)
    finally:
        if mm is not None:
            mm.close()
        os.close(fd)
    return bad


def _need(d, off, n):
    if off < 0 or off + n > len(d):
        raise EOFError('read of %d bytes at %d past end (%d)' % (n, off, len(d)))


def read_u8(d, off):
    _need(d, off, 1)
    return d[off]


def read_u16(d, off):
    _need(d, off, 2)
    b = d[off:off + 2]
    return b[0] | (b[1] << 8)


def read_u32(d, off):
    _need(d, off, 4)
    b = d[off:off + 4]
    return b[0] | (b[1] << 8) | (b[2] << 16) | (b[3] << 24)


def read_u64(d, off):
    _need(d, off, 8)
    return int.from_bytes(d[off:off + 8], 'little')


def read_i32(d, off):
    v = read_u32(d, off)
    return v - (1 << 32) if v & 0x80000000 else v


def cstr(d, off):
    if off < 0 or off >= len(d):
        return ''
    e = d.find(b'\0', off)
    return d[off:e if e >= 0 else len(d)].decode('utf-8', 'replace')


if __name__ == '__main__':
    import sys
    for p in sys.argv[1:]:
        image = read_image(p)
        bad = verify(image, p)
        print('%-48s %9d bytes  %s' % (p, len(image), 'OK' if not bad else 'MISMATCH %s' % bad))
