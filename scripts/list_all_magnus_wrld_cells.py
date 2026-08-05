import struct, zlib

def walk(data, pos, found, wrld_fid):
    gend = pos + struct.unpack('<I', data[pos+4:pos+8])[0]
    inner = pos + 24
    while inner < gend:
        sig = data[inner:inner+4].decode('ascii', errors='replace')
        if sig == 'GRUP':
            walk(data, inner, found, wrld_fid)
            inner += struct.unpack('<I', data[inner+4:inner+8])[0]
        elif sig == 'CELL':
            size = struct.unpack('<I', data[inner+4:inner+8])[0]
            flags = struct.unpack('<I', data[inner+8:inner+12])[0]
            fid = struct.unpack('<I', data[inner+12:inner+16])[0]
            body = data[inner+24:inner+24+size]
            if flags & 0x00040000:
                body = zlib.decompress(body[4:])
            sub = 0
            x = y = None
            while sub < len(body):
                ssig = body[sub:sub+4].decode('ascii', errors='replace')
                sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                if ssig == 'XCLC':
                    x, y, _ = struct.unpack('<iii', body[sub+6:sub+6+sln])
                    found.append((wrld_fid, fid, x, y))
                    break
                sub += 6 + sln
            inner += 24 + size
        else:
            inner += 24 + struct.unpack('<I', data[inner+4:inner+8])[0]

data = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()
all_cells = []
pos = 24 + struct.unpack('<I', data[4:8])[0]
while pos < len(data):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    if sig == 'GRUP' and data[pos+8:pos+12] == b'WRLD':
        inner = pos + 24
        gend = pos + struct.unpack('<I', data[pos+4:pos+8])[0]
        while inner < gend:
            if data[inner:inner+4] == b'WRLD':
                wrld_fid = struct.unpack('<I', data[inner+12:inner+16])[0]
                wrld_size = struct.unpack('<I', data[inner+4:inner+8])[0]
                cg_pos = inner + 24 + wrld_size
                if data[cg_pos:cg_pos+4] == b'GRUP':
                    walk(data, cg_pos, all_cells, wrld_fid)
                break
            inner += 24 + struct.unpack('<I', data[inner+4:inner+8])[0]
        break
    pos += struct.unpack('<I', data[pos+4:pos+8])[0]

print('All exterior cells in WRLD groups:')
for wrld_fid, fid, x, y in all_cells:
    print(f'  WRLD 0x{wrld_fid:08X} CELL 0x{fid:08X} grid ({x}, {y})')
