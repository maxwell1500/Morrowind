import struct

with open(r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BedBunk01.nif', 'rb') as f:
    data = f.read()

# The block type string table is at offset 72-200
# After that is the node data (parent/child pointers)
# Then block data for each node

# Let's look for "bhkNP" in the raw data to find where the bhkNP block data is
# The bhkNP string is at offset 100 (in the string table)
# The bhkNP block data should be elsewhere

# Search for bhkNP in the file (excluding the string table at 100)
pos = 200  # Skip the string table
while True:
    idx = data.find(b'bhkNP', pos)
    if idx < 0:
        break
    print(f'Found "bhkNP" at offset {idx}')
    # Print context
    print(f'  Context: {data[idx-20:idx+40].hex()}')
    pos = idx + 1

# Also search for the bhkNP block data by looking for known patterns
# bhkNPCollisionObject has:
# - NiNode base (parent pointer, children pointers)
# - hkpCollisionObject base
# - transform matrix (4x4 floats)

# Let's look at the end of the file where block data is usually stored
print('\nEnd of file (last 500 bytes):')
start = max(0, len(data) - 500)
for i in range(start, len(data), 16):
    hex_str = data[i:i+16].hex()
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f'{i:4d}: {hex_str:<32} {ascii_str}')
