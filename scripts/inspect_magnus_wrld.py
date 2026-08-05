import struct
data = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()
pos = 0
while pos < len(data) - 24:
    if data[pos:pos+4] == b'WRLD':
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        formid = struct.unpack('<I', data[pos+12:pos+16])[0]
        if formid == 0x0100E1C8:
            rec = data[pos:pos+24+size]
            print(f'WRLD size {size}')
            print(rec[:128].hex())
            break
        pos += 24 + size
    else:
        pos += 1
