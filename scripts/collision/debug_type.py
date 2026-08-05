import struct, sys
sys.path.insert(0, r'C:\Users\max\Projects\Morrowind\scripts\collision')
import hk_decode_lib as lib

nif_path = r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_de_docks_center.nif'
with open(nif_path, 'rb') as f:
    data = f.read()

def le32(buf, off): return struct.unpack_from('<I', buf, off)[0]
def le16(buf, off): return struct.unpack_from('<H', buf, off)[0]

p = 0
assert data[:38] == b'Gamebryo File Format, Version 20.2.0.7'
p += 38 + 5 + 1 + 4
num_blocks = le32(data, p); p+=4
p += 4
aL = data[p]; p+=1+aL
p+=4
psL=data[p]; p+=1+psL
u2L=data[p]; p+=1+u2L
num_types=le16(data,p); p+=2
blk_types=[]
for _ in range(num_types):
    L=le32(data,p); p+=4
    blk_types.append(data[p:p+L].decode('latin-1')); p+=L
blk_ti=[le16(data,p+i*2) for i in range(num_blocks)]; p+=num_blocks*2
blk_sizes=[le32(data,p+i*4) for i in range(num_blocks)]; p+=num_blocks*4
p+=4; p+=4
for _ in range(le32(data,p-8)):
    L=le32(data,p); p+=4+L
p+=4
header_end=p

phys_idx = next(i for i in range(num_blocks) if blk_types[blk_ti[i]]=='bhkPhysicsSystem')
blk_off = header_end + sum(blk_sizes[:phys_idx])
data_len = le32(data, blk_off)
tag0_start = blk_off + 4

chunks = lib.walk_tag0(data, tag0_start, tag0_start + data_len)

# Index chunks
chunks_by_fcc = {}
def idx(c):
    chunks_by_fcc.setdefault(c.fourcc, []).append(c)
    for ch in c.children: idx(ch)
for c in chunks: idx(c)

# Parse TYPE TNA1 / TST1 / TBDY to get class names
type_chunk = chunks_by_fcc[b'TYPE'][0]
tna1_chunks = [c for c in chunks_by_fcc.get(b'TNA1', []) if c.parent == type_chunk]
tst1_chunks = [c for c in chunks_by_fcc.get(b'TST1', []) if c.parent == type_chunk]
fst1_chunks = [c for c in chunks_by_fcc.get(b'FST1', []) if c.parent == type_chunk]
tbdy_chunks = [c for c in chunks_by_fcc.get(b'TBDY', []) if c.parent == type_chunk]

# TST1: type name strings
type_names = lib.parse_tst1(data, tst1_chunks[0].body_off, tst1_chunks[0].body_end)
print(f'Type names ({len(type_names)}):')
for i, n in enumerate(type_names):
    print(f'  [{i}] {n}')

# FST1: field name strings (if present)
if fst1_chunks:
    field_names = lib.parse_fst1(data, fst1_chunks[0].body_off, fst1_chunks[0].body_end)
    print(f'\nField names ({len(field_names)}):')
    for i, n in enumerate(field_names):
        print(f'  [{i}] {n}')
else:
    field_names = []

# TNA1: type name assignments (maps item type_idx to class)
tna1 = tna1_chunks[0]
classes = lib.parse_tna1(data, tna1.body_off, tna1.body_end, type_names)
print(f'\nClasses ({len(classes)}):')
for i, c in enumerate(classes):
    if c.name:
        print(f'  [{i}] {c.name} (size={c.size}) parent={c.parent.name if c.parent else None}')

# TBDY: type body definitions
if tbdy_chunks:
    lib.parse_tbdy(data, tbdy_chunks[0].body_off, tbdy_chunks[0].body_end, classes, field_names)

# Now print items with their class names
item_c = chunks_by_fcc[b'ITEM'][0]
items = lib.parse_item(data, item_c.body_off, item_c.body_end)
print(f'\nItems ({len(items)}):')
for it in items:
    cn = classes[it['type_idx']].name if it['type_idx'] < len(classes) else '???'
    print(f"  [{it['i']}] {cn} (type_idx={it['type_idx']}) data_off=0x{it['data_off']:x} count={it['count']}")

# Print first 80 bytes of DATA body
data_chunk = chunks_by_fcc[b'DATA'][0]
data_body = data[data_chunk.body_off : data_chunk.body_end]
print(f'\nDATA body size: {len(data_body)}')
print(f'First 64 bytes hex: {data_body[:64].hex()}')
print(f'Bytes 608-704 hex: {data_body[608:704].hex()}')
