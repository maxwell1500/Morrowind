"""Test: encode box vertices using the KITCHENETTE's domain and codecParms,
but map the uint16 values so they dequantize to the MESH's AABB coordinates.

If the engine dequants via codecParms: u16 = (target_coord - offset) / scale
If the engine dequants via domain: u16 = (target_coord - domain_min) / (domain_max - domain_min) * 65535

We set BOTH domain AND codecParms to match the mesh AABB, so both methods
produce the same result.
"""
import struct

# Kitchenette codecParms
KITCH = {
    'offset': (1.17037034034729, -1.9087656736373901, 0.6170892715454102),
    'scale': 0.00029514392372220755,
    'dmin': (1.17037034034729, -1.9087656736373901, 0.0),
    'dmax': (1.999778389930725, 1.0799816846847534, 2.047852039337158),
}

# Mesh AABB
mesh_min = (-2.67, -2.09, -3.73)
mesh_max = (2.67, 2.09, 3.56)

# Option 1: Set domain = mesh AABB, keep codecParms = kitchenette's
# If engine uses domain dequant: vertices correct
# If engine uses codecParms dequant: vertices WRONG (kitchenette range)

# Option 2: Set domain = mesh AABB, set codecParms offset = mesh_min, scale = max_extent/65535
# But scale is single value... let's use the max extent
max_extent = max(mesh_max[i] - mesh_min[i] for i in range(3))  # 7.29
scale = max_extent / 65535.0  # 0.000111
# If engine uses codecParms: x = mesh_min[0] + u16 * scale
# For u16=65535: x = mesh_min[0] + max_extent = -2.67 + 7.29 = 4.62 (WRONG for x-axis, should be 2.67)
# So single-scale codecParms can't map differently per axis.

# Option 3: DON'T change domain. Keep kitchenette domain. Encode uint16 so
# that domain-dequant gives mesh coordinates:
# u16 = (target - kitch_dmin) / (kitch_dmax - kitch_dmin) * 65535
# For target = mesh_min[0] = -2.67:
#   u16 = (-2.67 - 1.17) / (2.0 - 1.17) * 65535 = -3.84 / 0.83 * 65535 = negative!
# Can't encode negative uint16. So we can't map mesh coords outside kitchenette domain.

# Option 4: Scale the mesh into the kitchenette domain, then place the REFR
# with a scale modifier. But we don't want to scale the visual mesh.

# REAL SOLUTION: The packed vertices use domain-based dequant (Method B works).
# So we need to:
# 1. Set domain = mesh AABB (already done in encode_static_box.py)
# 2. Encode uint16 = 0 or 65535 for box corners (already done)
# 3. Also update codecParms to match domain, in case engine uses it

# For codecParms with per-axis scale, we need to know the exact format.
# Let's check: maybe codecParms is (offsetX, offsetY, offsetZ, scaleBits)
# where scaleBits is a shared scale with per-axis multipliers stored elsewhere.

# Actually, let me just check: does the kitchenette's codecParms[3] = 0.000295
# correspond to ANY of the domain extents?
ext = [KITCH['dmax'][i] - KITCH['dmin'][i] for i in range(3)]
print(f"Kitchenette domain extents: {ext}")
print(f"  ext/65535 = {[e/65535 for e in ext]}")
print(f"  ext/8191 = {[e/8191 for e in ext]}")  # 13-bit
print(f"  codecParms[3] = {KITCH['scale']}")
print(f"  codecParms[3] * 65535 = {KITCH['scale'] * 65535}")
print(f"  codecParms[3] * 8191 = {KITCH['scale'] * 8191}")

# 0.000295 * 65535 = 19.33 - doesn't match any extent
# 0.000295 * 8191 = 2.42 - close to z extent (2.048)? Not really.
# Maybe codecParms[3] is not a scale at all. Maybe it's 1/max_quantization_value.
# Or it's the scale for the Aabb4 tree, not the packed vertices.

# Let me try: codecParms might be (scaleX, scaleY, scaleZ, offset)
# reversed from what I assumed.
print(f"\nReversed interpretation: (scaleX, scaleY, scaleZ, offset)")
print(f"  scaleX={KITCH['offset'][0]}, scaleY={KITCH['offset'][1]}, scaleZ={KITCH['offset'][2]}")
print(f"  offset={KITCH['scale']}")
# x = u16 * scaleX + offset?
# For u16=65535, x = 65535 * 1.17 + 0.000295 = 76806. NO.

# Let me try: maybe the packed vertex format is NOT 3×uint16.
# The class is "Aabb5BytesCodec" — 5 bytes.
# Let me check the TBDY field offsets more carefully.
# From decode_kitchenette_full.py output:
#   Aabb5BytesCodec: hiData offset=3, loData offset=4
# So the 8-byte vertex has:
#   bytes 0-2: some data (3 bytes)
#   byte 3: hiData
#   byte 4-7: loData (4 bytes)
# That's 3 + 1 + 4 = 8 bytes, but only 5 are "data" (hence Aabb5Bytes).

# Maybe: bytes 0-2 = 3 hi-bytes (one per axis, unsigned 8-bit)
#         byte 3 = shared lo-bits byte
#         bytes 4-7 = padding/flags
# Each coordinate = hi_byte * 256 + lo_bits
# But which lo-bits from byte 3 go to which axis?

# Let me try: 3 hi-bytes + 1 byte with 2 lo-bits per axis = 10 bits per axis
# 10 bits = 0..1023
print(f"\n\nTrying 10-bit per axis (3 hi-bytes + 1 lo-byte with 2 bits per axis):")
# Kitchenette vertices
verts_raw = [
    "00f83f0000000000", "1307c03313ffff33", "00f8ff330000c033",
    "130740bb13ff7fbb", "040340bb04fb7fbb", "ffffffff1afbbfc1",
    "1a0380c1ff07c0ff", "0000000000000000", "f2b4f4ffff030000",
    "f2b4140000000000", "ffffffffff030000", "feffffffffffffff",
    "ffff1f0000000000", "feff1f0000fcffff",
]
for i, h in enumerate(verts_raw):
    b = bytes.fromhex(h)
    hi = (b[0], b[1], b[2])
    lo_byte = b[3]
    # 2 bits per axis: bits 0-1 = x_lo, bits 2-3 = y_lo, bits 4-5 = z_lo, bits 6-7 = flags
    x_lo = lo_byte & 0x03
    y_lo = (lo_byte >> 2) & 0x03
    z_lo = (lo_byte >> 4) & 0x03
    flags = (lo_byte >> 6) & 0x03

    x10 = (hi[0] << 2) | x_lo
    y10 = (hi[1] << 2) | y_lo
    z10 = (hi[2] << 2) | z_lo

    # Dequant with domain (10-bit: 0..1023)
    dx = KITCH['dmin'][0] + (x10/1023.0) * (KITCH['dmax'][0]-KITCH['dmin'][0])
    dy = KITCH['dmin'][1] + (y10/1023.0) * (KITCH['dmax'][1]-KITCH['dmin'][1])
    dz = KITCH['dmin'][2] + (z10/1023.0) * (KITCH['dmax'][2]-KITCH['dmin'][2])

    print(f"  [{i:2d}] hi={hi} lo_byte=0x{lo_byte:02x} x10={x10} y10={y10} z10={z10} flags={flags}")
    print(f"       deq: ({dx:.4f}, {dy:.4f}, {dz:.4f})")