import struct

magnus = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()
pos = 0x7df88
magnus_rec = magnus[pos:pos+16+struct.unpack('<I', magnus[pos+4:pos+8])[0]]

our = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
pos2 = 0x16c
our_rec = our[pos2:pos2+16+struct.unpack('<I', our[pos2+4:pos2+8])[0]]

print('Magnus WRLD record length:', len(magnus_rec))
print('Our WRLD record length:', len(our_rec))
print('Magnus hex:', magnus_rec.hex())
print('Our hex:   ', our_rec.hex())
if magnus_rec == our_rec:
    print('MATCH')
else:
    print('DIFFER')
    for i in range(min(len(magnus_rec), len(our_rec))):
        if magnus_rec[i] != our_rec[i]:
            print(f'first diff at {i}: {magnus_rec[i]:02x} vs {our_rec[i]:02x}')
            break
