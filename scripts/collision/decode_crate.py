"""Decode the crate's bhkPhysicsSystem to understand how to make it static."""
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
    types.append(data[p:p+L].decode("latin-1")); p += L
ti = [struct.unpack_from('<H', data, p+i*2)[0] for i in range(nb)]; p += nb*2
sizes = [struct.unpack_from('<I', data, p+i*4)[0] for i in range(nb)]; p += nb*4
ns = struct.unpack_from('<I', data, p)[0]; p += 4+4
for _ in range(ns):
    L = struct.unpack_from('<I', data, p)[0]; p += 4+L
p += 4
he = p

# Print type table
print("Type table:")
for i, t in enumerate(types):
    print(f"  [{i}] {t}")

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
items = lib.parse_item(data, by_fcc[b"ITEM"][0].body_off, by_fcc[b"ITEM"][0].body_end)

print(f"\nItems ({len(items)}):")
for it in items:
    cn = types[it['type_idx']] if it['type_idx'] < len(types) else '???'
    print(f"  [{it['i']}] {cn} type_idx={it['type_idx']} off=0x{it['data_off']:x} count={it['count']} flags={it['flags']}")

# Decode bodyCinfo (item 3 @0xc0)
print(f"\nbodyCinfo (item 3 @0xc0):")
shape_ref = struct.unpack_from('<I', data, db+0xc0)[0]
flags = struct.unpack_from('<I', data, db+0xc8)[0]
print(f"  shape_ref={shape_ref} flags={flags}")
print(f"  bytes 0xc0-0x140: {data[db+0xc0:db+0x140].hex()}")

# bodyCinfo has fields at offsets:
# 0: shape ref (u32)  = 4 (item 4)
# 8: flags (u32)
# 12: collisionCntrl
# 16: collisionFilterInfo
# 20: materialId
# 22: qualityId
# 24: name
# 32: userData
# 40: motionType (u8)
mt = data[db+0xc0+40]
print(f"  motionType at +40: {mt} (0=dynamic? 2=static?)")

# Print item 4 (shape) data
print(f"\nShape (item 4 @0x180), 128 bytes:")
print(f"  {data[db+0x180:db+0x180+128].hex()}")
# shape type at +26, dispatchType at +28, numShapeKeyBits at +27
print(f"  type={data[db+0x180+26]}, dispatchType={data[db+0x180+28]}, numShapeKeyBits={data[db+0x180+27]}")
print(f"  data ref at +64: {struct.unpack_from('<I', data, db+0x180+64)[0]}")
print(f"  numTriangles at +96: {struct.unpack_from('<I', data, db+0x180+96)[0]}")
print(f"  numConvexShapes at +100: {struct.unpack_from('<I', data, db+0x180+100)[0]}")

# Convex hull shape is item 4, data ref to item 6 (vertices?)
# item 6 = type_idx=77, 8 vertices at 0x230
print(f"\nItem 6 (vertices?) @0x230, 8 count:")
for i in range(8):
    v = data[db+0x230+i*12 : db+0x230+i*12+12]
    x,y,z = struct.unpack_from('<fff', v, 0)
    print(f"  [{i}] ({x:.3f}, {y:.3f}, {z:.3f})")

# Planes (item 7 @0x290, 6 planes)
print(f"\nItem 7 (planes) @0x290, 6 count:")
for i in range(6):
    p = data[db+0x290+i*16 : db+0x290+i*16+16]
    a,b,c,d = struct.unpack_from('<ffff', p, 0)
    print(f"  [{i}] ({a:.3f}, {b:.3f}, {c:.3f}, {d:.3f})")

# BodyCinfo at 0xc0 — check for mass, velocity fields
print(f"\nbodyCinfo full 192 bytes:")
for i in range(0, 192, 16):
    print(f"  {i:04x}: {data[db+0xc0+i:db+0xc0+i+16].hex()}")