import struct

new = open(r'C:\Users\max\Projects\Morrowind\ex_nord_house_03.nif', 'rb').read()

# bhk data: @244 to @484 (240 bytes)
bhk = new[244:484]
print(f'bhk data: {len(bhk)} bytes')
print('Hex dump:')
for i in range(0, len(bhk), 32):
    chunk = bhk[i:i+32]
    hex_str = ' '.join(f'{b:02x}' for b in chunk)
    print(f'  +{i:3d}: {hex_str}')

# The first part is 0x01000100 pattern repeated - this might be a header
# Or these might be block references (block type, block size, ...)
# Looking at the data:
# 01 00 = 1
# 01 00 = 1
# 01 00 = 1
# 01 00 = 1
# ... repeated 10 times
# 02 00 = 2
# 03 00 = 3
# 04 00 = 4
# 03 00 = 3
# 04 00 = 3
# 04 00 = 3
# 04 00 = 3
# 04 00 = 3
# 04 00 = 3
# 04 00 = 3
# 04 00 = 3
# 04 00 = 3
# 04 00 = 3
# 05 00 = 5
# 06 00 = 6
# 07 00 = 7

# Looking at this as a sequence of uint16:
# 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 5, 6, 7
# That's 34 entries. With 3 new bhk block types + 31 existing = 34 total blocks
# Hmm, but the original had 32 blocks. NEW has 35 block types, so still 32 blocks (no new blocks were added to the main index).

# So this 0x01000100 pattern is something else - maybe a NIF 20.x block index
# Each entry might be (block_type_index, block_size) in some encoding

# Let me look at the rest of the data
print('\nFull bytes:')
print(bhk.hex())
print()
print('As uint16:')
for i in range(0, len(bhk), 2):
    val = struct.unpack('<H', bhk[i:i+2])[0]
    print(f'  +{i}: {val}')
