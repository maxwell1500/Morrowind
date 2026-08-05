"""Find and dump STAT records from Starfield.esm or ImperialCity.esm."""
import struct

def dump_stat(path, max_results=5):
    with open(path, "rb") as f:
        data = f.read()
    pos = 0
    found = 0
    while pos < len(data) - 16 and found < max_results:
        if data[pos:pos+4] == b"STAT":
            try:
                size = struct.unpack("<I", data[pos+4:pos+8])[0]
                flags = struct.unpack("<I", data[pos+8:pos+12])[0]
                formid = struct.unpack("<I", data[pos+12:pos+16])[0]
                if 0 < size < 2000:
                    chunk = data[pos+16:pos+16+size]
                    print(f"STAT at 0x{pos:x}: size={size} flags=0x{flags:08X} formid=0x{formid:08X}")
                    print(f"  first 64 bytes: {chunk[:64].hex()}")
                    if not (flags & 0x00040000):
                        # uncompressed
                        p = 0
                        while p < len(chunk) - 6:
                            sig = chunk[p:p+4].decode("ascii", errors="replace")
                            sz = struct.unpack("<H", chunk[p+4:p+6])[0]
                            if sig.isalpha() and sz < 1000:
                                print(f"    subrecord {sig} size={sz}")
                                p += 6 + sz
                            else:
                                break
                    found += 1
                    print()
            except Exception as e:
                pass
        pos += 1

print("=== ImperialCity STATs ===")
dump_stat(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm")
print("=== Starfield.esm STATs ===")
dump_stat(r"C:\XboxGames\Starfield\Content\Data\Starfield.esm", 3)
