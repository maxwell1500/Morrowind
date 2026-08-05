import struct
data = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()
pos = 0x7df88
size = struct.unpack('<I', data[pos+4:pos+8])[0]
rec = data[pos+16:pos+16+size]
print('First 32 bytes of Magnus WRLD content:', rec[:32].hex())
print('First 16 bytes ascii-ish:', repr(rec[:16]))
