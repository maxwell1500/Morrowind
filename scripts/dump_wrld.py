import struct
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
pos = 0x16c
sig = data[pos:pos+4].decode()
size = struct.unpack('<I', data[pos+4:pos+8])[0]
flags = struct.unpack('<I', data[pos+8:pos+12])[0]
formid = struct.unpack('<I', data[pos+12:pos+16])[0]
print(f'WRLD record at 0x{pos:x}: size={size} flags=0x{flags:08X} formid=0x{formid:08X}')
rec = data[pos+16:pos+16+size]
print(f'Record content ({len(rec)} bytes):')
print(rec.hex())
