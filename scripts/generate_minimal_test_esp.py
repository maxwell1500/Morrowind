"""
Minimal test ESP: 1 STAT + 1 REFR in Magnus Morrowind cell (-1,-1)
Tests whether the game runtime loads ESL-formID records at all.
"""
import struct, os, io, zlib

OUTPUT = r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen_Minimal.esp'

STAT_FID = 0xFE000100
REFR_FID = 0xFE000200
CELL_FID = 0x010478A1
WRLD_FID = 0x0100E1C8
PERSIST_CELL_FID = 0x0100E954

POS_X, POS_Y, POS_Z = -2050.0, -2050.0, 482.0

def wsub(out, sig, data):
    out.write(sig.encode('ascii') if isinstance(sig, str) else sig)
    out.write(struct.pack('<H', len(data)))
    out.write(data)

def make_grup(label, gtype, children):
    out = io.BytesIO()
    out.write(b'GRUP')
    out.write(struct.pack('<I', 24 + len(children)))
    out.write(label if isinstance(label, bytes) else label.encode('ascii'))
    out.write(struct.pack('<I', gtype))
    out.write(b'\x00' * 8)
    out.write(children)
    return out.getvalue()

# --- Build all records ---
out = io.BytesIO()

# TES4 header (24 bytes: 4 sig + 5 ints)
out.write(b'TES4')
dsp = out.tell()
out.write(struct.pack('<IIIII', 0, 0x101, 0, 0, 0x240))
srs = out.tell()
wsub(out, 'HEDR', struct.pack('<fII', 0.96, 10, STAT_FID))
wsub(out, 'CNAM', b'Test\x00')
wsub(out, 'BNAM', b'Test\x00')
wsub(out, 'INCC', struct.pack('<I', 0))
wsub(out, 'MAST', b'Starfield.esm\x00')
wsub(out, 'DATA', struct.pack('<Q', 0))
ds = out.tell() - srs
out.seek(dsp)
out.write(struct.pack('<I', ds))
out.seek(0, 2)

# --- STAT record ---
stat = io.BytesIO()
wsub(stat, 'EDID', b'test_box\x00')
wsub(stat, 'OBND', struct.pack('<ffffff', -1, -1, -1, 1, 1, 1))
wsub(stat, 'ODTY', struct.pack('<I', 0))
wsub(stat, 'BFCB', b'BGSKeywordForm_Component\x00')
wsub(stat, 'BFCE', b'')
wsub(stat, 'MODL', b'clutter\\box01.nif\x00')
wsub(stat, 'FLLD', struct.pack('<I', 1))
wsub(stat, 'DNAM', struct.pack('<2f', 1.0, 1.0))
stat_data = stat.getvalue()

stat_rec = io.BytesIO()
stat_rec.write(b'STAT')
stat_rec.write(struct.pack('<I', len(stat_data)))
stat_rec.write(struct.pack('<I', 0))  # flags
stat_rec.write(struct.pack('<I', STAT_FID))
stat_rec.write(struct.pack('<HH', 0, 0x240))
stat_rec.write(stat_data)

# --- REFR record ---
refr = io.BytesIO()
wsub(refr, 'NAME', struct.pack('<I', STAT_FID))
wsub(refr, 'DATA', struct.pack('<6f', POS_X, POS_Y, POS_Z, 0, 0, 0))
refr_data = refr.getvalue()

refr_rec = io.BytesIO()
refr_rec.write(b'REFR')
refr_rec.write(struct.pack('<I', len(refr_data)))
refr_rec.write(struct.pack('<I', 0))
refr_rec.write(struct.pack('<I', REFR_FID))
refr_rec.write(struct.pack('<HH', 0, 0x240))
refr_rec.write(refr_data)

# --- CELL record (exterior) ---
cell = io.BytesIO()
wsub(cell, 'EDID', b'Surface\x00')
wsub(cell, 'DATA', struct.pack('<I', 0x202))
wsub(cell, 'XCLC', struct.pack('<iiI', -1, -1, 0))
wsub(cell, 'LTMP', struct.pack('<I', 0))
wsub(cell, 'XCLW', struct.pack('<f', 3.4028234663852886e+38))
wsub(cell, 'XILS', struct.pack('<f', 1.0))
cell_data = cell.getvalue()

cell_rec = io.BytesIO()
cell_rec.write(b'CELL')
cell_rec.write(struct.pack('<I', len(cell_data)))
cell_rec.write(struct.pack('<I', 0))
cell_rec.write(struct.pack('<I', CELL_FID))
cell_rec.write(struct.pack('<HH', 0, 0x240))
cell_rec.write(cell_data)

# --- Persistent CELL (compressed) ---
persist = io.BytesIO()
wsub(persist, 'EDID', b'Persistent\x00')
wsub(persist, 'DATA', struct.pack('<I', 0x202))
persist_inner = persist.getvalue()
persist_compressed = zlib.compress(persist_inner)
persist_payload = struct.pack('<I', len(persist_inner)) + persist_compressed

persist_rec = io.BytesIO()
persist_rec.write(b'CELL')
persist_rec.write(struct.pack('<I', len(persist_payload)))
persist_rec.write(struct.pack('<I', 0x40000))  # compressed
persist_rec.write(struct.pack('<I', PERSIST_CELL_FID))
persist_rec.write(struct.pack('<HH', 0, 0x240))
persist_rec.write(persist_payload)

# --- WRLD record ---
wrld = io.BytesIO()
wsub(wrld, 'EDID', b'Morrowind\x00')
wsub(wrld, 'DNAM', struct.pack('<2f', 200.0, 160.0))
wrld_data = wrld.getvalue()

wrld_rec = io.BytesIO()
wrld_rec.write(b'WRLD')
wrld_rec.write(struct.pack('<I', len(wrld_data)))
wrld_rec.write(struct.pack('<I', 0x4))  # override
wrld_rec.write(struct.pack('<I', WRLD_FID))
wrld_rec.write(struct.pack('<HH', 0, 0x240))
wrld_rec.write(wrld_data)

# --- Build GRUP hierarchy ---
temp_refs = make_grup(struct.pack('<I', CELL_FID), 9, refr_rec.getvalue())
cell_children = make_grup(struct.pack('<I', CELL_FID), 6, temp_refs)
subblock = make_grup(struct.pack('<hh', -1, -1), 5, cell_rec.getvalue() + cell_children)
block = make_grup(struct.pack('<hh', -1, -1), 4, subblock)

persist_empty = make_grup(struct.pack('<I', PERSIST_CELL_FID), 8, b'')
persist_children = make_grup(struct.pack('<I', PERSIST_CELL_FID), 6, persist_empty)
wrld_children = make_grup(struct.pack('<I', WRLD_FID), 1,
    persist_rec.getvalue() + persist_children + block)

# --- Write file ---
stat_top = make_grup(b'STAT', 0, stat_rec.getvalue())
wrld_top = make_grup(b'WRLD', 0, wrld_rec.getvalue() + wrld_children)

with open(OUTPUT, 'wb') as f:
    f.write(out.getvalue())
    f.write(stat_top)
    f.write(wrld_top)

print(f'Minimal test ESP: {OUTPUT} ({os.path.getsize(OUTPUT)} bytes)')
print(f'STAT: clutter\\box01.nif')
print(f'REFR: ({POS_X}, {POS_Y}, {POS_Z})')
