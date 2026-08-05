import struct, zlib

data = open(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 'rb').read()
pos = 0x7df88
sig = data[pos:pos+4].decode('ascii')
size = struct.unpack('<I', data[pos+4:pos+8])[0]
flags = struct.unpack('<I', data[pos+8:pos+12])[0]
formid = struct.unpack('<I', data[pos+12:pos+16])[0]
print(f'WRLD record at 0x{pos:x}: sig={sig} size={size} flags=0x{flags:08X} formid=0x{formid:08X}')
rec = data[pos+16:pos+16+size]
print(f'Full record hex ({len(rec)} bytes):')
print(rec.hex())
