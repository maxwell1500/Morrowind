import struct
for path in [r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm']:
    print('===', path, '===')
    data = open(path, 'rb').read()
    pos = 24 + struct.unpack('<I', data[4:8])[0]
    while pos < len(data):
        sig = data[pos:pos+4].decode('ascii', errors='replace')
        if sig == 'GRUP' and data[pos+8:pos+12] == b'STAT':
            inner = pos + 24
            gend = pos + struct.unpack('<I', data[pos+4:pos+8])[0]
            cnt = 0
            while inner < gend and cnt < 5:
                rsig = data[inner:inner+4].decode('ascii', errors='replace')
                rsize = struct.unpack('<I', data[inner+4:inner+8])[0]
                rfid = struct.unpack('<I', data[inner+12:inner+16])[0]
                body = data[inner+24:inner+24+rsize]
                sub = 0
                while sub < len(body):
                    ssig = body[sub:sub+4].decode('ascii', errors='replace')
                    sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                    if ssig == 'EDID':
                        edid = body[sub+6:sub+6+sln]
                        print(f'  0x{rfid:08X}: {edid}')
                        break
                    sub += 6 + sln
                inner += 24 + rsize
                cnt += 1
            break
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]
