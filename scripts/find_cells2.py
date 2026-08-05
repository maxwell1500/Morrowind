import struct, zlib

def walk_grup(data, pos, depth=0):
    results = []
    gend = pos + struct.unpack('<I', data[pos+4:pos+8])[0]
    glabel = data[pos+8:pos+12]
    gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
    inner = pos + 24
    while inner < gend:
        sig = data[inner:inner+4].decode('ascii', errors='replace')
        if sig == 'GRUP':
            results.extend(walk_grup(data, inner, depth+1))
            inner += struct.unpack('<I', data[inner+4:inner+8])[0]
        elif sig in ('CELL','REFR','WRLD','STAT'):
            results.append((depth, inner, sig, struct.unpack('<I', data[inner+8:inner+12])[0], struct.unpack('<I', data[inner+12:inner+16])[0], struct.unpack('<I', data[inner+4:inner+8])[0]))
            inner += 24 + struct.unpack('<I', data[inner+4:inner+8])[0]
        else:
            # unknown record, skip by size
            inner += 24 + struct.unpack('<I', data[inner+4:inner+8])[0]
    return results

def find_cells(path):
    data = open(path, 'rb').read()
    pos = 24 + struct.unpack('<I', data[4:8])[0]
    records = []
    while pos < len(data):
        sig = data[pos:pos+4].decode('ascii', errors='replace')
        if sig == 'GRUP':
            records.extend(walk_grup(data, pos))
            pos += struct.unpack('<I', data[pos+4:pos+8])[0]
        else:
            # top-level record (rare)
            pos += 24 + struct.unpack('<I', data[pos+4:pos+8])[0]
    cells = [r for r in records if r[2] == 'CELL']
    print(f'{path}: found {len(cells)} CELL records')
    for depth, pos, sig, flags, fid, size in cells[:3]:
        print(f'  depth={depth} pos=0x{pos:x} size={size} flags=0x{flags:08X} fid=0x{fid:08X}')
        body = data[pos+24:pos+24+size]
        if flags & 0x00040000:
            unc_len = struct.unpack('<I', body[:4])[0]
            body = zlib.decompress(body[4:])
            print(f'    decompressed {len(body)} bytes')
        sub = 0
        while sub < len(body):
            ssig = body[sub:sub+4].decode('ascii', errors='replace')
            sln = struct.unpack('<H', body[sub+4:sub+6])[0]
            payload = body[sub+6:sub+6+sln]
            if ssig in ('EDID','FULL','XCLC','DATA','LTMP','XCLW','CNAM','WNAM'):
                if ssig == 'DATA':
                    print(f'    {ssig} len={sln} hex={payload.hex()}')
                else:
                    print(f'    {ssig} len={sln} {payload[:50]}')
            sub += 6 + sln

print('=== ImperialCity ===')
find_cells(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm')
print('\n=== Magnus ===')
find_cells(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm')
