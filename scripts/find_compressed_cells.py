"""Find and dump compressed CELL records from ImperialCity or Starfield.esm - fast scan."""
import struct, zlib

def find_compressed_cells(path, max_results=3):
    with open(path, "rb") as f:
        data = f.read()
    # Fast scan: jump to every CELL signature
    pos = 0
    found = 0
    while True:
        pos = data.find(b"CELL", pos)
        if pos == -1:
            break
        if pos + 16 <= len(data):
            try:
                size = struct.unpack("<I", data[pos+4:pos+8])[0]
                flags = struct.unpack("<I", data[pos+8:pos+12])[0]
                formid = struct.unpack("<I", data[pos+12:pos+16])[0]
                if (flags & 0x00040000) and 4 < size < 5000 and pos + 16 + size <= len(data):
                    chunk = data[pos+16:pos+16+size]
                    uncomp = struct.unpack("<I", chunk[:4])[0]
                    if 0 < uncomp < 20000:
                        print(f"CELL at 0x{pos:x}: size={size} flags=0x{flags:08X} formid=0x{formid:08X}")
                        print(f"  uncompressed prefix={uncomp}")
                        print(f"  payload size={size-4}")
                        print(f"  first 8 bytes: {chunk[:8].hex()}")
                        try:
                            decomp = zlib.decompress(chunk[4:])
                            print(f"  python zlib OK, len={len(decomp)}")
                            print(f"  first subrecord sig={decomp[:4].decode('ascii', errors='replace')}")
                        except Exception as e:
                            print(f"  python zlib failed: {e}")
                        print()
                        found += 1
                        if found >= max_results:
                            return
            except Exception:
                pass
        pos += 1

print("=== ImperialCity compressed CELLs ===")
find_compressed_cells(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm")
print("=== Starfield.esm compressed CELLs ===")
find_compressed_cells(r"C:\XboxGames\Starfield\Content\Data\Starfield.esm", 2)
