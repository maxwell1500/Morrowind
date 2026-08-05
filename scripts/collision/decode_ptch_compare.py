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
    patches = lib.parse_ptch(data, by[b'PTCH'][0].body_off, by[b'PTCH'][0].body_end)
    print(f"\n{label} patches:")
    for p in patches:
        tname = types[p['type_idx']] if p['type_idx'] < len(types) else f"type{p['type_idx']}"
        print(f"  type={tname} n={len(p['offsets'])} offsets={p['offsets']}")
    # Decode each patch target around its offsets
    # Focus on bodyCinfoWithAttachment (type_idx 9 for kit, maybe same for crate)
    # and hknpMaterial
    for p in patches:
        if p['type_idx'] == 9:
            print(f"\n  bodyCinfoWithAttachment patches ({len(p['offsets'])}):")
            for off in p['offsets']:
                bo = db + off
                print(f"    off=0x{off:x}: {data[bo:bo+192].hex()}")
        if p['type_idx'] == 4:  # material
            print(f"\n  material patches ({len(p['offsets'])}):")
            for off in p['offsets']:
                mo = db + off
                print(f"    off=0x{off:x}: {data[mo:mo+80].hex()}")