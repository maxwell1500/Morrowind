import struct, zlib

def dump_wrld(path):
    data = open(path, 'rb').read()
    pos = 24 + struct.unpack('<I', data[4:8])[0]
    while pos < len(data):
        sig = data[pos:pos+4].decode('ascii', errors='replace')
        if sig == 'GRUP' and data[pos+8:pos+12] == b'WRLD':
            inner = pos + 24
            gend = pos + struct.unpack('<I', data[pos+4:pos+8])[0]
            while inner < gend:
                if data[inner:inner+4] == b'WRLD':
                    size = struct.unpack('<I', data[inner+4:inner+8])[0]
                    flags = struct.unpack('<I', data[inner+8:inner+12])[0]
                    fid = struct.unpack('<I', data[inner+12:inner+16])[0]
                    print(f'WRLD at 0x{inner:x} size={size} flags=0x{flags:08X} fid=0x{fid:08X}')
                    body = data[inner+24:inner+24+size]
                    print(f'  body first 60 bytes: {body[:60].hex()}')
                    sub = 0
                    while sub < len(body):
                        ssig = body[sub:sub+4].decode('ascii', errors='replace')
                        sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                        payload = body[sub+6:sub+6+sln]
                        print(f'  {ssig} len={sln} {payload[:50]}')
                        sub += 6 + sln
                    return
                inner += 24 + struct.unpack('<I', data[inner+4:inner+8])[0]
            return
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]

print('=== Our WRLD ===')
dump_wrld(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp')
