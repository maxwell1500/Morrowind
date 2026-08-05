"""Check ImperialCity WRLD structure."""
import struct

with open(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm", "rb") as f:
    data = f.read()

pos = 0x6390
if data[pos:pos+4] == b"GRUP":
    gsize = struct.unpack("<I", data[pos+4:pos+8])[0]
    print(f"WRLD GRUP at 0x{pos:x}, size={gsize}")
    inner = pos + 24
    inner_end = pos + gsize
    while inner < inner_end:
        if data[inner:inner+4] == b"GRUP":
            igsize = struct.unpack("<I", data[inner+4:inner+8])[0]
            try:
                ilabel = data[inner+8:inner+12].decode("ascii")
            except:
                ilabel = data[inner+8:inner+12].hex()
            igtype = struct.unpack("<I", data[inner+12:inner+16])[0]
            print(f"  Child GRUP at 0x{inner:x}: label={ilabel!r} type={igtype} size={igsize}")
            inner += igsize
        elif data[inner:inner+4] == b"WRLD":
            size = struct.unpack("<I", data[inner+4:inner+8])[0]
            flags = struct.unpack("<I", data[inner+8:inner+12])[0]
            formid = struct.unpack("<I", data[inner+12:inner+16])[0]
            print(f"  WRLD RECORD at 0x{inner:x}: formid=0x{formid:08X} size={size} flags=0x{flags:08X}")
            inner += 16 + size
        else:
            print(f"  Unexpected at 0x{inner:x}: {data[inner:inner+4].hex()}")
            inner += 1
