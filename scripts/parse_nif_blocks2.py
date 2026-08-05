import struct

with open(r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BedBunk01.nif', 'rb') as f:
    data = f.read()

# Parse block type string table
# Starts at offset 64 (after 40-byte version string + 8-byte hash)
pos = 64
num_strings = struct.unpack_from('<H', data, pos)[0]
print(f'Number of block types: {num_strings}')
pos += 2

strings = []
for i in range(num_strings):
    length = struct.unpack_from('<I', data, pos)[0]
    pos += 4
    s = data[pos:pos+length].decode('ascii')
    strings.append(s)
    print(f'  {i}: {s} (length {length})')
    pos += length

print(f'\nBlock data starts at offset: {pos}')

# Now parse block data
# Each block: block_type_index (uint32) + data_size (uint32) + data
# Find blocks with index 2 (bhkNPCollisionObject) and 3 (bhkPhysicsSystem)

print('\nParsing block data:')
while pos < len(data) - 8:
    block_type_idx = struct.unpack_from('<I', data, pos)[0]
    data_size = struct.unpack_from('<I', data, pos+4)[0]
    block_type_name = strings[block_type_idx] if block_type_idx < len(strings) else f'UNKNOWN({block_type_idx})'
    
    if block_type_name in ['bhkNPCollisionObject', 'bhkPhysicsSystem']:
        print(f'\n{block_type_name} (index {block_type_idx}, size {data_size}):')
        print(f'  Hex: {data[pos:pos+min(48, 8+data_size)].hex()}')
        print(f'  Bytes:')
        for j in range(pos, pos+min(48, 8+data_size)):
            print(f'    {j}: {data[j]:02x} ({chr(data[j]) if 32 <= data[j] < 127 else "."})')
    
    pos += 8 + data_size
