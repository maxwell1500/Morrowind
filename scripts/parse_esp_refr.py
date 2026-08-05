import struct

with open(r'C:\XboxGames\Starfield\Content\Data\SeydaNeen2.esp', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')

# Find REFR records (only look at first 5000 bytes for now)
pos = 0
refs_found = 0
while pos < 5000 and refs_found < 10:
    if data[pos:pos+4] == b'REFR':
        formid = struct.unpack_from('<I', data, pos+12)[0]
        data_size = struct.unpack_from('<I', data, pos+4)[0]
        flags = struct.unpack_from('<I', data, pos+8)[0]
        print(f'REFR at offset {pos}, FormID: 0x{formid:08X}, size: {data_size}')
        
        # Print hex dump of REFR data
        print(f'  Hex: {data[pos+24:pos+24+min(48, data_size)].hex()}')
        pos = pos + 24 + data_size
        refs_found += 1
    pos += 1
