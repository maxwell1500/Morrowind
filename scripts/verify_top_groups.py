import struct
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
# Parse top-level groups
pos = 24 + struct.unpack('<I', data[4:8])[0]
print('Top-level groups start at', pos)
while pos < len(data):
    sig = data[pos:pos+4].decode()
    size = struct.unpack('<I', data[pos+4:pos+8])[0]
    label = data[pos+8:pos+12]
    gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
    print(f'{sig} at 0x{pos:x} size={size} label={label} type={gtype}')
    if sig != 'GRUP':
        print('  ERROR: not a GRUP')
        break
    pos += size
print('End of top-level groups at', pos)
