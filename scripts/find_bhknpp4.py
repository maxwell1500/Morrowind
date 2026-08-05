import struct

with open(r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BedBunk01.nif', 'rb') as f:
    data = f.read()

# Let's look for the bhkNP block by searching for "bhkNP" in the context of block data
# The bhkNP string is at offset 100 (in the string table)
# The bhkNP block data should be elsewhere

# In NIF, the block data is typically stored as:
# - For each node:
#   - Node header (type index, data size)
#   - Node data
# - Then for each block type, the actual data

# Let's look at the structure around offset 200-400 more carefully
# This is where the node data and block data should be

# Search for "bhkNP" as a block type reference (not in the string table)
# The block type reference is a uint32 index into the string table
# bhkNP is index 2

# Look for pattern: uint32(2) + uint32(data_size) + data
# But this might be confused with other uint32(2) values

# Let's search for the bhkPhysicsSystem block instead
# bhkPhysicsSystem is index 3

# Actually, let's look at the NIF structure differently
# The block data is typically at the END of the file
# Let's look at the last 1000 bytes

print('Last 1000 bytes (hex):')
start = max(0, len(data) - 1000)
for i in range(start, len(data), 16):
    hex_str = data[i:i+16].hex()
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f'{i:4d}: {hex_str:<32} {ascii_str}')
