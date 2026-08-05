import struct
with open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen_Minimal.esp', 'rb') as f:
    data = f.read()
sig = data[0:4]
dsz = struct.unpack_from('<I', data, 4)[0]
flags = struct.unpack_from('<I', data, 8)[0]
print(f'TES4 sig={sig} data_size={dsz} flags=0x{flags:08X}')
print(f'First record at offset {24+dsz}: {data[24+dsz:24+dsz+4]}')
pos = 0
while pos < len(data):
    s = data[pos:pos+4]
    if s == b'GRUP':
        gs = struct.unpack_from('<I', data, pos+4)[0]
        gt = struct.unpack_from('<I', data, pos+12)[0]
        print(f'GRUP type={gt} @ {pos} size={gs}')
        pos += gs
    elif s in (b'TES4', b'STAT', b'WRLD', b'CELL', b'REFR'):
        sz = struct.unpack_from('<I', data, pos+4)[0]
        fid = struct.unpack_from('<I', data, pos+12)[0]
        print(f'{s.decode()} FID=0x{fid:08X} @ {pos} size={sz}')
        pos += 24 + sz
    else:
        print(f'Unknown @ {pos}: {s.hex()}')
        break
print(f'Final: {pos}/{len(data)} OK={pos==len(data)}')
