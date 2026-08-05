import struct, zlib

def walk(data, start, end, depth=0):
    pos = start
    while pos < end:
        sig = data[pos:pos+4].decode('ascii', errors='replace')
        if sig == 'GRUP':
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
            label = data[pos+8:pos+12]
            print('  '*depth + 'GRUP type=%d label=%s size=%d' % (gtype, label, size))
            walk(data, pos+24, pos+size, depth+1)
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
            data_val = None
            xclc = None
            while sub < len(body):
                ssig = body[sub:sub+4].decode('ascii', errors='replace')
                sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                sdata = body[sub+6:sub+6+sln]
                if ssig == 'EDID':
                    edid = sdata.rstrip(b'\x00').decode('ascii', errors='replace')
                elif ssig == 'DATA':
                    data_val = struct.unpack('<I', sdata)[0] if sln == 4 else None
                elif ssig == 'XCLC':
                    xclc = struct.unpack('<iii', sdata)
                sub += 6 + sln
            print('  '*depth + 'CELL 0x%08X edid=%s DATA=%08x XCLC=%s' % (fid, edid or '???', data_val or 0, xclc))
            pos += 24 + size
        else:
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            fid = struct.unpack('<I', data[pos+12:pos+16])[0]
            print('  '*depth + '%s 0x%08X size=%d' % (sig, fid, size))
            pos += 24 + size

data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 24 + struct.unpack('<I', data[4:8])[0]
# Find CELL group
while pos < len(data) - 24:
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    if sig == 'GRUP':
        gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
        label = data[pos+8:pos+12]
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        if gtype == 0 and label == b'CELL':
            print('Found CELL group at %d size=%d' % (pos, size))
            walk(data, pos+24, pos+size, 0)
            break
        pos += size
    else:
        pos += 24 + struct.unpack('<I', data[pos+4:pos+8])[0]
