import struct
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
print('File size:', len(data))
print('Offset 0-400 hex:')
print(data[:400].hex())
print()
print('At offset 348 (0x15c):')
print(data[348:348+64].hex())
print('As ASCII:', repr(data[348:348+64]))
print()
# Parse TES4 size
size = struct.unpack('<I', data[4:8])[0]
print('TES4 subrecord data size:', size)
print('Top-level groups start at:', 24 + size, hex(24+size))
