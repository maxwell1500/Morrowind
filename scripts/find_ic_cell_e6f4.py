import struct, zlib
data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 0
count = 0
while pos < len(data) - 24:
    if data[pos:pos+4] == b'CELL':
        fid = struct.unpack('<I', data[pos+12:pos+16])[0]
        if fid == 0x0100E6F4:
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            flags = struct.unpack('<I', data[pos+8:pos+12])[0]
            print(f'Found CELL 0x{fid:08X} at 0x{pos:x} size={size} flags=0x{flags:08X}')
            body = data[pos+24:pos+24+size]
            if flags & 0x00040000:
                body = zlib.decompress(body[4:])
            sub = 0
            while sub < len(body):
                ssig = body[sub:sub+4].decode('ascii', errors='replace')
                sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                payload = body[sub+6:sub+6+sln]
                if ssig == 'XCLC':
                    x,y,z = struct.unpack('<iii', payload)
                    print(f'  XCLC ({x}, {y}, {z})')
                elif ssig in ('EDID','FULL'):
                    print(f'  {ssig} {payload}')
                sub += 6 + sln
            count += 1
    pos += 1
print(f'Total matches: {count}')
