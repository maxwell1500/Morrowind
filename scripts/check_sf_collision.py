import struct

# Check Starfield native NIF for bhkNP blocks
with open(r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BedBunk01.nif', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')

# Search for bhkNP or bhkR
for marker in [b'bhkNP', b'bhkR', b'bhkC', b'bhkBV', b'bhkRigidBody', b'bhkBoxShape', b'bhkConvex']:
    marker_name = marker.decode()
    idx = data.find(marker)
    if idx >= 0:
        print(f'Found "{marker_name}" at offset {idx}')
    else:
        print(f'"{marker_name}" not found')

# Check version
version = data[24:64].decode('ascii', errors='ignore')
print(f'Version: {version}')
