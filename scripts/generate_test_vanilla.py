"""Override Magnus's WRLD + override his existing -2,-10 cell.
Place bed + barrel in Magnus's cell, no new cells."""
import os, struct, io

OUTPUT = r"C:\Users\max\Projects\Morrowind\Data\test_vanilla.esp"
MAGNUS_WRLD = 0x0100E1C8
MAGNUS_PERSIST = 0x0100E954
MAGNUS_CELL_NEG2_NEG10 = 0x010488FA
MAGNUS_CELL_NEG2_NEG9 = 0x01047C5B

FID_STAT_BED = 0xFE000001
FID_STAT_BARREL = 0xFE000002
FID_REFR_BED = 0xFE000003
FID_REFR_BARREL = 0xFE000004


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

    # TES4 - 24 bytes
    out.write(b"TES4")
    dsp = out.tell()
    out.write(struct.pack("<IIIII", 0, 0x00000101, 0, 0, 0x00000240))
    srs = out.tell()
    wsub(out, "HEDR", struct.pack("<fII", 0.96, 6, 0xFE000FFF))
    wsub(out, "CNAM", b"Vanilla Override Test\x00")
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

    # STAT records
    for fid, edid, modl in [
        (FID_STAT_BED, "TestVanillaBed", "FurnishedStarborn\\Starborn_BedBunk01.nif"),
        (FID_STAT_BARREL, "TestBarrel01", "morrowind\\barrel_01.nif"),
    ]:
        st = io.BytesIO()
        wsub(st, "EDID", edid.encode() + b"\x00")
        wsub(st, "OBND", struct.pack("<ffffff", -50, -50, -50, 50, 50, 50))
        wsub(st, "ODTY", struct.pack("<I", 0))
        wsub(st, "BFCB", b"BGSKeywordForm_Component\x00")
        wsub(st, "BFCE", b"")
        wsub(st, "MODL", modl.encode() + b"\x00")
        wsub(st, "FLLD", struct.pack("<I", 1))
        wsub(st, "DNAM", struct.pack("<ff", 1.0, 1.0))
        wrec(out, "STAT", fid, 0, st)

    # WRLD override (flag 0x00000004)
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
    wsub(ws, "DNAM", struct.pack("<ff", 200.0, 200.0))
    wsub(ws, "MNAM", b"\x00" * 16)
    wsub(ws, "ONAM", struct.pack("<ffff", 1.0, 0.0, 0.0, 0.0))
    wsub(ws, "NAMA", struct.pack("<f", 1.0))
    wsub(ws, "DATA", b"\x00")
    wsub(ws, "FNAM", b"\x1a")
    wsub(ws, "NAM0", struct.pack("<ff", -5000.0, -5000.0))
    wsub(ws, "NAM9", struct.pack("<ff", 5000.0, 5000.0))
    wsub(ws, "GNAM", struct.pack("<f", 1.0))
    wsub(ws, "XCLW", b"")
    wsub(ws, "WHGT", b"")
    wsub(ws, "HNAM", b"\x00")
    wrld_rec = io.BytesIO()
    wrec(wrld_rec, "WRLD", MAGNUS_WRLD, 0x00000004, ws)

    # Override Magnus's persistent cell (keep XCLC matching Magnus!)
    pcs = io.BytesIO()
    wsub(pcs, "EDID", b"MorrowindPersistentCell\x00")
    wsub(pcs, "DATA", struct.pack("<I", 0x00000002))
    # Keep Magnus's original XCLC - don't change it
    wsub(pcs, "XCLC", struct.pack("<iii", 0, 0, 0))  # Magnus uses (0,0) for persistent
    wsub(pcs, "LTMP", struct.pack("<I", 0))
    wsub(pcs, "XCLW", struct.pack("<f", -100.0))
    wsub(pcs, "XILS", struct.pack("<f", 1.0))

    # Override Magnus's cell -2,-10 (0x010488FA) for bed+barrel
    cs = io.BytesIO()
    wsub(cs, "EDID", b"MorrowindCellNeg2Neg10\x00")
    wsub(cs, "FULL", b"Morrowind Cell -2,-10\x00")
    wsub(cs, "DATA", struct.pack("<I", 0x00000002))
    wsub(cs, "XCLC", struct.pack("<iii", -2, -10, 0))
    wsub(cs, "LTMP", struct.pack("<I", 0))
    wsub(cs, "XCLW", struct.pack("<f", -100.0))
    wsub(cs, "XILS", struct.pack("<f", 1.0))
    cb = io.BytesIO()
    wrec(cb, "CELL", MAGNUS_CELL_NEG2_NEG10, 0x00000004, cs)

    # REFRs - bed at (0,0,500), barrel at (200,0,0) both in -2,-10 cell
    # Coordinates in this cell's local space: cell starts at (-2*4096, -10*4096)
    # World (0,0,500) is in cell (0,0), not (-2,-10)!
    # We need to put objects at coordinates within -2,-10 cell's bounds
    # Cell -2,-10 covers x:[-8192, -4096), y:[-40960, -36864)
    # Let's place at (-6000, -40000, 500) and (-5800, -40000, 0)
    refrs = io.BytesIO()
    for rfid, sfid, x, y, z in [
        (FID_REFR_BED, FID_STAT_BED, -6000.0, -40000.0, 500.0),
        (FID_REFR_BARREL, FID_STAT_BARREL, -5800.0, -40000.0, 0.0),
    ]:
        rs = io.BytesIO()
        wsub(rs, "NAME", struct.pack("<I", sfid))
        wsub(rs, "DATA", struct.pack("<ffffff", x, y, z, 0.0, 0.0, 0.0))
        wrec(refrs, "REFR", rfid, 0x00000000, rs)

    # Cell children: type 9 (temp REFRs)
    cell_children = io.BytesIO()
    wgrup(cell_children, MAGNUS_CELL_NEG2_NEG10, 9, refrs.getvalue())
    cc = io.BytesIO()
    wgrup(cc, MAGNUS_CELL_NEG2_NEG10, 6, cell_children.getvalue())

    # Block/subblock for cell (-2,-10)
    bx, by = -2 // 32, -10 // 32
    sx, sy = -2 // 8, -10 // 8
    blk = struct.pack("<hh", by, bx)
    sub = struct.pack("<hh", sy, sx)

    subblock = io.BytesIO()
    subblock.write(cb.getvalue())
    subblock.write(cc.getvalue())
    subblock_grup = io.BytesIO()
    wgrup(subblock_grup, sub, 5, subblock.getvalue())

    block_grup = io.BytesIO()
    wgrup(block_grup, blk, 4, subblock_grup.getvalue())

    # Persistent cell - just override, keep children empty
    pcell_rec = io.BytesIO()
    wrec(pcell_rec, "CELL", MAGNUS_PERSIST, 0x00000004, pcs)
    pcell_children = io.BytesIO()
    wgrup(pcell_children, MAGNUS_PERSIST, 6, io.BytesIO())

    # WRLD children GRUP (type 1)
    wc = io.BytesIO()
    wc.write(pcell_rec.getvalue())
    wc.write(pcell_children.getvalue())
    wc.write(block_grup.getvalue())
    wcg = io.BytesIO()
    wgrup(wcg, MAGNUS_WRLD, 1, wc.getvalue())

    # Top-level WRLD GRUP (type 0)
    wg = io.BytesIO()
    wg.write(wrld_rec.getvalue())
    wg.write(wcg.getvalue())
    wgrup(out, "WRLD", 0, wg.getvalue())

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "wb") as f:
        f.write(out.getvalue())
    print(f"Created {OUTPUT}, size={out.tell()}")


if __name__ == "__main__":
    main()
