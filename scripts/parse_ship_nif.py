import struct

with open(r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_ShipModel01.nif', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')

# Parse block type string table
pos = 72
num_strings = struct.unpack_from('<H', data, pos)[0]
print(f'Number of block types: {num_strings}')
pos += 2

strings = []
for i in range(num_strings):
    length = struct.unpack_from('<I', data, pos)[0]
    pos += 4
    s = data[pos:pos+length].decode('ascii', errors='ignore')
    strings.append(s)
    print(f'  {i}: {s} (length {length})')
    pos += length

print(f'\nBlock data starts at offset: {pos}')

# Find bhkNP and bhkPhysics indices
bhknp_idx = None
bhkps_idx = None
for i, s in enumerate(strings):
    if s == 'bhkNPCollisionObject':
        bhknp_idx = i
        print(f'\nbhkNPCollisionObject is at index {i}')
    if s == 'bhkPhysicsSystem':
        bhkps_idx = i
        print(f'bhkPhysicsSystem is at index {i}')

# Now parse block data
# Each block: block_type_index (uint32) + data_size (uint32) + data
print(f'\nParsing block data:')
while pos < len(data) - 8:
    block_type_idx = struct.unpack_from('<I', data, pos)[0]
    data_size = struct.unpack_from('<I', data, pos+4)[0]
    block_type_name = strings[block_type_idx] if block_type_idx < len(strings) else f'UNKNOWN({block_type_idx})'
    
    if block_type_name in ['bhkNPCollisionObject', 'bhkPhysicsSystem', 'NiNode']:
        print(f'\n{block_type_name} (index {block_type_idx}, size {data_size}):')
        print(f'  Hex (first 80 bytes): {data[pos:pos+min(88, 8+data_size)].hex()}')
    
    pos += 8 + data_size
