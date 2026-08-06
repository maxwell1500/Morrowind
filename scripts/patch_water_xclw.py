"""
Patch water into the golden SeydaNeen.esp.

Sets XCLW = 479.0 on the exterior cell (0x010478A1, grid -1,-1) so the
harbor/dock low ground shows water while the village stays dry:
  - all 435 exterior REFRs sit at z >= 479.22 (terrain mesh is the only
    object lower, at 475.75); every placed object stays dry
  - dock deck under the harbor is 478.07-479.08 -> submerged (harbor water)
  - dock planks at 479.65-480.16 -> above water
  - persistent cell + interior cells keep XCLW = FLT_MAX (no water)

The patch is a single 4-byte float replacement in the existing XCLW
subrecord; record sizes do not change, so the ESP stays structurally
identical otherwise.

Usage: python scripts/patch_water_xclw.py [esp_path ...]
"""
import struct
import sys

WATER_LEVEL = 479.0
FLT_MAX = 3.4028234663852886e+38
EXTERIOR_CELL_FID = 0x010478A1

DEFAULT_PATHS = [
    r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp',
    r'C:\XboxGames\Starfield\Content\Data\SeydaNeen.esp',
]


def patch(path):
    with open(path, 'rb') as f:
        data = bytearray(f.read())

    # TES4 record = sig(4) + size(4) + flags(4) + formid(4) + version(4) + unknown(4)
    tes4_size = struct.unpack_from('<I', data, 4)[0]
    pos = 24 + tes4_size
    patched = 0

    def walk(start, end):
        nonlocal patched
        p = start
        while p + 24 <= end:
            sig = bytes(data[p:p+4])
            rsize = struct.unpack_from('<I', data, p+4)[0]
            if sig == b'GRUP':
                gsize = struct.unpack_from('<I', data, p+4)[0]
                walk(p + 24, p + gsize)
                p += gsize
            else:
                fid = struct.unpack_from('<I', data, p+12)[0]
                if sig == b'CELL' and fid == EXTERIOR_CELL_FID:
                    # find XCLW subrecord
                    sp = p + 24
                    while sp + 6 <= p + 24 + rsize:
                        ss = bytes(data[sp:sp+4])
                        ssz = struct.unpack_from('<H', data, sp+4)[0]
                        if ss == b'XCLW':
                            old = struct.unpack_from('<f', data, sp+6)[0]
                            if abs(old - FLT_MAX) < 1e-5:
                                struct.pack_into('<f', data, sp+6, WATER_LEVEL)
                                patched += 1
                                print(f'  XCLW @0x{sp:06X}: {old} -> {WATER_LEVEL}')
                            else:
                                print(f'  XCLW @0x{sp:06X}: already {old} (skipped)')
                        sp += 6 + ssz
                p += 24 + rsize

    walk(pos, len(data))
    if patched == 0:
        print('ERROR: exterior cell XCLW not found/patched in', path)
        return False
    with open(path, 'wb') as f:
        f.write(data)
    print(f'patched {path} ({patched} XCLW)')
    return True


def main():
    paths = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_PATHS
    ok = all(patch(p) for p in paths)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
