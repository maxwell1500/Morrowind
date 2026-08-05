"""Generate Vvardenfell.esp with our own WRLD/PNDT/LCTN.
Build a new planet "Vvardenfell" in Magnus's star system.
Use formIDs in 0xFE001xxx range (within first 24 bits = 0x001xxx).
"""
import os
import struct
import io
import zlib
import math
import csv

OUTPUT_DIR = r"C:\Users\max\Projects\Morrowind\Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Vvardenfell.esp")
EXTERIOR_REFR_LIMIT = None  # Set to int to limit for testing
PLACEMENT_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv"
MAPPING_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\mapping\seyda_neen_asset_mapping.csv"

PLUGIN_FLAGS = 0x00000101  # master + ESL

MW_CELL_SIZE = 8192.0
# Use Morrowind-scale coordinates directly (Magnus Morrowind WRLD uses Morrowind units)
DEG2RAD = math.pi / 180.0

# Our own formIDs in safe range 0xFE001xxx
# Top byte 0xFE = file index (ESL flag)
# Lower 24 bits = record ID, must be < 0xFFFFFF
OUR_WRLD_FID = 0xFE001000
OUR_PNDT_FID = 0xFE001001
OUR_LCTN_FID = 0xFE001002
OUR_PERSISTENT_CELL_FID = 0xFE001003

# STAT formIDs start at 0xFE001100
NEXT_STAT_FID = 0xFE001100
NEXT_REFR_FID = 0xFE001800
NEXT_INT_CELL_FID = 0xFE002000  # interior cells
NEXT_EXT_CELL_FID = 0xFE003000  # exterior cells (if we need to create our own)


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
    def c_div(a, b):
        q = abs(a) // abs(b)
        if (a < 0) != (b < 0):
            q = -q
        return q
    def c_mod(a, b):
        return a - c_div(a, b) * b
    block_x = c_div(grid_x, 32)
    block_y = c_div(grid_y, 32)
    sub_x = c_div(c_mod(grid_x, 32), 8)
    sub_y = c_div(c_mod(grid_y, 32), 8)
    return struct.pack("<hh", block_y, block_x), struct.pack("<hh", sub_y, sub_x)


def sanitize_edid(s):
    safe = "".join(c if c.isalnum() else "_" for c in s)
    if safe and safe[0].isdigit():
        safe = "_" + safe
    return safe[:30]


def main():
    # Load placements
    placements = []
    with open(PLACEMENT_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            placements.append(row)

    # Build STAT records - only for objects whose NIFs actually exist
    nif_path_by_object = {}
    with open(MAPPING_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            obj_id = row["object_id"].strip().lower()
            if row.get("nif_converted", "").strip().lower() == "true":
                full_nif_path = r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\%s.nif" % obj_id
                if os.path.exists(full_nif_path):
                    nif_path_by_object[obj_id] = "morrowind\\%s.nif" % obj_id

    converted_objects = sorted(nif_path_by_object.keys())

    global NEXT_STAT_FID
    stat_formids = {}
    stat_records = []
    for obj in converted_objects:
        fid = NEXT_STAT_FID
        NEXT_STAT_FID += 1
        stat_formids[obj] = fid
        nif_path = nif_path_by_object[obj]
        stat_records.append((fid, obj, nif_path.encode("ascii")))

    print(f"Generated {len(stat_records)} STAT records")

    # Group REFRs by cell
    refrs_by_cell = {}
    for row in placements:
        obj = row["object_id"].strip().lower()
        if obj not in stat_formids:
            continue
        x_mw = float(row["x_mw"])
        y_mw = float(row["y_mw"])
        z_mw = float(row["z_mw"])
        cell_name = row["cell"].strip()
        if cell_name == "Seyda Neen":
            gx = int(math.floor(x_mw / MW_CELL_SIZE))
            gy = int(math.floor(y_mw / MW_CELL_SIZE))
            # Use Morrowind coordinates directly (since we have our own WRLD)
            # Cell-relative within 8192 units
            x = x_mw - gx * MW_CELL_SIZE
            y = y_mw - gy * MW_CELL_SIZE
            z = z_mw
        else:
            gx = 0
            gy = 0
            x = x_mw
            y = y_mw
            z = z_mw
        global NEXT_REFR_FID
        refr_fid = NEXT_REFR_FID
        NEXT_REFR_FID += 1
        refrs_by_cell.setdefault(cell_name, []).append({
            "x": x, "y": y, "z": z,
            "rx": float(row["rot_x"]) * DEG2RAD,
            "ry": float(row["rot_y"]) * DEG2RAD,
            "rz": float(row["rot_z"]) * DEG2RAD,
            "grid_x": gx, "grid_y": gy,
            "name": stat_formids[obj],
            "object_id": obj,
            "formid": refr_fid,
        })

    exterior_cells = {}
    for r in refrs_by_cell.get("Seyda Neen", []):
        key = (r["grid_x"], r["grid_y"])
        exterior_cells.setdefault(key, []).append(r)

    interior_cells = {k: v for k, v in refrs_by_cell.items() if k != "Seyda Neen"}
    total_exterior_refrs = sum(len(v) for v in exterior_cells.values())
    total_interior_refrs = sum(len(v) for v in interior_cells.values())
    print(f"Exterior cells: {len(exterior_cells)}, REFRs: {total_exterior_refrs}")
    print(f"Interior cells: {len(interior_cells)}, REFRs: {total_interior_refrs}")

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
    num_records = len(stat_records) + len(interior_cells) + len(exterior_cells) + 1 + total_exterior_refrs + total_interior_refrs
    write_subrecord(buf, "HEDR", struct.pack("<fII", 0.96, num_records, NEXT_REFR_FID))
    write_subrecord(buf, "CNAM", b"Vvardenfell - Seyda Neen\x00")
    # Master files
    write_subrecord(buf, "MAST", b"Starfield.esm\x00")
    write_subrecord(buf, "MAST", b"The Elder Star System - Magnus.esm\x00")
    write_subrecord(buf, "BNAM", b"Main\x00")
    write_subrecord(buf, "INCC", struct.pack("<I", 0))
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
    global NEXT_INT_CELL_FID
    for cell_name in sorted(interior_cells.keys()):
        refrs = interior_cells[cell_name]
        cell_fid = NEXT_INT_CELL_FID
        NEXT_INT_CELL_FID += 1
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

    # WRLD - our own Vvardenfell
    wrld_sub = io.BytesIO()
    write_subrecord(wrld_sub, "EDID", b"ElderStarSystem-Magnus_PVvardenfell\x00")
    write_subrecord(wrld_sub, "FULL", b"Vvardenfell\x00")
    write_subrecord(wrld_sub, "BFCB", b"BGSWorldSpaceOverlay_Component\x00")
    write_subrecord(wrld_sub, "BFCE", b"")
    # World bounds - tight around our cells (-2, -10) and (-2, -9)
    # Cell origin: (-2*8192, -10*8192) = (-16384, -81920)
    # World extent: x in [-16384, 0], y in [-90000, -65000]
    # DNAM: terrain min
    write_subrecord(wrld_sub, "DNAM", struct.pack("<ff", -20000.0, -90000.0))
    # MNAM: 4 floats (offset)
    write_subrecord(wrld_sub, "MNAM", struct.pack("<ffff", 0.0, 0.0, 1.0, 1.0))
    # ONAM: 4 floats (orientation)
    write_subrecord(wrld_sub, "ONAM", struct.pack("<ffff", 1.0, 0.0, 0.0, 0.0))
    # NAM0: outer NW corner (small, just our cells)
    write_subrecord(wrld_sub, "NAM0", struct.pack("<ff", -20000.0, -90000.0))
    # NAM9: outer SE corner
    write_subrecord(wrld_sub, "NAM9", struct.pack("<ff", 0.0, -65000.0))
    # NAMA: 1 float
    write_subrecord(wrld_sub, "NAMA", struct.pack("<f", 1.0))
    # DATA
    write_subrecord(wrld_sub, "DATA", b"\x00")
    # FNAM
    write_subrecord(wrld_sub, "FNAM", b"\x1a")
    # GNAM
    write_subrecord(wrld_sub, "GNAM", struct.pack("<f", 1.0))
    wrld_buf = io.BytesIO()
    write_record(wrld_buf, "WRLD", OUR_WRLD_FID, 0, wrld_sub)

    # WRLD children
    wrld_children = io.BytesIO()

    # Persistent cell (we need this for the WRLD to be valid)
    persistent_cell_sub = io.BytesIO()
    write_subrecord(persistent_cell_sub, "EDID", b"VvardenfellPersistent\x00")
    write_subrecord(persistent_cell_sub, "DATA", struct.pack("<I", 0x00000002))
    write_subrecord(persistent_cell_sub, "XCLC", struct.pack("<iii", 0x7FFFFFFF, 0x7FFFFFFF, 0))
    write_subrecord(persistent_cell_sub, "LTMP", struct.pack("<I", 0))
    write_subrecord(persistent_cell_sub, "XCLW", struct.pack("<f", 0.0))
    write_subrecord(persistent_cell_sub, "XILS", struct.pack("<f", 1.0))
    persistent_cell_buf = io.BytesIO()
    write_compressed_record(persistent_cell_buf, "CELL", OUR_PERSISTENT_CELL_FID, 0, persistent_cell_sub)
    persistent_grup = io.BytesIO()
    write_grup(persistent_grup, OUR_PERSISTENT_CELL_FID, 8, b"")
    persistent_children = io.BytesIO()
    write_grup(persistent_children, OUR_PERSISTENT_CELL_FID, 6, persistent_grup.getvalue())
    wrld_children.write(persistent_children.getvalue())

    # Exterior cells with our own formIDs
    global NEXT_EXT_CELL_FID
    for (grid_x, grid_y), refrs in sorted(exterior_cells.items()):
        if EXTERIOR_REFR_LIMIT is not None:
            refrs = refrs[:EXTERIOR_REFR_LIMIT]
        cell_fid = NEXT_EXT_CELL_FID
        NEXT_EXT_CELL_FID += 1

        # CELL record
        cell_sub = io.BytesIO()
        write_subrecord(cell_sub, "EDID", ("Vvardenfell_%d_%d\x00" % (grid_x, grid_y)).encode("ascii"))
        write_subrecord(cell_sub, "FULL", ("Seyda Neen [%d,%d]\x00" % (grid_x, grid_y)).encode("ascii"))
        write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00000202))
        write_subrecord(cell_sub, "XCLC", struct.pack("<iii", grid_x, grid_y, 0))
        write_subrecord(cell_sub, "LTMP", struct.pack("<I", 0))
        write_subrecord(cell_sub, "XCLW", struct.pack("<f", 0.0))
        write_subrecord(cell_sub, "XILS", struct.pack("<f", 1.0))
        cell_buf = io.BytesIO()
        write_record(cell_buf, "CELL", cell_fid, 0, cell_sub)

        # REFRs
        refr_group = io.BytesIO()
        for refr in refrs:
            refr_sub = io.BytesIO()
            write_subrecord(refr_sub, "NAME", struct.pack("<I", refr["name"]))
            write_subrecord(refr_sub, "DATA", struct.pack("<ffffff",
                refr["x"], refr["y"], refr["z"], refr["rx"], refr["ry"], refr["rz"]))
            write_record(refr_group, "REFR", refr["formid"], 0x00010400, refr_sub)

        temp_grup = io.BytesIO()
        write_grup(temp_grup, cell_fid, 9, refr_group.getvalue())
        cell_children = io.BytesIO()
        write_grup(cell_children, cell_fid, 6, temp_grup.getvalue())

        # Block/sub-block structure
        block_label, sub_label = grid_block_labels(grid_x, grid_y)
        subblock = io.BytesIO()
        subblock.write(cell_buf.getvalue())
        subblock.write(cell_children.getvalue())
        cell_block = io.BytesIO()
        write_grup(cell_block, sub_label, 5, subblock.getvalue())
        block = io.BytesIO()
        write_grup(block, block_label, 4, cell_block.getvalue())
        wrld_children.write(block.getvalue())

    wrld_children_grup = io.BytesIO()
    write_grup(wrld_children_grup, OUR_WRLD_FID, 1, wrld_children.getvalue())

    wrld_group_content = io.BytesIO()
    wrld_group_content.write(wrld_buf.getvalue())
    wrld_group_content.write(wrld_children_grup.getvalue())
    write_grup(buf, "WRLD", 0, wrld_group_content.getvalue())

    # PNDT (Planet Data) - our own planet
    # Needs Magnus's PNDT parent celestial body
    pndt_sub = io.BytesIO()
    write_subrecord(pndt_sub, "EDID", b"ElderStarSystem-Magnus_PVvardenfell\x00")
    write_subrecord(pndt_sub, "FULL", b"Vvardenfell\x00")
    # Model path for planet visual
    write_subrecord(pndt_sub, "BFCB", b"TESPlanetModel_Component\x00")
    write_subrecord(pndt_sub, "MODL", b"planets\\Magnus\\planet_Nirn.nif\x00")
    write_subrecord(pndt_sub, "FLLD", struct.pack("<I", 1))
    write_subrecord(pndt_sub, "BFCE", b"")
    # BFCB for BGSKeywordForm
    write_subrecord(pndt_sub, "BFCB", b"BGSKeywordForm_Component\x00")
    write_subrecord(pndt_sub, "KSIZ", struct.pack("<I", 0))
    write_subrecord(pndt_sub, "BFCE", b"")
    # BFCB for TESFullName
    write_subrecord(pndt_sub, "BFCB", b"TESFullName_Component\x00")
    write_subrecord(pndt_sub, "BFCE", b"")
    # Parent celestial body - Magnus's Nirn-Mundus PNDT is 0x0100080A
    write_subrecord(pndt_sub, "PNAM", struct.pack("<I", 0x0100080A))
    pndt_buf = io.BytesIO()
    write_record(pndt_buf, "PNDT", OUR_PNDT_FID, 0, pndt_sub)
    write_grup(buf, "PNDT", 0, pndt_buf.getvalue())

    # LCTN (Location) - Seyda Neen on Vvardenfell
    lctn_sub = io.BytesIO()
    write_subrecord(lctn_sub, "EDID", b"ElderStarSystem-Magnus_PVvardenfell_SeydaNeen\x00")
    write_subrecord(lctn_sub, "FULL", b"Seyda Neen\x00")
    # PNAM points to parent LCTN
    # Magnus's Nirn-Mundus LCTN is 0x0100080B
    write_subrecord(lctn_sub, "PNAM", struct.pack("<I", 0x0100080B))
    lctn_buf = io.BytesIO()
    write_record(lctn_buf, "LCTN", OUR_LCTN_FID, 0, lctn_sub)
    write_grup(buf, "LCTN", 0, lctn_buf.getvalue())

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "wb") as f:
        f.write(buf.getvalue())
    print(f"Created {OUTPUT_FILE}")
    print(f"Size: {buf.tell()} bytes")


if __name__ == "__main__":
    main()
