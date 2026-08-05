import struct, zlib

data = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()
pos = 0x7df88
size = struct.unpack('<I', data[pos+4:pos+8])[0]
flags = struct.unpack('<I', data[pos+8:pos+12])[0]
rec = data[pos+16:pos+16+size]
print('Magnus WRLD record flags=', hex(flags), 'size=', size)
magnus_body = rec[8:]  # strip prefix

our_data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
# find WRLD record
pos2 = 0x16c
size2 = struct.unpack('<I', our_data[pos2+4:pos2+8])[0]
rec2 = our_data[pos2+16:pos2+16+size2]
print('Our WRLD record size=', size2)
our_body = rec2[8:]  # strip prefix

print('Magnus body length:', len(magnus_body))
print('Our body length:', len(our_body))
if magnus_body == our_body:
    print('Bodies MATCH')
else:
    print('Bodies DIFFER')
    # find first diff
    for i in range(min(len(magnus_body), len(our_body))):
        if magnus_body[i] != our_body[i]:
            print(f'First diff at byte {i}: Magnus={magnus_body[i]:02x} Our={our_body[i]:02x}')
            print(f'Context Magnus: {magnus_body[max(0,i-8):i+16].hex()}')
            print(f'Context Our:    {our_body[max(0,i-8):i+16].hex()}')
            break
