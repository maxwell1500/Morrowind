"""Build the kitchenette's 18 triangles from packed vertices (domain dequant,
Method B) and check if they form a closed 3D shape (Euler characteristic).

If V - E + F = 2 (closed manifold), the uint16×3 format is correct.
"""
import struct

KITCH_DMIN = (1.17037034034729, -1.9087656736373901, 0.0)
KITCH_DMAX = (1.999778389930725, 1.0799816846847534, 2.047852039337158)

verts_raw = [
    "00f83f0000000000", "1307c03313ffff33", "00f8ff330000c033",
    "130740bb13ff7fbb", "040340bb04fb7fbb", "ffffffff1afbbfc1",
    "1a0380c1ff07c0ff", "0000000000000000", "f2b4f4ffff030000",
    "f2b4140000000000", "ffffffffff030000", "feffffffffffffff",
    "ffff1f0000000000", "feff1f0000fcffff",
]

# Method B: uint16 × 3 + pad × 2
verts = []
for h in verts_raw:
    b = bytes.fromhex(h)
    u16 = struct.unpack_from('<HHH', b, 0)
    x = KITCH_DMIN[0] + (u16[0]/65535.0) * (KITCH_DMAX[0]-KITCH_DMIN[0])
    y = KITCH_DMIN[1] + (u16[1]/65535.0) * (KITCH_DMAX[1]-KITCH_DMIN[1])
    z = KITCH_DMIN[2] + (u16[2]/65535.0) * (KITCH_DMAX[2]-KITCH_DMIN[2])
    verts.append((x, y, z))

print("Vertices (Method B - uint16 domain dequant):")
for i, v in enumerate(verts):
    print(f"  [{i:2d}] ({v[0]:.4f}, {v[1]:.4f}, {v[2]:.4f})")

# Primitives (4 bytes: 3 uint8 indices + 1 extra)
prims_raw = [
    "0c0d0a0b", "0c0b0908", "05120202", "02121306",
    "090b1107", "0c130d0d", "13110a0d", "0b0a1111",
    "130c0806", "05040001", "06070302", "000e0f01",
    "04050203", "08090706", "11100307", "010f1205",
    "04031000", "0e001010",
]

# Shared vertices index
sv = (0, 1, 2, 3, 4, 5)

def resolve(idx):
    if idx < 14:
        return idx
    return sv[idx - 14]

triangles = []
for h in prims_raw:
    b = bytes.fromhex(h)
    v0 = resolve(b[0])
    v1 = resolve(b[1])
    v2 = resolve(b[2])
    triangles.append((v0, v1, v2))

print(f"\n{len(triangles)} triangles:")
for i, t in enumerate(triangles):
    v0, v1, v2 = verts[t[0]], verts[t[1]], verts[t[2]]
    print(f"  [{i:2d}] ({v0[0]:.2f},{v0[1]:.2f},{v0[2]:.2f}) ({v1[0]:.2f},{v1[1]:.2f},{v1[2]:.2f}) ({v2[0]:.2f},{v2[1]:.2f},{v2[2]:.2f})")

# Check Euler characteristic
edges = set()
for v0, v1, v2 in triangles:
    for a, b in [(v0,v1), (v1,v2), (v2,v0)]:
        edge = (min(a,b), max(a,b))
        edges.add(edge)

V = len(verts)
E = len(edges)
F = len(triangles)
print(f"\nV={V}, E={E}, F={F}")
print(f"V - E + F = {V - E + F} (should be 2 for closed manifold)")
print(f"2E = {2*E}, 3F = {3*F} (should be equal for triangular mesh)")

# Check bounding box of all triangle vertices
all_coords = []
for t in triangles:
    for vi in t:
        all_coords.append(verts[vi])
import numpy as np
pts = np.array(all_coords)
print(f"\nBounding box: min={pts.min(axis=0)} max={pts.max(axis=0)}")
print(f"Domain: min={KITCH_DMIN} max={KITCH_DMAX}")