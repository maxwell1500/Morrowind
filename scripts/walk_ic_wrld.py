import struct
def walk_wrld_children(data, pos, depth=0):
    gsize = struct.unpack('<I', data[pos+4:pos+8])[0]
    glabel = data[pos+8:pos+12]
    gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
    print(f'{"  "*depth}GRUP at 0x{pos:x} size={gsize} label={glabel} type={gtype}')
    inner = pos + 24
    while inner < pos + gsize:
        sig = data[inner:inner+4].decode('ascii', errors='replace')
        if sig == 'GRUP':
            walk_wrld_children(data, inner, depth+1)
            inner += struct.unpack('<I', data[inner+4:inner+8])[0]
        else:
            size = struct.unpack('<I', data[inner+4:inner+8])[0]
            flags = struct.unpack('<I', data[inner+8:inner+12])[0]
            fid = struct.unpack('<I', data[inner+12:inner+16])[0]
            print(f'{"  "*depth}{sig} at 0x{inner:x} size={size} flags=0x{flags:08X} fid=0x{fid:08X}')
            inner += 24 + size

data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 24 + struct.unpack('<I', data[4:8])[0]
while pos < len(data):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    if sig == 'GRUP' and data[pos+8:pos+12] == b'WRLD':
        walk_wrld_children(data, pos, 0)
        break
    pos += struct.unpack('<I', data[pos+4:pos+8])[0]
