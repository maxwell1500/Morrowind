"""Dump subrecords of a Starfield STAT record - safe output."""
import struct

with open(r"C:\XboxGames\Starfield\Content\Data\Starfield.esm", "rb") as f:
    data = f.read()

pos = 0x722b95
size = struct.unpack("<I", data[pos+4:pos+8])[0]
chunk = data[pos+16:pos+16+size]

p = 8
while p < len(chunk) - 6:
    sig = chunk[p:p+4].decode("ascii", errors="replace")
    sz = struct.unpack("<H", chunk[p+4:p+6])[0]
    if not all(b >= 32 and b <= 126 for b in chunk[p:p+4]) or sz > 1000:
        print(f"stopping at 0x{p:x}: hex={chunk[p:p+4].hex()}")
        break
    data_bytes = chunk[p+6:p+6+min(sz, 40)]
    text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data_bytes)
    print(f"0x{p:x}: {sig} size={sz} data={data_bytes.hex()} text={text}")
    p += 6 + sz
