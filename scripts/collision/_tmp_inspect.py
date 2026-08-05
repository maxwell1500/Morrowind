import struct
with open(r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_CrewChest01.nif','rb') as f: d=f.read()
print('magic:', d[:38])
print('bytes 38-60:', d[38:60].hex())
p=38+5+1+4
print('num_blocks at', p, '=', struct.unpack_from('<I',d,p)[0])
p+=4
print('bs_ver at', p, '=', struct.unpack_from('<I',d,p)[0])
p+=4
aL=d[p]; print('author_len at', p, '=', aL); p+=1+aL
print('unk1 at', p, '=', hex(struct.unpack_from('<I',d,p)[0])); p+=4
psL=d[p]; print('ps_len at', p, '=', psL); p+=1+psL
u2L=d[p]; print('u2_len at', p, '=', u2L); p+=1+u2L
print('num_types at', p, '=', struct.unpack_from('<H',d,p)[0])
print('byte at', p-1, '=', hex(d[p-1]))
print('hex around:', d[p-4:p+8].hex())