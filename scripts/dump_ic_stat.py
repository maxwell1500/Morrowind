import struct
data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
# Find first STAT top-level record
pos = 24 + struct.unpack('<I', data[4:8])[0]
while pos < len(data):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    if sig == 'GRUP' and data[pos+8:pos+12] == b'STAT':
        print(f'Found STAT group at 0x{pos:x}')
        inner = pos + 24
        rsig = data[inner:inner+4].decode('ascii', errors='replace')
        size = struct.unpack('<I', data[inner+4:inner+8])[0]
        flags = struct.unpack('<I', data[inner+8:inner+12])[0]
        formid = struct.unpack('<I', data[inner+12:inner+16])[0]
        print(f'0x{inner:x}: {rsig} size={size} flags=0x{flags:08X} formid=0x{formid:08X}')
        # print first 24 bytes of body
        body = data[inner+16:inner+16+24]
        print(f'Body first 24 bytes: {body.hex()}')
        # parse subrecords naively
        sub = inner+16
        end = inner+16+size
        cnt = 0
        while sub < end and cnt < 4:
            ssig = data[sub:sub+4].decode('ascii', errors='replace')
            sln = struct.unpack('<H', data[sub+4:sub+6])[0]
            print(f'  0x{sub:x}: {ssig!r} len={sln}')
            sub += 6 + sln
            cnt += 1
        break
    pos += struct.unpack('<I', data[pos+4:pos+8])[0]
