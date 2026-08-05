import struct

def parse(name, body):
    print(f'\n=== {name} (len {len(body)}) ===')
    i = 0
    while i < len(body) - 6:
        sub_sig = body[i:i+4].decode('ascii', errors='replace')
        sub_len = struct.unpack('<H', body[i+4:i+6])[0]
        sub_data = body[i+6:i+6+sub_len]
        print(f'{i:3d}: {sub_sig} len={sub_len:3d} data={sub_data.hex() if sub_len>16 else repr(sub_data)}')
        i += 6 + sub_len

data = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()
pos = 0x7df88
size = struct.unpack('<I', data[pos+4:pos+8])[0]
magnus_body = data[pos+16:pos+16+size][8:]

our_data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
pos2 = 0x16c
size2 = struct.unpack('<I', our_data[pos2+4:pos2+8])[0]
our_body = our_data[pos2+16:pos2+16+size2][8:]

parse('Magnus', magnus_body)
parse('Our', our_body)
