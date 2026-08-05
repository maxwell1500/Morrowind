"""Debug GRUP boundary."""
import struct

with open(r"C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp", "rb") as f:
    data = f.read()

print("Bytes at 0xd0-0xe0:", data[0xd0:0xe0].hex())
print("Bytes at 0xd5-0xe0:", data[0xd5:0xe0].hex())
print("Interpreted as little-endian uint32:")
for i in range(0xd5, 0xe0, 4):
    print(f"  0x{i:x}: {int.from_bytes(data[i:i+4], 'little')}")

# Let's verify sub-block size 256 means content length 232 bytes from 0xd5 to 0x1bd
print(f"Sub-block at 0xbd, size=256, content_end = 0xbd + 256 = 0x{0xbd + 256:x}")
print(f"Content range: 0xd5 - 0x{0xbd + 256:x} (length {0xbd + 256 - 0xd5})")
