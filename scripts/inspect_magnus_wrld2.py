import struct, zlib
data = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()
pos = 0
while pos < len(data) - 24:
    if data[pos:pos+4] == b'WRLD':
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        flags = struct.unpack('<I', data[pos+8:pos+12])[0]
        formid = struct.unpack('<I', data[pos+12:pos+16])[0]
        if formid == 0x0100E1C8:
            body = data[pos+24:pos+24+size]
            if flags & 0x00040000:
                unc_len = struct.unpack('<I', body[:4])[0]
                body = zlib.decompress(body[4:])
            sub = 0
            while sub < len(body):
                ssig = body[sub:sub+4].decode('ascii', errors='replace')
                sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                sdata = body[sub+6:sub+6+sln]
                print(f'{ssig} len={sln} hex={sdata[:64].hex()}')
                sub += 6 + sln
            break
        pos += 24 + size
    else:
        pos += 1
