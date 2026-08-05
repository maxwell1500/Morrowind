"""Verify packed vertex decoding by extracting the kitchenette's ACTUAL
rendered triangle vertices from the BSGeometry blocks, then comparing
against the dequantized packed vertices.

If the dequant matches the rendered vertices, we know the format.
Then we can encode box vertices correctly.
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

# Find BSGeometry blocks and extract vertex data
block_offs = []
cur = he
for i in range(nb):
    block_offs.append(cur)
    cur += sizes[i]

# The kitchenette has many BSGeometry blocks. The collision vertices
# should match the rendered mesh vertices (since collision = rendered mesh).
# Let's dump first BSGeometry's vertex data.

# BSGeometry layout (Starfield): need to find vertex buffer offset
# Let me dump first BSGeometry block structure
geom_idx = next(i for i in range(nb) if types[ti[i]] == "BSGeometry')
goff = block_offs[geom_idx]
gsize = sizes[geom_idx]
gblk = data[goff:goff+gsize]
print(f"BSGeometry [{geom_idx}] at 0x{goff:x}, size={gsize}")
print(f"  first 64 bytes: {gblk[:64].hex()}")

# BSGeometry starts with: num_extra(u32), extra_refs..., then data
num_extra = struct.unpack_from('<I', gblk, 0)[0]
print(f"  num_extra: {num_extra}")
# After extras: shader_ref(u32), ...
# This is complex. Let me try a different approach:
# search for float patterns that match known kitchenette coordinates.

# The kitchenette domain is x=[1.17, 2.0], y=[-1.91, 1.08], z=[0, 2.05]
# Search for floats in this range in the geometry block
print(f"\nSearching for floats in kitchenette coordinate range in BSGeometry block...")
matches = []
for off in range(0, gsize - 4, 4):
    f = struct.unpack_from('<f', gblk, off)[0]
    if 0.5 < f < 2.5:  # x or z range
        matches.append((off, f))
    elif -2.5 < f < -0.5:  # y range
        matches.append((off, f))

print(f"  Found {len(matches)} floats in range")
# Show clusters
if matches:
    print(f"  First 20:")
    for off, f in matches[:20]:
        print(f"    offset 0x{off:04x}: {f:.4f}")

# Actually, let me just search the entire NIF for the known vertex coordinates
# from the collision packed verts dequantized both ways

# Get the collision DATA body
phys_idx = next(i for i in range(nb) if types[ti[i]] == "bhkPhysicsSystem")
blk_off = block_offs[phys_idx]
dlen = struct.unpack_from('<I', data, blk_off)[0]
chunks = lib.walk_tag0(data, blk_off+4, blk_off+4+dlen)
by_fcc = {}
def idx(c):
    by_fcc.setdefault(c.fourcc, []).append(c)
    for ch in c.children: idx(ch)
for c in chunks: idx(c)
dc = by_fcc[b"DATA"][0]
db = dc.body_off

# codecParms
codec = struct.unpack_from('<ffff', data, db+0x360+48)
dmin = struct.unpack_from('<fff', data, db+0x360+16)
dmax = struct.unpack_from('<fff', data, db+0x360+32)
print(f"\nCodec params: {codec}")
print(f"Domain min: {dmin}")
print(f"Domain max: {dmax}")

# Decode all 14 packed vertices both ways
print(f"\nPacked vertex dequantization comparison:")
for i in range(14):
    v = data[db+0x420+i*8 : db+0x420+i*8+8]
    u16 = struct.unpack_from('<HHH', v, 0)
    pad = struct.unpack_from('<H', v, 6)[0]

    # Method A: codecParms (offset + u16 * scale)
    a = (codec[0] + u16[0]*codec[3], codec[1] + u16[1]*codec[3], codec[2] + u16[2]*codec[3])

    # Method B: domain (min + u16/65535 * (max-min))
    b = (dmin[0] + (u16[0]/65535.0)*(dmax[0]-dmin[0]),
         dmin[1] + (u16[1]/65535.0)*(dmax[1]-dmin[1]),
         dmin[2] + (u16[2]/65535.0)*(dmax[2]-dmin[2]))

    print(f"  [{i:2d}] u16=({u16[0]:5d},{u16[1]:5d},{u16[2]:5d}) pad={pad}")
    print(f"       A(codec): ({a[0]:.4f}, {a[1]:.4f}, {a[2]:.4f})")
    print(f"       B(domain): ({b[0]:.4f}, {b[1]:.4f}, {b[2]:.4f})")

# Now check: do the primitives reference these 14 packed vertices?
# Primitives are 4-byte: 3 uint8 indices + 1 byte
print(f"\nPrimitives (4 bytes each, 18 triangles):")
for i in range(18):
    p = data[db+0x3c0+i*4 : db+0x3c0+i*4+4]
    print(f"  [{i:2d}] indices=({p[0]},{p[1]},{p[2]}) extra={p[3]}")
    # Vertex index p[0] references packed vertex p[0]
    # But some indices are > 13 (e.g. 18, 19). These must be "shared vertices"
    if p[0] > 13 or p[1] > 13 or p[2] > 13:
        print(f"    -> references SHARED vertices (index > 13)")

# Item 13: sharedVerticesIndex (hkUint16 × 6)
sv = struct.unpack_from('<HHHHHH', data, db+0x410)
print(f"\nShared vertices index: {sv}")
# These map shared vertex slots (14-19) to packed vertex indices (0-13)
# So primitive index 14 -> packed vertex sv[0], etc.
# But sv = (0,1,2,3,4,5) — so shared vertex 14=packed vertex 0, etc.
# That means primitive indices 14-19 map to packed vertices 0-5
# And index 18 maps to shared vertex 18-14=4 -> packed vertex sv[4]=4
# Wait, that doesn't work. Let me check: indices > 13 might use a different mapping.

# Actually: numPackedVertices=14, so indices 0-13 are packed verts.
# Indices 14+ are "shared vertices" indexed by (idx - 14) into the sharedVerticesIndex array.
# sharedVerticesIndex = (0,1,2,3,4,5), so:
#   idx 14 -> sharedVerticesIndex[0] = 0 (packed vert 0)
#   idx 15 -> sharedVerticesIndex[1] = 1
#   idx 16 -> sharedVerticesIndex[2] = 2
#   idx 17 -> sharedVerticesIndex[3] = 3
#   idx 18 -> sharedVerticesIndex[4] = 4
#   idx 19 -> sharedVerticesIndex[5] = 5
# So all primitives reference packed vertices 0-13.
print(f"\nResolved primitive vertices (with shared vertex mapping):")
for i in range(18):
    p = data[db+0x3c0+i*4 : db+0x3c0+i*4+4]
    v0 = p[0] if p[0] < 14 else sv[p[0]-14]
    v1 = p[1] if p[1] < 14 else sv[p[1]-14]
    v2 = p[2] if p[2] < 14 else sv[p[2]-14]
    print(f"  [{i:2d}] raw=({p[0]},{p[1]},{p[2]}) resolved=({v0},{v1},{v2}) extra={p[3]}")