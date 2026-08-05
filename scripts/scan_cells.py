"""Scan all CELL records in a file and show flags."""
import struct

path = r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm"
with open(path, "rb") as f:
    data = f.read()

pos = 0
count = 0
print(f"Scanning {path}")
while pos < len(data) - 16 and count < 20:
    if data[pos:pos+4] == b"CELL":
        try:
            size = struct.unpack("<I", data[pos+4:pos+8])[0]
            flags = struct.unpack("<I", data[pos+8:pos+12])[0]
            formid = struct.unpack("<I", data[pos+12:pos+16])[0]
            if size < 100000:
                chunk = data[pos+16:pos+16+min(size,16)]
                print(f"CELL 0x{pos:x}: size={size} flags=0x{flags:08X} formid=0x{formid:08X} firstbytes={chunk.hex()}")
                count += 1
        except Exception:
            pass
    pos += 1
