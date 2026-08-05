import struct
with open(r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_nord_house_03.nif.bak','rb') as f: d=f.read()
p=38+5+1+4
nb=struct.unpack_from('<I',d,p)[0]; p+=4+4
aL=d[p]; p+=1+aL+4
psL=d[p]; p+=1+psL
u2L=d[p]; p+=1+u2L
nt=struct.unpack_from('<H',d,p)[0]; p+=2
types=[]
for _ in range(nt):
    L=struct.unpack_from('<I',d,p)[0]; p+=4
    types.append(d[p:p+L].decode()); p+=L
ti=[struct.unpack_from('<H',d,p+i*2)[0] for i in range(nb)]; p+=nb*2
sizes=[struct.unpack_from('<I',d,p+i*4)[0] for i in range(nb)]; p+=nb*4
ns=struct.unpack_from('<I',d,p)[0]; p+=4+4
for _ in range(ns):
    L=struct.unpack_from('<I',d,p)[0]; p+=4+L
p+=4
he=p
print('bak blocks:', nb, 'NiNode size:', sizes[0])
ni = d[he:he+sizes[0]]
print('bak NiNode:')
for i in range(0, len(ni), 16):
    print(f'  {i:04x}: {ni[i:i+16].hex()}')
print('val at 0x48:', hex(struct.unpack_from('<I', ni, 0x48)[0]))
print('num_extra at 0x04:', struct.unpack_from('<I', ni, 4)[0])
# Compute what the script did: ni_off + 8 + 4*num_extra + 60
num_extra = struct.unpack_from('<I', ni, 4)[0]
print(f'script offset: 8 + 4*{num_extra} + 60 = {8 + 4*num_extra + 60}')
print(f'NiNode size: {sizes[0]}')