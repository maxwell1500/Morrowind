import struct
with open(r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_nord_house_03.nif','rb') as f: d=f.read()
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
print('blocks:', nb, 'header_end:', hex(he))
ni = d[he:he+sizes[0]]
print('cloned NiNode:')
for i in range(0, len(ni), 16):
    print(f'  {i:04x}: {ni[i:i+16].hex()}')
print('val at 0x48:', struct.unpack_from('<I', ni, 0x48)[0])
print('num_extra at 0x04:', struct.unpack_from('<I', ni, 4)[0])
num_extra = struct.unpack_from('<I', ni, 4)[0]
script_off = 8 + 4*num_extra + 60
print(f'script wrote at NiNode offset {script_off} (0x{script_off:x})')
print(f'NiNode size: {sizes[0]}, value there: {struct.unpack_from("<I", ni, script_off)[0] if script_off+4 <= sizes[0] else "OUT OF BOUNDS"}')
print()
print('Block list:')
cur=he
for i in range(nb):
    tn=types[ti[i]]
    if tn in ('NiNode','BSXFlags','bhkNPCollisionObject','bhkPhysicsSystem'):
        print(f'  [{i}] {tn} off=0x{cur:x} size={sizes[i]}')
    cur+=sizes[i]