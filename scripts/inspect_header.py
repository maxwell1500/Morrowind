import struct
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
print('First 128 bytes hex:')
print(data[:128].hex())
print('sig:', data[:4])
print('size:', struct.unpack('<I', data[4:8])[0])
print('flags:', struct.unpack('<I', data[8:12])[0])
print('fid:', struct.unpack('<I', data[12:16])[0])
print('ver:', struct.unpack('<I', data[16:20])[0])
print('unk:', struct.unpack('<I', data[20:24])[0])
print('Total file size:', len(data))
# Manual scan for signatures
sigs = [b'STAT', b'CELL', b'REFR', b'WRLD', b'GRUP']
for sig in sigs:
    print(f'{sig.decode()}: {data.count(sig)} occurrences (naive)')
# Show first few 4-byte signatures
for i in range(0, min(200, len(data)-4), 4):
    s = data[i:i+4]
    if s in [b'STAT', b'CELL', b'REFR', b'WRLD', b'GRUP', b'TES4']:
        print(f'offset {i}: {s}')
