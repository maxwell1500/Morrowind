import struct

with open(r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BedBunk01.nif', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')

# Print hex dump with clear byte boundaries
print('\nHex dump (bytes 60-120):')
for i in range(60, 120):
    b = data[i]
    print(f'{i:3d}: {b:02x} ({chr(b) if 32 <= b < 127 else "."})')
