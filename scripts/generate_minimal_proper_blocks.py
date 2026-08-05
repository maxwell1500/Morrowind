import struct, io, zlib, os

OUTPUT_FILE = r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen_minimal_proper_blocks.esp'
MASTER_PATH = r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm'
PLUGIN_FLAGS = 0x00000101
FID_MORROWIND_WRLD = 0x0100E1C8


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
    if isinstance(label, (bytes, bytearray)):
        label_bytes = label[:4].ljust(4, b'\x00')
    elif isinstance(label, str):
        label_bytes = label.encode('ascii')[:4].ljust(4, b'\x00')
    else:
        label_bytes = struct.pack('<I', label & 0xFFFFFFFF)
    buf.write(label_bytes)
    buf.write(struct.pack('<I', grup_type))
    buf.write(b'\x00' * 8)
    buf.write(data)


def pack_int16_pair(a, b):
    return struct.pack('<hh', a, b)


def grid_block_labels(grid_x, grid_y):
    # Based on ImperialCity.esm analysis:
    # block label = (grid_y // 32, grid_x // 32) as signed int16s
    # sub-block label = (grid_y % 32 // 8, grid_x % 32 // 8) as signed int16s
    # Need C-style modulo for negatives: n % d in C truncates toward 0.
    def c_mod(n, d):
        r = n % d
        if r > d // 2:
            r -= d
        return r
    block_x = grid_x // 32
    block_y = grid_y // 32
    sub_x = c_mod(grid_x, 32) // 8
    sub_y = c_mod(grid_y, 32) // 8
    block_label = pack_int16_pair(block_y, block_x)
    sub_label = pack_int16_pair(sub_y, sub_x)
    return block_label, sub_label


next_formid = 0x00000800

def alloc():
    global next_formid
    fid = 0xFE000000 | next_formid
    next_formid += 1
    return fid


buf = io.BytesIO()
buf.write(b'TES4')
data_size_pos = buf.tell()
buf.write(struct.pack('<I', 0))
buf.write(struct.pack('<I', PLUGIN_FLAGS))
buf.write(struct.pack('<I', 0))
buf.write(struct.pack('<I', 0))
buf.write(struct.pack('<I', 0x00000240))
subrecord_start = buf.tell()
num_records = 4  # 1 STAT + 1 exterior CELL + 1 interior CELL + 1 REFR + 1 WRLD = 5? Actually 1 STAT + 2 CELL + 1 REFR + 1 WRLD = 5
write_subrecord(buf, 'HEDR', struct.pack('<fII', 0.96, 5, 0xFE000000 | next_formid))
write_subrecord(buf, 'CNAM', b'Proper Blocks Test\x00')
write_subrecord(buf, 'MAST', b'Starfield.esm\x00')
write_subrecord(buf, 'MAST', b'The Elder Star System - Magnus.esm\x00')
write_subrecord(buf, 'BNAM', b'Main\x00')
write_subrecord(buf, 'INCC', struct.pack('<I', 0))
data_size = buf.tell() - subrecord_start
buf.seek(data_size_pos)
buf.write(struct.pack('<I', data_size))
buf.seek(0, 2)

stat_fid = alloc()
stat_sub = io.BytesIO()
write_subrecord(stat_sub, 'EDID', b'test_marker\x00')
write_subrecord(stat_sub, 'OBND', struct.pack('<ffffff', -1, -1, -1, 1, 1, 1))
write_subrecord(stat_sub, 'ODTY', struct.pack('<I', 0))
write_subrecord(stat_sub, 'BFCB', b'BGSKeywordForm_Component\x00')
write_subrecord(stat_sub, 'BFCE', b'')
write_subrecord(stat_sub, 'MODL', b'morrowind\\active_de_bed_30.nif\x00')
stat_grup = io.BytesIO()
write_record(stat_grup, 'STAT', stat_fid, 0, stat_sub)
write_grup(buf, 'STAT', 0, stat_grup.getvalue())

# Interior dummy cell
interior_fid = alloc()
cell_sub = io.BytesIO()
write_subrecord(cell_sub, 'EDID', b'DummyInterior\x00')
write_subrecord(cell_sub, 'FULL', b'Dummy\x00')
write_subrecord(cell_sub, 'DATA', struct.pack('<I', 0x00010025))
cell_buf = io.BytesIO()
write_compressed_record(cell_buf, 'CELL', interior_fid, 0, cell_sub)
children = io.BytesIO()
write_grup(children, interior_fid, 6, b'')
subblock = io.BytesIO()
subblock.write(cell_buf.getvalue())
subblock.write(children.getvalue())
block = io.BytesIO()
write_grup(block, 0, 3, subblock.getvalue())
top = io.BytesIO()
write_grup(top, 0, 2, block.getvalue())
write_grup(buf, 'CELL', 0, top.getvalue())

# Exterior cell (-2,-10) with proper block labels and type 9 REFR group
grid_x, grid_y = -2, -10
block_label, sub_label = grid_block_labels(grid_x, grid_y)
print('Grid (%d,%d): block_label=%s sub_label=%s' % (grid_x, grid_y, block_label.hex(), sub_label.hex()))

cell_fid = alloc()
cell_sub = io.BytesIO()
write_subrecord(cell_sub, 'EDID', b'Seyda_Neen_Exterior_-2_-10\x00')
write_subrecord(cell_sub, 'FULL', b'Seyda Neen\x00')
write_subrecord(cell_sub, 'DATA', struct.pack('<I', 0x00000002))
write_subrecord(cell_sub, 'XCLC', struct.pack('<iii', grid_x, grid_y, 0))
write_subrecord(cell_sub, 'LTMP', struct.pack('<I', 0))
write_subrecord(cell_sub, 'XCLW', struct.pack('<f', 0.0))
cell_buf = io.BytesIO()
write_compressed_record(cell_buf, 'CELL', cell_fid, 0, cell_sub)

# Type 9 REFR group for exterior
refr_sub = io.BytesIO()
write_subrecord(refr_sub, 'NAME', struct.pack('<I', stat_fid))
write_subrecord(refr_sub, 'DATA', struct.pack('<ffffff', 0, 0, 0, 0, 0, 0))
temp = io.BytesIO()
write_record(temp, 'REFR', alloc(), 0x00010400, refr_sub)
temp_grup = io.BytesIO()
write_grup(temp_grup, cell_fid, 9, temp.getvalue())
children = io.BytesIO()
write_grup(children, cell_fid, 6, temp_grup.getvalue())

subblock = io.BytesIO()
subblock.write(cell_buf.getvalue())
subblock.write(children.getvalue())
cell_block = io.BytesIO()
write_grup(cell_block, sub_label, 5, subblock.getvalue())
block = io.BytesIO()
write_grup(block, block_label, 4, cell_block.getvalue())

wrld_children = io.BytesIO()
write_grup(wrld_children, FID_MORROWIND_WRLD, 1, block.getvalue())
wrld_override_subrecords = extract_wrld_body(MASTER_PATH, FID_MORROWIND_WRLD)
wrld_override = io.BytesIO()
write_record(wrld_override, 'WRLD', FID_MORROWIND_WRLD, 0x00000004, wrld_override_subrecords)
wrld_top = io.BytesIO()
wrld_top.write(wrld_override.getvalue())
wrld_top.write(wrld_children.getvalue())
write_grup(buf, 'WRLD', 0, wrld_top.getvalue())

with open(OUTPUT_FILE, 'wb') as f:
    f.write(buf.getvalue())
print('Created %s size=%d' % (OUTPUT_FILE, buf.tell()))
