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

OUTPUT_DIR = r"C:\Users\max\Projects\Morrowind\Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "SeydaNeen.esp")
PLACEMENT_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv"
MAPPING_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\mapping\seyda_neen_asset_mapping.csv"
MASTER_PATH = r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm"

PLUGIN_FLAGS = 0x00000101  # master + ESL
FID_MORROWIND_WRLD = 0x0100E1C8
EXTERIOR_GRID = (-11, -1)

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
    if isinstance(label, str):
        label_bytes = label.encode("ascii")[:4].ljust(4, b"\x00")
    else:
        label_bytes = struct.pack("<I", label)
    buf.write(label_bytes)
    buf.write(struct.pack("<I", grup_type))
    buf.write(b"\x00" * 8)
    buf.write(data)


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
        x = float(row["x_sf"])
        y = float(row["y_sf"])
        z = float(row["z_sf"])
        rx = float(row["rot_x"])
        ry = float(row["rot_y"])
        rz = float(row["rot_z"])
        refrs_by_cell[cell].append({
            "formid": alloc(),
            "edid": sanitize_edid(obj),
            "name": stat_formids[obj],
            "x": x, "y": y, "z": z,
            "rx": rx, "ry": ry, "rz": rz,
        })

    total_refr = sum(len(v) for v in refrs_by_cell.values())
    print(f"Generated {total_refr} REFR records")
    print(f"Next formid object id: 0x{next_formid:04X}")

    # Total record count for HEDR (STAT + CELL + REFR + WRLD override).
    num_records = len(stat_records) + len(cells) + total_refr + 1

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

    # Exterior Seyda Neen cell under Morrowind WRLD
    exterior_fid = cells["Seyda Neen"]
    cell_sub = io.BytesIO()
    write_subrecord(cell_sub, "EDID", b"Seyda_Neen_Exterior\x00")
    write_subrecord(cell_sub, "FULL", b"Seyda Neen\x00")
    # Starfield exterior CELL DATA is a 4-byte flags field.
    write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00000002))
    # XCLC is 12 bytes: grid x, grid y, plus an additional int (typically 0).
    write_subrecord(cell_sub, "XCLC", struct.pack("<iii", EXTERIOR_GRID[0], EXTERIOR_GRID[1], 0))
    # LTMP is a 4-byte formID reference to the default lighting template (0 = none).
    write_subrecord(cell_sub, "LTMP", struct.pack("<I", 0))
    write_subrecord(cell_sub, "XCLW", struct.pack("<f", 0.0))
    cell_buf = io.BytesIO()
    write_compressed_record(cell_buf, "CELL", exterior_fid, 0x00000000, cell_sub)

    persistent = io.BytesIO()
    EXTERIOR_REFR_LIMIT = 100
for refr in refrs_by_cell["Seyda Neen"][:EXTERIOR_REFR_LIMIT]:
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
    write_grup(persistent_grup, exterior_fid, 8, persistent.getvalue())
    cell_children = io.BytesIO()
    write_grup(cell_children, exterior_fid, 6, persistent_grup.getvalue())

    subblock = io.BytesIO()
    subblock.write(cell_buf.getvalue())
    subblock.write(cell_children.getvalue())
    exterior_block = io.BytesIO()
    write_grup(exterior_block, 0, 2, subblock.getvalue())

    wrld_children = io.BytesIO()
    write_grup(wrld_children, FID_MORROWIND_WRLD, 1, exterior_block.getvalue())

    wrld_override_subrecords = extract_wrld_body(MASTER_PATH, FID_MORROWIND_WRLD)
    wrld_override = io.BytesIO()
    write_record(wrld_override, "WRLD", FID_MORROWIND_WRLD, 0x00000004, wrld_override_subrecords)

    wrld_group_content = io.BytesIO()
    wrld_group_content.write(wrld_override.getvalue())
    wrld_group_content.write(wrld_children.getvalue())
    write_grup(buf, "WRLD", 0, wrld_group_content.getvalue())

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "wb") as f:
        f.write(buf.getvalue())

    print(f"Created {OUTPUT_FILE}")
    print(f"Size: {buf.tell()} bytes")


if __name__ == "__main__":
    main()
