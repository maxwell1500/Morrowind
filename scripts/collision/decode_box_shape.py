"""Decode the crate's hknpBoxShape in detail."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib

NIF = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_CrewChest01.nif"
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
    types.append(data[p:p+L].decode('latin-1')); p += L
ti = [struct.unpack_from('<H', data, p+i*2)[0] for i in range(nb)]; p += nb*2
sizes = [struct.unpack_from('<I', data, p+i*4)[0] for i in range(nb)]; p += nb*4
ns = struct.unpack_from('<I', data, p)[0]; p += 4+4
for _ in range(ns):
    L = struct.unpack_from('<I', data, p)[0]; p += 4+L
p += 4
he = p
phys_idx = next(i for i in range(nb) if types[ti[i]] == 'bhkPhysicsSystem')
blk_off = he + sum(sizes[:phys_idx])
dlen = struct.unpack_from('<I', data, blk_off)[0]
chunks = lib.walk_tag0(data, blk_off+4, blk_off+4+dlen)
by = {}
def idx(c):
    by.setdefault(c.fourcc, []).append(c)
    for ch in c.children: idx(ch)
for c in chunks: idx(c)
dc = by[b'DATA'][0]
db = dc.body_off
items = lib.parse_item(data, by[b'ITEM'][0].body_off, by[b'ITEM'][0].body_end)

# hknpBoxShape @0x180
box_off = db + 0x180
print("hknpBoxShape 176 bytes @0x180:")
print(f"  {data[box_off:box_off+176].hex()}")
# decode fields based on class layout
print("\nBase hknpShape fields:")
print(f"  flags: {struct.unpack_from('<H', data, box_off+24)[0]}")
print(f"  type: {data[box_off+26]} (5=box)")
print(f"  numShapeKeyBits: {data[box_off+27]}")
print(f"  dispatchType: {data[box_off+28]}")
print(f"  convexRadius: {struct.unpack_from('<f', data, box_off+32)[0]}")
print(f"  userData: {struct.unpack_from('<Q', data, box_off+40)[0]}")
# hknpConvexShape fields
print(f"\n  maxAllowedPenetration: {struct.unpack_from('<H', data, box_off+56)[0]}")
print(f"  hull offset: {box_off+60}")
# ConvexHull structure at +60? Actually field hull: hknpConvexHull at offset 60
hull_off = box_off + 60
print(f"\nConvexHull @+60:")
print(f"  bytes: {data[hull_off:hull_off+48].hex()}")
# hknpConvexHull fields:
# +0 vertices relarray
# +8 planes relarray
# +16 faces relarray
# +24 indices relarray
# +32 faceLinks relarray
# +40 vertexEdges relarray
for off, name in [(0,'vertices'), (8,'planes'), (16,'faces'), (24,'indices'), (32,'faceLinks'), (40,'vertexEdges')]:
    ro = struct.unpack_from('<i', data, hull_off+off)[0]
    rs = struct.unpack_from('<i', data, hull_off+off+4)[0]
    print(f"    {name}: rel_off={ro} size={rs}")

# OBB at +112
obb_off = box_off + 112
print(f"\nOBB transform @+112 (64 bytes):")
print(f"  {data[obb_off:obb_off+64].hex()}")
# hkTransformf: rotation 3x3 matrix (hkRotationf, 48 bytes) + translation (16 bytes)
print("  rotation columns:")
for c in range(3):
    col = struct.unpack_from('<ffff', data, obb_off + c*16)
    print(f"    col{c}: {col}")
trans = struct.unpack_from('<ffff', data, obb_off + 48)
print(f"  translation: {trans}")

# vertices at DATA+0x230 (8 hkFloat3)
verts_off = db + 0x230
print(f"\nVertices @0x230:")
for i in range(8):
    v = struct.unpack_from('<fff', data, verts_off + i*12)
    print(f"  [{i}] {v}")

# planes at DATA+0x290 (6 hkVector4)
planes_off = db + 0x290
print(f"\nPlanes @0x290:")
for i in range(6):
    p = struct.unpack_from('<ffff', data, planes_off + i*16)
    print(f"  [{i}] {p}")

# faces at DATA+0x2f0 (6 hknpConvexHull::Face = 4 bytes each)
faces_off = db + 0x2f0
print(f"\nFaces @0x2f0:")
for i in range(6):
    b = data[faces_off+i*4:faces_off+i*4+4]
    first, num, minangle = struct.unpack_from('<HBB', b, 0)
    print(f"  [{i}] first={first} num={num} minHalfAngle={minangle}")

# indices at DATA+0x310 (24 uint8)
idx_off = db + 0x310
print(f"\nIndices @0x310: {list(data[idx_off:idx_off+24])}")

# edges at DATA+0x330 and 0x390
print(f"\nEdges1 @0x330:")
for i in range(24):
    e = data[idx_off+0x20+i*4:idx_off+0x20+i*4+4]
    face, edge = struct.unpack_from('<HB', e, 0)
    print(f"  [{i}] face={face} edge={edge} pad={e[3]}")

# Mass properties at DATA+0x3f0
mp_off = db + 0x3f0
print(f"\nShapeMassProperties @0x3f0 (56 bytes):")
print(f"  {data[mp_off:mp_off+56].hex()}")
print(f"  mass: {struct.unpack_from('<f', data, mp_off+24)[0]}")
print(f"  volume: {struct.unpack_from('<f', data, mp_off+28)[0]}")