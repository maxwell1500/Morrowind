"""Parse the kitchen NIF to find bhk data structure."""
import struct
import re

path = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif"
with open(path, 'rb') as f:
    data = f.read()

# The header is 40 bytes (version string) + 4 bytes (0x00 0x02 0x14 0x01) + 4 bytes (num_roots = 0x0C = 12)
# Then more...
# Let me try to figure out the NIF 20.x structure

# I see at offset 80: 'Node\0' (this is a length-prefixed string with 4-byte length prefix)
# 4e 6f 64 65 = "Node"
# 08 00 00 00 = 8 = length
# Then 4e 6f 64 65 00 00 00 00 = "Node\0" + 3 bytes padding
# Wait - let me recount

# At offset 76: 01 00 03 00 (4 bytes)
# At offset 80: 00 00 00 14 (4 bytes) - 0x14 = 20
# At offset 84: 42 6c 65 6e 64 65 72 20 4d 65 73 68 20 50 6c 75 67 69 6e 00 (20 bytes "Blender Mesh Plugin\0")

# Hmm, let me look at this as: header
# After version string (40 bytes):
# 4 bytes 0x00021401
# 4 bytes 0x0000000C (some count = 12)
# 4 bytes ? 
# ...

# Let's look at the structure I see at offset 76
print('Bytes 40-200:')
for i in range(40, 200, 4):
    val = struct.unpack('<I', data[i:i+4])[0]
    print(f'  @{i:4d}: 0x{val:08X} = {val}')
print()

# The NIF 20.x format from NifSkope source:
# Header:
#  - 40 bytes version string
#  - 4 bytes header version (0x00021401 for v20.2.0.7)
#  - 4 bytes max string length (e.g., 0x0C00 = 3072)
#  - 4 bytes unknown
# Then a block type table:
#  - num_block_types uint32
#  - For each block type: 4 bytes length + string bytes (4-aligned)
#  - 4 bytes num_blocks
#  - 4 bytes num_roots
#  - num_roots * 4 bytes: root block indices
#  - num_blocks * (4+4+4+4) bytes: block index (block_type_index, block_size, ?, ?)
# Then block data

# But I'm not sure about the structure. Let me try a different approach
# The NifSkope source has a "BSDStream" file reader for NIF 20.2.0.7

# Let me find the offsets of certain block types
for marker, name in [(b'BSXFlags', 'BSXFlags'), (b'bhkNPCollisionObject', 'bhkNP'), (b'bhkPhysicsSystem', 'bhkPhys'), (b'BSGeometry', 'BSGeo'), (b'NiIntegerExtraData', 'NiInt'), (b'BSLightingShaderProperty', 'BSLSP'), (b'MaterialID', 'MatID')]:
    p = data.find(marker)
    while p != -1:
        # 4 bytes before this is the length
        if p >= 4:
            length = struct.unpack('<I', data[p-4:p])[0]
        else:
            length = -1
        print(f"  {name} at offset {p}, length prefix={length}")
        p = data.find(marker, p+1)

print()
# Find all length-prefixed strings
print("\nLooking at offset 76 area:")
for off in range(76, 200, 4):
    val = struct.unpack('<I', data[off:off+4])[0]
    # If this is a small length, look for string after it
    if 1 <= val <= 50:
        s = data[off+4:off+4+val]
        try:
            decoded = s.rstrip(b'\x00').decode('ascii')
            if all(32 <= b < 127 for b in s):
                print(f"  @{off}: length={val} string={decoded!r}")
        except:
            pass
