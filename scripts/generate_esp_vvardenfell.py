"""Generate Vvardenfell.esp - override Magnus's WRLD, add own cells.

Architecture: Override Magnus's WRLD (0x0100E1C8) with all 26 subrecords,
override Magnus's persistent cell, and add new CELLs at each unique grid
coordinate from placement data. Uses Magnus's planet terrain data.

Based on analysis of ImperialCity.esm which uses identical pattern.
"""
import os
import struct
import io
import csv
import zlib
import math

OUTPUT_DIR = r"C:\Users\max\Projects\Morrowind\Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Vvardenfell.esp")
EXTERIOR_REFR_LIMIT = None
PLACEMENT_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv"
MAPPING_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\mapping\seyda_neen_asset_mapping.csv"

PLUGIN_FLAGS = 0x00000100  # ESL only (not master)
STARFIELD_CELL_SIZE = 4096.0
DEG2RAD = math.pi / 180.0

# Magnus references (from ImperialCity.esm - which matches Magnus's data)
MAGNUS_WRLD = 0x0100E1C8           # Morrowind worldspace
MAGNUS_PERSISTENT_CELL = 0x0100E954  # Persistent cell (from ImperialCity)
MAGNUS_MORROWIND_LCTN = 0x0100E774  # Morrowind_ID LCTN

# Magnus subrecord values (from ImperialCity.esm override of 0x0100E1C8)
MAGNUS_SNAM = 0x01000808
MAGNUS_PNAM = 0x01008DA3   # Parent WRLD
MAGNUS_BNAM = 0x0100E265
MAGNUS_XLCN = 0x0100E774   # Morrowind_ID LCTN
MAGNUS_CNAM = 0x0000015F   # Climate

# Our formIDs in valid ESL range (0xFE000001 - 0xFE000FFF)
OUR_LCTN_FID = 0xFE000001
NEXT_STAT_FID = 0xFE000002
NEXT_REFR_FID = 0xFE000100
NEXT_CELL_FID = 0xFE000800


def write_subrecord(buf, sig, data):
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<H", len(data)))
    buf.write(data)


def write_record(buf, sig, formid, flags, subrecords):
    sub_data = subrecords.getvalue() if hasattr(subrecords, "getvalue") else subrecords
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<I", len(sub_data)))
    buf.write(struct.pack("<I", flags))
    buf.write(struct.pack("<I", formid))
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", 0x00000240))
    buf.write(sub_data)


def write_compressed_record(buf, sig, formid, flags, subrecords):
    sub_data = subrecords.getvalue() if hasattr(subrecords, "getvalue") else subrecords
    compressed = zlib.compress(sub_data)
    content = struct.pack("<I", len(sub_data)) + compressed
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<I", len(content)))
    buf.write(struct.pack("<I", flags | 0x00040000))
    buf.write(struct.pack("<I", formid))
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", 0x00000240))
    buf.write(content)


def write_grup(buf, label, grup_type, content):
    data = content.getvalue() if hasattr(content, "getvalue") else content
    buf.write(b"GRUP")
    buf.write(struct.pack("<I", len(data) + 24))
    if isinstance(label, (bytes, bytearray)):
        label_bytes = label[:4].ljust(4, b"\x00")
    elif isinstance(label, str):
        label_bytes = label.encode("ascii")[:4].ljust(4, b"\x00")
    else:
        label_bytes = struct.pack("<I", label & 0xFFFFFFFF)
    buf.write(label_bytes)
    buf.write(struct.pack("<I", grup_type))
    buf.write(b"\x00" * 8)
    buf.write(data)


def grid_block_labels(grid_x, grid_y):
    """Encode block and subblock labels for Starfield WRLD hierarchy.
    
    From ImperialCity.esm analysis: block_y, block_x as int16 pair,
    sub_y, sub_x as int16 pair. Uses Python floor division.
    """
    block_x = grid_x // 32
    block_y = grid_y // 32
    sub_x = grid_x // 8
    sub_y = grid_y // 8
    return struct.pack("<hh", block_y, block_x), struct.pack("<hh", sub_y, sub_x)


def sanitize_edid(s):
    safe = "".join(c if c.isalnum() else "_" for c in s)
    if safe and safe[0].isdigit():
        safe = "_" + safe
    return safe[:30]


def main():
    global NEXT_STAT_FID, NEXT_REFR_FID, NEXT_CELL_FID

    placements = []
    with open(PLACEMENT_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            placements.append(row)

    nif_path_by_object = {}
    with open(MAPPING_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            obj_id = row["object_id"].strip().lower()
            if row.get("nif_converted", "").strip().lower() == "true":
                full_nif_path = r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\%s.nif" % obj_id
                if os.path.exists(full_nif_path):
                    nif_path_by_object[obj_id] = "morrowind\\%s.nif" % obj_id

    converted_objects = set()
    for row in placements:
        if row["mesh_converted"].strip().lower() == "true":
            obj_id = row["object_id"].strip().lower()
            if obj_id in nif_path_by_object:
                converted_objects.add(obj_id)

    stat_formids = {}
    stat_records = []
    for obj in sorted(converted_objects):
        fid = NEXT_STAT_FID
        NEXT_STAT_FID += 1
        stat_formids[obj] = fid
        nif_path = nif_path_by_object.get(obj, "morrowind\\%s.nif" % obj)
        stat_records.append((fid, obj, nif_path.encode("ascii")))

    print(f"Generated {len(stat_records)} STAT records")

    refrs_by_cell_name = {}
    for row in placements:
        obj = row["object_id"].strip().lower()
        if obj not in stat_formids:
            continue
        x_mw = float(row["x_mw"])
        y_mw = float(row["y_mw"])
        z_mw = float(row["z_mw"])
        cell_name = row["cell"].strip()
        if cell_name == "Seyda Neen":
            gx = int(math.floor(x_mw / STARFIELD_CELL_SIZE))
            gy = int(math.floor(y_mw / STARFIELD_CELL_SIZE))
        else:
            gx = 0
            gy = 0
        x = x_mw
        y = y_mw
        z = z_mw
        refr_fid = NEXT_REFR_FID
        NEXT_REFR_FID += 1
        refrs_by_cell_name.setdefault(cell_name, []).append({
            "x": x, "y": y, "z": z,
            "rx": float(row["rot_x"]) * DEG2RAD,
            "ry": float(row["rot_y"]) * DEG2RAD,
            "rz": float(row["rot_z"]) * DEG2RAD,
            "grid_x": gx, "grid_y": gy,
            "name": stat_formids[obj],
            "object_id": obj,
            "formid": refr_fid,
        })

    # Group exterior REFRs by their actual grid cell
    exterior_by_grid = {}
    for r in refrs_by_cell_name.get("Seyda Neen", []):
        key = (r["grid_x"], r["grid_y"])
        exterior_by_grid.setdefault(key, []).append(r)

    interior_cells = {k: v for k, v in refrs_by_cell_name.items() if k != "Seyda Neen"}
    total_exterior_refrs = sum(len(v) for v in exterior_by_grid.values())
    total_interior_refrs = sum(len(v) for v in interior_cells.values())
    print(f"Exterior cells (unique grids): {len(exterior_by_grid)}")
    print(f"Exterior REFRs: {total_exterior_refrs}")
    print(f"Interior cells: {len(interior_cells)}")
    print(f"Interior REFRs: {total_interior_refrs}")

    # Build ESP
    buf = io.BytesIO()
    buf.write(b"TES4")
    data_size_pos = buf.tell()
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", PLUGIN_FLAGS))
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", 0x00000240))
    subrecord_start = buf.tell()
    num_records = (len(stat_records) + len(interior_cells) + len(exterior_by_grid) +
                   1 + 1 + 1 + total_exterior_refrs + total_interior_refrs)
    # +1 for WRLD override, +1 for persistent cell, +1 for LCTN
    next_fid = NEXT_REFR_FID if NEXT_REFR_FID > NEXT_CELL_FID else NEXT_CELL_FID
    write_subrecord(buf, "HEDR", struct.pack("<fII", 0.96, num_records, next_fid))
    write_subrecord(buf, "CNAM", b"Vvardenfell - Seyda Neen\x00")
    write_subrecord(buf, "BNAM", b"Main\x00")
    write_subrecord(buf, "INCC", struct.pack("<I", 0))
    write_subrecord(buf, "MAST", b"Starfield.esm\x00")
    write_subrecord(buf, "DATA", struct.pack("<Q", 0))
    write_subrecord(buf, "MAST", b"The Elder Star System - Magnus.esm\x00")
    write_subrecord(buf, "DATA", struct.pack("<Q", 0))
    data_size = buf.tell() - subrecord_start
    buf.seek(data_size_pos)
    buf.write(struct.pack("<I", data_size))
    buf.seek(0, 2)

    # STAT group
    stat_group = io.BytesIO()
    for fid, edid, nif_path in stat_records:
        stat_sub = io.BytesIO()
        write_subrecord(stat_sub, "EDID", edid.encode("ascii") + b"\x00")
        write_subrecord(stat_sub, "OBND", struct.pack("<ffffff", -1, -1, -1, 1, 1, 1))
        write_subrecord(stat_sub, "ODTY", struct.pack("<I", 0))
        write_subrecord(stat_sub, "BFCB", b"BGSKeywordForm_Component\x00")
        write_subrecord(stat_sub, "BFCE", b"")
        write_subrecord(stat_sub, "MODL", nif_path + b"\x00")
        write_subrecord(stat_sub, "FLLD", struct.pack("<I", 1))
        write_subrecord(stat_sub, "XFLG", b"\x02")
        write_subrecord(stat_sub, "DNAM", struct.pack("<ff", 1.0, 1.0))
        write_record(stat_group, "STAT", fid, 0, stat_sub)
    write_grup(buf, "STAT", 0, stat_group.getvalue())

    # Interior cells
    subblock_index = 0
    interior_block = io.BytesIO()
    seen_edids = set()
    for cell_name in sorted(interior_cells.keys()):
        refrs = interior_cells[cell_name]
        cell_fid = NEXT_CELL_FID
        NEXT_CELL_FID += 1
        cell_sub = io.BytesIO()
        edid = sanitize_edid(cell_name)
        original_edid = edid
        suffix = 0
        while edid in seen_edids:
            suffix += 1
            edid = "%s_%d" % (original_edid[:27], suffix)
        seen_edids.add(edid)
        write_subrecord(cell_sub, "EDID", (edid + "\x00").encode("ascii"))
        full_name = (cell_name[:33] + "\x00").encode("ascii")
        write_subrecord(cell_sub, "FULL", full_name)
        write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00010025))
        cell_buf = io.BytesIO()
        write_compressed_record(cell_buf, "CELL", cell_fid, 0, cell_sub)

        refr_group = io.BytesIO()
        for refr in refrs:
            refr_sub = io.BytesIO()
            write_subrecord(refr_sub, "NAME", struct.pack("<I", refr["name"]))
            write_subrecord(refr_sub, "DATA", struct.pack("<ffffff",
                refr["x"], refr["y"], refr["z"], refr["rx"], refr["ry"], refr["rz"]))
            write_record(refr_group, "REFR", refr["formid"], 0x00010400, refr_sub)

        persistent_grup = io.BytesIO()
        write_grup(persistent_grup, cell_fid, 8, refr_group.getvalue())
        cell_children = io.BytesIO()
        write_grup(cell_children, cell_fid, 6, persistent_grup.getvalue())

        subblock = io.BytesIO()
        subblock.write(cell_buf.getvalue())
        subblock.write(cell_children.getvalue())
        write_grup(interior_block, subblock_index, 3, subblock.getvalue())
        subblock_index += 1

    interior_top_block = io.BytesIO()
    write_grup(interior_top_block, 0, 2, interior_block.getvalue())
    write_grup(buf, "CELL", 0, interior_top_block.getvalue())

    # WRLD - OVERRIDE Magnus's Morrowind WRLD with all subrecords
    # Matches ImperialCity.esm structure exactly
    wrld_sub = io.BytesIO()
    write_subrecord(wrld_sub, "EDID", b"Morrowind\x00")
    write_subrecord(wrld_sub, "BFCB", b"BGSWorldSpaceOverlay_Component\x00")
    write_subrecord(wrld_sub, "SNAM", struct.pack("<I", MAGNUS_SNAM))
    write_subrecord(wrld_sub, "PNAM", struct.pack("<I", MAGNUS_PNAM))
    write_subrecord(wrld_sub, "BNAM", struct.pack("<I", MAGNUS_BNAM))
    write_subrecord(wrld_sub, "BFCE", b"")
    write_subrecord(wrld_sub, "FULL", b"Morrowind\x00")
    write_subrecord(wrld_sub, "XLCN", struct.pack("<I", MAGNUS_XLCN))
    write_subrecord(wrld_sub, "CNAM", struct.pack("<I", MAGNUS_CNAM))
    write_subrecord(wrld_sub, "NAM2", struct.pack("<I", 0x18))
    write_subrecord(wrld_sub, "NAM7", b"Data\\MATERIALS\\Water\\WaterChoppyLarge.mat\x00")
    write_subrecord(wrld_sub, "NAM3", struct.pack("<I", 0x18))
    write_subrecord(wrld_sub, "NAM4", struct.pack("<I", 0))
    write_subrecord(wrld_sub, "DNAM", struct.pack("<ff", 200.0, 160.0))
    write_subrecord(wrld_sub, "MNAM", b"\x00" * 16)
    write_subrecord(wrld_sub, "ONAM", struct.pack("<ffff", 1.0, 0.0, 0.0, 0.0))
    write_subrecord(wrld_sub, "NAMA", struct.pack("<f", 1.0))
    write_subrecord(wrld_sub, "DATA", b"\x01")
    write_subrecord(wrld_sub, "FNAM", b"\x18")
    # Expanded bounds to cover our cell range (-4,-20) to (0,0)
    write_subrecord(wrld_sub, "NAM0", struct.pack("<ff", -16500.0, -83000.0))
    write_subrecord(wrld_sub, "NAM9", struct.pack("<ff", 2000.0, 2000.0))
    write_subrecord(wrld_sub, "GNAM", struct.pack("<f", 1.0))
    write_subrecord(wrld_sub, "XCLW", b"")
    write_subrecord(wrld_sub, "WHGT", b"")
    write_subrecord(wrld_sub, "HNAM", b"\x00")
    wrld_buf = io.BytesIO()
    write_record(wrld_buf, "WRLD", MAGNUS_WRLD, 0x00000004, wrld_sub)

    # WRLD children
    wrld_children = io.BytesIO()

    # 1. Override Magnus's persistent cell (compressed, persistent flag)
    cell_sub = io.BytesIO()
    write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00000002))
    write_subrecord(cell_sub, "XCLC", struct.pack("<iii", 0x7FFFFFFF, 0x7FFFFFFF, 0))
    cell_buf = io.BytesIO()
    write_compressed_record(cell_buf, "CELL", MAGNUS_PERSISTENT_CELL, 0x00000400, cell_sub)

    persistent_children = io.BytesIO()
    pers_grup = io.BytesIO()
    write_grup(pers_grup, MAGNUS_PERSISTENT_CELL, 8, b"")
    write_grup(persistent_children, MAGNUS_PERSISTENT_CELL, 6, pers_grup.getvalue())

    wrld_children.write(cell_buf.getvalue())
    wrld_children.write(persistent_children.getvalue())

    # 2. Exterior cells - one per unique grid coordinate with proper block/subblock
    # Group cells by block for proper hierarchy
    blocks = {}  # (block_x, block_y) -> {(sub_x, sub_y) -> [cell_data]}
    for (grid_x, grid_y), refrs in sorted(exterior_by_grid.items()):
        if EXTERIOR_REFR_LIMIT is not None:
            refrs = refrs[:EXTERIOR_REFR_LIMIT]

        cell_fid = NEXT_CELL_FID
        NEXT_CELL_FID += 1

        # Exterior cell - DATA=0x00000002 (matching ImperialCity)
        cell_sub = io.BytesIO()
        write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00000002))
        write_subrecord(cell_sub, "XCLC", struct.pack("<iii", grid_x, grid_y, 0))
        write_subrecord(cell_sub, "LTMP", struct.pack("<I", 0))
        write_subrecord(cell_sub, "XCLW", struct.pack("<f", 0.0))
        write_subrecord(cell_sub, "XILS", struct.pack("<f", 1.0))
        cell_buf = io.BytesIO()
        write_record(cell_buf, "CELL", cell_fid, 0, cell_sub)

        # REFRs for this cell
        refr_grup_content = io.BytesIO()
        for refr in refrs:
            refr_sub = io.BytesIO()
            write_subrecord(refr_sub, "NAME", struct.pack("<I", refr["name"]))
            write_subrecord(refr_sub, "DATA", struct.pack("<ffffff",
                refr["x"], refr["y"], refr["z"], refr["rx"], refr["ry"], refr["rz"]))
            write_record(refr_grup_content, "REFR", refr["formid"], 0x00010400, refr_sub)

        # Type 9 (temp) group under type 6 (cell children)
        temp_grup = io.BytesIO()
        write_grup(temp_grup, cell_fid, 9, refr_grup_content.getvalue())
        cell_children = io.BytesIO()
        write_grup(cell_children, cell_fid, 6, temp_grup.getvalue())

        # Determine block/subblock
        block_label, sub_label = grid_block_labels(grid_x, grid_y)
        bkey = (block_x, block_y) = struct.unpack("<hh", block_label)
        skey = (sub_x, sub_y) = struct.unpack("<hh", sub_label)

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
            write_grup(block_content, sub_label, 5, sub_content.getvalue())
        block_label = struct.pack("<hh", block_y, block_x)
        cell_block = io.BytesIO()
        write_grup(cell_block, block_label, 4, block_content.getvalue())
        wrld_children.write(cell_block.getvalue())

    wrld_children_grup = io.BytesIO()
    write_grup(wrld_children_grup, MAGNUS_WRLD, 1, wrld_children.getvalue())

    wrld_group_content = io.BytesIO()
    wrld_group_content.write(wrld_buf.getvalue())
    wrld_group_content.write(wrld_children_grup.getvalue())
    write_grup(buf, "WRLD", 0, wrld_group_content.getvalue())

    # LCTN - Seyda Neen parented to Morrowind_ID
    lctn_sub = io.BytesIO()
    write_subrecord(lctn_sub, "EDID", b"SeydaNeenLocation\x00")
    write_subrecord(lctn_sub, "FULL", b"Seyda Neen\x00")
    write_subrecord(lctn_sub, "PNAM", struct.pack("<I", MAGNUS_MORROWIND_LCTN))
    lctn_buf = io.BytesIO()
    write_record(lctn_buf, "LCTN", OUR_LCTN_FID, 0, lctn_sub)
    write_grup(buf, "LCTN", 0, lctn_buf.getvalue())

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "wb") as f:
        f.write(buf.getvalue())
    print(f"Created {OUTPUT_FILE}")
    print(f"Size: {buf.tell()} bytes")
    print(f"WRLD override (Magnus): 0x{MAGNUS_WRLD:08X}")
    print(f"Exterior cells: {len(exterior_by_grid)}, Interior cells: {len(interior_cells)}")
    print(f"Total REFRs: {total_exterior_refrs} exterior + {total_interior_refrs} interior")
    print(f"Blocks used: {len(blocks)}")


if __name__ == "__main__":
    main()
