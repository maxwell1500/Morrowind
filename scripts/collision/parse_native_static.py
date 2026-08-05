"""Parse native static NIF's bhkPhysicsSystem in detail.
Study Starborn_BuiltInKitchenette01.nif to understand the compressed mesh shape format.
"""
import struct, sys, os
sys.path.insert(0, r'C:\Users\max\Projects\Morrowind\scripts\collision')
import hk_decode_lib as lib

NIF_PATH = r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif'

def le32(buf, off): return struct.unpack_from('<I', buf, off)[0]
def le16(buf, off): return struct.unpack_from('<H', buf, off)[0]

with open(NIF_PATH, 'rb') as f:
    data = f.read()

# Parse NIF header
p = 0
assert data[:38] == b'Gamebryo File Format, Version 20.2.0.7'
p += 38 + 5 + 1 + 4
num_blocks = le32(data, p); p += 4
p += 4  # bs_version
aL = data[p]; p += 1 + aL; p += 4
psL = data[p]; p += 1 + psL
u2L = data[p]; p += 1 + u2L
num_types = le16(data, p); p += 2
blk_types = []
for _ in range(num_types):
    L = le32(data, p); p += 4
    blk_types.append(data[p:p+L].decode('latin-1')); p += L
blk_ti = [le16(data, p + i*2) for i in range(num_blocks)]; p += num_blocks * 2
blk_sizes = [le32(data, p + i*4) for i in range(num_blocks)]; p += num_blocks * 4
p += 4; p += 4
for _ in range(le32(data, p-8)):
    L = le32(data, p); p += 4 + L
p += 4
header_end = p

print(f'NIF: {os.path.basename(NIF_PATH)}')
print(f'Blocks: {num_blocks}')
for i in range(num_blocks):
    print(f'  [{i}] {blk_types[blk_ti[i]]} ({blk_sizes[i]}B)')

# Find bhkPhysicsSystem
phys_idx = next(i for i in range(num_blocks) if blk_types[blk_ti[i]] == 'bhkPhysicsSystem')
blk_off = header_end + sum(blk_sizes[:phys_idx])
data_len = le32(data, blk_off)
tag0_start = blk_off + 4

print(f'\nbhkPhysicsSystem: block [{phys_idx}] at 0x{blk_off:x}, data_len={data_len}')

# Walk TAG0
chunks = lib.walk_tag0(data, tag0_start, tag0_start + data_len)
by_fcc = {}
def idx(c):
    by_fcc.setdefault(c.fourcc, []).append(c)
    for ch in c.children: idx(ch)
for c in chunks: idx(c)

# Show chunk tree
def show(c, depth=0):
    pref = '  ' * depth
    print(f'{pref}{c.fourcc.decode()} @0x{c.abs_off:x} size={c.size}')
    for ch in c.children:
        show(ch, depth+1)
for c in chunks:
    show(c)

# Parse TYPE class table
type_chunk = by_fcc[b'TYPE'][0]
tst1 = [c for c in by_fcc.get(b'TST1', []) if c.parent == type_chunk][0]
fst1 = [c for c in by_fcc.get(b'FST1', []) if c.parent == type_chunk]
tna1 = [c for c in by_fcc.get(b'TNA1', []) if c.parent == type_chunk][0]
tbdy = [c for c in by_fcc.get(b'TBDY', []) if c.parent == type_chunk]

type_names = lib.parse_tst1(data, tst1.body_off, tst1.body_end)
print(f'\nType names ({len(type_names)}):')
for i, n in enumerate(type_names):
    print(f'  [{i}] {n}')

field_names = []
if fst1:
    field_names = lib.parse_fst1(data, fst1[0].body_off, fst1[0].body_end)
    print(f'\nField names ({len(field_names)}):')
    for i, n in enumerate(field_names):
        print(f'  [{i}] {n}')

classes = lib.parse_tna1(data, tna1.body_off, tna1.body_end, type_names)
print(f'\nClasses ({len(classes)}):')
for i, c in enumerate(classes):
    if c.name:
        print(f'  [{i}] {c.name} parent={c.parent.name if c.parent else None}')

if tbdy:
    lib.parse_tbdy(data, tbdy[0].body_off, tbdy[0].body_end, classes, field_names)
    print(f'\nClass details:')
    for i, c in enumerate(classes):
        if c.name and c.fields:
            print(f'  [{i}] {c.name}:')
            for f in c.fields:
                print(f'      {f["name"]} offset={f["offset"]} type={f["type"].name if f["type"] else None}')

# Parse items
item_c = by_fcc[b'ITEM'][0]
items = lib.parse_item(data, item_c.body_off, item_c.body_end)
print(f'\nItems ({len(items)}):')
for it in items:
    cn = classes[it['type_idx']].name if it['type_idx'] < len(classes) else '???'
    print(f"  [{it['i']}] {cn} type_idx={it['type_idx']} data_off=0x{it['data_off']:x} count={it['count']} flags={it['flags']}")

# Parse patches
ptch_c = by_fcc[b'PTCH'][0]
patches = lib.parse_ptch(data, ptch_c.body_off, ptch_c.body_end)
print(f'\nPatches ({len(patches)}):')
for p in patches:
    print(f'  type_idx={p["type_idx"]} offsets={[hex(o) for o in p["offsets"]]}')

# Show DATA chunk size
data_c = by_fcc[b'DATA'][0]
print(f'\nDATA chunk: body_size={data_c.size - 8}')

# Dump first 256 bytes of DATA body
data_body = data[data_c.body_off : data_c.body_off + min(256, data_c.size - 8)]
print(f'DATA first 256 bytes hex:')
for i in range(0, len(data_body), 16):
    hex_str = ' '.join(f'{b:02x}' for b in data_body[i:i+16])
    print(f'  {i:04x}: {hex_str}')

# Show BSXFlags value
bsx_idx = next(i for i in range(num_blocks) if blk_types[blk_ti[i]] == 'BSXFlags')
bsx_off = header_end + sum(blk_sizes[:bsx_idx])
bsx_val = le32(data, bsx_off + 4)  # skip 4-byte ref, read flags
print(f'\nBSXFlags: 0x{bsx_val:08x}')

# Show bhkNPCollisionObject
bhknp_idx = next(i for i in range(num_blocks) if blk_types[blk_ti[i]] == 'bhkNPCollisionObject')
bhknp_off = header_end + sum(blk_sizes[:bhknp_idx])
bhknp_data = data[bhknp_off : bhknp_off + blk_sizes[bhknp_idx]]
print(f'bhkNPCollisionObject ({blk_sizes[bhknp_idx]}B): {bhknp_data.hex()}')