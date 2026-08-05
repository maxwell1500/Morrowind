import struct
data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 0x6390
print('Top-level WRLD group header:', data[pos:pos+24].hex())
print('After WRLD record at 0x63a8, size 342, ends at', hex(0x63a8+16+342))
pos2 = 0x63a8 + 16 + 342
print('Next bytes:', data[pos2:pos2+40].hex())
print('Interpreted as GRUP? ', data[pos2:pos2+4])
print('Size if GRUP:', struct.unpack('<I', data[pos2+4:pos2+8])[0])
print('Label:', data[pos2+8:pos2+12])
print('Type:', struct.unpack('<I', data[pos2+12:pos2+16])[0])
