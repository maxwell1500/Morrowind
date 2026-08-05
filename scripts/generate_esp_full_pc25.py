"""Generate full SeydaNeen.esp from placement CSVs.

Creates one STAT per unique converted mesh, one CELL per unique cell,
and one REFR per placement row. Exterior Seyda Neen cell is attached to
Magnus's Morrowind WRLD; interior cells are top-level CELL groups.
"""
import os
import struct
import io
import csv
import zlib
import math

OUTPUT_DIR = r"C:\Users\max\Projects\Morrowind\Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "SeydaNeen_pc25.esp")
EXTERIOR_REFR_LIMIT = 25  # Set to int to limit exterior REFRs for testing
PLACEMENT_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv"
MAPPING_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\mapping\seyda_neen_asset_mapping.csv"
MASTER_PATH = r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm"

PLUGIN_FLAGS = 0x00000101  # master + ESL
FID_MORROWIND_WRLD = 0x0100E1C8

# Morrowind exterior cell size in original units and Starfield cm.
MW_CELL_SIZE = 8192.0
SF_CELL_SIZE = MW_CELL_SIZE * 50.0  # 409600 cm

RECORD_PREFIX = struct.pack("<II", 0, 0x00000240)


def extract_wrld_body(master_path, wrld_formid):
    with open(master_path, "rb") as f:
        data = f.read()
    pos = 0
    while pos < len(data) - 16:
        if data[pos:pos+4] == b"WRLD":
            size = struct.unpack("<I", data[pos+4:pos+8])[0]
            formid = struct.unpack("<I", data[pos+12:pos+16])[0]
            if formid == wrld_formid:
                rec = data[pos+16:pos+16+size]
                if rec[:8] == b"\x00\x00\x00\x00@\x02\x00\x00":
                    return rec[8:]
                return rec
            pos += 16 + size
        else:
            pos += 1
    raise RuntimeError(f"WRLD {wrld_formid:08X} not found")


def write_subrecord(buf, sig, data):
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<H", len(data)))
    buf.write(data)


def write_record(buf, sig, formid, flags, subrecords):
    """Write an uncompressed record with a 24-byte Starfield header."""
    sub_data = subrecords.getvalue() if hasattr(subrecords, "getvalue") else subrecords
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<I", len(sub_data)))
    buf.write(struct.pack("<I", flags))
    buf.write(struct.pack("<I", formid))
    buf.write(struct.pack("<I", 0))          # version
    buf.write(struct.pack("<I", 0x00000240)) # unknown
    buf.write(sub_data)


def write_compressed_record(buf, sig, formid, flags, subrecords):
    """Write a compressed record with a 24-byte Starfield header."""
    sub_data = subrecords.getvalue() if hasattr(subrecords, "getvalue") else subrecords
    compressed = zlib.compress(sub_data)
    content = struct.pack("<I", len(sub_data)) + compressed
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<I", len(content)))
    buf.write(struct.pack("<I", flags | 0x00040000))
    buf.write(struct.pack("<I", formid))
    buf.write(struct.pack("<I", 0))          # version
    buf.write(struct.pack("<I", 0x00000240)) # unknown
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
        label_bytes = struct.pack("<I", label)
    buf.write(label_bytes)
    buf.write(struct.pack("<I", grup_type))
    buf.write(b"\x00" * 8)
    buf.write(data)


def grid_block_labels(grid_x, grid_y):
    """Return (block_label, subblock_label) bytes for WRLD children groups.
    Based on ImperialCity.esm analysis: labels are two signed int16s packed
    as (block_y, block_x) and (subblock_y, subblock_x), using C-style division
    (truncation toward zero) for negative grids.
    """
    def c_div(a, b):
        q = abs(a) // abs(b)
        if (a < 0) != (b < 0):
            q = -q
        return q

    def c_mod(a, b):
        r = a - c_div(a, b) * b
        return r

    block_x = c_div(grid_x, 32)
    block_y = c_div(grid_y, 32)
    sub_x = c_div(c_mod(grid_x, 32), 8)
    sub_y = c_div(c_mod(grid_y, 32), 8)
    block_label = struct.pack("<hh", block_y, block_x)
    sub_label = struct.pack("<hh", sub_y, sub_x)
    return block_label, sub_label


def sanitize_edid(name):
    # CK EDIDs must be alphanumeric + underscore, no spaces or punctuation
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name).rstrip("_")


def main():
    # Load placement CSV
    placements = []
    with open(PLACEMENT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            placements.append(row)

    # Build mapping from object_id (lowercase) to NIF path (morrowind\{name}.nif)
    nif_path_by_object = {}
    with open(MAPPING_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            obj_id = row["object_id"].strip().lower()
            if row.get("nif_converted", "").strip().lower() == "true":
                nif_name = obj_id + ".nif"
                nif_path_by_object[obj_id] = f"morrowind\\{nif_name}"

    # Allocate formIDs
    next_formid = 0x00000800  # ESL object IDs start at 0x800
    def alloc():
        nonlocal next_formid
        fid = 0xFE000000 | next_formid
        next_formid += 1
        return fid

    # Unique converted meshes -> STAT
    converted_objects = set()
    for row in placements:
        if row["mesh_converted"].strip().lower() == "true":
            converted_objects.add(row["object_id"].strip().lower())

    stat_formids = {}
    stat_records = []  # (formid, edid, nif_path)
    for obj in sorted(converted_objects):
        fid = alloc()
        stat_formids[obj] = fid
        nif_path = nif_path_by_object.get(obj, f"morrowind\\{obj}.nif")
        stat_records.append((fid, sanitize_edid(obj), nif_path.encode("ascii")))

    print(f"Generated {len(stat_records)} STAT records")

    # Unique cells -> CELL formid
    cells = {}
    cell_order = []
    for row in placements:
        cell = row["cell"].strip()
        if cell not in cells:
            cells[cell] = alloc()
            cell_order.append(cell)

    print(f"Generated {len(cells)} CELL records")

    # REFRs per cell
    refrs_by_cell = {cell: [] for cell in cells}
    for row in placements:
        cell = row["cell"].strip()
        obj = row["object_id"].strip().lower()
        if obj not in stat_formids:
            continue  # skip unconverted objects
        x_mw = float(row["x_mw"])
        y_mw = float(row["y_mw"])
        z_mw = float(row["z_mw"])
        # Compute Morrowind grid for exterior refs.
        grid_x = int(math.floor(x_mw / MW_CELL_SIZE))
        grid_y = int(math.floor(y_mw / MW_CELL_SIZE))
        # Starfield coordinates: X/Y relative to Morrowind cell origin.
        # Morrowind X/Y units convert at 1 unit = 50 cm. Z is already in cm.
        x = (x_mw - grid_x * MW_CELL_SIZE) * 50.0
        y = (y_mw - grid_y * MW_CELL_SIZE) * 50.0
        z = z_mw
        # Starfield uses radians for rotation; CSV stores degrees.
        DEG2RAD = math.pi / 180.0
        rx = float(row["rot_x"]) * DEG2RAD
        ry = float(row["rot_y"]) * DEG2RAD
        rz = float(row["rot_z"]) * DEG2RAD
        refrs_by_cell[cell].append({
            "formid": alloc(),
            "edid": sanitize_edid(obj),
            "name": stat_formids[obj],
            "x": x, "y": y, "z": z,
            "rx": rx, "ry": ry, "rz": rz,
            "grid_x": grid_x, "grid_y": grid_y,
            "destination_cell": row.get("destination_cell", "").strip(),
        })

    total_refr = sum(len(v) for v in refrs_by_cell.values())
    print(f"Generated {total_refr} REFR records")
    print(f"Next formid object id: 0x{next_formid:04X}")

    # Total record count for HEDR (STAT + CELL + REFR + WRLD override).
    # Exterior Seyda Neen is split into one CELL per Morrowind grid.
    exterior_grids = set()
    for refr in refrs_by_cell.get("Seyda Neen", []):
        exterior_grids.add((refr["grid_x"], refr["grid_y"]))
    exterior_grid_cells = sorted(exterior_grids)
    num_records = len(stat_records) + len(cells) + len(exterior_grid_cells) - 1 + total_refr + 1 + 1  # +1 for persistent CELL

    # Build ESP
    buf = io.BytesIO()

    # TES4 header placeholder
    buf.write(b"TES4")
    data_size_pos = buf.tell()
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", PLUGIN_FLAGS))
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", 0x00000240))
    subrecord_start = buf.tell()

    write_subrecord(buf, "HEDR", struct.pack("<fII", 0.96, num_records, 0xFE000000 | next_formid))
    write_subrecord(buf, "CNAM", b"Seyda Neen Mod\x00")
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
        write_subrecord(stat_sub, "OBND", struct.pack("<ffffff", -1.0, -1.0, -1.0, 1.0, 1.0, 1.0))
        write_subrecord(stat_sub, "ODTY", struct.pack("<I", 0))
        write_subrecord(stat_sub, "BFCB", b"BGSKeywordForm_Component\x00")
        write_subrecord(stat_sub, "BFCE", b"")
        write_subrecord(stat_sub, "MODL", nif_path + b"\x00")
        # FLLD causes CK to reject STAT records; omit it.
        write_record(stat_group, "STAT", fid, 0x00000000, stat_sub)
    write_grup(buf, "STAT", 0, stat_group.getvalue())

    # Interior CELL groups (all under one top-level CELL group)
    interior_block = io.BytesIO()
    subblock_index = 0
    for cell_name in cell_order:
        if cell_name == "Seyda Neen":
            continue  # exterior handled below
        cell_fid = cells[cell_name]
        cell_sub = io.BytesIO()
        edid = sanitize_edid(cell_name)
        write_subrecord(cell_sub, "EDID", edid.encode("ascii") + b"\x00")
        write_subrecord(cell_sub, "FULL", cell_name.encode("ascii") + b"\x00")
        # Starfield interior CELL DATA is a 4-byte flags field (matches ImperialCity interiors).
        write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00010025))
        cell_buf = io.BytesIO()
        write_compressed_record(cell_buf, "CELL", cell_fid, 0x00000000, cell_sub)

        # REFR children
        persistent = io.BytesIO()
        for refr in refrs_by_cell[cell_name]:
            refr_sub = io.BytesIO()
            write_subrecord(refr_sub, "NAME", struct.pack("<I", refr["name"]))
            write_subrecord(refr_sub, "DATA", struct.pack("<ffffff",
                refr["x"], refr["y"], refr["z"], refr["rx"], refr["ry"], refr["rz"]))
            # Only write scale if non-default (matches reference REFRs).
            if refr.get("scale", 1.0) != 1.0:
                write_subrecord(refr_sub, "XSCL", struct.pack("<f", refr["scale"]))
            write_record(persistent, "REFR", refr["formid"], 0x00010400, refr_sub)

        # Children group type=6 contains persistent group type=8, which holds REFRs.
        persistent_grup = io.BytesIO()
        write_grup(persistent_grup, cell_fid, 8, persistent.getvalue())
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

    # Exterior Seyda Neen cells under Morrowind WRLD -- split by Morrowind grid.
    # Starfield WRLD children use block type 4 and sub-block type 5. Labels are
    # signed int16 pairs derived from the cell grid. Exterior REFRs live in group
    # type 9 (temporary), matching ImperialCity.esm.
    exterior_grids = sorted({(r["grid_x"], r["grid_y"]) for r in refrs_by_cell.get("Seyda Neen", [])})

    # Group cells by block/sub-block labels.
    block_map = {}
    for grid_x, grid_y in exterior_grids:
        block_label, sub_label = grid_block_labels(grid_x, grid_y)
        block_map.setdefault(block_label, {}).setdefault(sub_label, []).append((grid_x, grid_y))

    wrld_children = io.BytesIO()

    # Persistent cell at grid (INT_MAX, INT_MAX) — required by CK when a WRLD
    # has exterior cells with many REFRs. Without it CK crashes with a null
    # pointer dereference (access violation 0xC0000005 at offset 0x4D866A8).
    persistent_fid = alloc()
    cell_sub = io.BytesIO()
    write_subrecord(cell_sub, "EDID", b"MorrowindPersistent\x00")
    write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00000002))
    write_subrecord(cell_sub, "XCLC", struct.pack("<iii", 0x7FFFFFFF, 0x7FFFFFFF, 0))
    write_subrecord(cell_sub, "LTMP", struct.pack("<I", 0))
    write_subrecord(cell_sub, "XCLW", struct.pack("<f", 0.0))
    write_subrecord(cell_sub, "XILS", struct.pack("<f", 1.0))
    cell_buf = io.BytesIO()
    write_compressed_record(cell_buf, "CELL", persistent_fid, 0x00000000, cell_sub)
    # Empty persistent children group (type 8) for the persistent cell.
    persistent_grup = io.BytesIO()
    write_grup(persistent_grup, persistent_fid, 8, b"")
    persistent_children = io.BytesIO()
    write_grup(persistent_children, persistent_fid, 6, persistent_grup.getvalue())
    wrld_children.write(cell_buf.getvalue())
    wrld_children.write(persistent_children.getvalue())

    # Exterior grid cells grouped by block/sub-block.
    for block_label, subblocks in sorted(block_map.items(), key=lambda kv: kv[0]):
        block_content = io.BytesIO()
        for sub_label, grids in sorted(subblocks.items(), key=lambda kv: kv[0]):
            sub_content = io.BytesIO()
            for grid_x, grid_y in grids:
                grid_refs = [r for r in refrs_by_cell["Seyda Neen"] if (r["grid_x"], r["grid_y"]) == (grid_x, grid_y)]
                if EXTERIOR_REFR_LIMIT is not None:
                    grid_refs = grid_refs[:EXTERIOR_REFR_LIMIT]
                cell_fid = alloc()
                cell_sub = io.BytesIO()
                edid = f"Seyda_Neen_Exterior_{grid_x}_{grid_y}".encode("ascii")
                write_subrecord(cell_sub, "EDID", edid + b"\x00")
                write_subrecord(cell_sub, "FULL", b"Seyda Neen\x00")
                write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00000002))
                write_subrecord(cell_sub, "XCLC", struct.pack("<iii", grid_x, grid_y, 0))
                write_subrecord(cell_sub, "LTMP", struct.pack("<I", 0))
                write_subrecord(cell_sub, "XCLW", struct.pack("<f", 0.0))
                # XILS is required by CK for exterior cells (value 1.0 as float).
                write_subrecord(cell_sub, "XILS", struct.pack("<f", 1.0))
                cell_buf = io.BytesIO()
                write_compressed_record(cell_buf, "CELL", cell_fid, 0x00000000, cell_sub)

                refr_group = io.BytesIO()
                for refr in grid_refs:
                    refr_sub = io.BytesIO()
                    write_subrecord(refr_sub, "NAME", struct.pack("<I", refr["name"]))
                    write_subrecord(refr_sub, "DATA", struct.pack("<ffffff",
                        refr["x"], refr["y"], refr["z"], refr["rx"], refr["ry"], refr["rz"]))
                    if refr.get("scale", 1.0) != 1.0:
                        write_subrecord(refr_sub, "XSCL", struct.pack("<f", refr["scale"]))
                    write_record(refr_group, "REFR", refr["formid"], 0x00010400, refr_sub)

                # Exterior REFRs use temporary group type 9.
                temp_grup = io.BytesIO()
                write_grup(temp_grup, cell_fid, 9, refr_group.getvalue())
                cell_children = io.BytesIO()
                write_grup(cell_children, cell_fid, 6, temp_grup.getvalue())

                sub_content.write(cell_buf.getvalue())
                sub_content.write(cell_children.getvalue())

            write_grup(block_content, sub_label, 5, sub_content.getvalue())

        write_grup(wrld_children, block_label, 4, block_content.getvalue())

    wrld_children_grup = io.BytesIO()
    write_grup(wrld_children_grup, FID_MORROWIND_WRLD, 1, wrld_children.getvalue())

    wrld_override_subrecords = extract_wrld_body(MASTER_PATH, FID_MORROWIND_WRLD)
    wrld_override = io.BytesIO()
    write_record(wrld_override, "WRLD", FID_MORROWIND_WRLD, 0x00000004, wrld_override_subrecords)

    wrld_group_content = io.BytesIO()
    wrld_group_content.write(wrld_override.getvalue())
    wrld_group_content.write(wrld_children_grup.getvalue())
    write_grup(buf, "WRLD", 0, wrld_group_content.getvalue())

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "wb") as f:
        f.write(buf.getvalue())

    print(f"Created {OUTPUT_FILE}")
    print(f"Size: {buf.tell()} bytes")


if __name__ == "__main__":
    main()



































