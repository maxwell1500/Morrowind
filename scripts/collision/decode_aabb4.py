"""The SimdTree leaf nodes reference primitive indices up to 34, but
section numPrimitives=18 and item 12 only has 18 entries.
Find where primitives 18-34 are stored.

Hypothesis: The Aabb4BytesCodec tree (item 18, 35 nodes) is the STATIC mesh
tree's AABB tree, and its leaf nodes reference primitives. The SimdTree
(item 17) is a separate acceleration structure that references into the
Aabb4 tree's primitive array.

Let me decode the Aabb4 tree to find its structure.
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

# The Aabb4BytesCodec (item 18 @0x8a0, 35 × 6B) is for hkcdStaticTree::Aabb4BytesTree
# Each 6-byte node: 3 bytes for min + 3 bytes for max (quantized to tree domain)
# Leaf nodes have a special marker

# The tree domain is in the AabbTreeBase.domain (hkAabb: min(16) + max(16) = 32 bytes)
# hkcdStaticTree::Aabb4BytesTree has: nodes(hkArray) + domain(hkAabb)
# The Aabb4 tree is part of the mesh tree (hkcdDefaultStaticMeshTree sections)

# Let me check: item 10 (Aabb5BytesCodec @0x350, 8B) might be the codec for
# the packedVertices AABB tree (different from the section's primitive tree)

# Actually, the hkcdDefaultStaticMeshTree has:
#   sections (hkArray) — item 11 (Section)
#   primitives (hkArray) — item 12 (the triangle data)
#   sharedVerticesIndex (hkArray) — item 13
# And the hkcdStaticTree::Aabb4BytesTree has its own nodes array.

# The 35 Aabb4 nodes form a tree. Let me decode them.
# Aabb4BytesCodec: 6 bytes per node
# Format: xyz_min (3 bytes) + xyz_max (3 bytes), quantized to domain
# Leaf detection: when min==max or a special bit

# First, find the Aabb4 tree's domain. It should be in the Section or
# in the mesh tree base.
# The Section domain (at 0x360+16) = min=(1.17, -1.91, 0.0), max=(2.0, 1.08, 2.05)
# Let me check if the Aabb4 nodes decode with this domain.

dmin = struct.unpack_from('<fff', data, db+0x360+16)
dmax = struct.unpack_from('<fff', data, db+0x360+32)
print(f"Section domain: min={dmin} max={dmax}")
extent = (dmax[0]-dmin[0], dmax[1]-dmin[1], dmax[2]-dmin[2])
print(f"  extent: {extent}")

# Try decoding Aabb4 nodes as 3 bytes min + 3 bytes max (uint8 quantized)
print(f"\nAabb4 nodes decoded as uint8 × 6 (3 min + 3 max):")
for i in range(35):
    nd = data[db+0x8a0+i*6 : db+0x8a0+i*6+6]
    # 3 bytes min, 3 bytes max
    mn = (nd[0], nd[1], nd[2])
    mx = (nd[3], nd[4], nd[5])
    # Dequantize: val = domain_min + (byte/255) * extent
    dmnx = dmin[0] + (mn[0]/255.0) * extent[0]
    dmny = dmin[1] + (mn[1]/255.0) * extent[1]
    dmnz = dmin[2] + (mn[2]/255.0) * extent[2]
    dmxx = dmin[0] + (mx[0]/255.0) * extent[0]
    dmxy = dmin[1] + (mx[1]/255.0) * extent[1]
    dmxz = dmin[2] + (mx[2]/255.0) * extent[2]
    is_flat = (mn == mx)
    print(f"  [{i:2d}] min=({mn[0]:3d},{mn[1]:3d},{mn[2]:3d}) max=({mx[0]:3d},{mx[1]:3d},{mx[2]:3d}) flat={is_flat}")
    if i < 5 or is_flat:
        print(f"        deq: min=({dmnx:.3f},{dmny:.3f},{dmnz:.3f}) max=({dmxx:.3f},{dmxy:.3f},{dmxz:.3f})")

# Now check: the SimdTree leaves reference primitive indices 0-34
# The Aabb4 tree has 35 nodes. Maybe the Aabb4 tree IS the primitive array?
# i.e., each Aabb4 "node" is actually a primitive with an AABB?
# No — 35 nodes in an AABB tree for 18 primitives makes sense (18 leaves + 17 internal)

# Let me check which Aabb4 nodes are leaves (min==max might indicate leaf, or
# a different marker). Actually in Aabb4BytesCodec, leaf nodes store the
# child index/count, not AABB. Let me try a different interpretation:
# 6 bytes = 2 bytes child info + 4 bytes AABB? Or all 6 bytes AABB?

# Try: first 3 bytes = compressed min, next 3 bytes = compressed max
# Leaf nodes might have min > max or other sentinel

# Actually, let me check the hkcdStaticTree::Aabb4BytesTree structure.
# From the TBDY: Aabb4BytesCodec has "data" at offset 3.
# So the codec is: bytes 0-2 = something, byte 3-5 = data?
# Or: the 6 bytes are interpreted differently.

# Let me look at the raw bytes more carefully
print(f"\nRaw Aabb4 bytes:")
for i in range(35):
    nd = data[db+0x8a0+i*6 : db+0x8a0+i*6+6]
    # Check if any byte is 0xFF (sentinel)
    has_ff = any(b == 0xFF for b in nd)
    print(f"  [{i:2d}] {nd.hex()} ff={has_ff}")