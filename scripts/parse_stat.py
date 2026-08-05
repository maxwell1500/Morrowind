"""Parse a real Starfield STAT record fully - safe output."""
import struct

with open(r"C:\XboxGames\Starfield\Content\Data\Starfield.esm", "rb") as f:
    data = f.read()

# STAT at 0x722b95
pos = 0x722b95
size = struct.unpack("<I", data[pos+4:pos+8])[0]
flags = struct.unpack("<I", data[pos+8:pos+12])[0]
formid = struct.unpack("<I", data[pos+12:pos+16])[0]
print(f"STAT at 0x{pos:x}: size={size} flags=0x{flags:08X} formid=0x{formid:08X}")

chunk = data[pos+16:pos+16+size]
print(f"first 80 bytes: {chunk[:80].hex()}")

# First 8 bytes seem to be a prefix like in CELL? Actually Starfield STATs might also have prefix.
print(f"uint32 at 0: {struct.unpack('<I', chunk[:4])[0]} hex: {chunk[:4].hex()}")
print(f"uint32 at 4: {hex(struct.unpack('<I', chunk[4:8])[0])}")

# Parse subrecords starting at byte 8 (or maybe byte 0 if no prefix for STAT)
for start in [0, 8]:
    print(f"\nTrying subrecords at offset {start}:")
    p = start
    while p < len(chunk) - 6:
        sig_bytes = chunk[p:p+4]
        sig = sig_bytes.decode("ascii", errors="replace")
        sz = struct.unpack("<H", chunk[p+4:p+6])[0]
        if not all(b >= 32 and b <= 126 for b in sig_bytes):
            print(f"  stopping at 0x{p:x}: sig_hex={sig_bytes.hex()} size={sz}")
            break
        if sz > 1000:
            print(f"  suspicious size at 0x{p:x}: sig={sig!r} size={sz}")
            break
        print(f"  0x{p:x}: {sig} size={sz}")
        p += 6 + sz
        if p > len(chunk):
            print("  overran")
            break
