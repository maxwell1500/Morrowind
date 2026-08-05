import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib

NIF = r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif'
with open(NIF, 'rb') as f: data = f.read()
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
by_fcc = {}
def idx(c):
    by_fcc.setdefault(c.fourcc, []).append(c)
    for ch in c.children: idx(ch)
for c in chunks: idx(c)
dc = by_fcc[b'DATA'][0]
db = dc.body_off
print('bodyCinfo at 0xc0 (static kitchenette):')
print(data[db+0xc0:db+0xc0+192].hex())
print('motionType at +40:', data[db+0xc0+40])