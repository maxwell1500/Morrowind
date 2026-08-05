import struct, zlib

data = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()
pos = 24 + struct.unpack('<I', data[4:8])[0]
while pos < len(data):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    if sig == 'GRUP' and data[pos+8:pos+12] == b'CELL':
        print(f'Top-level CELL group at 0x{pos:x}')
        inner = pos + 24
        gend = pos + struct.unpack('<I', data[pos+4:pos+8])[0]
        cnt = 0
        while inner < gend and cnt < 20:
            # block group
            if data[inner:inner+4] == b'GRUP':
                inner2 = inner + 24
                gend2 = inner + struct.unpack('<I', data[inner+4:inner+8])[0]
                while inner2 < gend2 and cnt < 20:
                    if data[inner2:inner2+4] == b'CELL':
                        size = struct.unpack('<I', data[inner2+4:inner2+8])[0]
                        flags = struct.unpack('<I', data[inner2+8:inner2+12])[0]
                        fid = struct.unpack('<I', data[inner2+12:inner2+16])[0]
                        body = data[inner2+24:inner2+24+size]
                        if flags & 0x00040000:
                            body = zlib.decompress(body[4:])
                        sub = 0
                        x=y=None
                        while sub < len(body):
                            ssig = body[sub:sub+4].decode('ascii', errors='replace')
                            sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                            if ssig == 'XCLC':
                                x,y,_ = struct.unpack('<iii', body[sub+6:sub+6+sln])
                                break
                            sub += 6 + sln
                        if x is not None:
                            print(f'  CELL 0x{fid:08X} grid ({x}, {y})')
                            cnt += 1
                        inner2 += 24 + size
                    else:
                        inner2 += 24 + struct.unpack('<I', data[inner2+4:inner2+8])[0]
                inner += struct.unpack('<I', data[inner+4:inner+8])[0]
            else:
                inner += 24 + struct.unpack('<I', data[inner+4:inner+8])[0]
        break
    pos += struct.unpack('<I', data[pos+4:pos+8])[0]
