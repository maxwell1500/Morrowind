import struct

def parse_file(path):
    data = open(path, 'rb').read()
    records = []
    # TES4 header
    sig = data[0:4].decode()
    size = struct.unpack('<I', data[4:8])[0]
    flags = struct.unpack('<I', data[8:12])[0]
    fid = struct.unpack('<I', data[12:16])[0]
    ver = struct.unpack('<I', data[16:20])[0]
    unk = struct.unpack('<I', data[20:24])[0]
    body = data[24:24+size]
    records.append(('TES4', size, flags, fid, ver, unk, body, 0))
    pos = 24 + size
    while pos < len(data):
        sig = data[pos:pos+4].decode('ascii', errors='replace')
        if sig != 'GRUP':
            print(f'  ERROR: expected GRUP at 0x{pos:x}, got {sig!r}')
            break
        gsize = struct.unpack('<I', data[pos+4:pos+8])[0]
        glabel = data[pos+8:pos+12]
        gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
        gstamp = struct.unpack('<I', data[pos+16:pos+20])[0]
        gunk = struct.unpack('<I', data[pos+20:pos+24])[0]
        records.append(('GRUP', gsize, glabel, gtype, gstamp, gunk, pos))
        pos += gsize
    return data, records

def parse_subrecords(body, skip_prefix=8):
    """Parse subrecords, optionally skipping an 8-byte prefix."""
    subs = []
    sub = skip_prefix
    end = len(body)
    while sub < end:
        if sub + 6 > end:
            subs.append(('TRUNC', end-sub, body[sub:end]))
            break
        ssig = body[sub:sub+4].decode('ascii', errors='replace')
        sln = struct.unpack('<H', body[sub+4:sub+6])[0]
        payload = body[sub+6:sub+6+sln]
        if sub+6+sln > end:
            subs.append(('OVERFLOW', sln, payload))
            break
        subs.append((ssig, sln, payload))
        sub += 6 + sln
    return subs

def dump_first_stat(path, label):
    print(f'\n=== {label}: {path} ===')
    data, records = parse_file(path)
    # find STAT group
    for r in records:
        if r[0] == 'GRUP' and r[2] == b'STAT':
            gpos = r[6]
            inner = gpos + 24
            # parse records inside
            gend = gpos + r[1]
            cnt = 0
            while inner < gend and cnt < 3:
                rsig = data[inner:inner+4].decode('ascii', errors='replace')
                rsize = struct.unpack('<I', data[inner+4:inner+8])[0]
                rflags = struct.unpack('<I', data[inner+8:inner+12])[0]
                rfid = struct.unpack('<I', data[inner+12:inner+16])[0]
                rver = struct.unpack('<I', data[inner+16:inner+20])[0]
                runk = struct.unpack('<I', data[inner+20:inner+24])[0]
                print(f'\nSTAT #{cnt} at 0x{inner:x}: size={rsize} flags=0x{rflags:08X} fid=0x{rfid:08X} ver={rver} unk={runk}')
                body = data[inner+24:inner+24+rsize]
                print(f'  body first 40 bytes: {body[:40].hex()}')
                subs = parse_subrecords(body, skip_prefix=8)
                for ssig, sln, payload in subs:
                    print(f'    {ssig!r} len={sln} payload={payload[:60]}')
                inner += 24 + rsize
                cnt += 1
            break

dump_first_stat(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'ImperialCity')
dump_first_stat(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'SeydaNeen')
