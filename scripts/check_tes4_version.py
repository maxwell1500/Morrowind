"""Check TES4 version field vs STAT prefixes."""
import struct

with open(r"C:\XboxGames\Starfield\Content\Data\Starfield.esm", "rb") as f:
    data = f.read()

print("Starfield.esm TES4 header:")
for i in range(0, 24, 4):
    val = struct.unpack("<I", data[i:i+4])[0]
    print(f"  0x{i:x}-{i+4:x}: {data[i:i+4].hex()} = {val} ({hex(val)})")

stat_prefix = data[0x722b95+16:0x722b95+24]
print(f"\nSTAT at 0x722b95 data first 8 bytes: {stat_prefix.hex()}")

with open(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm", "rb") as f:
    data2 = f.read()
print("\nImperialCity.esm TES4 header:")
for i in range(0, 24, 4):
    val = struct.unpack("<I", data2[i:i+4])[0]
    print(f"  0x{i:x}-{i+4:x}: {data2[i:i+4].hex()} = {val} ({hex(val)})")

ic_stat_prefix = data2[0x233b+16:0x233b+24]
print(f"\nImperialCity STAT at 0x233b data first 8 bytes: {ic_stat_prefix.hex()}")

# Also check our generated file
with open(r"C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp", "rb") as f:
    data3 = f.read()
print("\nSeydaNeen.esp TES4 header:")
for i in range(0, 24, 4):
    val = struct.unpack("<I", data3[i:i+4])[0]
    print(f"  0x{i:x}-{i+4:x}: {data3[i:i+4].hex()} = {val} ({hex(val)})")
cell_prefix = data3[0xd9+16:0xd9+24]
print(f"\nSeydaNeen CELL data first 8 bytes: {cell_prefix.hex()}")
