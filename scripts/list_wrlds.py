import struct
data = open(r'C:\XboxGames\Starfield\Content\Data\Starfield.esm', 'rb').read()
wrlds = []
pos = 0
while pos < len(data) - 24:
    if data[pos:pos+4] == b'WRLD':
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        fid = struct.unpack('<I', data[pos+12:pos+16])[0]
        wrlds.append((pos, fid, size))
        pos += 24 + size
    elif data[pos:pos+4] == b'GRUP':
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]
    else:
        pos += 24 + struct.unpack('<I', data[pos+4:pos+8])[0]
print('WRLD records in Starfield.esm:')
for pos, fid, size in wrlds[:20]:
    print(f'  0x{fid:08X} size={size}')
