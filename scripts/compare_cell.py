"""Find and compare first CELL record in ImperialCity.esm."""
import struct, zlib

def find_first_cell(path):
    with open(path, "rb") as f:
        data = f.read()
    # Find first "CELL" that looks like a record header
    pos = 0
    while True:
        pos = data.find(b"CELL", pos)
        if pos == -1:
            return None
        # Check if it's followed by a reasonable size
        try:
            size = struct.unpack("<I", data[pos+4:pos+8])[0]
            flags = struct.unpack("<I", data[pos+8:pos+12])[0]
            if size < 100000:
                return pos
        except:
            pass
        pos += 1

def dump_cell(path, offset=None):
    with open(path, "rb") as f:
        data = f.read()
    if offset is None:
        offset = find_first_cell(path)
    print(f"First CELL at 0x{offset:x}")
    rec_sig = data[offset:offset+4].decode()
    rec_size = struct.unpack("<I", data[offset+4:offset+8])[0]
    flags = struct.unpack("<I", data[offset+8:offset+12])[0]
    formid = struct.unpack("<I", data[offset+12:offset+16])[0]
    chunk = data[offset+16:offset+16+rec_size]
    print(f"sig={rec_sig} size={rec_size} flags=0x{flags:08X} formid=0x{formid:08X}")
    print(f"first 16 bytes: {chunk[:16].hex()}")
    if flags & 0x00040000:
        uncompr_size = struct.unpack("<I", chunk[:4])[0]
        print(f"uncompressed size prefix: {uncompr_size}")
        decomp = zlib.decompress(chunk[4:])
        print(f"decompressed size: {len(decomp)}")
        print(f"first 64 bytes: {decomp[:64].hex()}")
        print("subrecords:")
        p = 0
        while p < len(decomp) - 6:
            sig = decomp[p:p+4].decode("ascii", errors="replace")
            size = struct.unpack("<H", decomp[p+4:p+6])[0]
            print(f"  0x{p:x}: {sig} size={size}")
            p += 6 + size
            if p > len(decomp):
                print("  WARNING: subrecord parsing overran")
                break
        return decomp
    else:
        print("not compressed")
        return chunk

print("=== ImperialCity first CELL ===")
dump_cell(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm")
print("\n=== Our CELL ===")
dump_cell(r"C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp", 0xec)
