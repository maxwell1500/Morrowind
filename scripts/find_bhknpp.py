import struct

with open(r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BedBunk01.nif', 'rb') as f:
    data = f.read()

# Find all occurrences of "bhkNP"
pos = 0
while True:
    idx = data.find(b'bhkNP', pos)
    if idx < 0:
        break
    print(f'Found "bhkNP" at offset {idx}')
    print(f'  Hex: {data[idx:idx+30].hex()}')
    print(f'  ASCII: {data[idx:idx+30]}')
    pos = idx + 1

# The bhkNP string is at offset 100 (as a block type name)
# The bhkNP block DATA should be somewhere else
# Let's search for the actual bhkNP block data

# In NIF, block data is stored after the block index table
# The block index table references block types by index
# bhkNPCollisionObject is index 2

# Let's find the block index table
# It should be a list of (block_type_index, data_offset) pairs

# Look for a pattern where we have:
# - uint32 block_type_index (should be 2 for bhkNP)
# - uint32 data_offset (relative to block data start)
# - Then the actual block data

# Search for 02 00 00 00 (block type index 2)
print('\nSearching for block type index 2 (bhkNPCollisionObject):')
pos = 0
while True:
    idx = data.find(b'\x02\x00\x00\x00', pos)
    if idx < 0:
        break
    # Check if this looks like a block index entry
    if idx + 8 <= len(data):
        data_offset = struct.unpack_from('<I', data, idx+4)[0]
        print(f'  Found at offset {idx}, data_offset: {data_offset}')
    pos = idx + 1
