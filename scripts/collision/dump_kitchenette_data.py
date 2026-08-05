"""Deep-dump of kitchenette bhkPhysicsSystem DATA + items/patches.
We need to understand:
  - DATA body byte layout (system metadata + bodyCinfo + shape + mesh tree + simd tree + materials)
  - How ITEM indices map into DATA offsets
  - The PTCH pattern (which item offsets get patched)
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib

NIF = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif"

with open(NIF, "rb") as f:
    data = f.read()

# header
p = 38+5+1+4
nb = struct.unpack_from('<I', data, p)[0]; p += 4
p += 4
aL = data[p]; p += 1+aL+4
psL = data[p]; p += 1+psL
u2L = data[p]; p += 1+u2L
nt = struct.unpack_from('<H', data, p)[0]; p += 2
types = []
for _ in range(nt):
    L = struct.unpack_from('<I', data, p)[0]; p += 4
    types.append(data[p:p+L].decode("latin-1")); p += L
ti = [struct.unpack_from('<H', data, p+i*2)[0] for i in range(nb)]; p += nb*2
sizes = [struct.unpack_from('<I', data, p+i*4)[0] for i in range(nb)]; p += nb*4
ns = struct.unpack_from('<I', data, p)[0]; p += 4
p += 4
for _ in range(ns):
    L = struct.unpack_from('<I', data, p)[0]; p += 4+L
p += 4
he = p

phys_idx = next(i for i in range(nb) if types[ti[i]] == "bhkPhysicsSystem")
blk_off = he + sum(sizes[:phys_idx])
dlen = struct.unpack_from('<I', data, blk_off)[0]
tag0 = blk_off + 4

chunks = lib.walk_tag0(data, tag0, tag0+dlen)
by_fcc = {}
def idx(c):
    by_fcc.setdefault(c.fourcc, []).append(c)
    for ch in c.children: idx(ch)
for c in chunks: idx(c)

data_c = by_fcc[b"DATA"][0]
items = lib.parse_item(data, by_fcc[b"ITEM"][0].body_off, by_fcc[b"ITEM"][0].body_end)
patches = lib.parse_ptch(data, by_fcc[b"PTCH"][0].body_off, by_fcc[b"PTCH"][0].body_end)

print(f"DATA body: off=0x{data_c.body_off:x} size={data_c.size-8}")
print(f"\nItems ({len(items)}):")
for it in items:
    print(f"  [{it['i']}] type_idx={it['type_idx']} data_off=0x{it['data_off']:x} count={it['count']} flags={it['flags']}")

print(f"\nPatches ({len(patches)}):")
for pch in patches:
    print(f"  type_idx={pch['type_idx']} offsets={[hex(o) for o in pch['offsets']]}")

# Dump DATA hex with item boundaries marked
db_off = data_c.body_off
db_size = data_c.size - 8
print(f"\nFull DATA hex dump ({db_size}B):")
# Mark item ranges
item_ranges = []
for it in items:
    if it['count'] == 0:
        continue
    item_ranges.append((it['data_off'], it['data_off'] + 0, it['i']))  # just offset
# Print 16-byte rows with annotations
for i in range(0, db_size, 16):
    row = data[db_off+i:db_off+i+16]
    if not row:
        break
    hexs = ' '.join(f'{b:02x}' for b in row)
    # find item whose data_off == i
    mark = ""
    for it in items:
        if it['count'] > 0 and it['data_off'] == i:
            mark = f"  <- item[{it['i']}]"
            break
    print(f"  {i:04x}: {hexs}{mark}")

# Now interpret specific known offsets based on class layout
print("\n=== Interpretation ===")
# Item 0: hknpPhysicsSystemData (size 0x70? at 0x0)
# Item 1: bodyCinfo at 0xc0
# Item 2: hknpMaterial at 0x70
# Item 3: bodyCinfo at 0xc0
# Item 4: hknpCompressedMeshShape at 0x180
# etc.

# Just dump known scalar fields
def u32(o): return struct.unpack_from('<I', data, db_off+o)[0]
def f32(o): return struct.unpack_from('<f', data, db_off+o)[0]

print(f"\nbodyCinfo (item 3 @0xc0):")
print(f"  shape ref (offset 0xc0): {u32(0xc0)}")  # hkRefPtr -> item idx?
print(f"  flags (0xc8): {u32(0xc8)}")
print(f"  motionType (0xe8): {data[db_off+0xe8]}")
print(f"  position (0xf0): ({f32(0xf0)}, {f32(0xf4)}, {f32(0xf8)})")

print(f"\nhknpCompressedMeshShape (item 4 @0x180):")
print(f"  shape.type (offset 0x180+26): {data[db_off+0x180+26]}")
print(f"  shape.dispatchType (0x180+28): {data[db_off+0x180+28]}")
print(f"  shape.numShapeKeyBits (0x180+27): {data[db_off+0x180+27]}")
print(f"  data ref (0x180+64=0x1c0): {u32(0x1c0)}")  # hkRefPtr to item 6 (meshShapeData)
print(f"  numTriangles (0x180+96=0x1e0): {u32(0x1e0)}")
print(f"  numConvexShapes (0x180+100=0x1e4): {u32(0x1e4)}")

print(f"\nhknpCompressedMeshShapeData (item 6 @0x240):")
print(f"  meshTree starts at 0x240+32=0x260")
print(f"  simdTree starts at 0x240+192=0x300")
print(f"  connectivity starts at 0x240+216=0x318")
print(f"  hasSimdTree (0x240+264=0x348): {data[db_off+0x348]}")

# Aabb5BytesCodec at item 10 @0x350
print(f"\nAabb5BytesCodec (item 10 @0x350): {data[db_off+0x350:db_off+0x350+8].hex()}")

# Section at item 11 @0x360 (size 96 bytes, hkcdStaticMeshTree::Section)
print(f"\nSection (item 11 @0x360), 96 bytes:")
sec = data[db_off+0x360:db_off+0x360+96]
for i in range(0, 96, 16):
    print(f"  {i:04x}: {' '.join(f'{b:02x}' for b in sec[i:i+16])}")

# Primitives at item 12 @0x3c0, count=18 (18 triangles, each 8 bytes = 3 indices + padding)
print(f"\nPrimitives (item 12 @0x3c0), 18 count, each ~8B:")
for i in range(18):
    p_off = 0x3c0 + i*8
    prim = data[db_off+p_off:db_off+p_off+8]
    print(f"  [{i}] {prim.hex()}")

# SimdTree nodes at item 17 @0x4a0, count=8, each 128B
print(f"\nSimdTree Nodes (item 17 @0x4a0), 8 count, 128B each:")
for i in range(8):
    n_off = 0x4a0 + i*128
    nd = data[db_off+n_off:db_off+n_off+128]
    is_leaf = nd[112]
    print(f"  [{i}] isLeaf={is_leaf} first16={nd[:16].hex()}")

# Aabb4BytesCodec at item 18 @0x8a0, count=35 (35 nodes for Aabb4 tree)
print(f"\nAabb4BytesCodec (item 18 @0x8a0), 35 count, 6B each:")
for i in range(min(10, 35)):
    n_off = 0x8a0 + i*6
    nd = data[db_off+n_off:db_off+n_off+6]
    print(f"  [{i}] {nd.hex()}")
print(f"  ... ({35-10} more)")

# hknpBSMaterial at item 19 @0x960
print(f"\nhknpBSMaterial (item 19 @0x960), 1 count, 32B:")
print(f"  {data[db_off+0x960:db_off+0x960+32].hex()}")