import struct

with open(r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_de_docks_center.nif', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')

# NIF header is 40 bytes
# Version string is at offset 24, 40 bytes
version = data[24:64].decode('ascii', errors='ignore')
print(f'Version (offset 24-64): "{version}"')

# The block type string table is usually after the version string
# Let's look for "NiNode" or "BSGeometry" to find where it starts
for marker in [b'NiNode', b'BSGeometry', b'bhkNP', b'bhkR']:
    idx = data.find(marker)
    if idx >= 0:
        print(f'Found "{marker}" at offset {idx}')

# Try to find the block type string table
# In Skyrim/FO4 NIFs, it's right after the header
# Header is 40 bytes, then block type strings
# But in Starfield NIFs, the structure might be different

# Let's print the first 200 bytes
print('\nFirst 200 bytes (hex):')
for i in range(0, min(200, len(data)), 16):
    hex_str = data[i:i+16].hex()
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f'{i:4d}: {hex_str:<32} {ascii_str}')
