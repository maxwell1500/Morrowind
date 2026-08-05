import struct

with open(r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')

# Parse block type string table (starts at offset 72)
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
    print(f'  {i}: {s} (len {length})')
    pos += length

print(f'\nBlock data starts at offset: {pos}')

# Parse block data - find bhkNP blocks
bhknp_blocks = []
bhkps_blocks = []
while pos < len(data) - 8:
    block_type_idx = struct.unpack_from('<I', data, pos)[0]
    data_size = struct.unpack_from('<I', data, pos+4)[0]
    block_type_name = strings[block_type_idx] if block_type_idx < len(strings) else f'UNKNOWN({block_type_idx})'
    
    if block_type_name == 'bhkNPCollisionObject':
        bhknp_blocks.append((pos, data_size, data[pos:pos+8+data_size]))
        print(f'\nbhkNPCollisionObject at {pos}, size {data_size}:')
        print(f'  {data[pos:pos+min(88, 8+data_size)].hex()}')
    
    if block_type_name == 'bhkPhysicsSystem':
        bhkps_blocks.append((pos, data_size, data[pos:pos+8+data_size]))
        print(f'\nbhkPhysicsSystem at {pos}, size {data_size}:')
        print(f'  {data[pos:pos+min(88, 8+data_size)].hex()}')
    
    pos += 8 + data_size

print(f'\nTotal bhkNP blocks: {len(bhknp_blocks)}')
print(f'Total bhkPS blocks: {len(bhkps_blocks)}')
