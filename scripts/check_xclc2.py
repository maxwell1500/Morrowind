import struct, zlib

def walk(data, start, end, callback):
    pos = start
    while pos < end and pos < len(data) - 24:
        sig = data[pos:pos+4]
        if sig == b'GRUP':
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            callback('GRUP', pos, size, None)
            walk(data, pos+24, pos+size, callback)
            pos += size
        else:
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            flags = struct.unpack('<I', data[pos+8:pos+12])[0]
            fid = struct.unpack('<I', data[pos+12:pos+16])[0]
            body = data[pos+24:pos+24+size]
            callback(sig, pos, size, (flags, fid, body))
            pos += 24 + size

def on_record(sig, pos, size, payload):
    if sig == b'CELL' and payload:
        flags, fid, body = payload
        if flags & 0x00040000:
            try:
                body = zlib.decompress(body[4:])
            except Exception:
                return
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
            print('Exterior CELL 0x%08X edid=%s grid=%s' % (fid, edid or '???', xclc[:2]))

data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
tes4_size = struct.unpack('<I', data[4:8])[0]
walk(data, 24+tes4_size, len(data), on_record)
