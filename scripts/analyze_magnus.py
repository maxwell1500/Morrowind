"""Analyze Magnus.esm structure - skip bad chars."""
import struct

with open(r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm", "rb") as f:
    data = f.read()

print(f"File size: {len(data)} bytes")
print(f"Header: {data[0:4].decode()}")
flags = struct.unpack("<I", data[8:12])[0]
print(f"Flags: 0x{flags:08X}")

# Find top-level GRUPs
tes4_size = struct.unpack("<I", data[4:8])[0]
pos = 20 + tes4_size
grup_count = 0
while pos < len(data) and grup_count < 30:
    if data[pos:pos+4] == b"GRUP":
        size = struct.unpack("<I", data[pos+4:pos+8])[0]
        label = data[pos+8:pos+12]
        gtype = struct.unpack("<I", data[pos+12:pos+16])[0]
        try:
            label_str = label.decode("ascii")
        except:
            label_str = label.hex()
        print(f"GRUP: label={label_str} type={gtype} size={size}")
        grup_count += 1
        pos += size + 8
    else:
        pos += 1
