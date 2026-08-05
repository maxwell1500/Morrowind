import struct, zlib

def find_first_cell_with_xclc(path):
    data = open(path, 'rb').read()
    pos = 24 + struct.unpack('<I', data[4:8])[0]
    while pos < len(data):
        sig = data[pos:pos+4].decode('ascii', errors='replace')
        if sig == 'GRUP' and data[pos+8:pos+12] == b'CELL':
            print(f'CELL top group at 0x{pos:x}')
            inner = pos + 24
            gend = pos + struct.unpack('<I', data[pos+4:pos+8])[0]
            cnt = 0
            while inner < gend and cnt < 5:
                rsig = data[inner:inner+4].decode('ascii', errors='replace')
                rsize = struct.unpack('<I', data[inner+4:inner+8])[0]
                rflags = struct.unpack('<I', data[inner+8:inner+12])[0]
                rfid = struct.unpack('<I', data[inner+12:inner+16])[0]
                rver = struct.unpack('<I', data[inner+16:inner+20])[0]
                runk = struct.unpack('<I', data[inner+20:inner+24])[0]
                print(f'\n{rsig} at 0x{inner:x}: size={rsize} flags=0x{rflags:08X} fid=0x{rfid:08X}')
                body = data[inner+24:inner+24+rsize]
                # decompress if needed
                if rflags & 0x00040000:
                    unc_len = struct.unpack('<I', body[:4])[0]
                    body = zlib.decompress(body[4:])
                    print(f'  decompressed len={len(body)}')
                sub = 0
                while sub < len(body):
                    ssig = body[sub:sub+4].decode('ascii', errors='replace')
                    sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                    payload = body[sub+6:sub+6+sln]
                    if ssig == 'DATA':
                        print(f'  {ssig} len={sln} value={payload.hex()}')
                    elif ssig in ('EDID','FULL','XCLC','LTMP','XCLW','CNAM','WNAM'):
                        print(f'  {ssig} len={sln} {payload[:40]}')
                    else:
                        print(f'  {ssig} len={sln}')
                    sub += 6 + sln
                    if sub > len(body):
                        print('  OVERRUN')
                        break
                inner += 24 + rsize
                cnt += 1
            break
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]

print('\n=== ImperialCity ===')
find_first_cell_with_xclc(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm')
print('\n=== Magnus ===')
find_first_cell_with_xclc(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm')
