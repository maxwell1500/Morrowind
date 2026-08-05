import os, struct, io, csv, zlib, math

OUTPUT_DIR = r"C:\Users\max\Projects\Morrowind\Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "SeydaNeen_pc12_override.esp")
PLACEMENT_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv"
MAPPING_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\mapping\seyda_neen_asset_mapping.csv"
MASTER_PATH = r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm"
PLUGIN_FLAGS = 0x00000101
FID_MORROWIND_WRLD = 0x0100E1C8
MW_CELL_SIZE = 8192.0
DEG2RAD = math.pi / 180.0
EXISTING_CELL_FID = 0x010488FA


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

refrs = []
for row in placements:
    if row["cell"].strip() != "Seyda Neen":
        continue
    obj = row["object_id"].strip().lower()
    if obj not in stat_formids:
        continue
    x_mw = float(row["x_mw"]); y_mw = float(row["y_mw"]); z_mw = float(row["z_mw"])
    gx = int(math.floor(x_mw / MW_CELL_SIZE))
    gy = int(math.floor(y_mw / MW_CELL_SIZE))
    x = (x_mw - gx*MW_CELL_SIZE)*50.0
    y = (y_mw - gy*MW_CELL_SIZE)*50.0
    z = z_mw
    rx = float(row["rot_x"])*DEG2RAD; ry = float(row["rot_y"])*DEG2RAD; rz = float(row["rot_z"])*DEG2RAD
    refrs.append({"x":x,"y":y,"z":z,"rx":rx,"ry":ry,"rz":rz,"gx":gx,"gy":gy})

grid_refs = [r for r in refrs if (r['gx'], r['gy']) == (-2, -10)][:12]

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
write_subrecord(buf, "CNAM", b"Override 12 REFR\x00")
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

# 1 dummy interior
interior_fid = alloc()
cell_sub = io.BytesIO()
write_subrecord(cell_sub, "EDID", b"DummyInterior\x00")
write_subrecord(cell_sub, "FULL", b"Dummy\x00")
write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00010025))
cell_buf = io.BytesIO()
write_compressed_record(cell_buf, "CELL", interior_fid, 0, cell_sub)
children = io.BytesIO()
write_grup(children, interior_fid, 6, b"")
subblock = io.BytesIO()
subblock.write(cell_buf.getvalue())
subblock.write(children.getvalue())
block = io.BytesIO()
write_grup(block, 0, 3, subblock.getvalue())
top = io.BytesIO()
write_grup(top, 0, 2, block.getvalue())
write_grup(buf, "CELL", 0, top.getvalue())

# WRLD group
wrld_children = io.BytesIO()

# Persistent cell at INT_MAX
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

# Exterior cell using EXISTING formID 0x010488FA
grid_x, grid_y = -2, -10
block_label, sub_label = grid_block_labels(grid_x, grid_y)
cell_sub = io.BytesIO()
write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00000002))
write_subrecord(cell_sub, "XCLC", struct.pack("<iii", grid_x, grid_y, 0))
write_subrecord(cell_sub, "LTMP", struct.pack("<I", 0))
write_subrecord(cell_sub, "XCLW", struct.pack("<f", 0.0))
write_subrecord(cell_sub, "XILS", struct.pack("<f", 1.0))
cell_buf = io.BytesIO()
write_compressed_record(cell_buf, "CELL", EXISTING_CELL_FID, 0x00000000, cell_sub)

refr_group = io.BytesIO()
for refr in grid_refs:
    refr_sub = io.BytesIO()
    write_subrecord(refr_sub, "NAME", struct.pack("<I", marker_fid))
    write_subrecord(refr_sub, "DATA", struct.pack("<ffffff",
        refr["x"], refr["y"], refr["z"], refr["rx"], refr["ry"], refr["rz"]))
    write_record(refr_group, "REFR", alloc(), 0x00010400, refr_sub)

temp_grup = io.BytesIO()
write_grup(temp_grup, EXISTING_CELL_FID, 9, refr_group.getvalue())
cell_children = io.BytesIO()
write_grup(cell_children, EXISTING_CELL_FID, 6, temp_grup.getvalue())

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
print("8 REFRs in existing cell 0x%08X at grid (-2,-10)" % EXISTING_CELL_FID)

