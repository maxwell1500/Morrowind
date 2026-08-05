"""Generate full Seyda Neen ESP.
Overrides Magnus's WRLD + cells, places ALL exterior + interior objects.
Offset: x_mw+5986, y_mw+51539 — centers in Magnus's available cells (-3,-8) to (-1,-4).
"""
import os, struct, io, csv, math, zlib

OUTPUT = r"C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp"
PLACEMENTS = r"C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv"
MAPPING = r"C:\Users\max\Projects\Morrowind\converted_assets\mapping\seyda_neen_asset_mapping.csv"

MAGNUS_WRLD = 0x0100E1C8
MAGNUS_PERSIST = 0x0100E954
MAGNUS_LCTN = 0x0100E774  # Morrowind_ID LCTN
MAGNUS_SNAM = 0x01000808
MAGNUS_PNAM = 0x01008DA3
MAGNUS_BNAM = 0x0100E265
MAGNUS_XLCN = 0x0100E774
MAGNUS_CNAM = 0x0000015F

# Seyda Neen offset to center within Magnus cells
OFFSET_X = 5986.0
OFFSET_Y = 51539.0

# Our formIDs
NEXT_FID = 0xFE000001
LCTN_FID = 0xFE000001
FIRST_STAT = 0xFE000002
FIRST_REFR = 0xFE000100
FIRST_CELL_INTERIOR = 0xFE000800

# Magnus cell formIDs for our cell range (x:-3..-1, y:-8..-4)
MAGNUS_CELLS = {
    (-3, -8): 0x01047C41,
    (-2, -8): 0x01047C43,
    (-1, -8): 0x01047C45,
    (-3, -7): 0x0104788A,
    (-2, -7): 0x01047A60,
    (-1, -7): 0x01047BD0,
    (-3, -6): 0x010478A0,
    (-2, -6): 0x01047B01,
    (-1, -6): 0x01047BD2,
    (-3, -5): 0x01044683,
    (-2, -5): 0x01047BCB,
    (-1, -5): 0x01047BD4,
    (-3, -4): 0x010479FB,
    (-2, -4): 0x01047BCD,
    (-1, -4): 0x01047BD6,
}

DEG2RAD = math.pi / 180.0

# --- Binary helpers ---
fid_counter = NEXT_FID

def next_fid():
    global fid_counter
    f = fid_counter
    fid_counter += 1
    return f

def wsub(buf, sig, data):
    buf.write(sig.encode("ascii") + struct.pack("<H", len(data)) + data)

def wrec(buf, sig, fid, flags, subs):
    d = subs.getvalue() if hasattr(subs, "getvalue") else subs
    buf.write(sig.encode("ascii") + struct.pack("<I", len(d)) +
              struct.pack("<IIII", flags, fid, 0, 0x00000240) + d)

def wcomp(buf, sig, fid, flags, subs):
    d = subs.getvalue() if hasattr(subs, "getvalue") else subs
    comp = zlib.compress(d)
    content = struct.pack("<I", len(d)) + comp
    buf.write(sig.encode("ascii") + struct.pack("<I", len(content)) +
              struct.pack("<IIII", flags | 0x00040000, fid, 0, 0x00000240) + content)

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

def sanitize_edid(s):
    safe = "".join(c if c.isalnum() else "_" for c in s)
    if safe and safe[0].isdigit():
        safe = "_" + safe
    return safe[:30]

def grid_block_labels(gx, gy):
    block_x = gx // 32
    block_y = gy // 32
    sub_x = gx // 8
    sub_y = gy // 8
    return struct.pack("<hh", block_y, block_x), struct.pack("<hh", sub_y, sub_x)

# --- Main ---
def main():
    # Read placements
    placements = []
    with open(PLACEMENTS, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            placements.append(row)

    # Read mapping for NIF paths
    nif_paths = {}
    with open(MAPPING, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            obj_id = row["object_id"].strip().lower()
            if row.get("nif_converted", "").strip().lower() == "true":
                nif_paths[obj_id] = "morrowind\\%s.nif" % obj_id

    # Build STAT records for each unique object
    stat_by_object = {}
    stat_list = []
    for row in placements:
        obj = row["object_id"].strip().lower()
        if obj in stat_by_object:
            continue
        if row["mesh_converted"].strip().lower() != "true":
            continue
        if obj not in nif_paths:
            continue
        fid = next_fid()
        stat_by_object[obj] = fid
        nif = nif_paths.get(obj, "morrowind\\%s.nif" % obj).encode("ascii")
        stat_list.append((fid, obj, nif))

    print(f"STAT records: {len(stat_list)}")

    # Build REFR records by cell
    exterior_refrs = []  # objects in "Seyda Neen" cell (exterior world)
    interior_refrs_by_name = {}  # objects by interior cell name

    for row in placements:
        obj = row["object_id"].strip().lower()
        if obj not in stat_by_object:
            continue

        x = float(row["x_mw"]) + OFFSET_X
        y = float(row["y_mw"]) + OFFSET_Y
        z = float(row["z_mw"])
        rx = float(row["rot_x"]) * DEG2RAD
        ry = float(row["rot_y"]) * DEG2RAD
        rz = float(row["rot_z"]) * DEG2RAD
        cell_name = row["cell"].strip()
        is_temp = row.get("temporary", "False").strip().lower() == "true"
        dest = row.get("destination_cell", "").strip()

        refr = {
            "x": x, "y": y, "z": z,
            "rx": rx, "ry": ry, "rz": rz,
            "name": stat_by_object[obj],
            "formid": next_fid(),
            "temp": is_temp,
            "dest": dest,
            "object_id": obj,
        }

        if cell_name == "Seyda Neen":
            exterior_refrs.append(refr)
        else:
            interior_refrs_by_name.setdefault(cell_name, []).append(refr)

    print(f"Exterior REFRs: {len(exterior_refrs)}")
    print(f"Interior cells: {len(interior_refrs_by_name)}")
    total_int_refrs = sum(len(v) for v in interior_refrs_by_name.values())
    print(f"Interior REFRs: {total_int_refrs}")

    # Group exterior by grid cell
    exterior_by_grid = {}
    for r in exterior_refrs:
        gx = int(math.floor(r["x"] / 4096.0))
        gy = int(math.floor(r["y"] / 4096.0))
        exterior_by_grid.setdefault((gx, gy), []).append(r)

    print(f"Unique exterior grids: {len(exterior_by_grid)}")
    for g, refrs in sorted(exterior_by_grid.items()):
        print(f"  ({g[0]},{g[1]}): {len(refrs)} REFRs")

    # --- Build ESP ---
    out = io.BytesIO()

    # TES4 - 24-byte header
    out.write(b"TES4")
    dsp = out.tell()
    num_records = (1 + len(stat_list) + 1 + 1 + len(exterior_by_grid) +
                   len(interior_refrs_by_name) + len(exterior_refrs) + total_int_refrs + 1)
    out.write(struct.pack("<IIIII", 0, 0x00000101, 0, 0, 0x00000240))
    srs = out.tell()
    wsub(out, "HEDR", struct.pack("<fII", 0.96, num_records, fid_counter))
    wsub(out, "CNAM", b"Seyda Neen - Vvardenfell\x00")
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

    # --- STAT group ---
    stat_group = io.BytesIO()
    for fid, edid, nif_path in stat_list:
        sb = io.BytesIO()
        wsub(sb, "EDID", edid.encode("ascii") + b"\x00")
        wsub(sb, "OBND", struct.pack("<ffffff", -1, -1, -1, 1, 1, 1))
        wsub(sb, "ODTY", struct.pack("<I", 0))
        wsub(sb, "BFCB", b"BGSKeywordForm_Component\x00")
        wsub(sb, "BFCE", b"")
        wsub(sb, "MODL", nif_path + b"\x00")
        wsub(sb, "FLLD", struct.pack("<I", 1))
        wsub(sb, "DNAM", struct.pack("<ff", 1.0, 1.0))
        wrec(stat_group, "STAT", fid, 0, sb)
    wgrup(out, "STAT", 0, stat_group.getvalue())

    # --- WRLD override (all 26 subrecords) ---
    # Matches ImperialCity.esm pattern
    wrld_sub = io.BytesIO()
    wsub(wrld_sub, "EDID", b"Morrowind\x00")
    wsub(wrld_sub, "BFCB", b"BGSWorldSpaceOverlay_Component\x00")
    wsub(wrld_sub, "SNAM", struct.pack("<I", MAGNUS_SNAM))
    wsub(wrld_sub, "PNAM", struct.pack("<I", MAGNUS_PNAM))
    wsub(wrld_sub, "BNAM", struct.pack("<I", MAGNUS_BNAM))
    wsub(wrld_sub, "BFCE", b"")
    wsub(wrld_sub, "FULL", b"Morrowind\x00")
    wsub(wrld_sub, "XLCN", struct.pack("<I", MAGNUS_XLCN))
    wsub(wrld_sub, "CNAM", struct.pack("<I", MAGNUS_CNAM))
    wsub(wrld_sub, "NAM2", struct.pack("<I", 0x18))
    wsub(wrld_sub, "NAM7", b"Data\\MATERIALS\\Water\\WaterChoppyLarge.mat\x00")
    wsub(wrld_sub, "NAM3", struct.pack("<I", 0x18))
    wsub(wrld_sub, "NAM4", struct.pack("<I", 0))
    wsub(wrld_sub, "DNAM", struct.pack("<ff", 200.0, 160.0))
    wsub(wrld_sub, "MNAM", b"\x00" * 16)
    wsub(wrld_sub, "ONAM", struct.pack("<ffff", 1.0, 0.0, 0.0, 0.0))
    wsub(wrld_sub, "NAMA", struct.pack("<f", 1.0))
    wsub(wrld_sub, "DATA", b"\x01")
    wsub(wrld_sub, "FNAM", b"\x18")
    wsub(wrld_sub, "NAM0", struct.pack("<ff", -16500.0, -83000.0))
    wsub(wrld_sub, "NAM9", struct.pack("<ff", 2000.0, 2000.0))
    wsub(wrld_sub, "GNAM", struct.pack("<f", 1.0))
    wsub(wrld_sub, "XCLW", b"")
    wsub(wrld_sub, "WHGT", b"")
    wsub(wrld_sub, "HNAM", b"\x00")
    wrld_buf = io.BytesIO()
    wrec(wrld_buf, "WRLD", MAGNUS_WRLD, 0x00000004, wrld_sub)

    # WRLD children
    wrld_children = io.BytesIO()

    # 1. Persistent cell override
    cell_sub = io.BytesIO()
    wsub(cell_sub, "DATA", struct.pack("<I", 0x00000002))
    wsub(cell_sub, "XCLC", struct.pack("<iii", 0x7FFFFFFF, 0x7FFFFFFF, 0))
    wsub(cell_sub, "LTMP", struct.pack("<I", 0))
    wsub(cell_sub, "XCLW", struct.pack("<f", 0.0))
    wsub(cell_sub, "XILS", struct.pack("<f", 1.0))
    cell_buf = io.BytesIO()
    wcomp(cell_buf, "CELL", MAGNUS_PERSIST, 0x00000400, cell_sub)

    persistent_children = io.BytesIO()
    pers_grup = io.BytesIO()
    wgrup(pers_grup, MAGNUS_PERSIST, 8, b"")
    wgrup(persistent_children, MAGNUS_PERSIST, 6, pers_grup.getvalue())

    wrld_children.write(cell_buf.getvalue())
    wrld_children.write(persistent_children.getvalue())

    # 2. Exterior cells - override Magnus's cells at our grid coordinates
    blocks = {}
    for (gx, gy), refrs in sorted(exterior_by_grid.items()):
        if (gx, gy) not in MAGNUS_CELLS:
            print(f"  WARNING: ({gx},{gy}) has no Magnus cell formID, skipping {len(refrs)} REFRs")
            continue
        cell_fid = MAGNUS_CELLS[(gx, gy)]

        # Cell subrecords
        cell_sub = io.BytesIO()
        wsub(cell_sub, "DATA", struct.pack("<I", 0x00000002))
        wsub(cell_sub, "XCLC", struct.pack("<iii", gx, gy, 0))
        wsub(cell_sub, "LTMP", struct.pack("<I", 0))
        wsub(cell_sub, "XCLW", struct.pack("<f", 0.0))
        wsub(cell_sub, "XILS", struct.pack("<f", 1.0))
        cell_buf = io.BytesIO()
        wrec(cell_buf, "CELL", cell_fid, 0, cell_sub)

        # REFR records
        refr_grup_content = io.BytesIO()
        for r in refrs:
            refr_sub = io.BytesIO()
            wsub(refr_sub, "NAME", struct.pack("<I", r["name"]))
            wsub(refr_sub, "DATA", struct.pack("<ffffff",
                r["x"], r["y"], r["z"], r["rx"], r["ry"], r["rz"]))
            wrec(refr_grup_content, "REFR", r["formid"], 0x00010400, refr_sub)

        temp_grup = io.BytesIO()
        wgrup(temp_grup, cell_fid, 9, refr_grup_content.getvalue())
        cell_children = io.BytesIO()
        wgrup(cell_children, cell_fid, 6, temp_grup.getvalue())

        block_label, sub_label = grid_block_labels(gx, gy)
        bkey = struct.unpack("<hh", block_label)
        skey = struct.unpack("<hh", sub_label)
        cell_data = cell_buf.getvalue() + cell_children.getvalue()
        blocks.setdefault(bkey, {}).setdefault(skey, []).append(cell_data)

    # Write blocks and subblocks
    for (block_y, block_x) in sorted(blocks.keys()):
        block_content = io.BytesIO()
        subblocks = blocks[(block_y, block_x)]
        for (sub_y, sub_x) in sorted(subblocks.keys()):
            sub_content = io.BytesIO()
            for cell_data in subblocks[(sub_y, sub_x)]:
                sub_content.write(cell_data)
            sub_label = struct.pack("<hh", sub_y, sub_x)
            wgrup(block_content, sub_label, 5, sub_content.getvalue())
        block_label = struct.pack("<hh", block_y, block_x)
        cell_block = io.BytesIO()
        wgrup(cell_block, block_label, 4, block_content.getvalue())
        wrld_children.write(cell_block.getvalue())

    wrld_children_grup = io.BytesIO()
    wgrup(wrld_children_grup, MAGNUS_WRLD, 1, wrld_children.getvalue())

    wrld_group_content = io.BytesIO()
    wrld_group_content.write(wrld_buf.getvalue())
    wrld_group_content.write(wrld_children_grup.getvalue())
    wgrup(out, "WRLD", 0, wrld_group_content.getvalue())

    # --- Interior cells ---
    seen_edids = set()
    interior_block = io.BytesIO()
    subblock_index = 0
    for cell_name in sorted(interior_refrs_by_name.keys()):
        refrs = interior_refrs_by_name[cell_name]
        cell_fid = next_fid()

        cell_sub = io.BytesIO()
        edid = sanitize_edid(cell_name)
        orig_edid = edid
        suffix = 0
        while edid in seen_edids:
            suffix += 1
            edid = "%s_%d" % (orig_edid[:27], suffix)
        seen_edids.add(edid)
        wsub(cell_sub, "EDID", (edid + "\x00").encode("ascii"))
        full_name = (cell_name[:33] + "\x00").encode("ascii")
        wsub(cell_sub, "FULL", full_name)
        wsub(cell_sub, "DATA", struct.pack("<I", 0x00010025))
        cell_buf = io.BytesIO()
        wcomp(cell_buf, "CELL", cell_fid, 0, cell_sub)

        refr_group = io.BytesIO()
        for r in refrs:
            refr_sub = io.BytesIO()
            wsub(refr_sub, "NAME", struct.pack("<I", r["name"]))
            wsub(refr_sub, "DATA", struct.pack("<ffffff",
                r["x"], r["y"], r["z"], r["rx"], r["ry"], r["rz"]))
            wrec(refr_group, "REFR", r["formid"], 0x00010400, refr_sub)

        persistent_grup = io.BytesIO()
        wgrup(persistent_grup, cell_fid, 8, refr_group.getvalue())
        cell_children = io.BytesIO()
        wgrup(cell_children, cell_fid, 6, persistent_grup.getvalue())

        subblock = io.BytesIO()
        subblock.write(cell_buf.getvalue())
        subblock.write(cell_children.getvalue())
        wgrup(interior_block, subblock_index, 3, subblock.getvalue())
        subblock_index += 1

    interior_top_block = io.BytesIO()
    wgrup(interior_top_block, 0, 2, interior_block.getvalue())
    wgrup(out, "CELL", 0, interior_top_block.getvalue())

    # --- LCTN - Seyda Neen parented to Morrowind_ID ---
    lctn_sub = io.BytesIO()
    wsub(lctn_sub, "EDID", b"SeydaNeenLocation\x00")
    wsub(lctn_sub, "FULL", b"Seyda Neen\x00")
    wsub(lctn_sub, "PNAM", struct.pack("<I", MAGNUS_LCTN))
    lctn_buf = io.BytesIO()
    wrec(lctn_buf, "LCTN", LCTN_FID, 0, lctn_sub)
    wgrup(out, "LCTN", 0, lctn_buf.getvalue())

    # --- Write ---
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "wb") as f:
        f.write(out.getvalue())
    print(f"\nCreated {OUTPUT}")
    print(f"Size: {out.tell()} bytes")
    print(f"STATs: {len(stat_list)}")
    print(f"Exterior cells: {len(exterior_by_grid)} ({len([g for g in exterior_by_grid if g in MAGNUS_CELLS])} overridden)")
    print(f"Interior cells: {len(interior_refrs_by_name)}")
    print(f"Total REFRs: {len(exterior_refrs)} ext + {total_int_refrs} int")

if __name__ == "__main__":
    main()
