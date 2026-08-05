"""Parse BFCB component subrecords in Starfield STAT records."""
import struct

with open(r"C:\XboxGames\Starfield\Content\Data\Starfield.esm", "rb") as f:
    data = f.read()

pos = 0x722b95
size = struct.unpack("<I", data[pos+4:pos+8])[0]
chunk = data[pos+16:pos+16+size]

# Subrecords start at byte 8
p = 8
while p < len(chunk) - 6:
    sig = chunk[p:p+4].decode("ascii", errors="replace")
    sz = struct.unpack("<H", chunk[p+4:p+6])[0]
    if not all(32 <= b <= 126 for b in chunk[p:p+4]) or sz > 1000:
        break
    d = chunk[p+6:p+6+sz]
    print(f"\n=== {sig} size={sz} ===")
    print(f"hex: {d.hex()}")
    print(f"len: {len(d)}")
    if sig in ["BFCB", "BFCE", "MODL", "FLTR", "EDID"]:
        print(f"text: {''.join(chr(b) if 32 <= b < 127 else '.' for b in d)}")
    if sig == "BFCB":
        # Component data may have internal structure
        if sz >= 4:
            print(f"  uint32 at 0: {struct.unpack('<I', d[:4])[0]}")
        if sz >= 8:
            print(f"  uint32 at 4: {struct.unpack('<I', d[4:8])[0]}")
    p += 6 + sz
