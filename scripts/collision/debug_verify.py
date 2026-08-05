"""Verify reshaped NIF: parse and show items, check counts."""
import struct, os, sys
sys.path.insert(0, r'C:\Users\max\Projects\Morrowind\scripts\collision')
import hk_decode_lib as lib

nif_path = r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_de_docks_center.nif'
with open(nif_path, 'rb') as f:
    data = f.read()

def le32(buf, off): return struct.unpack_from('<I', buf, off)[0]
def le16(buf, off): return struct.unpack_from('<H', buf, off)[0]

# Parse NIF header
p = 0
assert data[:38] == b'Gamebryo File Format, Version 20.2.0.7'
p += 38 + 5 + 1 + 4
num_blocks = le32(data, p); p+=4
p += 4  # bs_version
aL = data[p]; p+=1+aL; p+=4
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

print(f'Blocks: {num_blocks}')
for i in range(num_blocks):
    sz_diff = blk_sizes[i] - (blk_sizes[i] if i == 0 else 0)
    print(f'  [{i}] {blk_types[blk_ti[i]]} ({blk_sizes[i]}B)')

# Find physics
phys_idx = next(i for i in range(num_blocks) if blk_types[blk_ti[i]]=='bhkPhysicsSystem')
blk_off = header_end + sum(blk_sizes[:phys_idx])
data_len = le32(data, blk_off)
tag0_start = blk_off + 4

chunks = lib.walk_tag0(data, tag0_start, tag0_start + data_len)
by_fcc = {}
def idx(c):
    by_fcc.setdefault(c.fourcc, []).append(c)
    for ch in c.children: idx(ch)
for c in chunks: idx(c)

item_c = by_fcc[b'ITEM'][0]
items = lib.parse_item(data, item_c.body_off, item_c.body_end)

# Get type names from TST1
type_chunk = by_fcc[b'TYPE'][0]
tst1 = [c for c in by_fcc.get(b'TST1', []) if c.parent == type_chunk][0]
type_names = lib.parse_tst1(data, tst1.body_off, tst1.body_end)

# Get TNA1 for class mapping
tna1 = [c for c in by_fcc.get(b'TNA1', []) if c.parent == type_chunk][0]
classes = lib.parse_tna1(data, tna1.body_off, tna1.body_end, type_names)

print(f'\nItems ({len(items)}):')
for it in items:
    cn = classes[it['type_idx']].name if it['type_idx'] < len(classes) else '???'
    print(f"  [{it['i']}] {cn} type_idx={it['type_idx']} data_off=0x{it['data_off']:x} count={it['count']}")

# Verify: convex hull items should have correct counts
print(f'\n=== Polytope check ===')
# Item 6 = vertices
# Item 7 = planes
# Item 8 = faces
# Item 9 = indices
# Item 10 = faceLinks
# Item 11 = vertexEdges
it6 = next(it for it in items if it['i']==6)
it7 = next(it for it in items if it['i']==7)
it8 = next(it for it in items if it['i']==8)
it9 = next(it for it in items if it['i']==9)
it10 = next(it for it in items if it['i']==10)
it11 = next(it for it in items if it['i']==11)

print(f'  vertices:    {it6["count"]}')
print(f'  planes:      {it7["count"]}')
print(f'  faces:       {it8["count"]}')
print(f'  indices:     {it9["count"]}')
print(f'  faceLinks:   {it10["count"]}')
print(f'  vertexEdges: {it11["count"]}')

# Compute DATA body size
data_c = by_fcc[b'DATA'][0]
data_body = data[data_c.body_off : data_c.body_end]
print(f'\nDATA body size: {len(data_body)}')

# Check TAG0 size (should match block size - 4)
tag0_chunk = by_fcc[b'TAG0'][0]
print(f'TAG0 chunk size: {tag0_chunk.size}')
print(f'Block size: {blk_sizes[phys_idx]}')
print(f'Expected consistency: 4 + {tag0_chunk.size} = {4+tag0_chunk.size}')
print(f'Match: {blk_sizes[phys_idx] == 4 + tag0_chunk.size}')

# Simple validation: check block sizes add up
total_block_data = sum(blk_sizes)
file_size = len(data)
print(f'\nTotal block data: {total_block_data}')
print(f'Header end: {header_end}')
print(f'Footer: {file_size - header_end - total_block_data} bytes')
