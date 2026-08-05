"""Analyze prefix of uncompressed CELL records."""
import struct

with open(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm", "rb") as f:
    data = f.read()

positions = [0x6622, 0x8830, 0x889a, 0x8a1c, 0x8a86]
for pos in positions:
    size = struct.unpack("<I", data[pos+4:pos+8])[0]
    flags = struct.unpack("<I", data[pos+8:pos+12])[0]
    chunk = data[pos+16:pos+16+size]
    print(f"CELL 0x{pos:x}: size={size} flags=0x{flags:08X}")
    print(f"  first 16 bytes: {chunk[:16].hex()}")
    print(f"  uint32 at 0: {struct.unpack('<I', chunk[:4])[0]}")
    print(f"  uint32 at 4: {hex(struct.unpack('<I', chunk[4:8])[0])}")
