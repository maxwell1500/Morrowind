import struct

data = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()
pos = 0x7df88
size = struct.unpack('<I', data[pos+4:pos+8])[0]
rec = data[pos+16:pos+16+size]
magnus_body = rec[8:]

our_data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
pos2 = 0x16c
size2 = struct.unpack('<I', our_data[pos2+4:pos2+8])[0]
rec2 = our_data[pos2+16:pos2+16+size2]
our_body = rec2[8:]

print('Magnus body len', len(magnus_body))
print('Our body len', len(our_body))

# Print all diffs
for i in range(min(len(magnus_body), len(our_body))):
    if magnus_body[i] != our_body[i]:
        print(f'Diff at {i}: Magnus={magnus_body[i]:02x} Our={our_body[i]:02x}')
        print(f'  Magnus context: {magnus_body[max(0,i-12):i+16].hex()}')
        print(f'  Our context:    {our_body[max(0,i-12):i+16].hex()}')
        print()
