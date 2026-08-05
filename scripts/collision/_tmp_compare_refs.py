import struct, sys
sys.path.insert(0, r'C:\Users\max\Projects\Morrowind\scripts\collision')
import hk_decode_lib as lib

for label, path in [
    ('donor', r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif'),
    ('cloned', r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_nord_house_03.nif'),
]:
    with open(path, 'rb') as f: d = f.read()
    p = 38+5+1+4
    nb = struct.unpack_from('<I', d, p)[0]; p += 4+4
    aL = d[p]; p += 1+aL+4
    psL = d[p]; p += 1+psL
    u2L = d[p]; p += 1+u2L
    nt = struct.unpack_from('<H', d, p)[0]; p += 2
    types = []
    for _ in range(nt):
        L = struct.unpack_from('<I', d, p)[0]; p += 4
        types.append(d[p:p+L].decode()); p += L
    ti = [struct.unpack_from('<H', d, p+i*2)[0] for i in range(nb)]; p += nb*2
    sizes = [struct.unpack_from('<I', d, p+i*4)[0] for i in range(nb)]; p += nb*4
    ns = struct.unpack_from('<I', d, p)[0]; p += 4+4
    for _ in range(ns):
        L = struct.unpack_from('<I', d, p)[0]; p += 4+L
    p += 4
    he = p
    pi = next(i for i in range(nb) if types[ti[i]] == 'bhkPhysicsSystem')
    off = he + sum(sizes[:pi])
    dlen = struct.unpack_from('<I', d, off)[0]
    chunks = lib.walk_tag0(d, off+4, off+4+dlen)
    by = {}
    def idx(c):
        by.setdefault(c.fourcc, []).append(c)
        for ch in c.children: idx(ch)
    for c in chunks: idx(c)
    dc = by[b'DATA'][0]
    items = lib.parse_item(d, by[b'ITEM'][0].body_off, by[b'ITEM'][0].body_end)

    bcinfo_item = next(i for i in items if i['i'] == 3)
    bo = dc.body_off + bcinfo_item['data_off']
    print(f"{label}: bodyCinfo at DATA+0x{bcinfo_item['data_off']:x}")
    shape_ref = struct.unpack_from('<I', d, bo)[0]
    print(f"  shape_ref (item idx): {shape_ref}")
    flags = struct.unpack_from('<I', d, bo+8)[0]
    print(f"  flags: 0x{flags:08x}")
    mt = d[bo+40]
    print(f"  motionType: {mt}")

    shape_item = next(i for i in items if i['i'] == 4)
    so = dc.body_off + shape_item['data_off']
    data_ref = struct.unpack_from('<I', d, so+64)[0]
    print(f"  shape.data_ref (item idx): {data_ref}")

    # Check item 5 (RefCountedProperties) and item 7/8 (entries)
    rcp_item = next(i for i in items if i['i'] == 5)
    ro = dc.body_off + rcp_item['data_off']
    print(f"  RefCountedProperties at DATA+0x{rcp_item['data_off']:x}")
    # entries hkArray at offset 24: m_data (ptr=4), m_size (4), m_cap (4)
    entries_data = struct.unpack_from('<I', d, ro+24)[0]
    entries_size = struct.unpack_from('<i', d, ro+32)[0]
    print(f"    entries: data_ref={entries_data} size={entries_size}")

    # PTCH analysis
    patches = lib.parse_ptch(d, by[b'PTCH'][0].body_off, by[b'PTCH'][0].body_end)
    print(f"  Patches: {len(patches)}")
    print()