"""Decode SimdTree leaf nodes + items 13/15/16 to understand primitive refs.

SimdTree leaf nodes (bytes 96-111) contain primitive indices.
Item 13 (hkUint16 × 6 @0x410) = sharedVerticesIndex
Item 15 (u64 × 6 @0x460) = ??
Item 16 (PrimitiveDataRun × 1 @0x490) = data run for the section

We need to understand how leaf nodes reference primitives and how
shared vertices map to packed vertices.
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib

NIF = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif"
with open(NIF, "rb") as f: data = f.read()

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
chunks = lib.walk_tag0(data, blk_off+4, blk_off+4+dlen)
by_fcc = {}
def idx(c):
    by_fcc.setdefault(c.fourcc, []).append(c)
    for ch in c.children: idx(ch)
for c in chunks: idx(c)
dc = by_fcc[b"DATA"][0]
db = dc.body_off

# SimdTree leaf nodes — decode bytes 96-111 as 4 × uint32 (primitive indices)
print("=== SimdTree leaf nodes (bytes 96-127) ===")
for node_i in range(8):
    n_off = 0x4a0 + node_i * 128
    nd = data[db+n_off:db+n_off+128]
    is_leaf = nd[112]
    if is_leaf:
        # bytes 96-111: 4 uint32 = primitive indices
        prims = struct.unpack_from('<IIII', nd, 96)
        # bytes 112-113: isLeaf, isActive
        # bytes 114-127: ??
        print(f"  node[{node_i}] LEAF prims={prims} active={nd[113]}")
        print(f"    bytes 114-127: {nd[114:128].hex()}")
    else:
        # Internal node: bytes 96-111 = 4 child node indices?
        children = struct.unpack_from('<IIII', nd, 96)
        print(f"  node[{node_i}] INTERNAL children={children}")

# Item 13: hkUint16 × 6 @0x410 — sharedVerticesIndex
print(f"\n=== Item 13 (sharedVerticesIndex, hkUint16 × 6 @0x410) ===")
vals = struct.unpack_from('<HHHHHH', data, db+0x410)
print(f"  values: {vals}")
# These likely map to packed vertex indices (0-13)

# Item 15: unsigned long long × 6 @0x460
print(f"\n=== Item 15 (u64 × 6 @0x460) ===")
for i in range(6):
    v = struct.unpack_from('<Q', data, db+0x460+i*8)[0]
    print(f"  [{i}] 0x{v:016x} = {v}")
    # Try as bitfield: maybe 3 × 20-bit or 3 × 21-bit packed vertex coords?
    # Each u64 might encode a 3D point in some compressed way

# Item 16: PrimitiveDataRun × 1 @0x490
# hkcdDefaultStaticMeshTree::PrimitiveDataRun: value(u16) + index(u8) + count(u8) = 4 bytes
print(f"\n=== Item 16 (PrimitiveDataRun × 1 @0x490) ===")
dr = data[db+0x490:db+0x490+4]
val = struct.unpack_from('<H', dr, 0)[0]
idx_val = dr[2]
count = dr[3]
print(f"  value={val} index={idx_val} count={count}")
# + 4 bytes padding
print(f"  full 8 bytes: {data[db+0x490:db+0x490+8].hex()}")

# Check the Aabb4 tree (item 18) — how does it reference primitives?
print(f"\n=== Aabb4BytesCodec (item 18 @0x8a0, 35 × 6B) ===")
# Each 6-byte node: likely 3 bytes min + 3 bytes max (quantized AABB)
# OR: leaf nodes reference primitives
for i in range(35):
    nd = data[db+0x8a0+i*6 : db+0x8a0+i*6+6]
    print(f"  [{i:2d}] {nd.hex()}")

# Check item 10 (Aabb5BytesCodec × 1 @0x350) — tree domain
print(f"\n=== Item 10 (Aabb5BytesCodec @0x350) ===")
print(f"  {data[db+0x350:db+0x350+8].hex()}")