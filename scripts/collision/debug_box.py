import struct, sys
sys.path.insert(0, r'C:\Users\max\Projects\Morrowind\scripts\collision')
import hk_decode_lib as lib

nif = r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_nord_house_01.nif'
with open(nif, 'rb') as f:
    data = f.read()

def le32(buf, off): return struct.unpack_from('<I', buf, off)[0]
def le16(buf, off): return struct.unpack_from('<H', buf, off)[0]

p = 0
assert data[:38] == b'Gamebryo File Format, Version 20.2.0.7'
p += 38 + 5 + 1 + 4
num_blocks = le32(data, p); p+=4
p+=4; aL=data[p]; p+=1+aL; p+=4; psL=data[p]; p+=1+psL; u2L=data[p]; p+=1+u2L
num_types=le16(data,p); p+=2
blk_types=[]
for _ in range(num_types):
    L=le32(data,p); p+=4
    blk_types.append(data[p:p+L].decode('latin-1')); p+=L
blk_ti=[le16(data,p+i*2) for i in range(num_blocks)]; p+=num_blocks*2
blk_sizes=[le32(data,p+i*4) for i in range(num_blocks)]; p+=num_blocks*4
p+=4; p+=4
for _ in range(le32(data,p-8)):
    L=le32(data,p); p+=4+L
p+=4
header_end=p

phys_idx = next(i for i in range(num_blocks) if blk_types[blk_ti[i]]=='bhkPhysicsSystem')
blk_off = header_end + sum(blk_sizes[:phys_idx])
data_len = le32(data, blk_off)
tag0_start = blk_off + 4

chunks = lib.walk_tag0(data, tag0_start, tag0_start+data_len)
by_fcc = {}
def idx(c):
    by_fcc.setdefault(c.fourcc, []).append(c)
    for ch in c.children: idx(ch)
for c in chunks: idx(c)

data_c = by_fcc[b'DATA'][0]
body = data_c.body_off

verts = []
for i in range(8):
    off = body + 0x230 + i*12
    x,y,z = struct.unpack_from('<fff', data, off)
    verts.append((x,y,z))

print(f'Box vertices:')
for v in verts:
    print(f'  ({v[0]:.2f}, {v[1]:.2f}, {v[2]:.2f})')
xs = [v[0] for v in verts]; ys = [v[1] for v in verts]; zs = [v[2] for v in verts]
print(f'Extent: X={max(xs)-min(xs):.2f} Y={max(ys)-min(ys):.2f} Z={max(zs)-min(zs):.2f}')
