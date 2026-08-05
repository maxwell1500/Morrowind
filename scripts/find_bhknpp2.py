import struct

with open(r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BedBunk01.nif', 'rb') as f:
    data = f.read()

# Find "bhkPhysicsSystem" in the raw data
bhkps_pos = data.find(b'bhkPhysicsSystem')
print(f'bhkPhysicsSystem string at offset {bhkps_pos}')

# The bhkPhysicsSystem block data should be nearby
# bhkPhysicsSystem has:
# - NiNode base class (pointer to parent, pointers to children)
# - hkpPhysicsSystem data

# Let's search for the block data section
# In NIF, the block data is typically at the end of the file or after the block index table

# Find "bhkNP" string position
bhknp_pos = data.find(b'bhkNP')
print(f'bhkNP string at offset {bhknp_pos}')

# The block data should be after all the block type strings
# Block type strings end at: 72 + 2 + sum(4 + len(s) for s in strings)
# Strings: NiNode(6), BSXFlags(8), bhkNPCollisionObject(20), bhkPhysicsSystem(16), BSGeometry(10), NiIntegerExtraData(18), BSLightingShaderProperty(24)
# Total: 72 + 2 + (4+6) + (4+8) + (4+20) + (4+16) + (4+10) + (4+18) + (4+24) = 72 + 2 + 126 = 200

# So block data starts at offset 200
# Let's print from offset 200 to 500
print('\nHex dump (offset 200-500):')
for i in range(200, 500, 16):
    hex_str = data[i:i+16].hex()
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f'{i:4d}: {hex_str:<32} {ascii_str}')
