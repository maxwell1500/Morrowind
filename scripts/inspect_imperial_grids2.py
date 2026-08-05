import struct, zlib
data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
grids = {}
pos = 24 + struct.unpack('<I', data[4:8])[0]
while pos < len(data) - 24:
    sig = data[pos:pos+4]
    if sig == b'CELL':
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        flags = struct.unpack('<I', data[pos+8:pos+12])[0]
        body = data[pos+24:pos+24+size]
        if flags & 0x00040000:
            unc_len = struct.unpack('<I', body[:4])[0]
            body = zlib.decompress(body[4:])
        sub = 0
        while sub < len(body) - 8:
            ssig = body[sub:sub+4]
            sln = struct.unpack('<H', body[sub+4:sub+6])[0]
            if ssig == b'XCLC':
                gx, gy, _ = struct.unpack('<iii', body[sub+6:sub+6+sln])
                grids[(gx, gy)] = grids.get((gx, gy), 0) + 1
                break
            sub += 6 + sln
        pos += 24 + size
    elif sig == b'GRUP':
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]
    else:
        pos += 24 + struct.unpack('<I', data[pos+4:pos+8])[0]
print('ImperialCity grids:')
for k, v in sorted(grids.items()):
    print(f'  {k}: {v}')
