import struct, zlib

data = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()

target_fid = 0x0100E1C8
pos = 0
while pos < len(data) - 24:
    sig = data[pos:pos+4]
    if sig == b'GRUP':
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        if size == 0:
            pos += 24
            continue
        pos += size
    elif sig == b'WRLD':
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        flags = struct.unpack('<I', data[pos+8:pos+12])[0]
        fid = struct.unpack('<I', data[pos+12:pos+16])[0]
        if fid == target_fid:
            print('Found WRLD 0x%08X at offset 0x%X, size=%d, flags=0x%08X' % (fid, pos, size, flags))
            body = data[pos+24:pos+24+size]
            if flags & 0x00040000:
                try:
                    body = zlib.decompress(body[4:])
                    print('  (compressed)')
                except:
                    pass
            subpos = 0
            while subpos < len(body) - 6:
                ssig = body[subpos:subpos+4].decode('ascii', errors='replace')
                slen = struct.unpack('<H', body[subpos+4:subpos+6])[0]
                sdata = body[subpos+6:subpos+6+slen]
                print('  %s: size=%d' % (ssig, slen))
                if ssig == 'EDID':
                    print('    = %s' % sdata.rstrip(b'\x00').decode('ascii', errors='replace'))
                elif ssig == 'DNAM' and len(sdata) >= 8:
                    floats = struct.unpack('<ff', sdata[:8])
                    print('    = %s' % str(floats))
                elif ssig == 'DATA' and len(sdata) >= 1:
                    print('    = 0x%02X' % sdata[0])
                elif ssig == 'FNAM' and len(sdata) >= 1:
                    print('    = 0x%02X' % sdata[0])
                elif ssig == 'NAM0' and len(sdata) >= 8:
                    floats = struct.unpack('<ff', sdata[:8])
                    print('    = %s' % str(floats))
                elif ssig == 'NAM9' and len(sdata) >= 8:
                    floats = struct.unpack('<ff', sdata[:8])
                    print('    = %s' % str(floats))
                subpos += 6 + slen
            break
        pos += 24 + size
    else:
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        pos += 24 + size
