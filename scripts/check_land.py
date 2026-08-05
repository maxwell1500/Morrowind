import struct, zlib

def walk(data, start, end, depth=0, found_cells=None):
    if found_cells is None:
        found_cells = []
    pos = start
    while pos < end:
        sig = data[pos:pos+4]
        if sig == b'GRUP':
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            walk(data, pos+24, pos+size, depth+1, found_cells)
            pos += size
        elif sig == b'CELL':
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            flags = struct.unpack('<I', data[pos+8:pos+12])[0]
            fid = struct.unpack('<I', data[pos+12:pos+16])[0]
            body = data[pos+24:pos+24+size]
            if flags & 0x00040000:
                try:
                    body = zlib.decompress(body[4:])
                except Exception:
                    body = b''
            sub = 0
            xclc = None
            subrecords = []
            while sub < len(body):
                ssig = body[sub:sub+4].decode('ascii', errors='replace')
                sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                subrecords.append(ssig)
                if ssig == 'XCLC':
                    xclc = struct.unpack('<iii', body[sub+6:sub+6+sln])
                sub += 6 + sln
            if xclc:
                found_cells.append((fid, xclc[:2], subrecords))
            pos += 24 + size
        elif sig == b'LAND':
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            fid = struct.unpack('<I', data[pos+12:pos+16])[0]
            print('LAND record fid=0x%08X size=%d' % (fid, size))
            pos += 24 + size
        else:
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            pos += 24 + size
    return found_cells

data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 24 + struct.unpack('<I', data[4:8])[0]
while pos < len(data) - 24:
    sig = data[pos:pos+4]
    if sig == b'GRUP':
        gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
        label = data[pos+8:pos+12]
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        if gtype == 0 and label == b'WRLD':
            cells = walk(data, pos+24, pos+size)
            for fid, grid, subs in cells:
                print('CELL 0x%08X grid=%s subrecords=%s' % (fid, grid, subs))
            break
        pos += size
    else:
        pos += 24 + struct.unpack('<I', data[pos+4:pos+8])[0]
