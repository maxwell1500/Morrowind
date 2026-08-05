"""Verify the scaled box in an injected NIF, parsing DATA offset correctly."""
import struct, sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib

NIF = r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_nord_house_03.nif"
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

box_off = db + 0x180
verts_off = db + 0x230
planes_off = db + 0x290
obb_off = box_off + 112

print("Box shape type:", data[box_off+26], "dispatchType:", data[box_off+28])
print("convexRadius:", struct.unpack_from('<f', data, box_off+32)[0])
print("OBB transform:")
for c in range(3):
    col = struct.unpack_from('<ffff', data, obb_off + c*16)
    print(f"  col{c}: {col}")
trans = struct.unpack_from('<ffff', data, obb_off + 48)
print(f"  translation: {trans}")

print("\nVertices:")
for i in range(8):
    v = struct.unpack_from('<fff', data, verts_off + i*12)
    print(f"  [{i}] {v}")

print("\nPlanes:")
for i in range(6):
    pl = struct.unpack_from('<ffff', data, planes_off + i*16)
    print(f"  [{i}] {pl}")

with open(r"C:\Users\max\Projects\Morrowind\converted_assets\mapping\morrowind_mesh_bounds.json") as f:
    bounds = json.load(f)['ex_nord_house_03']
print(f"\nBounds: min={bounds['min']} max={bounds['max']}")