import struct

data = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()
pos = 0
while pos < len(data) - 16:
    if data[pos:pos+4] == b'CELL':
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        flags = struct.unpack('<I', data[pos+8:pos+12])[0]
        formid = struct.unpack('<I', data[pos+12:pos+16])[0]
        rec = data[pos+16:pos+16+size]
        try:
            if flags & 0x00040000:
                rec = __import__('zlib').decompress(rec[12:])
            elif rec[:8] == b'\x00\x00\x00\x00@\x02\x00\x00':
                rec = rec[8:]
            has_xclc = False
            has_cnam = False
            cnam_len = 0
            i = 0
            while i < len(rec) - 6:
                sub_sig = rec[i:i+4].decode('ascii', errors='replace')
                sub_len = struct.unpack('<H', rec[i+4:i+6])[0]
                if sub_sig == 'XCLC':
                    has_xclc = True
                if sub_sig == 'CNAM':
                    has_cnam = True
                    cnam_len = sub_len
                i += 6 + sub_len
            if has_xclc and has_cnam:
                print(f'Exterior CELL 0x{formid:08X} CNAM len={cnam_len}')
            if not has_xclc and has_cnam:
                print(f'Interior CELL 0x{formid:08X} CNAM len={cnam_len}')
        except:
            pass
        pos += 16 + size
    else:
        pos += 1
