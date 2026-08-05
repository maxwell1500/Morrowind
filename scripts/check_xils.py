import struct, zlib

data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 24 + struct.unpack('<I', data[4:8])[0]
found = 0
while pos < len(data) - 24 and found < 5:
    sig = data[pos:pos+4]
    if sig == b'CELL':
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        flags = struct.unpack('<I', data[pos+8:pos+12])[0]
        fid = struct.unpack('<I', data[pos+12:pos+16])[0]
        body = data[pos+24:pos+24+size]
        if flags & 0x00040000:
            try:
                body = zlib.decompress(body[4:])
            except Exception:
                body = b''
        sub = 0
        while sub < len(body):
            ssig = body[sub:sub+4].decode('ascii', errors='replace')
            sln = struct.unpack('<H', body[sub+4:sub+6])[0]
            sdata = body[sub+6:sub+6+sln]
            if ssig == 'XILS':
                val = struct.unpack('<I', sdata)[0] if sln == 4 else None
                print('CELL 0x%08X XILS len=%d value=0x%08X' % (fid, sln, val or 0))
                found += 1
            sub += 6 + sln
        pos += 24 + size
    elif sig == b'GRUP':
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]
    else:
        pos += 24 + struct.unpack('<I', data[pos+4:pos+8])[0]
