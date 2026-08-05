import struct, zlib

def walk(data, start, end, depth=0, max_depth=5):
    if depth > max_depth:
        return
    pos = start
    while pos < end:
        sig = data[pos:pos+4].decode('ascii', errors='replace')
        if sig == 'GRUP':
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
            label = data[pos+8:pos+12]
            print('  '*depth + 'GRUP type=%d label=%s size=%d' % (gtype, label, size))
            walk(data, pos+24, pos+size, depth+1, max_depth)
            pos += size
        elif sig == 'CELL':
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
            edid = None
            xclc = None
            while sub < len(body):
                ssig = body[sub:sub+4].decode('ascii', errors='replace')
                sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                sdata = body[sub+6:sub+6+sln]
                if ssig == 'EDID':
                    edid = sdata.rstrip(b'\x00').decode('ascii', errors='replace')
                elif ssig == 'XCLC':
                    xclc = struct.unpack('<iii', sdata)
                sub += 6 + sln
            print('  '*depth + 'CELL 0x%08X edid=%s grid=%s' % (fid, edid or '???', xclc[:2] if xclc else None))
            pos += 24 + size
        elif sig in ('WRLD', 'REFR'):
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            fid = struct.unpack('<I', data[pos+12:pos+16])[0]
            print('  '*depth + '%s 0x%08X size=%d' % (sig, fid, size))
            pos += 24 + size
        else:
            pos += 24 + struct.unpack('<I', data[pos+4:pos+8])[0]

data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 24 + struct.unpack('<I', data[4:8])[0]
while pos < len(data) - 24:
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    if sig == 'GRUP':
        gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
        label = data[pos+8:pos+12]
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        if gtype == 0 and label == b'WRLD':
            print('Found WRLD group at %d size=%d' % (pos, size))
            walk(data, pos+24, pos+size, 0, 5)
            break
        pos += size
    else:
        pos += 24 + struct.unpack('<I', data[pos+4:pos+8])[0]
