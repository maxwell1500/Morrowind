import struct, sys
path = sys.argv[1] if len(sys.argv) > 1 else r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_nord_house_03.nif.bak'
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
print(f'{path.split(chr(92))[-1]}: {nb} blocks, {len(d)}B')
cur = he
for i in range(nb):
    tn = types[ti[i]]
    print(f'  [{i}] {tn} off=0x{cur:x} size={sizes[i]}')
    if tn in ('NiNode', 'BSXFlags', 'bhkCollisionObject', 'bhkRigidBody', 'bhkConvexVerticesShape', 'bhkNPCollisionObject'):
        blk = d[cur:cur+min(sizes[i], 64)]
        print(f'      first bytes: {blk.hex()}')
    cur += sizes[i]
footer = d[cur:]
print(f'footer ({len(footer)}B): {footer.hex()}')