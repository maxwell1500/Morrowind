"""Parse ImperialCity.esm to compare with our ESP."""
import struct, zlib

with open(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm", "rb") as f:
    data = f.read()

def read_record(pos, depth=0):
    sig = data[pos:pos+4].decode("ascii", errors="replace")
    size = struct.unpack("<I", data[pos+4:pos+8])[0]
    flags = struct.unpack("<I", data[pos+8:pos+12])[0]
    formid = struct.unpack("<I", data[pos+12:pos+16])[0]
    total = 16 + size
    print(f"{'  '*depth}RECORD at 0x{pos:x}: {sig} size={size} flags=0x{flags:08X} formid=0x{formid:08X}")
    if sig == "CELL" and (flags & 0x00040000):
        chunk = data[pos+16:pos+16+size]
        uncomp_size = struct.unpack("<I", chunk[:4])[0]
        try:
            decomp = zlib.decompress(chunk[4:])
            print(f"{'  '*depth}  compressed, uncompressed prefix={uncomp_size}, decompressed={len(decomp)}")
        except Exception as e:
            print(f"{'  '*depth}  decompress error: {e}")
    return pos + total

def read_grup(pos, depth=0):
    if data[pos:pos+4] != b"GRUP":
        print(f"{'  '*depth}Not a GRUP at 0x{pos:x}: {data[pos:pos+4]}")
        return pos + 1
    size = struct.unpack("<I", data[pos+4:pos+8])[0]
    label = data[pos+8:pos+12]
    try:
        label_str = label.decode("ascii")
    except:
        label_str = f"0x{label.hex()}"
    gtype = struct.unpack("<I", data[pos+12:pos+16])[0]
    content_size = size - 24
    print(f"{'  '*depth}GRUP at 0x{pos:x}: label={label_str!r} type={gtype} size={size} content={content_size}")
    end = pos + size
    inner = pos + 24
    indent = depth + 1
    while inner < end:
        if data[inner:inner+4] == b"GRUP":
            inner = read_grup(inner, indent)
        elif data[inner:inner+4].isalpha():
            inner = read_record(inner, indent)
        else:
            print(f"{'  '*indent}Unknown at 0x{inner:x}: {data[inner:inner+4].hex()}")
            inner += 1
    return end

# TES4
print("=== TES4 Header ===")
print(f"sig={data[0:4].decode()} size={struct.unpack('<I', data[4:8])[0]} flags=0x{struct.unpack('<I', data[8:12])[0]:08X}")

# Top-level GRUPs
tes4_size = struct.unpack("<I", data[4:8])[0]
pos = 20 + tes4_size
print(f"\n=== Top-level groups starting at 0x{pos:x} ===")
count = 0
while pos < len(data) and count < 5:
    pos = read_grup(pos, 0)
    print()
    count += 1
