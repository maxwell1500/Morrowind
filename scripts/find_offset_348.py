import struct
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
pos = 0
i = 0
while pos < len(data) and i < 5:
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    if sig == 'GRUP':
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        print(f'0x{pos:x}: GRUP size={size}')
        pos += size
    else:
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        flags = struct.unpack('<I', data[pos+8:pos+12])[0]
        formid = struct.unpack('<I', data[pos+12:pos+16])[0]
        print(f'0x{pos:x}: {sig} size={size} flags=0x{flags:08X} formid=0x{formid:08X}')
        pos += 16 + size
    i += 1
print(f'Offset 0x15c=348 is at:')
print(data[348:348+16].hex())
print('context:', data[340:360].hex())
