import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib

def dump_tbd_data(path):
    with open(path, 'rb') as f: data = f.read()
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
    type_names = lib.parse_tst1(data, by[b'TST1'][0].body_off, by[b'TST1'][0].body_end)
    field_names = lib.parse_fst1(data, by[b'FST1'][0].body_off, by[b'FST1'][0].body_end)
    classes = lib.parse_tna1(data, by[b'TNA1'][0].body_off, by[b'TNA1'][0].body_end, type_names)
    lib.parse_tbdy(data, by[b'TBDY'][0].body_off, by[b'TBDY'][0].body_end, classes, field_names)
    print(f"\n=== {path} ===")
    print("Item types:")
    for it in items:
        c = classes[it['type_idx']]
        print(f"  [{it['i']}] {c.name} off=0x{it['data_off']:x} count={it['count']}")
    return data, db, items

dump_tbd_data(r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_CrewChest01.nif")
dump_tbd_data(r"C:\XboxGames\Starfield\Content\Data\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif")