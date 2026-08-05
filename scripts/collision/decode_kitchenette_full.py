"""Decode the kitchenette's hknpCompressedMeshShape tree in full detail.

We need to understand:
1. Section header (item 11 @0x360, 96B) — what each field means
2. Primitives (item 12 @0x3c0, 18 triangles × 8B) — vertex index encoding
3. Packed vertices — where are they stored? The Section references "packedVertices"
   but the items list doesn't have an explicit "vertices" item. They must be
   embedded in one of the other items.
4. SimdTree (item 17, 8 nodes × 128B) — AABB tree structure
5. Aabb4BytesCodec (item 18, 35 nodes × 6B) — compressed AABB tree

The key question: which item holds the packed vertex coordinates?
"""
import struct, sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib

NIF = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif"

with open(NIF, "rb") as f:
    data = f.read()

p = 38+5+1+4
nb = struct.unpack_from('<I', data, p)[0]; p += 4+4
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
ns = struct.unpack_from('<I', data, p)[0]; p += 4+4
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

db_off = data_c.body_off
db_size = data_c.size - 8

def u32(o): return struct.unpack_from('<I', data, db_off+o)[0]
def u16(o): return struct.unpack_from('<H', data, db_off+o)[0]
def f32(o): return struct.unpack_from('<f', data, db_off+o)[0]

# ============================================================================
# SECTION (item 11 @0x360, 96 bytes) — hkcdStaticMeshTree::Section
# Class layout from TBDY:
#   codecParms: offset 48, T[N] (16 bytes)
#   firstPackedVertexIndex: offset 72, hkUint32
#   firstSharedVertexIndex: offset 76, hkUint32
#   firstPrimitiveIndex: offset 80, hkUint32
#   firstDataRunIndex: offset 84, hkUint32
#   numPackedVertices: offset 88, hkUint8
#   numPrimitives: offset 89, hkUint8
#   numDataRuns: offset 90, hkUint8
#   page: offset 91, hkUint8
#   leafIndex: offset 92, hkUint16
#   layerData: offset 94, hkUint8
#   flags: offset 95, hkUint8
print("=== SECTION (item 11 @0x360) ===")
sec_off = 0x360
print(f"  codecParms (48-63): {data[db_off+sec_off+48:db_off+sec_off+64].hex()}")
print(f"  firstPackedVertexIndex (72): {u32(sec_off+72)}")
print(f"  firstSharedVertexIndex (76): {u32(sec_off+76)}")
print(f"  firstPrimitiveIndex (80): {u32(sec_off+80)}")
print(f"  firstDataRunIndex (84): {u32(sec_off+84)}")
print(f"  numPackedVertices (88): {data[db_off+sec_off+88]}")
print(f"  numPrimitives (89): {data[db_off+sec_off+89]}")
print(f"  numDataRuns (90): {data[db_off+sec_off+90]}")
print(f"  page (91): {data[db_off+sec_off+91]}")
print(f"  leafIndex (92): {u16(sec_off+92)}")
print(f"  layerData (94): {data[db_off+sec_off+94]}")
print(f"  flags (95): {data[db_off+sec_off+95]}")
# domain AABB (first 48 bytes of section: min(16) + max(16) + ... actually check layout)
# Section offset 0-47 might be domain or other fields
print(f"  bytes 0-47: {data[db_off+sec_off:db_off+sec_off+48].hex()}")

# ============================================================================
# PRIMITIVES (item 12 @0x3c0, 18 count)
# hkcdStaticMeshTree::Primitive: indices[0] = T[N] (N=3 for triangles?)
# Each primitive is 8 bytes. 3 indices + 1 padding? Or 4 indices?
print("\n=== PRIMITIVES (item 12 @0x3c0, 18 count) ===")
for i in range(18):
    p_off = 0x3c0 + i*8
    b = data[db_off+p_off:db_off+p_off+8]
    # Try as 4 uint8 indices + 4 uint8 indices, or 3 uint16 + padding
    u8s = list(b)
    print(f"  [{i:2d}] {b.hex()}  u8={u8s}")

# ============================================================================
# Find PACKED VERTICES
# Section says numPackedVertices=18, firstPackedVertexIndex=0
# The packedVertices array is an hkArray in hkcdDefaultStaticMeshTree at offset 112
# hkcdDefaultStaticMeshTree is item 6 (hknpCompressedMeshShapeData) base?
# Actually hknpCompressedMeshShapeData.meshTree is at +32, which contains the
# packedVertices array.
# Let me check item 6 structure.

print("\n=== CompressedMeshShapeData (item 6 @0x240) ===")
# meshTree at +32, simdTree at +192, connectivity at +216, hasSimdTree at +264
# meshTree is hknpCompressedMeshShapeTree which extends hkcdDefaultStaticMeshTree
# hkcdDefaultStaticMeshTree fields:
#   packedVertices: offset 112, hkArray
#   sharedVertices: offset 128, hkArray
#   primitiveDataRuns: offset 144, hkArray
# So within meshTree (starting at 0x240+32=0x260):
#   packedVertices at 0x260+112 = 0x2d0
#   sharedVertices at 0x260+128 = 0x2e0
#   primitiveDataRuns at 0x260+144 = 0x2f0
print(f"  meshTree starts at 0x260")
print(f"  packedVertices (hkArray at 0x2d0): m_data={u32(0x2d0)}, m_size={struct.unpack_from('<i',data,db_off+0x2d8)[0]}, m_cap={u32(0x2dc)}")
print(f"  sharedVertices (hkArray at 0x2e0): m_data={u32(0x2e0)}, m_size={struct.unpack_from('<i',data,db_off+0x2e8)[0]}, m_cap={u32(0x2ec)}")
print(f"  primitiveDataRuns (hkArray at 0x2f0): m_data={u32(0x2f0)}, m_size={struct.unpack_from('<i',data,db_off+0x2f8)[0]}, m_cap={u32(0x2fc)}")

# The m_data fields are ITEM INDICES (not byte offsets). Let me check:
# packedVertices.m_data = item index of the vertex array
pv_data = u32(0x2d0)
pv_size = struct.unpack_from('<i', data, db_off+0x2d8)[0]
print(f"\n  packedVertices m_data={pv_data}, m_size={pv_size}")
# This is an item index. Item with i==? Let me check items
for it in items:
    if it['i'] == pv_data:
        print(f"    -> item [{it['i']}] type_idx={it['type_idx']} data_off=0x{it['data_off']:x} count={it['count']}")
        # Dump first few entries
        for j in range(min(it['count'], 4)):
            eo = db_off + it['data_off'] + j * 8  # Aabb5BytesCodec is 8 bytes?
            print(f"      [{j}] {data[eo:eo+8].hex()}")
        break

# ============================================================================
# Aabb5BytesCodec (item 10 @0x350, 1 count, 8 bytes)
print("\n=== Aabb5BytesCodec (item 10 @0x350) ===")
aabb5 = data[db_off+0x350:db_off+0x350+8]
print(f"  bytes: {aabb5.hex()}")
# Layout: hiData(3) + loData(4)? offset 3 and 4
# Actually field "hiData" at offset 3, "loData" at offset 4
# This is the ROOT domain of the tree probably

# ============================================================================
# SimdTree Nodes (item 17 @0x4a0, 8 nodes × 128B)
print("\n=== SimdTree (item 17 @0x4a0, 8 nodes) ===")
# hkcdSimdTree::Node: data(96B) + isLeaf(1B) + isActive(1B)
# data is T[N] = 4 × hkAabb (4×24B=96B)? Or 4 × hkVector4f min + 4 × hkVector4f max
for i in range(8):
    n_off = 0x4a0 + i*128
    nd = data[db_off+n_off:db_off+n_off+128]
    is_leaf = nd[112]
    is_active = nd[113]
    # data: 4 children, each AABB = min(16B vec4) + max(16B vec4) = 32B? 4*24=96
    # Actually 4 AABBs × 24 bytes = 96. But hkAabb is min(16)+max(16)=32. 4*32=128 != 96.
    # Maybe compressed: each child is 3 floats min + 3 floats max = 24 bytes
    # 4 × 24 = 96. Let me parse as 4 × (3 floats min, 3 floats max, pad 8B)
    children = []
    for c in range(4):
        co = c * 24
        mn = struct.unpack_from('<fff', nd, co)
        mx = struct.unpack_from('<fff', nd, co+12)
        children.append((mn, mx))
    print(f"  [{i}] leaf={is_leaf} active={is_active}")
    for c in range(4):
        mn, mx = children[c]
        if mn != (0,0,0) or mx != (0,0,0):
            print(f"    child[{c}] min=({mn[0]:.3f},{mn[1]:.3f},{mn[2]:.3f}) max=({mx[0]:.3f},{mx[1]:.3f},{mx[2]:.3f})")
    if is_leaf:
        # leaf nodes have primitive indices in bytes 96-111?
        print(f"    leaf data: {nd[96:128].hex()}")

# ============================================================================
# Aabb4BytesCodec (item 18 @0x8a0, 35 nodes × 6B)
print("\n=== Aabb4BytesCodec (item 18 @0x8a0, 35 nodes) ===")
# hkcdCompressedAabbCodecs::Aabb4BytesCodec: data at offset 3, 6 bytes total
# Each node is 6 bytes: 3 bytes min + 3 bytes max? Or 4 bytes + 2 bytes?
for i in range(min(10, 35)):
    n_off = 0x8a0 + i*6
    nd = data[db_off+n_off:db_off+n_off+6]
    print(f"  [{i:2d}] {nd.hex()}")
print(f"  ... ({35-10} more)")

# ============================================================================
# hknpBSMaterial (item 19 @0x960) and hknpBSMaterialProperties (item 9 @0x930)
print("\n=== hknpBSMaterialProperties (item 9 @0x930) ===")
print(f"  32 bytes: {data[db_off+0x930:db_off+0x930+32].hex()}")
print(f"\n=== hknpBSMaterial (item 19 @0x960) ===")
print(f"  32 bytes: {data[db_off+0x960:db_off+0x960+32].hex()}")