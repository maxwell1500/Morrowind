import struct, zlib

def walk(data, start, end, callback, depth=0):
    pos = start
    while pos < end and pos < len(data) - 24:
        sig = data[pos:pos+4]
        if sig == b'GRUP':
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
            label = data[pos+8:pos+12]
            callback('GRUP', pos, size, (gtype, label), depth)
            walk(data, pos+24, pos+size, callback, depth+1)
            pos += size
        else:
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            flags = struct.unpack('<I', data[pos+8:pos+12])[0]
            fid = struct.unpack('<I', data[pos+12:pos+16])[0]
            body = data[pos+24:pos+24+size]
            callback(sig.decode('ascii', errors='replace'), pos, size, (flags, fid, body), depth)
            pos += 24 + size

def on_record(sig, pos, size, payload, depth):
    prefix = '  ' * depth
    if sig == 'GRUP':
        gtype, label = payload
        print('%sGRUP type=%d label=%s size=%d' % (prefix, gtype, label, size))
    elif sig == 'CELL':
        flags, fid, body = payload
        if flags & 0x00040000:
            try:
                body = zlib.decompress(body[4:])
            except Exception:
                body = b''
        sub = 0
        xclc = None
        edid = None
        while sub < len(body):
            ssig = body[sub:sub+4].decode('ascii', errors='replace')
            sln = struct.unpack('<H', body[sub+4:sub+6])[0]
            sdata = body[sub+6:sub+6+sln]
            if ssig == 'XCLC':
                xclc = struct.unpack('<iii', sdata)
            elif ssig == 'EDID':
                edid = sdata.rstrip(b'\x00').decode('ascii', errors='replace')
            sub += 6 + sln
        if xclc:
            print('%sCELL 0x%08X edid=%s grid=%s' % (prefix, fid, edid or '???', xclc[:2]))
    elif sig == 'WRLD':
        flags, fid, body = payload
        print('%sWRLD 0x%08X flags=%08x size=%d' % (prefix, fid, flags, size))

# Check a known exterior worldspace in Starfield.esm, e.g. New Atlantis WRLD 0x00001A26
# Also check ImperialCity if it has a WRLD group
for path, wrld_fid in [(r'C:\XboxGames\Starfield\Content\Data\Starfield.esm', 0x00001A26)]:
    print('== %s WRLD 0x%08X ==' % (path, wrld_fid))
    data = open(path, 'rb').read()
    # Find WRLD group for this worldspace
    pos = 24 + struct.unpack('<I', data[4:8])[0]
    while pos < len(data) - 24:
        if data[pos:pos+4] == b'WRLD':
            this_fid = struct.unpack('<I', data[pos+12:pos+16])[0]
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            if this_fid == wrld_fid:
                walk(data, pos, pos + 24 + size, on_record, depth=0)
                break
            pos += 24 + size
        elif data[pos:pos+4] == b'GRUP':
            pos += struct.unpack('<I', data[pos+4:pos+8])[0]
        else:
            pos += 24 + struct.unpack('<I', data[pos+4:pos+8])[0]
    print()
