import struct
def walk(data, pos, depth=0, indent=''):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    if sig == 'GRUP':
        gsize = struct.unpack('<I', data[pos+4:pos+8])[0]
        glabel = data[pos+8:pos+12]
        gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
        print(f'{indent}GRUP at 0x{pos:x} size={gsize} label={glabel} type={gtype}')
        inner = pos + 24
        while inner < pos + gsize:
            walk(data, inner, depth+1, indent + '  ')
            s = data[inner:inner+4].decode('ascii', errors='replace')
            if s == 'GRUP':
                inner += struct.unpack('<I', data[inner+4:inner+8])[0]
            else:
                inner += 24 + struct.unpack('<I', data[inner+4:inner+8])[0]
    else:
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        flags = struct.unpack('<I', data[pos+8:pos+12])[0]
        fid = struct.unpack('<I', data[pos+12:pos+16])[0]
        if sig in ('CELL','REFR','WRLD','STAT') or depth < 3:
            print(f'{indent}{sig} at 0x{pos:x} size={size} flags=0x{flags:08X} fid=0x{fid:08X}')

# Just walk first top-level GRUPs of ImperialCity to depth 3
data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 24 + struct.unpack('<I', data[4:8])[0]
cnt = 0
while pos < len(data) and cnt < 3:
    walk(data, pos, 0, '')
    pos += struct.unpack('<I', data[pos+4:pos+8])[0]
    cnt += 1
