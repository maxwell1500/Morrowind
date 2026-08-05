import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib

for label, path in [('crate', r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_CrewChest01.nif'),
                    ('kit',   r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif')]:
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
    print(f"\n{label}")
    print('Items:')
    for it in items:
        print(f"  [{it['i']}] ti={it['type_idx']} off=0x{it['data_off']:x} count={it['count']} flags={it['flags']}")
    print('PhysicsSystemData @0:')
    print('  bytes 0-128:', data[db:db+128].hex())
    for off, name in [(24, 'materials'), (40, 'motionProperties'), (56, 'bodyCinfos')]:
        ref = struct.unpack_from('<I', data, db+off)[0]
        size = struct.unpack_from('<i', data, db+off+8)[0]
        cap = struct.unpack_from('<i', data, db+off+12)[0]
        print(f'  {name}: ref={ref} size={size} cap={cap}')