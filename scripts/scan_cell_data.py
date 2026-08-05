import struct

data = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()

# Scan all CELL records and print their DATA subrecord
pos = 0
results = []
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
            i = 0
            has_data = False
            while i < len(rec) - 6:
                sub_sig = rec[i:i+4].decode('ascii', errors='replace')
                try:
                    sub_len = struct.unpack('<H', rec[i+4:i+6])[0]
                except:
                    break
                if sub_sig == 'DATA':
                    d = rec[i+6:i+6+sub_len]
                    results.append((formid, d, len(d)))
                    has_data = True
                    break
                i += 6 + sub_len
            if not has_data:
                results.append((formid, b'', 0))
        except Exception as e:
            pass
        pos += 16 + size
    else:
        pos += 1

print(f'Found {len(results)} CELL records')
for formid, d, ln in results[:30]:
    print(f'CELL 0x{formid:08X}: DATA len={ln} hex={d.hex()}')
