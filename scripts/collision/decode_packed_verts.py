"""Decode the kitchenette's packed vertex format (Aabb5BytesCodec).

Item 14 @0x420, 14 entries × 8 bytes each.
The Section.codecParms (16 bytes at Section+48) define quantization.

We need to understand:
- How 8 bytes encode a 3D vertex
- The quantization domain (codecParms)
- How to encode our own 8 box vertices
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

# Section at 0x360
# codecParms at Section+48 (16 bytes)
codec = data[db+0x360+48 : db+0x360+48+16]
print(f"codecParms (16B): {codec.hex()}")
# Per TBDY: codecParms is T[N] - likely 4 floats (offsetX, offsetY, offsetZ, scale)
# or (domainMin xyz + scale)
f = struct.unpack_from('<ffff', codec)
print(f"  as 4 floats: {f}")

# Domain (section offset 16-47)
dmin = struct.unpack_from('<fff', data, db+0x360+16)
dmax = struct.unpack_from('<fff', data, db+0x360+32)
print(f"section domain min: {dmin}")
print(f"section domain max: {dmax}")

# Packed vertices: item 14 @0x420, 14 × 8 bytes
print(f"\nPacked vertices (14 × 8B at 0x420):")
for i in range(14):
    v = data[db+0x420+i*8 : db+0x420+i*8+8]
    print(f"  [{i:2d}] {v.hex()}")

# Aabb5BytesCodec layout (from TBDY):
#   hiData: offset 3 (hkUint8)
#   loData: offset 4 (hkUint8)
# So 8 bytes = 3 bytes hi + 1 byte + 4 bytes lo? Or different split.
# Let me try: each coord is 2 bytes (hi+lo)? 3 coords × 2 bytes = 6, + 2 pad?
# Or each coord is hi byte + lo byte = 2 bytes quantized, 3 coords = 6 bytes + 2 pad

# Try: 3 coords, each uint16, scaled by codecParms
print("\nTrying uint16 × 3 + pad × 2:")
for i in range(14):
    v = data[db+0x420+i*8 : db+0x420+i*8+8]
    x = struct.unpack_from('<H', v, 0)[0]
    y = struct.unpack_from('<H', v, 2)[0]
    z = struct.unpack_from('<H', v, 4)[0]
    pad = struct.unpack_from('<H', v, 6)[0]
    # Dequantize: vertex = domain_min + (uint16/65535) * (domain_max - domain_min)
    if f[3] != 0:
        # Maybe codecParms[3] is scale, and coords are offset + uint16 * scale
        fx = f[0] + x * f[3]
        fy = f[1] + y * f[3]
        fz = f[2] + z * f[3]
        print(f"  [{i:2d}] u16=({x},{y},{z}) pad={pad} -> f=({fx:.4f},{fy:.4f},{fz:.4f})")
    # Also try domain-based dequant
    dx = dmin[0] + (x/65535.0) * (dmax[0]-dmin[0])
    dy = dmin[1] + (y/65535.0) * (dmax[1]-dmin[1])
    dz = dmin[2] + (z/65535.0) * (dmax[2]-dmin[2])
    print(f"        domain-deq: ({dx:.4f},{dy:.4f},{dz:.4f})")

# Also check item 13 (hkUint16, 6 count @0x410) — might be sharedVerticesIndex
print(f"\nItem 13 (hkUint16 × 6 @0x410): {data[db+0x410:db+0x410+12].hex()}")
u16s = struct.unpack_from('<HHHHHH', data, db+0x410)
print(f"  values: {u16s}")

# Item 15 (unsigned long long × 6 @0x460) — might be something else
print(f"\nItem 15 (u64 × 6 @0x460):")
for i in range(6):
    v = struct.unpack_from('<Q', data, db+0x460+i*8)[0]
    print(f"  [{i}] 0x{v:016x}")