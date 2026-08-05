import struct, zlib
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()

def walk(data, pos, found):
    gend = pos + struct.unpack('<I', data[pos+4:pos+8])[0]
    inner = pos + 24
    while inner < gend:
        sig = data[inner:inner+4].decode('ascii', errors='replace')
        if sig == 'GRUP':
            walk(data, inner, found)
            inner += struct.unpack('<I', data[inner+4:inner+8])[0]
        elif sig == 'CELL':
            size = struct.unpack('<I', data[inner+4:inner+8])[0]
            flags = struct.unpack('<I', data[inner+8:inner+12])[0]
            fid = struct.unpack('<I', data[inner+12:inner+16])[0]
            body = data[inner+24:inner+24+size]
            if flags & 0x00040000:
                body = zlib.decompress(body[4:])
            sub = 0
            while sub < len(body):
                ssig = body[sub:sub+4].decode('ascii', errors='replace')
                sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                if ssig == 'XCLC':
                    x,y,_ = struct.unpack('<iii', body[sub+6:sub+6+sln])
                    found.append((fid, x, y))
                    break
                sub += 6 + sln
            inner += 24 + size
        else:
            inner += 24 + struct.unpack('<I', data[inner+4:inner+8])[0]

pos = 24 + struct.unpack('<I', data[4:8])[0]
found = []
while pos < len(data):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    if sig == 'GRUP':
        walk(data, pos, found)
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]
    else:
        pos += 24 + struct.unpack('<I', data[pos+4:pos+8])[0]

for fid, x, y in found:
    print(f'CELL 0x{fid:08X} grid ({x}, {y})')
