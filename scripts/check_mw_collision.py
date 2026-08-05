import struct

# Check original Morrowind dock NIF
with open(r'C:\Users\max\Projects\Morrowind\raw_assets\Morrowind_Full\meshes\x\ex_de_docks_center.nif', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')

# Search for collision-related markers
for marker in [b'bhkNP', b'bhkR', b'bhkC', b'RootCollision', b'NiCollision', b'NiTriShape']:
    marker_name = marker.decode()
    idx = data.find(marker)
    if idx >= 0:
        print(f'Found "{marker_name}" at offset {idx}')
    else:
        print(f'"{marker_name}" not found')

# Check version
version = data[24:64].decode('ascii', errors='ignore')
print(f'Version: {version}')
