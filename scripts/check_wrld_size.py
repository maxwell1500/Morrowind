"""Check WRLD record size vs parsed subrecords."""
import struct

with open(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm", "rb") as f:
    data = f.read()

pos = 0x63a8
size = struct.unpack("<I", data[pos+4:pos+8])[0]
chunk = data[pos+16:pos+16+size]
print(f"size={size}, chunk_len={len(chunk)}")
print(f"bytes after 0x151: {chunk[0x151:0x160].hex()}")

# Parse subrecords
p = 8
while p < len(chunk) - 6:
    sig = chunk[p:p+4].decode("ascii", errors="replace")
    sz = struct.unpack("<H", chunk[p+4:p+6])[0]
    if not all(32 <= b <= 126 for b in chunk[p:p+4]) or sz > 1000:
        print(f"stopping at 0x{p:x}: hex={chunk[p:p+4].hex()}")
        break
    p += 6 + sz
print(f"parsed subrecords end at 0x{p:x}")
print(f"remaining bytes: {len(chunk) - p}")
