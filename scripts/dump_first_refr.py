import struct, zlib

def dump_first_refr(path):
    data = open(path, 'rb').read()
    pos = 24 + struct.unpack('<I', data[4:8])[0]
    while pos < len(data):
        sig = data[pos:pos+4].decode('ascii', errors='replace')
        if sig == 'GRUP' and data[pos+8:pos+12] == b'CELL':
            inner = pos + 24
            gend = pos + struct.unpack('<I', data[pos+4:pos+8])[0]
            while inner < gend:
                if data[inner:inner+4] == b'GRUP':
                    inner2 = inner + 24
                    gend2 = inner + struct.unpack('<I', data[inner+4:inner+8])[0]
                    while inner2 < gend2:
                        if data[inner2:inner2+4] == b'CELL':
                            # cell found, look for children GRUP
                            csize = struct.unpack('<I', data[inner2+4:inner2+8])[0]
                            cflags = struct.unpack('<I', data[inner2+8:inner2+12])[0]
                            cfid = struct.unpack('<I', data[inner2+12:inner2+16])[0]
                            print(f'CELL at 0x{inner2:x} size={csize} flags=0x{cflags:08X} fid=0x{cfid:08X}')
                            cend = inner2 + 24 + csize
                            inner3 = cend
                            # after cell record should be children GRUP
                            if data[inner3:inner3+4] == b'GRUP':
                                cgend = inner3 + struct.unpack('<I', data[inner3+4:inner3+8])[0]
                                inner4 = inner3 + 24
                                while inner4 < cgend:
                                    if data[inner4:inner4+4] == b'GRUP':
                                        # persistent group
                                        pgend = inner4 + struct.unpack('<I', data[inner4+4:inner4+8])[0]
                                        inner5 = inner4 + 24
                                        while inner5 < pgend:
                                            if data[inner5:inner5+4] == b'REFR':
                                                rsize = struct.unpack('<I', data[inner5+4:inner5+8])[0]
                                                rfid = struct.unpack('<I', data[inner5+12:inner5+16])[0]
                                                print(f'  REFR at 0x{inner5:x} size={rsize} fid=0x{rfid:08X}')
                                                body = data[inner5+24:inner5+24+rsize]
                                                sub = 0
                                                while sub < len(body):
                                                    ssig = body[sub:sub+4].decode('ascii', errors='replace')
                                                    sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                                                    payload = body[sub+6:sub+6+sln]
                                                    if ssig in ('EDID','NAME','DATA','XSCL'):
                                                        print(f'    {ssig} len={sln} {payload[:40].hex() if ssig=="DATA" else payload[:40]}')
                                                    sub += 6 + sln
                                                return
                                            inner5 += 24 + struct.unpack('<I', data[inner5+4:inner5+8])[0]
                                    inner4 += struct.unpack('<I', data[inner4+4:inner4+8])[0]
                        inner2 += 24 + struct.unpack('<I', data[inner2+4:inner2+8])[0]
                inner += struct.unpack('<I', data[inner+4:inner+8])[0]
            return
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]

dump_first_refr(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp')
