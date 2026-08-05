import struct

with open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb') as f:
    data = f.read()

# Read first STAT record and list all subrecords
pos = 183 + 24  # skip GRUP header
sig = data[pos:pos+4]
sz = struct.unpack_from('<I', data, pos+4)[0]
fid = struct.unpack_from('<I', data, pos+12)[0]
print(f'First STAT: FID=0x{fid:08X}, size={sz}')

sp = pos + 24
while sp < pos + 24 + sz - 6:
    ss = data[sp:sp+4]
    ssz = struct.unpack_from('<H', data, sp+4)[0]
    ss_name = ss.decode('ascii', errors='replace')
    
    content = data[sp+6:sp+6+ssz]
    if ss_name == 'EDID':
        print(f'  {ss_name} ({ssz}): {content.rstrip(b"\\x00").decode("ascii", errors="replace")}')
    elif ss_name == 'MODL':
        print(f'  {ss_name} ({ssz}): {content.rstrip(b"\\x00").decode("ascii", errors="replace")}')
    elif ss_name in ('OBND',):
        vals = struct.unpack_from('<6h', content)
        print(f'  {ss_name} ({ssz}): {vals}')
    elif ss_name in ('ODTY', 'FLLD'):
        val = struct.unpack_from('<I', content)[0]
        print(f'  {ss_name} ({ssz}): 0x{val:08X} ({val})')
    elif ss_name == 'DNAM':
        a, b = struct.unpack_from('<2f', content)
        print(f'  {ss_name} ({ssz}): ({a}, {b})')
    elif ss_name == 'BFCB':
        print(f'  {ss_name} ({ssz}): {content}')
    elif ss_name == 'BFCE':
        print(f'  {ss_name} ({ssz}): {content.hex() if ssz > 0 else "(empty)"}')
    else:
        print(f'  {ss_name} ({ssz}): {content.hex()[:40]}')
    
    sp += 6 + ssz
