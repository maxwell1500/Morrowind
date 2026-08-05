"""Test ESP: single ex_nord_house_01 with Havok collision in cell (-1,-1)."""
import os, struct, io, math

OUTPUT = r"C:\Users\max\Projects\Morrowind\Data\test_house.esp"
MAGNUS_WRLD = 0x0100E1C8
MAGNUS_PERSIST = 0x0100E954
MAGNUS_CELL = 0x010478A1  # (-1,-1)

SCALE = 100.0 / 8192.0
OFFSET_X = 92.6
OFFSET_Y = 802.0
DEG2RAD = math.pi / 180.0

# ex_nord_house_01 placement from CSV
x_mw = -12107.828
y_mw = -68105.14
z_mw = 336.37225
rot_z = 226.31828896962952

x = x_mw * SCALE + OFFSET_X
y = y_mw * SCALE + OFFSET_Y
z = z_mw * SCALE + 480.0
rz = rot_z * DEG2RAD

FID_STAT = 0xFE000100  # first STAT
FID_REFR = 0xFE000800  # first REFR


def wsub(buf, sig, data):
    buf.write(sig.encode("ascii") + struct.pack("<H", len(data)) + data)


def wrec(buf, sig, fid, flags, subs):
    d = subs.getvalue() if hasattr(subs, "getvalue") else subs
    buf.write(sig.encode("ascii") + struct.pack("<I", len(d)) +
              struct.pack("<IIII", flags, fid, 0, 0x00000240) + d)


def wgrup(buf, label, gtype, content):
    d = content.getvalue() if hasattr(content, "getvalue") else content
    buf.write(b"GRUP" + struct.pack("<I", len(d) + 24))
    if isinstance(label, (bytes, bytearray)):
        lbl = label[:4].ljust(4, b"\x00")
    elif isinstance(label, str):
        lbl = label.encode("ascii")[:4].ljust(4, b"\x00")
    else:
        lbl = struct.pack("<I", label & 0xFFFFFFFF)
    buf.write(lbl + struct.pack("<I", gtype) + b"\x00" * 8 + d)


def main():
    out = io.BytesIO()

    # TES4 header
    out.write(b"TES4")
    dsp = out.tell()
    out.write(struct.pack("<IIIII", 0, 0x00000101, 0, 0, 0x00000240))
    srs = out.tell()
    wsub(out, "HEDR", struct.pack("<fII", 0.96, 2, 0xFE000FFF))
    wsub(out, "CNAM", b"House Havok Test\x00")
    wsub(out, "BNAM", b"Main\x00")
    wsub(out, "INCC", struct.pack("<I", 0))
    wsub(out, "MAST", b"Starfield.esm\x00")
    wsub(out, "DATA", struct.pack("<Q", 0))
    wsub(out, "MAST", b"The Elder Star System - Magnus.esm\x00")
    wsub(out, "DATA", struct.pack("<Q", 0))
    ds = out.tell() - srs
    out.seek(dsp)
    out.write(struct.pack("<I", ds))
    out.seek(0, 2)

    # STAT record
    stat_grup = io.BytesIO()
    st = io.BytesIO()
    wsub(st, "EDID", b"ex_nord_house_01\x00")
    wsub(st, "OBND", struct.pack("<ffffff", -500, -500, -500, 500, 500, 500))
    wsub(st, "ODTY", struct.pack("<I", 0))
    wsub(st, "BFCB", b"BGSKeywordForm_Component\x00")
    wsub(st, "BFCE", b"")
    wsub(st, "MODL", b"morrowind\\ex_nord_house_01.nif\x00")
    wsub(st, "FLLD", struct.pack("<I", 1))
    wsub(st, "DNAM", struct.pack("<ff", 1.0, 1.0))
    wrec(stat_grup, "STAT", FID_STAT, 0, st)
    wgrup(out, "STAT", 0, stat_grup.getvalue())

    # WRLD override
    ws = io.BytesIO()
    wsub(ws, "EDID", b"Morrowind\x00")
    wsub(ws, "FULL", b"Morrowind\x00")
    wsub(ws, "BFCB", b"BGSWorldSpaceOverlay_Component\x00")
    wsub(ws, "SNAM", struct.pack("<I", 0x01000808))
    wsub(ws, "PNAM", struct.pack("<I", 0x0100E23F))
    wsub(ws, "BNAM", struct.pack("<I", 0x0100E265))
    wsub(ws, "BFCE", b"")
    wsub(ws, "XLCN", struct.pack("<I", 0x0100E774))
    wsub(ws, "CNAM", struct.pack("<I", 0x0000015F))
    wsub(ws, "NAM2", struct.pack("<I", 0x18))
    wsub(ws, "NAM7", b"Data\\MATERIALS\\Water\\WaterChoppyLarge.mat\x00")
    wsub(ws, "NAM3", struct.pack("<I", 0x18))
    wsub(ws, "NAM4", struct.pack("<I", 0))
    wsub(ws, "DNAM", struct.pack("<ff", 200.0, 160.0))
    wsub(ws, "MNAM", b"\x00" * 16)
    wsub(ws, "ONAM", struct.pack("<ffff", 1.0, 0.0, 0.0, 0.0))
    wsub(ws, "NAMA", struct.pack("<f", 1.0))
    wsub(ws, "DATA", b"\x01")
    wsub(ws, "FNAM", b"\x18")
    wsub(ws, "NAM0", struct.pack("<ff", -4100.0, -1000.0))
    wsub(ws, "NAM9", struct.pack("<ff", 200.0, 2400.0))
    wsub(ws, "GNAM", struct.pack("<f", 1.0))
    wsub(ws, "XCLW", b"")
    wsub(ws, "WHGT", b"")
    wsub(ws, "HNAM", b"\x00")
    wrld_rec = io.BytesIO()
    wrec(wrld_rec, "WRLD", MAGNUS_WRLD, 0x00000004, ws)

    # Persistent cell override
    pcs = io.BytesIO()
    wsub(pcs, "EDID", b"MorrowindPersistentCell\x00")
    wsub(pcs, "DATA", struct.pack("<I", 0x00000002))
    wsub(pcs, "XCLC", struct.pack("<iii", 2147483647, 2147483647, 0x4DC80000))
    wsub(pcs, "LTMP", struct.pack("<I", 0))
    wsub(pcs, "XCLW", struct.pack("<f", 3.4028234663852886e+38))
    wsub(pcs, "XILS", struct.pack("<f", 1.0))

    # Cell (-1,-1) override
    cs = io.BytesIO()
    wsub(cs, "EDID", b"MorrowindCellNeg1Neg1\x00")
    wsub(cs, "DATA", struct.pack("<I", 0x00000202))
    wsub(cs, "XCLC", struct.pack("<iii", -1, -1, 0))
    wsub(cs, "LTMP", struct.pack("<I", 0))
    wsub(cs, "XCLW", struct.pack("<f", 3.4028234663852886e+38))
    wsub(cs, "XILS", struct.pack("<f", 1.0))
    cb = io.BytesIO()
    wrec(cb, "CELL", MAGNUS_CELL, 0x00000000, cs)

    # REFR - house
    refrs = io.BytesIO()
    rs = io.BytesIO()
    wsub(rs, "NAME", struct.pack("<I", FID_STAT))
    wsub(rs, "DATA", struct.pack("<ffffff", x, y, z, 0.0, 0.0, rz))
    wrec(refrs, "REFR", FID_REFR, 0x00000000, rs)

    # Cell children
    cell_children = io.BytesIO()
    wgrup(cell_children, MAGNUS_CELL, 9, refrs.getvalue())
    cc = io.BytesIO()
    wgrup(cc, MAGNUS_CELL, 6, cell_children.getvalue())

    # Block/subblock for (-1,-1)
    bx, by = -1 // 32, -1 // 32
    sx, sy = -1 // 8, -1 // 8
    blk = struct.pack("<hh", by, bx)
    sub = struct.pack("<hh", sy, sx)

    subblock = io.BytesIO()
    subblock.write(cb.getvalue())
    subblock.write(cc.getvalue())
    subblock_grup = io.BytesIO()
    wgrup(subblock_grup, sub, 5, subblock.getvalue())

    block_grup = io.BytesIO()
    wgrup(block_grup, blk, 4, subblock_grup.getvalue())

    # Persistent cell children (empty)
    pcell_rec = io.BytesIO()
    wrec(pcell_rec, "CELL", MAGNUS_PERSIST, 0x00000000, pcs)
    pcell_type8 = io.BytesIO()
    wgrup(pcell_type8, MAGNUS_PERSIST, 8, io.BytesIO())
    pcell_children = io.BytesIO()
    wgrup(pcell_children, MAGNUS_PERSIST, 6, pcell_type8.getvalue())

    # WRLD children
    wc = io.BytesIO()
    wc.write(pcell_rec.getvalue())
    wc.write(pcell_children.getvalue())
    wc.write(block_grup.getvalue())
    wcg = io.BytesIO()
    wgrup(wcg, MAGNUS_WRLD, 1, wc.getvalue())

    # Top-level WRLD GRUP
    wg = io.BytesIO()
    wg.write(wrld_rec.getvalue())
    wg.write(wcg.getvalue())
    wgrup(out, "WRLD", 0, wg.getvalue())

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "wb") as f:
        f.write(out.getvalue())
    print(f"Created {OUTPUT}, size={out.tell()}")
    print(f"House at ({x:.1f}, {y:.1f}, {z:.1f}) rot_z={rz:.4f} rad")


if __name__ == "__main__":
    main()
