import struct
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
target = struct.pack('<I', 0x00000240)
print('Occurrences of 40020000 (0x240):')
for i in range(len(data) - 4):
    if data[i:i+4] == target:
        print(f'  0x{i:x}: context = {data[max(0,i-8):i+8].hex()}')
