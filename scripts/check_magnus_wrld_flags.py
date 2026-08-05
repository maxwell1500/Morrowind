import struct
def check():
    data = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()
    pos = 24 + struct.unpack('<I', data[4:8])[0]
    while pos < len(data):
        sig = data[pos:pos+4].decode('ascii', errors='replace')
        if sig == 'GRUP' and data[pos+8:pos+12] == b'WRLD':
            inner = pos + 24
            while inner < pos + struct.unpack('<I', data[pos+4:pos+8])[0]:
                if data[inner:inner+4] == b'WRLD':
                    size = struct.unpack('<I', data[inner+4:inner+8])[0]
                    flags = struct.unpack('<I', data[inner+8:inner+12])[0]
                    fid = struct.unpack('<I', data[inner+12:inner+16])[0]
                    print(f'WRLD at 0x{inner:x} size={size} flags=0x{flags:08X} fid=0x{fid:08X}')
                    return
                inner += 24 + struct.unpack('<I', data[inner+4:inner+8])[0]
            return
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]
check()
