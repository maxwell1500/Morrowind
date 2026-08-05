"""Analyze the prefix of compressed CELL records."""
import struct

with open(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm", "rb") as f:
    data = f.read()

positions = [0x5b80, 0x652e, 0x6714, 0x694c, 0x87b0, 0x9908]
for pos in positions:
    size = struct.unpack("<I", data[pos+4:pos+8])[0]
    flags = struct.unpack("<I", data[pos+8:pos+12])[0]
    if flags & 0x00040000:
        chunk = data[pos+16:pos+16+size]
        print(f"CELL 0x{pos:x}: size={size}")
        print(f"  first 16 bytes: {chunk[:16].hex()}")
        print(f"  uint32 at 0: {struct.unpack('<I', chunk[:4])[0]}")
        print(f"  uint32 at 4: {hex(struct.unpack('<I', chunk[4:8])[0])}")
        print(f"  uint32 at 8: {struct.unpack('<I', chunk[8:12])[0]}")
