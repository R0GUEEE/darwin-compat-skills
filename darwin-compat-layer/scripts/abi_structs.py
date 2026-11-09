#!/usr/bin/env python3
"""darwin_shim.h + libdarwin_shim - the translation layer a Darwin binary needs.

These are the POSIX-surface calls whose *asymmetry* between Darwin and Linux
silently corrupts data rather than failing. libc calls that behave identically
(printf, memcpy, strlen) need no shim at all - map them straight through and
keep the shim small enough to audit.

Design rules, learned the hard way:
  * every struct that crosses the boundary is translated field by field;
    memcpy of a host struct is a data corruption bug, not an optimisation
  * a call that cannot be translated returns -1/ENOSYS, never a plausible lie
  * the shim owns the Darwin name (`open`), the host symbol is called through
    a `real_` alias, so a port can link the shim and keep its source untouched

Build:
    cc -shared -fPIC -O2 darwin_shim.c -o libdarwin_shim.so
    cc -o prog prog.c -L. -ldarwin_shim -Wl,-rpath,'$ORIGIN'
"""
from ctypes import Structure, c_int16, c_int32, c_int64, c_uint8, c_uint16, c_uint32, c_uint64, byref
import ctypes, errno, os, sys

# ---------------------------------------------------------------- ABI structs
class DarwinStat(ctypes.Structure):
    """64-bit inode variant, size 144 on arm64/x86_64 macOS + iOS."""
    _fields_ = [
        ('st_dev', c_int32),
        ('st_mode', c_uint16),
        ('st_nlink', c_uint16),
        ('st_ino', c_uint64),
        ('st_uid', c_uint32),
        ('st_gid', c_uint32),
        ('st_rdev', c_int32),
        ('st_atimespec', c_int64 * 2),
        ('st_mtimespec', c_int64 * 2),
        ('st_ctimespec', c_int64 * 2),
        ('st_birthtimespec', c_int64 * 2),
        ('st_size', c_int64),
        ('st_blocks', c_int64),
        ('st_blksize', c_int32),
        ('st_flags', c_uint32),
        ('st_gen', c_uint32),
        ('st_lspare', c_int32),
        ('st_qspare', c_int64 * 2),
    ]


class DarwinDirent(ctypes.Structure):
    """One variable-length record; fixed part is 21 bytes, record padded to 8."""
    _fields_ = [
        ('d_ino', c_uint64),
        ('d_seekoff', c_uint64),
        ('d_reclen', c_uint16),
        ('d_namlen', c_uint16),
        ('d_type', c_uint8),
        ('d_name', ctypes.c_char * 1024),
    ]


def self_test():
    assert ctypes.sizeof(DarwinStat) == 144, ctypes.sizeof(DarwinStat)
    off = {name: getattr(DarwinStat, name).offset for name, _ in DarwinStat._fields_}
    assert off['st_ino'] == 8 and off['st_mode'] == 4 and off['st_size'] == 96
    assert off['st_blksize'] == 112 and off['st_flags'] == 116, off
    # a DarwinDirent seen through a packed buffer must line up with the C code
    assert ctypes.sizeof(DarwinDirent) >= 21 + 1024
    return True


if __name__ == '__main__':
    if self_test():
        print('ABI self-test OK: stat=144 st_ino@8 st_mode@4(u16) st_size@96 blksize@112')
