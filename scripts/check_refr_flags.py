import struct, zlib
def check_refr(path):
    data = open(path, 'rb').read()
    pos = 24 + struct.unpack('<I', data[4:8])[0]
    while pos < len(data):
        sig = data[pos:pos+4].decode('ascii', errors='replace')
        if sig == 'GRUP' and data[pos+8:pos+12] == b'CELL':
            inner = pos + 24
            while inner < pos + struct.unpack('<I', data[pos+4:pos+8])[0]:
                if data[inner:inner+4] == b'GRUP':
                    inner2 = inner + 24
                    while inner2 < inner + struct.unpack('<I', data[inner+4:inner+8])[0]:
                        if data[inner2:inner2+4] == b'CELL':
                            csize = struct.unpack('<I', data[inner2+4:inner2+8])[0]
                            # children grup follows
                            cend = inner2 + 24 + csize
                            inner3 = cend
                            if data[inner3:inner3+4] == b'GRUP':
                                inner4 = inner3 + 24
                                while inner4 < inner3 + struct.unpack('<I', data[inner3+4:inner3+8])[0]:
                                    if data[inner4:inner4+4] == b'GRUP':
                                        inner5 = inner4 + 24
                                        while inner5 < inner4 + struct.unpack('<I', data[inner4+4:inner4+8])[0]:
                                            if data[inner5:inner5+4] == b'REFR':
                                                rsize = struct.unpack('<I', data[inner5+4:inner5+8])[0]
                                                rflags = struct.unpack('<I', data[inner5+8:inner5+12])[0]
                                                rfid = struct.unpack('<I', data[inner5+12:inner5+16])[0]
                                                print(f'REFR at 0x{inner5:x} size={rsize} flags=0x{rflags:08X} fid=0x{rfid:08X}')
                                                return
                                            inner5 += 24 + struct.unpack('<I', data[inner5+4:inner5+8])[0]
                                    inner4 += struct.unpack('<I', data[inner4+4:inner4+8])[0]
                            return
                        inner2 += 24 + struct.unpack('<I', data[inner2+4:inner2+8])[0]
                inner += struct.unpack('<I', data[inner+4:inner+8])[0]
            return
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]

print('ImperialCity:')
check_refr(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm')
print('Magnus:')
check_refr(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm')
