import struct, zlib

def dump_first_cell(path):
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
                            size = struct.unpack('<I', data[inner2+4:inner2+8])[0]
                            flags = struct.unpack('<I', data[inner2+8:inner2+12])[0]
                            fid = struct.unpack('<I', data[inner2+12:inner2+16])[0]
                            print(f'CELL at 0x{inner2:x} size={size} flags=0x{flags:08X} fid=0x{fid:08X}')
                            body = data[inner2+24:inner2+24+size]
                            if flags & 0x00040000:
                                body = zlib.decompress(body[4:])
                            sub = 0
                            while sub < len(body):
                                ssig = body[sub:sub+4].decode('ascii', errors='replace')
                                sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                                payload = body[sub+6:sub+6+sln]
                                if ssig == 'DATA':
                                    print(f'  {ssig} len={sln} hex={payload.hex()} uint32=0x{struct.unpack("<I", payload)[0]:08X}')
                                elif ssig in ('EDID','FULL'):
                                    print(f'  {ssig} len={sln} {payload}')
                                else:
                                    print(f'  {ssig} len={sln}')
                                sub += 6 + sln
                            return
                        inner2 += 24 + struct.unpack('<I', data[inner2+4:inner2+8])[0]
                inner += struct.unpack('<I', data[inner+4:inner+8])[0]
            return
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]

dump_first_cell(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp')
