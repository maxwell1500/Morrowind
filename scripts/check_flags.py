import struct

with open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb') as f:
    data = f.read()

# Check ALL REFR record flags and the persistent cell's flags
print('=== Record Flags Analysis ===\n')

# Persistent cell flags
pos = 91744  # CELL 0x0100E954
sig = data[pos:pos+4].decode()
sz = struct.unpack_from('<I', data, pos+4)[0]
flags = struct.unpack_from('<I', data, pos+8)[0]
fid = struct.unpack_from('<I', data, pos+12)[0]
print(f'Persistent CELL 0x{fid:08X}: flags=0x{flags:08X}')

# Exterior cell flags
pos = 91981
sig = data[pos:pos+4].decode()
sz = struct.unpack_from('<I', data, pos+4)[0]
flags = struct.unpack_from('<I', data, pos+8)[0]
fid = struct.unpack_from('<I', data, pos+12)[0]
print(f'Exterior CELL 0x{fid:08X}: flags=0x{flags:08X}')

# WRLD flags
pos = 91354
sig = data[pos:pos+4].decode()
sz = struct.unpack_from('<I', data, pos+4)[0]
flags = struct.unpack_from('<I', data, pos+8)[0]
fid = struct.unpack_from('<I', data, pos+12)[0]
print(f'WRLD 0x{fid:08X}: flags=0x{flags:08X}')

# STAT record flags
print('\n=== STAT Record Flags ===')
pos = 183 + 24
for i in range(3):
    sig = data[pos:pos+4].decode()
    sz = struct.unpack_from('<I', data, pos+4)[0]
    flags = struct.unpack_from('<I', data, pos+8)[0]
    fid = struct.unpack_from('<I', data, pos+12)[0]
    print(f'STAT 0x{fid:08X}: flags=0x{flags:08X}')
    pos += 24 + sz

# Check ALL REFR flags for variation
print('\n=== REFR Record Flags (sampling) ===')
rp = 92029 + 24
flag_counts = {}
refr_count = 0
while rp < 119829:
    sig = data[rp:rp+4]
    if sig != b'REFR':
        break
    sz = struct.unpack_from('<I', data, rp+4)[0]
    flags = struct.unpack_from('<I', data, rp+8)[0]
    flag_hex = f'0x{flags:08X}'
    flag_counts[flag_hex] = flag_counts.get(flag_hex, 0) + 1
    refr_count += 1
    rp += 24 + sz

print(f'Total REFRs: {refr_count}')
print(f'Flag distributions:')
for flag, count in sorted(flag_counts.items()):
    print(f'  {flag}: {count} records')

# Decode the most common flags
print('\n=== Flag Decode (for 0x00010400) ===')
f = 0x00010400
print(f'  Bit 8  (0x100):  {bool(f & 0x100)} -- Is Persistent in Starfield?')
print(f'  Bit 10 (0x400):  {bool(f & 0x400)} -- Full LOD?')
print(f'  Bit 16 (0x10000): {bool(f & 0x10000)} -- ??')
