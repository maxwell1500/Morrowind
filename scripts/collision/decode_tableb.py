"""Decode Starborn_TableB.nif collision geometry to see if it's a simple box."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib

NIF = r"C:\XboxGames\Starfield\Content\Data\meshes\Ships\Interior\Starborn\Starborn_TableB.nif"
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
items = lib.parse_item(data, by_fcc[b"ITEM"][0].body_off, by_fcc[b"ITEM"][0].body_end)

print(f"Items ({len(items)}):")
for it in items:
    print(f"  [{it['i']}] type_idx={it['type_idx']} off=0x{it['data_off']:x} count={it['count']} flags={it['flags']}")

# Section
sec_off = items[11]['data_off']
print(f"\nSection @0x{sec_off:x}:")
print(f"  domain min: {struct.unpack_from('<fff', data, db+sec_off+16)}")
print(f"  domain max: {struct.unpack_from('<fff', data, db+sec_off+32)}")
print(f"  codecParms: {data[db+sec_off+48:db+sec_off+64].hex()}")
print(f"  numPackedVerts: {data[db+sec_off+88]}")
print(f"  numPrimitives: {data[db+sec_off+89]}")

# Primitives
prim_off = items[12]['data_off']
print(f"\nPrimitives ({items[12]['count']}):")
for i in range(items[12]['count']):
    b = data[db+prim_off+i*4 : db+prim_off+i*4+4]
    print(f"  [{i}] {b.hex()} indices=({b[0]},{b[1]},{b[2]}) extra={b[3]}")

# Packed vertices
pv_off = items[13]['data_off']
pv_count = items[13]['count']
dmin = struct.unpack_from('<fff', data, db+sec_off+16)
dmax = struct.unpack_from('<fff', data, db+sec_off+32)
print(f"\nPacked vertices ({pv_count}):")
for i in range(pv_count):
    v = data[db+pv_off+i*8 : db+pv_off+i*8+8]
    u16 = struct.unpack_from('<HHH', v, 0)
    x = dmin[0] + (u16[0]/65535.0)*(dmax[0]-dmin[0])
    y = dmin[1] + (u16[1]/65535.0)*(dmax[1]-dmin[1])
    z = dmin[2] + (u16[2]/65535.0)*(dmax[2]-dmin[2])
    print(f"  [{i}] {v.hex()} u16={u16} -> ({x:.4f}, {y:.4f}, {z:.4f})")

# SimdTree
st_off = items[15]['data_off']
print(f"\nSimdTree ({items[15]['count']} nodes):")
for i in range(items[15]['count']):
    n_off = db + st_off + i*128
    nd = data[n_off:n_off+128]
    is_leaf = nd[112]
    prims = struct.unpack_from('<IIII', nd, 96)
    print(f"  [{i}] leaf={is_leaf} prims/children={prims} active={nd[113]}")
    if is_leaf:
        # children AABBs
        for c in range(4):
            mn = struct.unpack_from('<fff', nd, c*24)
            mx = struct.unpack_from('<fff', nd, c*24+12)
            print(f"    child[{c}] min=({mn[0]:.3f},{mn[1]:.3f},{mn[2]:.3f}) max=({mx[0]:.3f},{mx[1]:.3f},{mx[2]:.3f})")

# Aabb4 tree
a4_off = items[16]['data_off']
a4_count = items[16]['count']
print(f"\nAabb4 tree ({a4_count} nodes):")
for i in range(a4_count):
    nd = data[db+a4_off+i*6 : db+a4_off+i*6+6]
    print(f"  [{i:2d}] {nd.hex()}")

# PrimitiveDataRun
pdr_off = items[14]['data_off']
print(f"\nPrimitiveDataRun @0x{pdr_off:x}: {data[db+pdr_off:db+pdr_off+8].hex()}")