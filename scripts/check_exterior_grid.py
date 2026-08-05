import struct, zlib
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
# Find WRLD children and first cell
pos = 24 + struct.unpack('<I', data[4:8])[0]
while pos < len(data):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    if sig == 'GRUP' and data[pos+8:pos+12] == b'WRLD':
        inner = pos + 24
        gend = pos + struct.unpack('<I', data[pos+4:pos+8])[0]
        while inner < gend:
            if data[inner:inner+4] == b'CELL':
                size = struct.unpack('<I', data[inner+4:inner+8])[0]
                fid = struct.unpack('<I', data[inner+12:inner+16])[0]
                body = data[inner+24:inner+24+size]
                body = zlib.decompress(body[4:])
                sub = 0
                while sub < len(body):
                    ssig = body[sub:sub+4].decode('ascii', errors='replace')
                    sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                    if ssig == 'XCLC':
                        x,y,_ = struct.unpack('<iii', body[sub+6:sub+6+sln])
                        print(f'Exterior CELL 0x{fid:08X} grid ({x}, {y})')
                        break
                    sub += 6 + sln
                break
            inner += 24 + struct.unpack('<I', data[inner+4:inner+8])[0]
        break
    pos += struct.unpack('<I', data[pos+4:pos+8])[0]
