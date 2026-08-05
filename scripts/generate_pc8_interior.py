import os, struct, io, csv, zlib, math

OUTPUT_DIR = r"C:\Users\max\Projects\Morrowind\Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "SeydaNeen_pc8_interior.esp")
PLACEMENT_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv"
MAPPING_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\mapping\seyda_neen_asset_mapping.csv"
MASTER_PATH = r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm"
PLUGIN_FLAGS = 0x00000101
FID_MORROWIND_WRLD = 0x0100E1C8
MW_CELL_SIZE = 8192.0
DEG2RAD = math.pi / 180.0


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
    raise RuntimeError("WRLD not found")


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


next_formid = 0x00000800

def alloc():
    global next_formid
    fid = 0xFE000000 | next_formid
    next_formid += 1
    return fid


placements = []
with open(PLACEMENT_FILE, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        placements.append(row)

nif_path_by_object = {}
with open(MAPPING_FILE, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        obj_id = row["object_id"].strip().lower()
        if row.get("nif_converted", "").strip().lower() == "true":
            nif_path_by_object[obj_id] = "morrowind\\%s.nif" % obj_id

converted_objects = set()
for row in placements:
    if row["mesh_converted"].strip().lower() == "true":
        converted_objects.add(row["object_id"].strip().lower())

stat_formids = {}
stat_records = []
for obj in sorted(converted_objects):
    fid = alloc()
    stat_formids[obj] = fid
    nif_path = nif_path_by_object.get(obj, "morrowind\\%s.nif" % obj)
    stat_records.append((fid, obj, nif_path.encode("ascii")))

marker_fid = stat_formids[sorted(converted_objects)[0]]

buf = io.BytesIO()
buf.write(b"TES4")
data_size_pos = buf.tell()
buf.write(struct.pack("<I", 0))
buf.write(struct.pack("<I", PLUGIN_FLAGS))
buf.write(struct.pack("<I", 0))
buf.write(struct.pack("<I", 0))
buf.write(struct.pack("<I", 0x00000240))
subrecord_start = buf.tell()
num_records = len(stat_records) + 1 + 1 + 8 + 1 + 1
write_subrecord(buf, "HEDR", struct.pack("<fII", 0.96, num_records, 0xFE000000 | next_formid))
write_subrecord(buf, "CNAM", b"241STAT 8INTREFR\x00")
write_subrecord(buf, "MAST", b"Starfield.esm\x00")
write_subrecord(buf, "MAST", b"The Elder Star System - Magnus.esm\x00")
write_subrecord(buf, "BNAM", b"Main\x00")
write_subrecord(buf, "INCC", struct.pack("<I", 0))
data_size = buf.tell() - subrecord_start
buf.seek(data_size_pos)
buf.write(struct.pack("<I", data_size))
buf.seek(0, 2)

stat_group = io.BytesIO()
for fid, edid, nif_path in stat_records:
    stat_sub = io.BytesIO()
    write_subrecord(stat_sub, "EDID", edid.encode("ascii") + b"\x00")
    write_subrecord(stat_sub, "OBND", struct.pack("<ffffff", -1, -1, -1, 1, 1, 1))
    write_subrecord(stat_sub, "ODTY", struct.pack("<I", 0))
    write_subrecord(stat_sub, "BFCB", b"BGSKeywordForm_Component\x00")
    write_subrecord(stat_sub, "BFCE", b"")
    write_subrecord(stat_sub, "MODL", nif_path + b"\x00")
    write_record(stat_group, "STAT", fid, 0, stat_sub)
write_grup(buf, "STAT", 0, stat_group.getvalue())

# Interior cell with 8 REFRs
interior_fid = alloc()
cell_sub = io.BytesIO()
write_subrecord(cell_sub, "EDID", b"TestInterior\x00")
write_subrecord(cell_sub, "FULL", b"Test Interior\x00")
write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00010025))
cell_buf = io.BytesIO()
write_compressed_record(cell_buf, "CELL", interior_fid, 0, cell_sub)

persistent = io.BytesIO()
for _ in range(8):
    refr_sub = io.BytesIO()
    write_subrecord(refr_sub, "NAME", struct.pack("<I", marker_fid))
    write_subrecord(refr_sub, "DATA", struct.pack("<ffffff", 0, 0, 0, 0, 0, 0))
    write_record(persistent, "REFR", alloc(), 0x00010400, refr_sub)

persistent_grup = io.BytesIO()
write_grup(persistent_grup, interior_fid, 8, persistent.getvalue())
cell_children = io.BytesIO()
write_grup(cell_children, interior_fid, 6, persistent_grup.getvalue())

subblock = io.BytesIO()
subblock.write(cell_buf.getvalue())
subblock.write(cell_children.getvalue())
block = io.BytesIO()
write_grup(block, 0, 3, subblock.getvalue())
top = io.BytesIO()
write_grup(top, 0, 2, block.getvalue())
write_grup(buf, "CELL", 0, top.getvalue())

# WRLD group with persistent cell + empty grid cell
wrld_children = io.BytesIO()
persistent_fid = alloc()
cell_sub = io.BytesIO()
write_subrecord(cell_sub, "EDID", b"MorrowindPersistent\x00")
write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00000002))
write_subrecord(cell_sub, "XCLC", struct.pack("<iii", 0x7FFFFFFF, 0x7FFFFFFF, 0))
write_subrecord(cell_sub, "LTMP", struct.pack("<I", 0))
write_subrecord(cell_sub, "XCLW", struct.pack("<f", 0.0))
write_subrecord(cell_sub, "XILS", struct.pack("<f", 1.0))
cell_buf = io.BytesIO()
write_compressed_record(cell_buf, "CELL", persistent_fid, 0, cell_sub)
persistent_grup = io.BytesIO()
write_grup(persistent_grup, persistent_fid, 8, b"")
persistent_children = io.BytesIO()
write_grup(persistent_children, persistent_fid, 6, persistent_grup.getvalue())
wrld_children.write(cell_buf.getvalue())
wrld_children.write(persistent_children.getvalue())

grid_x, grid_y = -2, -10
block_label, sub_label = grid_block_labels(grid_x, grid_y)
cell_fid = alloc()
cell_sub = io.BytesIO()
edid = ("Seyda_Neen_Exterior_%d_%d" % (grid_x, grid_y)).encode("ascii")
write_subrecord(cell_sub, "EDID", edid + b"\x00")
write_subrecord(cell_sub, "FULL", b"Seyda Neen\x00")
write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00000002))
write_subrecord(cell_sub, "XCLC", struct.pack("<iii", grid_x, grid_y, 0))
write_subrecord(cell_sub, "LTMP", struct.pack("<I", 0))
write_subrecord(cell_sub, "XCLW", struct.pack("<f", 0.0))
write_subrecord(cell_sub, "XILS", struct.pack("<f", 1.0))
cell_buf = io.BytesIO()
write_compressed_record(cell_buf, "CELL", cell_fid, 0, cell_sub)
cell_children = io.BytesIO()
write_grup(cell_children, cell_fid, 6, b"")

subblock = io.BytesIO()
subblock.write(cell_buf.getvalue())
subblock.write(cell_children.getvalue())
cell_block = io.BytesIO()
write_grup(cell_block, sub_label, 5, subblock.getvalue())
block = io.BytesIO()
write_grup(block, block_label, 4, cell_block.getvalue())
wrld_children.write(block.getvalue())

wrld_children_grup = io.BytesIO()
write_grup(wrld_children_grup, FID_MORROWIND_WRLD, 1, wrld_children.getvalue())
wrld_override_subrecords = extract_wrld_body(MASTER_PATH, FID_MORROWIND_WRLD)
wrld_override = io.BytesIO()
write_record(wrld_override, "WRLD", FID_MORROWIND_WRLD, 0x00000004, wrld_override_subrecords)
wrld_group_content = io.BytesIO()
wrld_group_content.write(wrld_override.getvalue())
wrld_group_content.write(wrld_children_grup.getvalue())
write_grup(buf, "WRLD", 0, wrld_group_content.getvalue())

with open(OUTPUT_FILE, "wb") as f:
    f.write(buf.getvalue())
print("Created %s size=%d" % (OUTPUT_FILE, buf.tell()))
print("241 STATs + 8 REFRs in INTERIOR cell + persistent cell + empty grid")
