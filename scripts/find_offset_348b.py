import struct
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
# TES4 is 24 bytes header + 121 bytes subrecords = 145 total
pos = 24 + struct.unpack('<I', data[4:8])[0]
print('Start of top-level groups at', pos, hex(pos))
# STAT group at pos
sig = data[pos:pos+4].decode()
size = struct.unpack('<I', data[pos+4:pos+8])[0]
print(f'0x{pos:x}: {sig} size={size}')
inner = pos + 24
# first STAT
sig = data[inner:inner+4].decode()
size = struct.unpack('<I', data[inner+4:inner+8])[0]
flags = struct.unpack('<I', data[inner+8:inner+12])[0]
formid = struct.unpack('<I', data[inner+12:inner+16])[0]
print(f'0x{inner:x}: {sig} size={size} flags=0x{flags:08X} formid=0x{formid:08X}')
inner += 16 + size
# second STAT
sig = data[inner:inner+4].decode()
size = struct.unpack('<I', data[inner+4:inner+8])[0]
flags = struct.unpack('<I', data[inner+8:inner+12])[0]
formid = struct.unpack('<I', data[inner+12:inner+16])[0]
print(f'0x{inner:x}: {sig} size={size} flags=0x{flags:08X} formid=0x{formid:08X}')
print('Offset 348 =', hex(348))
print('Byte at 348:', data[348:348+4].hex())
