"""Compare the cloned ex_nord_house_03 NIF's physics system against the donor
kitchenette. Look for any difference that could cause CK/game to reject it.
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib

def le32(buf, off): return struct.unpack_from("<I", buf, off)[0]
def le16(buf, off): return struct.unpack_from("<H", buf, off)[0]

def parse_header(data):
    p = 38+5+1+4
    nb = le32(data, p); p += 4
    p += 4
    aL = data[p]; p += 1+aL+4
    psL = data[p]; p += 1+psL
    u2L = data[p]; p += 1+u2L
    nt = le16(data, p); p += 2
    types = []
    for _ in range(nt):
        L = le32(data, p); p += 4
        types.append(data[p:p+L].decode("latin-1")); p += L
    ti = [le16(data, p+i*2)[0] for i in range(nb)] if False else [le16(data, p+i*2) for i in range(nb)]; p += nb*2
    sizes = [le32(data, p+i*4) for i in range(nb)]; p += nb*4
    ns = le32(data, p); p += 4
    p += 4
    for _ in range(ns):
        L = le32(data, p); p += 4+L
    p += 4
    he = p
    return nb, types, ti, sizes, he

def get_phys_block(data):
    nb, types, ti, sizes, he = parse_header(data)
    phys_idx = next(i for i in range(nb) if types[ti[i]] == "bhkPhysicsSystem")
    blk_off = he + sum(sizes[:phys_idx])
    return blk_off, sizes[phys_idx]

def get_bhknp_block(data):
    nb, types, ti, sizes, he = parse_header(data)
    idx = next(i for i in range(nb) if types[ti[i]] == 'bhkNPCollisionObject')
    off = he + sum(sizes[:idx])
    return off, sizes[idx], idx

DONOR = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif"
CLONED = r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_nord_house_03.nif"

with open(DONOR, "rb") as f: d_don = f.read()
with open(CLONED, "rb") as f: d_clo = f.read()

# Compare bhkNPCollisionObject
don_off, don_sz, don_idx = get_bhknp_block(d_don)
clo_off, clo_sz, clo_idx = get_bhknp_block(d_clo)
print(f"Donor bhkNP [{don_idx}] {don_sz}B: {d_don[don_off:don_off+don_sz].hex()}")
print(f"Cloned bhkNP [{clo_idx}] {clo_sz}B: {d_clo[clo_off:clo_off+clo_sz].hex()}")
# Diff
don_np = d_don[don_off:don_off+don_sz]
clo_np = d_clo[clo_off:clo_off+clo_sz]
print("Diff (offset: donor cloned):")
for i in range(min(len(don_np), len(clo_np))):
    if don_np[i] != clo_np[i]:
        print(f"  [{i}] 0x{don_np[i]:02x} vs 0x{clo_np[i]:02x}")

# Compare bhkPhysicsSystem byte-by-byte (after the first 4-byte data_len)
don_poff, don_psz = get_phys_block(d_don)
clo_poff, clo_psz = get_phys_block(d_clo)
print(f"\nDonor phys block {don_psz}B, cloned {clo_psz}B (equal: {don_psz == clo_psz})")
don_phys = d_don[don_poff:don_poff+don_psz]
clo_phys = d_clo[clo_poff:clo_poff+clo_psz]
diffs = []
for i in range(min(len(don_phys), len(clo_phys))):
    if don_phys[i] != clo_phys[i]:
        diffs.append((i, don_phys[i], clo_phys[i]))
print(f"Diff bytes: {len(diffs)}")
if diffs:
    print("First 30 diffs (offset: donor cloned):")
    for (i, a, b) in diffs[:30]:
        print(f"  0x{i:04x}: 0x{a:02x} vs 0x{b:02x}")

# Also check the NiNode collision ref
nb, types, ti, sizes, he = parse_header(d_clo)
ni_off = he
ni_num_extra = le32(d_clo, ni_off + 4)
coll_off = ni_off + 8 + 4*ni_num_extra + 60
print(f"\nCloned NiNode collision_object_ref at 0x{coll_off:x}: {le32(d_clo, coll_off)}")
print(f"  (should be bhkNP block idx = {clo_idx})")