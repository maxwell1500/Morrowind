import struct, zlib

data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
# find exterior cell formid 0xFE0008F1
pos = 0
while pos < len(data) - 16:
    if data[pos:pos+4] == b'CELL':
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        flags = struct.unpack('<I', data[pos+8:pos+12])[0]
        formid = struct.unpack('<I', data[pos+12:pos+16])[0]
        if formid == 0xFE0008F1:
            print(f'Exterior CELL at 0x{pos:x} size={size} flags=0x{flags:08X}')
            rec = data[pos+16:pos+16+size]
            if flags & 0x00040000:
                uncomp_size = struct.unpack('<I', rec[8:12])[0]
                body = zlib.decompress(rec[12:])
                print(f'Uncompressed size {uncomp_size}, decompressed {len(body)}')
            else:
                body = rec[8:]
            i = 0
            while i < len(body) - 6:
                sub_sig = body[i:i+4].decode('ascii', errors='replace')
                sub_len = struct.unpack('<H', body[i+4:i+6])[0]
                sub_data = body[i+6:i+6+sub_len]
                print(f'  {sub_sig} len={sub_len} data={sub_data.hex()[:40]}')
                i += 6 + sub_len
            break
        pos += 16 + size
    else:
        pos += 1
