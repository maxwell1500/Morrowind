import struct
data = open(r'C:\XboxGames\Starfield\Content\Data\Starfield.esm', 'rb').read()
pos = 375131446
print('WRLD header:', data[pos:pos+24].hex())
size = struct.unpack('<I', data[pos+4:pos+8])[0]
print('WRLD size:', size)
print('After WRLD record (first 256 bytes of children):')
print(data[pos+24+size:pos+24+size+256].hex())
