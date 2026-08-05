"""Decode item 15 (u64 × 6 @0x460) as potential shared vertex coordinates.
Each u64 might encode a 3D vertex in some packed format.

Also check: item 13 (hkUint16 × 6) = sharedVerticesIndex maps
shared vertex SLOTS to PACKED VERTEX INDICES. So shared vertex slot 0
maps to packed vertex 0, slot 1 -> packed vertex 1, etc.

But that would make shared vertices redundant with packed vertices.
Unless sharedVerticesIndex maps to a DIFFERENT vertex array.

Let me check the TBDY class layout for sharedVerticesIndex more carefully.
The field is in hkcdStaticMeshTree::Base at offset 96.
packedVertices at offset 112, sharedVertices at offset 128.

So sharedVerticesIndex and sharedVertices are DIFFERENT arrays.
sharedVerticesIndex[i] might be an INDEX into packedVertices.
sharedVertices[i] might be the actual vertex data (u64 packed coords).

Let me try decoding item 15 as packed 3D coordinates.
"""
import struct

KITCH_DMIN = (1.17037034034729, -1.9087656736373901, 0.0)
KITCH_DMAX = (1.999778389930725, 1.0799816846847534, 2.047852039337158)

# Item 15 raw data
item15 = [
    0x000003fffff4b4f2,
    0x000000000014b4f2,
    0x000003ffffffffff,
    0xfffffffffffffffe,
    0x00000000001fffff,
    0xfffffc00001ffffe,
]

print("Item 15 (u64 × 6) — trying various 3D decodings:")

# Try 1: 3 × 21-bit values (63 bits + 1 flag)
print("\nTry 1: 3 × 21-bit (0..2097151, 21 bits each):")
for i, val in enumerate(item15):
    flag = (val >> 63) & 1
    x21 = (val >> 0) & 0x1FFFFF
    y21 = (val >> 21) & 0x1FFFFF
    z21 = (val >> 42) & 0x1FFFFF
    # Dequant to domain (21-bit: 0..2097151)
    dx = KITCH_DMIN[0] + (x21/2097151.0) * (KITCH_DMAX[0]-KITCH_DMIN[0])
    dy = KITCH_DMIN[1] + (y21/2097151.0) * (KITCH_DMAX[1]-KITCH_DMIN[1])
    dz = KITCH_DMIN[2] + (z21/2097151.0) * (KITCH_DMAX[2]-KITCH_DMIN[2])
    print(f"  [{i}] x21={x21} y21={y21} z21={z21} flag={flag} -> ({dx:.4f}, {dy:.4f}, {dz:.4f})")

# Try 2: 3 × 20-bit + 4 flag bits
print("\nTry 2: 3 × 20-bit (0..1048575):")
for i, val in enumerate(item15):
    x20 = (val >> 0) & 0xFFFFF
    y20 = (val >> 20) & 0xFFFFF
    z20 = (val >> 40) & 0xFFFFF
    flags = (val >> 60) & 0xF
    dx = KITCH_DMIN[0] + (x20/1048575.0) * (KITCH_DMAX[0]-KITCH_DMIN[0])
    dy = KITCH_DMIN[1] + (y20/1048575.0) * (KITCH_DMAX[1]-KITCH_DMIN[1])
    dz = KITCH_DMIN[2] + (z20/1048575.0) * (KITCH_DMAX[2]-KITCH_DMIN[2])
    print(f"  [{i}] x20={x20} y20={y20} z20={z20} flags={flags} -> ({dx:.4f}, {dy:.4f}, {dz:.4f})")

# Try 3: signed values (2's complement) — note item 3 and 5 have high bits set
print("\nTry 3: 3 × 21-bit SIGNED:")
for i, val in enumerate(item15):
    x21 = (val >> 0) & 0x1FFFFF
    y21 = (val >> 21) & 0x1FFFFF
    z21 = (val >> 42) & 0x1FFFFF
    # Sign-extend 21-bit
    if x21 & 0x100000: x21 -= 0x200000
    if y21 & 0x100000: y21 -= 0x200000
    if z21 & 0x100000: z21 -= 0x200000
    print(f"  [{i}] x={x21} y={y21} z={z21}")

# Try 4: maybe these are NOT coordinates but bitfield indices/references
# Let me check if item 13 (sharedVerticesIndex) maps to THESE (item 15) vertices
# rather than to packed vertices (item 14).
print("\n\nItem 13 (sharedVerticesIndex) = (0,1,2,3,4,5)")
print("If these index into item 15 (6 shared vertices):")
print("  shared vertex 0 -> item15[0] = 0x000003fffff4b4f2")
print("  shared vertex 1 -> item15[1] = 0x000000000014b4f2")
print("  etc.")
print("Then primitive index 14 -> sharedVerticesIndex[0] = 0 -> item15[0]")

# Let me also check: maybe sharedVerticesIndex maps shared vertex SLOTS
# to packed vertex INDICES. So shared vertex 14 is at packedVertices[0].
# And item 15 stores something ELSE (maybe edge/connectivity data).

# Actually, let me check the field types from TBDY:
# hkcdStaticMeshTree::Base has:
#   sharedVerticesIndex: offset 96, type=hkArray<hkUint16>
# So sharedVerticesIndex is an array of uint16.
# And hkcdDefaultStaticMeshTree has:
#   sharedVertices: offset 128, type=hkArray<?>
# The sharedVertices array type is unknown (item 15 type_idx=21 = unsigned long long)
# So sharedVertices is an array of u64 values.

# Let me check what type_idx=21 resolves to
# From the parse output: [21] hkUint64
# So sharedVertices is hkArray<hkUint64> — each shared vertex is a u64.

# The u64 might encode a vertex in a compressed format.
# Let me try: maybe it's a 3D vector in half-float (hkHalf16) format
# 3 × hkHalf16 = 3 × 2 bytes = 6 bytes = 48 bits. u64 = 64 bits.
# Remaining 16 bits = padding/flags
print("\n\nTry 5: 3 × half-float (16-bit) + 16 bits flags:")
for i, val in enumerate(item15):
    # Try little-endian: first 6 bytes = 3 half-floats
    b = val.to_bytes(8, 'little')
    h0 = struct.unpack_from('<e', b, 0)[0]  # half-float
    h1 = struct.unpack_from('<e', b, 2)[0]
    h2 = struct.unpack_from('<e', b, 4)[0]
    flags = struct.unpack_from('<H', b, 6)[0]
    print(f"  [{i}] half=({h0:.4f}, {h1:.4f}, {h2:.4f}) flags={flags}")

# Try big-endian
print("\nTry 6: 3 × half-float BE:")
for i, val in enumerate(item15):
    b = val.to_bytes(8, 'big')
    h0 = struct.unpack_from('>e', b, 0)[0]
    h1 = struct.unpack_from('>e', b, 2)[0]
    h2 = struct.unpack_from('>e', b, 4)[0]
    flags = struct.unpack_from('>H', b, 6)[0]
    print(f"  [{i}] half=({h0:.4f}, {h1:.4f}, {h2:.4f}) flags={flags}")