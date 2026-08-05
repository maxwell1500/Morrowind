import struct

data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()

print('Scanning all 4-byte values in SeydaNeen.esp for 0x00000240:')
count = 0
for i in range(len(data) - 3):
    val = struct.unpack('<I', data[i:i+4])[0]
    if val == 0x00000240:
        print(f'  offset 0x{i:x}: context {data[max(0,i-4):i+8].hex()}')
        count += 1
print(f'Total occurrences: {count}')
