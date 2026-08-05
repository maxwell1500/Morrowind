"""Verify primitive size: item 12 at 0x3c0 count=18, item 13 at 0x410 count=6.
Gap = 0x410 - 0x3c0 = 80 bytes. 80/18 = 4.44 (not integer).
So either 4 bytes/prim + padding, or something else.
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
items = lib.parse_item(data, by_fcc[b"ITEM"][0].body_off, by_fcc[b"ITEM"][0].body_end)
db = dc.body_off

# Print item data_off and count to compute sizes
print("Item layout (data_off, count, implied size):")
for it in items:
    if it['count'] > 0:
        print(f"  [{it['i']:2d}] off=0x{it['data_off']:04x} count={it['count']}")

# Compute gaps between consecutive items
sorted_items = sorted([it for it in items if it['count'] > 0], key=lambda x: x['data_off'])
print("\nGaps between items:")
for i in range(len(sorted_items)-1):
    cur = sorted_items[i]
    nxt = sorted_items[i+1]
    gap = nxt['data_off'] - cur['data_off']
    per_elem = gap / cur['count'] if cur['count'] else 0
    print(f"  [{cur['i']:2d}] off=0x{cur['data_off']:04x} count={cur['count']} -> next at 0x{nxt['data_off']:04x} gap={gap} per_elem={per_elem:.2f}")

# Last item to end of DATA
last = sorted_items[-1]
db_size = dc.size - 8
gap = db_size - last['data_off']
per_elem = gap / last['count'] if last['count'] else 0
print(f"  [{last['i']:2d}] off=0x{last['data_off']:04x} count={last['count']} -> DATA end 0x{db_size:04x} gap={gap} per_elem={per_elem:.2f}")

# Dump primitives as 4-byte each
print(f"\nPrimitives as 4-byte each (18 triangles):")
for i in range(18):
    off = db + 0x3c0 + i*4
    b = data[off:off+4]
    print(f"  [{i:2d}] {b.hex()} = u8 {list(b)}")

# Dump the padding after 18*4=72 bytes
pad_off = db + 0x3c0 + 72
print(f"\nPadding at 0x{pad_off-db:04x} (after 72 bytes): {data[pad_off:pad_off+8].hex()}")