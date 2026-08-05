import struct, sys
sys.path.insert(0, r'C:\Users\max\Projects\Morrowind\scripts\collision')
import hk_decode_lib as lib

nif_path = r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_de_docks_center.nif'
with open(nif_path, 'rb') as f:
    data = f.read()

def le32(buf, off): return struct.unpack_from('<I', buf, off)[0]
def le16(buf, off): return struct.unpack_from('<H', buf, off)[0]

p = 0
assert data[:38] == b'Gamebryo File Format, Version 20.2.0.7'
p += 38 + 5 + 1 + 4
num_blocks = le32(data, p); p+=4
p += 4  # bs_version
aL = data[p]; p+=1+aL
p+=4  # unk1
psL=data[p]; p+=1+psL
u2L=data[p]; p+=1+u2L
num_types=le16(data,p); p+=2
blk_types=[]
for _ in range(num_types):
    L=le32(data,p); p+=4
    blk_types.append(data[p:p+L].decode('latin-1')); p+=L
blk_ti=[le16(data,p+i*2) for i in range(num_blocks)]; p+=num_blocks*2
blk_sizes=[le32(data,p+i*4) for i in range(num_blocks)]; p+=num_blocks*4
p+=4  # num_strings
p+=4  # max_sl
for _ in range(le32(data,p-8)):
    L=le32(data,p); p+=4+L
p+=4  # num_groups
header_end=p

print(f'Blocks: {num_blocks}')
for i in range(num_blocks):
    print(f'  [{i}] {blk_types[blk_ti[i]]} ({blk_sizes[i]}B)')

phys_idx = next(i for i in range(num_blocks) if blk_types[blk_ti[i]]=='bhkPhysicsSystem')
blk_off = header_end + sum(blk_sizes[:phys_idx])
data_len = le32(data, blk_off)
tag0_start = blk_off + 4

chunks = lib.walk_tag0(data, tag0_start, tag0_start+data_len)
def show(c, depth=0):
    pref = '  '*depth
    print(f'{pref}{c.fourcc.decode()} @0x{c.abs_off:x} size={c.size}')
    for ch in c.children:
        show(ch, depth+1)
for c in chunks:
    show(c)

chunks_by_fcc = {}
def idx(c):
    chunks_by_fcc.setdefault(c.fourcc, []).append(c)
    for ch in c.children: idx(ch)
for c in chunks: idx(c)

item_c = chunks_by_fcc[b'ITEM'][0]
items = lib.parse_item(data, item_c.body_off, item_c.body_end)
print(f'\nItems ({len(items)}):')
for it in items:
    print(f"  [{it['i']}] type_idx={it['type_idx']} data_off=0x{it['data_off']:x} count={it['count']} flags={it['flags']}")
