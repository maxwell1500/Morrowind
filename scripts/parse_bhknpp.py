import struct

with open(r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BedBunk01.nif', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')

# Find block type string table
pos = 64
strings = []
while pos < len(data) - 4:
    length = struct.unpack_from('<I', data, pos)[0]
    if length > 100 or length < 1 or pos + 4 + length > len(data):
        break
    s = data[pos+4:pos+4+length]
    try:
        s.decode('ascii')
        strings.append(s.decode('ascii'))
        pos += 4 + length
        pos = (pos + 3) & ~3
    except:
        break

print('Block types:')
for s in strings:
    print(f'  {s}')

# Find bhkNP block
bhknp_idx = strings.index('bhkNP')
print(f'\nbhkNP is block type index: {bhknp_idx}')

# Now find the block data (block index table)
# Block index table starts after version string + block type strings
# Each entry is a 4-byte block type index + 4-byte data offset (relative to block data start)
print('\nLooking for block index table...')

# The block index table is typically right after the header and string table
# Let's find "bhkNP" in the strings and look for the block data

# Find the bhkNP block data
# In NIF, block data comes after the header
# Each block has: block_type_index (uint32) + data_size (uint32) + data

# Let's search for the block data section
# Block data starts after the block index table
# Block index table size = num_blocks * 8 bytes

# Find "bhkNP" in the raw data to locate the block data
bhknp_pos = data.find(b'bhkNP')
print(f'bhkNP string found at offset {bhknp_pos}')

# The block data should be near this position
# Let's print the area around it
print(f'\nHex dump around offset {bhknp_pos}:')
for i in range(bhknp_pos - 20, min(bhknp_pos + 200, len(data)), 16):
    hex_str = data[i:i+16].hex()
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f'{i:4d}: {hex_str:<32} {ascii_str}')
