import struct, zlib

data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()

def scan(data, start, end, found):
    pos = start
    while pos < end and found[0] < 10:
        sig = data[pos:pos+4]
        if sig == b'GRUP':
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            scan(data, pos+24, pos+size, found)
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
            xils = None
            xclc = None
            while sub < len(body):
                ssig = body[sub:sub+4].decode('ascii', errors='replace')
                sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                sdata = body[sub+6:sub+6+sln]
                if ssig == 'XILS':
                    xils = struct.unpack('<I', sdata)[0] if sln == 4 else sdata.hex()
                elif ssig == 'XCLC':
                    xclc = struct.unpack('<iii', sdata)
                sub += 6 + sln
            if xils is not None:
                print('CELL 0x%08X grid=%s XILS=%s' % (fid, xclc[:2] if xclc else None, xils))
                found[0] += 1
            pos += 24 + size
        else:
            pos += 24 + struct.unpack('<I', data[pos+4:pos+8])[0]

found = [0]
tes4_size = struct.unpack('<I', data[4:8])[0]
scan(data, 24 + tes4_size, len(data), found)
