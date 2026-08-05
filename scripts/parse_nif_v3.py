import struct

with open(r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BedBunk01.nif', 'rb') as f:
    data = f.read()

# Find block type strings (4-byte length + string)
pos = 64
strings = []
while pos < len(data) - 8:
    # Check if this looks like a length prefix (1-50 bytes)
    length = struct.unpack_from('<I', data, pos)[0]
    if length == 0 or length > 50 or pos + 4 + length > len(data):
        break
    s = data[pos+4:pos+4+length]
    try:
        s.decode('ascii')
        strings.append(s.decode('ascii'))
        pos += 4 + length
    except:
        break

print('Block types:')
for i, s in enumerate(strings):
    print(f'  {i}: {s}')

# Now find block data
# Block data starts after the block type strings
# Each block: block_type_index (uint32) + data_size (uint32) + data

# The block data section should have blocks referencing the types above
# bhkNPCollisionObject is index 2, bhkPhysicsSystem is index 3

# Let's search for the block data by looking for known patterns
# bhkNPCollisionObject has 20 bytes of data
# bhkPhysicsSystem has 16 bytes of data

# Find "bhkNP" in the raw data to locate the block data section
bhknp_pos = data.find(b'bhkNP')
print(f'\nbhkNP string at offset {bhknp_pos}')

# The block data should be after the string table
# Let's print from offset 200 onwards to find it
print('\nLooking for block data (offset 200+):')
for i in range(200, min(500, len(data)), 16):
    if data[i:i+4] in [b'\x00\x00\x00\x02', b'\x00\x00\x00\x03']:  # indices 2 and 3
        print(f'Found block index 2 or 3 at offset {i}')
        print(f'  Context: {data[i-16:i+32].hex()}')
