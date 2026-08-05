import struct

with open(r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BedBunk01.nif', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')

# Print first 300 bytes
print('\nFirst 300 bytes (hex + ascii):')
for i in range(0, min(300, len(data)), 16):
    hex_str = data[i:i+16].hex()
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f'{i:4d}: {hex_str:<32} {ascii_str}')

# Find all occurrences of "bhkNP"
print('\nSearching for "bhkNP":')
pos = 0
while True:
    idx = data.find(b'bhkNP', pos)
    if idx < 0:
        break
    print(f'  Found at offset {idx}')
    print(f'    Context: {data[idx-10:idx+20].hex()}')
    pos = idx + 1
