"""Clone Havok + reshape AABB for 20 key meshes, then generate test ESP."""
import os, sys, subprocess, csv, struct, io, math, shutil

sys.path.insert(0, r'C:\Users\max\Projects\Morrowind\scripts\collision')
import hk_decode_lib as lib

NIF_DIR = r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind'
CLONE_SCRIPT = r'C:\Users\max\Projects\Morrowind\scripts\collision\clone_collision.py'
RESHAPE_SCRIPT = r'C:\Users\max\Projects\Morrowind\scripts\collision\reshape_collision.py'
PLACEMENT_CSV = r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv'
OUTPUT_ESP = r'C:\Users\max\Projects\Morrowind\Data\test_20.esp'

# 20 key structural meshes
KEY_MESHES = [
    'ex_nord_house_01', 'ex_nord_house_02', 'ex_nord_house_03',
    'ex_common_house_addon', 'ex_common_house_tall_01', 'ex_common_house_tall_02',
    'ex_common_lighthouse', 'ex_de_docks_center', 'ex_de_docks_end',
    'ex_de_docks_steps_01', 'ex_de_shack_02', 'ex_de_shack_03',
    'ex_drystonewall_c_01', 'ex_drystonewall_end_01', 'ex_drystonewall_s_01',
    'ex_nord_chimney_01', 'ex_common_balcony_01', 'ex_common_skywalk_01',
    'ex_common_tower_thatch', 'ex_common_plat_cent',
]

# ESP constants
MAGNUS_WRLD = 0x0100E1C8
MAGNUS_PERSIST = 0x0100E954
MAGNUS_CELL = 0x010478A1  # (-1,-1)
SCALE = 100.0 / 8192.0
OFFSET_X = 92.6
OFFSET_Y = 802.0
DEG2RAD = math.pi / 180.0

FID_STAT_BASE = 0xFE000100
FID_REFR_BASE = 0xFE000800


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
    # Step 1: Clone Havok into 20 key meshes
    print("=== Step 1: Clone Havok ===")
    for mesh in KEY_MESHES:
        nif_path = os.path.join(NIF_DIR, mesh + '.nif')
        if not os.path.exists(nif_path):
            print(f"  SKIP {mesh}: NIF not found")
            continue
        result = subprocess.run(
            ['python', CLONE_SCRIPT, '--test', nif_path],
            capture_output=True, text=True, timeout=30
        )
        if 'OK' in result.stdout:
            print(f"  OK {mesh}")
        else:
            print(f"  FAIL {mesh}: {result.stdout.strip()[-100:]}")

    # Step 2: Reshape to AABB boxes
    print("\n=== Step 2: Reshape AABB ===")
    for mesh in KEY_MESHES:
        nif_path = os.path.join(NIF_DIR, mesh + '.nif')
        if not os.path.exists(nif_path):
            continue
        result = subprocess.run(
            ['python', RESHAPE_SCRIPT, '--test', nif_path],
            capture_output=True, text=True, timeout=30
        )
        if 'OK' in result.stdout:
            print(f"  OK {mesh}")
        else:
            print(f"  FAIL {mesh}: {result.stdout.strip()[-100:]}")

    # Step 3: Load placement data for these meshes
    print("\n=== Step 3: Generate ESP ===")
    placements = {}
    with open(PLACEMENT_CSV) as f:
        r = csv.DictReader(f)
        for row in r:
            obj = row['object_id'].strip().lower()
            if obj in KEY_MESHES:
                if obj not in placements:
                    placements[obj] = []
                x_mw = float(row['x_mw'])
                y_mw = float(row['y_mw'])
                z_mw = float(row['z_mw'])
                x = x_mw * SCALE + OFFSET_X
                y = y_mw * SCALE + OFFSET_Y
                z = z_mw * SCALE + 480.0
                rx = float(row['rot_x']) * DEG2RAD
                ry = float(row['rot_y']) * DEG2RAD
                rz = float(row['rot_z']) * DEG2RAD
                placements[obj].append((x, y, z, rx, ry, rz))

    print(f"Loaded placements for {len(placements)} meshes")
    total_refrs = sum(len(v) for v in placements.values())
    print(f"Total REFRs: {total_refrs}")

    # Step 4: Build ESP
    out = io.BytesIO()

    # TES4 header
    out.write(b"TES4")
    dsp = out.tell()
    out.write(struct.pack("<IIIII", 0, 0x00000101, 0, 0, 0x00000240))
    srs = out.tell()
    wsub(out, "HEDR", struct.pack("<fII", 0.96, 2, 0xFE000FFF))
    wsub(out, "CNAM", b"20 Mesh Havok Test\x00")
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
    stat_grup = io.BytesIO()
    for i, mesh in enumerate(KEY_MESHES):
        st = io.BytesIO()
        wsub(st, "EDID", (mesh + "\x00").encode())
        wsub(st, "OBND", struct.pack("<ffffff", -500, -500, -500, 500, 500, 500))
        wsub(st, "ODTY", struct.pack("<I", 0))
        wsub(st, "BFCB", b"BGSKeywordForm_Component\x00")
        wsub(st, "BFCE", b"")
        wsub(st, "MODL", ("morrowind\\" + mesh + ".nif\x00").encode())
        wsub(st, "FLLD", struct.pack("<I", 1))
        wsub(st, "DNAM", struct.pack("<ff", 1.0, 1.0))
        wrec(stat_grup, "STAT", FID_STAT_BASE + i, 0, st)
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

    # REFRs
    refrs = io.BytesIO()
    refr_idx = 0
    for mesh in KEY_MESHES:
        if mesh not in placements:
            continue
        stat_fid = FID_STAT_BASE + KEY_MESHES.index(mesh)
        for (x, y, z, rx, ry, rz) in placements[mesh]:
            rs = io.BytesIO()
            wsub(rs, "NAME", struct.pack("<I", stat_fid))
            wsub(rs, "DATA", struct.pack("<ffffff", x, y, z, rx, ry, rz))
            wrec(refrs, "REFR", FID_REFR_BASE + refr_idx, 0x00000000, rs)
            refr_idx += 1

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

    os.makedirs(os.path.dirname(OUTPUT_ESP), exist_ok=True)
    with open(OUTPUT_ESP, "wb") as f:
        f.write(out.getvalue())
    print(f"\nCreated {OUTPUT_ESP}, size={out.tell()}")
    print(f"STATs: {len(KEY_MESHES)}, REFRs: {refr_idx}")


if __name__ == "__main__":
    main()
