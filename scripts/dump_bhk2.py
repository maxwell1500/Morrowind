import struct

new = open(r'C:\Users\max\Projects\Morrowind\ex_nord_house_03.nif', 'rb').read()

# bhk data: @244 to @484 (240 bytes)
bhk = new[244:484]
print(f'bhk data: {len(bhk)} bytes')
print('Hex dump:')
for i in range(0, len(bhk), 16):
    chunk = bhk[i:i+16]
    hex_str = ' '.join(f'{b:02x}' for b in chunk)
    print(f'  +{i:3d}: {hex_str}')

# Look at the data as uint32
print('\nAs uint32:')
for i in range(0, len(bhk), 4):
    val = struct.unpack('<I', bhk[i:i+4])[0]
    print(f'  +{i:3d}: 0x{val:08X} = {val}')

# Look at the data as float (some might be transform data)
print('\nAs float:')
for i in range(0, len(bhk), 4):
    val = struct.unpack('<f', bhk[i:i+4])[0]
    print(f'  +{i:3d}: {val}')
