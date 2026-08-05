"""Verify that encoding 8 box corners as uint16 (0 or 65535) with the
correct domain produces valid 3D box vertices.

Also test: if we set codecParms to match the domain, does Method A work too?
"""
import struct

# Mesh AABB (ex_nord_house_03)
mesh_min = (-2.67, -2.09, -3.73)
mesh_max = (2.67, 2.09, 3.56)

# Set section domain = mesh AABB
dmin = mesh_min
dmax = mesh_max

# 8 box corners: (x_bit, y_bit, z_bit) where 0=min, 1=max
corners = [
    (0,0,0), (1,0,0), (0,1,0), (1,1,0),
    (0,0,1), (1,0,1), (0,1,1), (1,1,1),
]

print("Box corners encoded as uint16 (0 or 65535), dequantized via domain:")
for i, (bx, by, bz) in enumerate(corners):
    u16 = (bx*65535, by*65535, bz*65535)
    # Method B: domain-based
    x = dmin[0] + (u16[0]/65535.0) * (dmax[0]-dmin[0])
    y = dmin[1] + (u16[1]/65535.0) * (dmax[1]-dmin[1])
    z = dmin[2] + (u16[2]/65535.0) * (dmax[2]-dmin[2])
    print(f"  [{i}] bits=({bx},{by},{bz}) u16={u16} -> ({x:.3f}, {y:.3f}, {z:.3f})")

# 12 triangles (CCW from outside)
tris = [
    (0,1,3), (0,3,2),  # -Z
    (4,6,7), (4,7,5),  # +Z
    (0,4,5), (0,5,1),  # -Y
    (2,3,7), (2,7,6),  # +Y
    (0,2,6), (0,6,4),  # -X
    (1,5,7), (1,7,3),  # +X
]
print(f"\n12 box triangles (vertex indices):")
for i, t in enumerate(tris):
    print(f"  [{i:2d}] {t}")

# Now test: what codecParms would make Method A match Method B?
# Method A: f = offset + u16 * scale
# For u16=0: f = offset = domain_min  -> offset = domain_min
# For u16=65535: f = domain_min + 65535*scale = domain_max
#   -> scale = (domain_max - domain_min) / 65535
print(f"\nCodecParms for Method A to match domain:")
for axis in range(3):
    offset = dmin[axis]
    scale = (dmax[axis] - dmin[axis]) / 65535.0
    print(f"  axis {axis}: offset={offset:.6f}, scale={scale:.8f}")
# But codecParms is (offsetX, offsetY, offsetZ, scale) — single scale for all axes!
# This means Method A can't work with different scales per axis.
# Unless codecParms is (offsetX, offsetY, offsetZ, scaleX, scaleY, scaleZ)?
# The kitchenette codecParms = (1.170, -1.909, 0.617, 0.000295)
# domain extent = (0.829, 2.989, 2.048)
# 0.829/65535 = 0.0000127, 2.989/65535 = 0.0000456, 2.048/65535 = 0.0000313
# None match 0.000295. So Method A with single scale does NOT work.
# codecParms[3] = 0.000295 might be something else entirely.

# Actually: 0.000295 * 65535 = 19.33. That's way bigger than the domain.
# Maybe codecParms defines the quantization for the Aabb5BytesCodec differently.
# The "5 bytes" in Aabb5BytesCodec might mean 5 bytes of data per vertex
# (not 6 = 3×uint16), and the layout is different from what I assumed.

# Let me check: 8 bytes per vertex, but "Aabb5BytesCodec" = 5 data bytes.
# Maybe: 3 hi-bytes (one per axis) + 2 lo-bytes (shared between axes) + 3 pad?
# Or: the uint16 values I'm reading are actually (hi_byte[axis0], hi_byte[axis1],
# hi_byte[axis2], lo_byte) packed differently.

# Actually looking at the raw bytes again:
# Vertex 0: 00 f8 3f 00 00 00 00 00
# If 5 bytes: 00 f8 3f 00 00 = data, 00 00 00 = pad
# Vertex 5: ff ff ff ff ff 03 00 00  -> wait, that's 00 f8 3f pattern...

# Let me re-examine the byte layout:
print("\nRaw packed vertex bytes (re-examined):")
verts_raw = [
    (0, "00f83f0000000000"),
    (1, "1307c03313ffff33"),
    (2, "00f8ff330000c033"),
    (3, "130740bb13ff7fbb"),
    (4, "040340bb04fb7fbb"),
    (5, "ffffffff1afbbfc1"),
    (6, "1a0380c1ff07c0ff"),
    (7, "0000000000000000"),
    (8, "f2b4f4ffff030000"),
    (9, "f2b4140000000000"),
    (10, "ffffffffff030000"),
    (11, "feffffffffffffff"),
    (12, "ffff1f0000000000"),
    (13, "feff1f0000fcffff"),
]
for i, h in verts_raw:
    b = bytes.fromhex(h)
    print(f"  [{i:2d}] {h}")
    # Try as: byte0, byte1, byte2, byte3, byte4 = 5 data bytes
    # Aabb5BytesCodec: hiData@3, loData@4
    # Maybe: bytes 0-2 = 3 hi-bytes for xyz, byte 3 = lo bits, byte 4 = ??
    # Or: the 5 bytes encode 3 × ~13-bit values packed into 5 bytes (39 bits)
    # 5 bytes = 40 bits, 3 axes = 13.3 bits each. That's Aabb5BytesCodec!
    # 13 bits per axis × 3 = 39 bits + 1 bit flag = 40 bits = 5 bytes

    # Let me try: each axis = 13 bits, packed as:
    # bits 0-12: x (13 bits)
    # bits 13-25: y (13 bits)
    # bits 26-38: z (13 bits)
    # bit 39: flag
    val40 = int.from_bytes(b[:5], 'little')
    flag = (val40 >> 39) & 1
    x13 = (val40 >> 0) & 0x1FFF
    y13 = (val40 >> 13) & 0x1FFF
    z13 = (val40 >> 26) & 0x1FFF
    # Dequant: domain_min + (val / 8191) * (domain_max - domain_min)
    # 13 bits = 0..8191
    dx = dmin[0] + (x13/8191.0) * (dmax[0]-dmin[0])
    dy = dmin[1] + (y13/8191.0) * (dmax[1]-dmin[1])
    dz = dmin[2] + (z13/8191.0) * (dmax[2]-dmin[2])
    print(f"    5B={b[:5].hex()} val40=0x{val40:010x} x13={x13} y13={y13} z13={z13} flag={flag}")
    print(f"    deq13: ({dx:.4f}, {dy:.4f}, {dz:.4f})")