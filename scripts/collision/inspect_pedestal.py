"""Inspect the Starborn_ShipModelPedestal01.nif bhkPhysicsSystem in detail."""
import struct, sys
sys.path.insert(0, 'scripts/collision')
import hk_decode_lib as lib

path = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_ShipModelPedestal01.nif"
with open(path, 'rb') as f: d = f.read()

p = 38+5+1+4
nb = struct.unpack_from('<I', d, p)[0]; p += 4+4
aL = d[p]; p += 1+aL+4
psL = d[p]; p += 1+psL
u2L = d[p]; p += 1+u2L
nt = struct.unpack_from('<H', d, p)[0]; p += 2
types = []
for _ in range(nt):
    L = struct.unpack_from('<I', d, p)[0]; p += 4
    types.append(d[p:p+L].decode('latin-1')); p += L
ti_off = p; p += nb*2
sizes = [struct.unpack_from('<I', d, p+i*4)[0] for i in range(nb)]; p += nb*4
ns = struct.unpack_from('<I', d, p)[0]; p += 4+4
for _ in range(ns):
    L = struct.unpack_from('<I', d, p)[0]; p += 4+L
p += 4; he = p

phys_idx = next(i for i in range(nb) if types[struct.unpack_from('<H', d, ti_off+i*2)[0]] == 'bhkPhysicsSystem')
blk_off = he + sum(sizes[:phys_idx])
dlen = struct.unpack_from('<I', d, blk_off)[0]
chunks = lib.walk_tag0(d, blk_off+4, blk_off+4+dlen)
by = {}
def idx(c):
    by.setdefault(c.fourcc, []).append(c)
    for ch in c.children: idx(ch)
for c in chunks: idx(c)

dc = by[b'DATA'][0]
db = dc.body_off
items = lib.parse_item(d, by[b'ITEM'][0].body_off, by[b'ITEM'][0].body_end)

print('Items:')
for it in items:
    tname = types[it['type_idx']] if it['type_idx'] < len(types) else f'type{it["type_idx"]}'
    print(f"  [{it['i']:2d}] {tname} (idx={it['type_idx']}) off=0x{it['data_off']:x} count={it['count']} flags={it['flags']}")

# Decode shape item 5
shape = db + items[5]['data_off']
print(f"\nShape (item 5) at DATA+0x{items[5]['data_off']:x}:")
print('  type byte:', d[shape+26])
print('  dispatch:', d[shape+28])
print('  convexRadius:', struct.unpack_from('<f', d, shape+32)[0])
print('  properties ref:', struct.unpack_from('<Q', d, shape+48)[0])
print('  hull relarrays at +60:', d[shape+60:shape+108].hex())

# Decode hull data
def decode_rel(off):
    rel = struct.unpack_from('<i', d, off)[0]
    sz = struct.unpack_from('<i', d, off+4)[0]
    return rel, sz

hull = shape + 60
verts_rel, verts_sz = decode_rel(hull+0)
planes_rel, planes_sz = decode_rel(hull+8)
faces_rel, faces_sz = decode_rel(hull+16)
indices_rel, indices_sz = decode_rel(hull+24)
faceLinks_rel, faceLinks_sz = decode_rel(hull+32)
vertexEdges_rel, vertexEdges_sz = decode_rel(hull+40)

print(f"\nHull relarrays:")
print(f"  vertices rel={verts_rel} sz={verts_sz}")
print(f"  planes rel={planes_rel} sz={planes_sz}")
print(f"  faces rel={faces_rel} sz={faces_sz}")
print(f"  indices rel={indices_rel} sz={indices_sz}")
print(f"  faceLinks rel={faceLinks_rel} sz={faceLinks_sz}")
print(f"  vertexEdges rel={vertexEdges_rel} sz={vertexEdges_sz}")

print('\nFirst 8 vertices (item 8):')
verts_abs = db + items[8]['data_off']
for i in range(min(8, items[8]['count'])):
    print('  ', [round(x,4) for x in struct.unpack_from('<fff', d, verts_abs+i*12)])

print('\nFirst 6 planes (item 9):')
planes_abs = db + items[9]['data_off']
for i in range(min(6, items[9]['count'])):
    print('  ', [round(x,4) for x in struct.unpack_from('<ffff', d, planes_abs+i*16)])

print('\nFaces (item 10):')
faces_abs = db + items[10]['data_off']
for i in range(items[10]['count']):
    b = d[faces_abs+i*4:faces_abs+i*4+4]
    first, num, ma = struct.unpack_from('<HBB', b, 0)
    print(f"  [{i}] first={first} num={num} minHalfAngle={ma}")

print('\nIndices (item 11):', list(d[db+items[11]['data_off']:db+items[11]['data_off']+items[11]['count']*1]))
print('\nVertexEdges (item 13):', list(d[db+items[13]['data_off']:db+items[13]['data_off']+items[13]['count']*2]))

# TST1 classes
print('\nTST1 shape-related strings:')
tst = lib.parse_tst1(d, by[b'TST1'][0].body_off, by[b'TST1'][0].body_end)
for i, s in enumerate(tst):
    if 'Shape' in s or 'Convex' in s or 'Hull' in s or 'Material' in s:
        print(i, s)

# PTCH
print('\nPatches:')
patches = lib.parse_ptch(d, by[b'PTCH'][0].body_off, by[b'PTCH'][0].body_end)
for pt in patches:
    tname = types[pt['type_idx']] if pt['type_idx'] < len(types) else f'type{pt["type_idx"]}'
    print(f"  type={tname} ({pt['type_idx']}) offsets={pt['offsets']}")
