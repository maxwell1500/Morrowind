import os, struct, io, csv, zlib, math

OUTPUT_DIR = r'C:\Users\max\Projects\Morrowind\Data'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'SeydaNeen_exterior_marker_10.esp')
PLACEMENT_FILE = r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv'
MAPPING_FILE = r'C:\Users\max\Projects\Morrowind\converted_assets\mapping\seyda_neen_asset_mapping.csv'
MASTER_PATH = r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm'
PLUGIN_FLAGS = 0x00000101
FID_MORROWIND_WRLD = 0x0100E1C8
MW_CELL_SIZE = 8192.0


def extract_wrld_body(master_path, wrld_formid):
    with open(master_path, 'rb') as f:
        data = f.read()
    pos = 0
    while pos < len(data) - 16:
        if data[pos:pos+4] == b'WRLD':
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            formid = struct.unpack('<I', data[pos+12:pos+16])[0]
            if formid == wrld_formid:
                rec = data[pos+16:pos+16+size]
                if rec[:8] == b'\x00\x00\x00\x00@\x02\x00\x00':
                    return rec[8:]
                return rec
            pos += 16 + size
        else:
            pos += 1
    raise RuntimeError('WRLD not found')


def write_subrecord(buf, sig, data):
    buf.write(sig.encode('ascii'))
    buf.write(struct.pack('<H', len(data)))
    buf.write(data)


def write_record(buf, sig, formid, flags, subrecords):
    sub_data = subrecords.getvalue() if hasattr(subrecords, 'getvalue') else subrecords
    buf.write(sig.encode('ascii'))
    buf.write(struct.pack('<I', len(sub_data)))
    buf.write(struct.pack('<I', flags))
    buf.write(struct.pack('<I', formid))
    buf.write(struct.pack('<I', 0))
    buf.write(struct.pack('<I', 0x00000240))
    buf.write(sub_data)


def write_compressed_record(buf, sig, formid, flags, subrecords):
    sub_data = subrecords.getvalue() if hasattr(subrecords, 'getvalue') else subrecords
    compressed = zlib.compress(sub_data)
    content = struct.pack('<I', len(sub_data)) + compressed
    buf.write(sig.encode('ascii'))
    buf.write(struct.pack('<I', len(content)))
    buf.write(struct.pack('<I', flags | 0x00040000))
    buf.write(struct.pack('<I', formid))
    buf.write(struct.pack('<I', 0))
    buf.write(struct.pack('<I', 0x00000240))
    buf.write(content)


def write_grup(buf, label, grup_type, content):
    data = content.getvalue() if hasattr(content, 'getvalue') else content
    buf.write(b'GRUP')
    buf.write(struct.pack('<I', len(data) + 24))
    if isinstance(label, str):
        label_bytes = label.encode('ascii')[:4].ljust(4, b'\x00')
    else:
        label_bytes = struct.pack('<I', label & 0xFFFFFFFF)
    buf.write(label_bytes)
    buf.write(struct.pack('<I', grup_type))
    buf.write(b'\x00' * 8)
    buf.write(data)


def sanitize_edid(name):
    return ''.join(c if c.isalnum() or c == '_' else '_' for c in name).rstrip('_')


next_formid = 0x00000800

def alloc():
    global next_formid
    fid = 0xFE000000 | next_formid
    next_formid += 1
    return fid


placements = []
with open(PLACEMENT_FILE, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        placements.append(row)

nif_path_by_object = {}
with open(MAPPING_FILE, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        obj_id = row['object_id'].strip().lower()
        if row.get('nif_converted', '').strip().lower() == 'true':
            nif_path_by_object[obj_id] = 'morrowind\\%s.nif' % obj_id

converted_objects = set()
for row in placements:
    if row['mesh_converted'].strip().lower() == 'true':
        converted_objects.add(row['object_id'].strip().lower())

stat_formids = {}
stat_records = []
for obj in sorted(converted_objects):
    fid = alloc()
    stat_formids[obj] = fid
    nif_path = nif_path_by_object.get(obj, 'morrowind\\%s.nif' % obj)
    stat_records.append((fid, sanitize_edid(obj), nif_path.encode('ascii')))

marker_fid = stat_formids[sorted(converted_objects)[0]]
print('Marker STAT:', sorted(converted_objects)[0], '0x%08X' % marker_fid)

cells = {}
cell_order = []
for row in placements:
    cell = row['cell'].strip()
    if cell not in cells:
        cells[cell] = alloc()
        cell_order.append(cell)

refrs_by_cell = {cell: [] for cell in cells}
for row in placements:
    cell = row['cell'].strip()
    obj = row['object_id'].strip().lower()
    if obj not in stat_formids:
        continue
    x_mw = float(row['x_mw'])
    y_mw = float(row['y_mw'])
    z_mw = float(row['z_mw'])
    grid_x = int(math.floor(x_mw / MW_CELL_SIZE))
    grid_y = int(math.floor(y_mw / MW_CELL_SIZE))
    x = (x_mw - grid_x * MW_CELL_SIZE) * 50.0
    y = (y_mw - grid_y * MW_CELL_SIZE) * 50.0
    z = z_mw * 50.0
    rx = float(row['rot_x'])
    ry = float(row['rot_y'])
    rz = float(row['rot_z'])
    refrs_by_cell[cell].append({
        'formid': alloc(),
        'name': marker_fid,  # ALL use marker
        'x': x, 'y': y, 'z': z,
        'rx': rx, 'ry': ry, 'rz': rz,
        'grid_x': grid_x, 'grid_y': grid_y,
    })

exterior_grids = sorted({(r['grid_x'], r['grid_y']) for r in refrs_by_cell.get('Seyda Neen', [])})
total_refr = sum(len(v) for v in refrs_by_cell.values())
num_records = len(stat_records) + len(cells) + len(exterior_grids) - 1 + total_refr + 1

buf = io.BytesIO()
buf.write(b'TES4')
data_size_pos = buf.tell()
buf.write(struct.pack('<I', 0))
buf.write(struct.pack('<I', PLUGIN_FLAGS))
buf.write(struct.pack('<I', 0))
buf.write(struct.pack('<I', 0))
buf.write(struct.pack('<I', 0x00000240))
subrecord_start = buf.tell()
write_subrecord(buf, 'HEDR', struct.pack('<fII', 0.96, num_records, 0xFE000000 | next_formid))
write_subrecord(buf, 'CNAM', b'Seyda Neen Exterior Marker 10\x00')
write_subrecord(buf, 'MAST', b'Starfield.esm\x00')
write_subrecord(buf, 'MAST', b'The Elder Star System - Magnus.esm\x00')
write_subrecord(buf, 'BNAM', b'Main\x00')
write_subrecord(buf, 'INCC', struct.pack('<I', 0))
data_size = buf.tell() - subrecord_start
buf.seek(data_size_pos)
buf.write(struct.pack('<I', data_size))
buf.seek(0, 2)

stat_group = io.BytesIO()
for fid, edid, nif_path in stat_records:
    stat_sub = io.BytesIO()
    write_subrecord(stat_sub, 'EDID', edid.encode('ascii') + b'\x00')
    write_subrecord(stat_sub, 'OBND', struct.pack('<ffffff', -1, -1, -1, 1, 1, 1))
    write_subrecord(stat_sub, 'ODTY', struct.pack('<I', 0))
    write_subrecord(stat_sub, 'BFCB', b'BGSKeywordForm_Component\x00')
    write_subrecord(stat_sub, 'BFCE', b'')
    write_subrecord(stat_sub, 'MODL', nif_path + b'\x00')
    write_record(stat_group, 'STAT', fid, 0, stat_sub)
write_grup(buf, 'STAT', 0, stat_group.getvalue())

# Empty interiors
interior_block = io.BytesIO()
subblock_index = 0
for cell_name in cell_order:
    if cell_name == 'Seyda Neen':
        continue
    cell_fid = cells[cell_name]
    cell_sub = io.BytesIO()
    edid = sanitize_edid(cell_name)
    write_subrecord(cell_sub, 'EDID', edid.encode('ascii') + b'\x00')
    write_subrecord(cell_sub, 'FULL', cell_name.encode('ascii') + b'\x00')
    write_subrecord(cell_sub, 'DATA', struct.pack('<I', 0x00010025))
    cell_buf = io.BytesIO()
    write_compressed_record(cell_buf, 'CELL', cell_fid, 0, cell_sub)
    children = io.BytesIO()
    write_grup(children, cell_fid, 6, b'')
    subblock = io.BytesIO()
    subblock.write(cell_buf.getvalue())
    subblock.write(children.getvalue())
    write_grup(interior_block, subblock_index, 3, subblock.getvalue())
    subblock_index += 1

interior_top_block = io.BytesIO()
write_grup(interior_top_block, 0, 2, interior_block.getvalue())
write_grup(buf, 'CELL', 0, interior_top_block.getvalue())

# Exterior cells with marker REFRs
exterior_block = io.BytesIO()
subblock_index = 0
for grid_x, grid_y in exterior_grids:
    grid_refs = [r for r in refrs_by_cell['Seyda Neen'] if (r['grid_x'], r['grid_y']) == (grid_x, grid_y)]
    cell_fid = alloc()
    cell_sub = io.BytesIO()
    edid = ('Seyda_Neen_Exterior_%d_%d' % (grid_x, grid_y)).encode('ascii')
    write_subrecord(cell_sub, 'EDID', edid + b'\x00')
    write_subrecord(cell_sub, 'FULL', b'Seyda Neen\x00')
    write_subrecord(cell_sub, 'DATA', struct.pack('<I', 0x00000002))
    write_subrecord(cell_sub, 'XCLC', struct.pack('<iii', grid_x, grid_y, 0))
    write_subrecord(cell_sub, 'LTMP', struct.pack('<I', 0))
    write_subrecord(cell_sub, 'XCLW', struct.pack('<f', 0.0))
    cell_buf = io.BytesIO()
    write_compressed_record(cell_buf, 'CELL', cell_fid, 0, cell_sub)

    persistent = io.BytesIO()
    for refr in grid_refs[:10]:
        refr_sub = io.BytesIO()
        write_subrecord(refr_sub, 'NAME', struct.pack('<I', marker_fid))
        write_subrecord(refr_sub, 'DATA', struct.pack('<ffffff',
            refr['x'], refr['y'], refr['z'], refr['rx'], refr['ry'], refr['rz']))
        write_record(persistent, 'REFR', refr['formid'], 0x00010400, refr_sub)

    persistent_grup = io.BytesIO()
    write_grup(persistent_grup, cell_fid, 8, persistent.getvalue())
    cell_children = io.BytesIO()
    write_grup(cell_children, cell_fid, 6, persistent_grup.getvalue())

    subblock = io.BytesIO()
    subblock.write(cell_buf.getvalue())
    subblock.write(cell_children.getvalue())
    write_grup(exterior_block, subblock_index, 5, subblock.getvalue())
    subblock_index += 1

exterior_top_block = io.BytesIO()
write_grup(exterior_top_block, 0, 4, exterior_block.getvalue())

wrld_children = io.BytesIO()
write_grup(wrld_children, FID_MORROWIND_WRLD, 1, exterior_top_block.getvalue())

wrld_override_subrecords = extract_wrld_body(MASTER_PATH, FID_MORROWIND_WRLD)
wrld_override = io.BytesIO()
write_record(wrld_override, 'WRLD', FID_MORROWIND_WRLD, 0x00000004, wrld_override_subrecords)

wrld_group_content = io.BytesIO()
wrld_group_content.write(wrld_override.getvalue())
wrld_group_content.write(wrld_children.getvalue())
write_grup(buf, 'WRLD', 0, wrld_group_content.getvalue())

with open(OUTPUT_FILE, 'wb') as f:
    f.write(buf.getvalue())
print('Created %s size=%d' % (OUTPUT_FILE, buf.tell()))



