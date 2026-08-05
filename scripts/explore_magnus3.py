"""Deep-dive into Morrowind WRLD children structure."""
import struct, zlib

PATH = r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm"

with open(PATH, "rb") as f:
    data = f.read()


def read_record_header(pos):
    sig = data[pos:pos+4].decode("ascii", errors="replace")
    size = struct.unpack("<I", data[pos+4:pos+8])[0]
    flags = struct.unpack("<I", data[pos+8:pos+12])[0]
    formid = struct.unpack("<I", data[pos+12:pos+16])[0]
    return sig, size, flags, formid


def decompress(flags, chunk):
    if not (flags & 0x00040000):
        return chunk
    try:
        return zlib.decompress(chunk[12:])
    except:
        return None


def parse_subrecords(chunk, has_prefix=True):
    start = 8 if has_prefix else 0
    pos = start
    result = []
    while pos < len(chunk) - 6:
        sig_bytes = chunk[pos:pos+4]
        if not all(32 <= b <= 126 for b in sig_bytes):
            break
        sig = sig_bytes.decode("ascii", errors="replace")
        sz = struct.unpack("<H", chunk[pos+4:pos+6])[0]
        if sz > 10000:
            break
        result.append({"sig": sig, "size": sz, "data": chunk[pos+6:pos+6+sz]})
        pos += 6 + sz
        if pos > len(chunk):
            break
    return result


def dump_grup(pos, depth=0, max_depth=3, max_records=5):
    if data[pos:pos+4] != b"GRUP":
        return None
    gsize = struct.unpack("<I", data[pos+4:pos+8])[0]
    label = data[pos+8:pos+12]
    gtype = struct.unpack("<I", data[pos+12:pos+16])[0]
    try:
        label_str = label.decode("ascii")
    except:
        label_str = f"0x{label.hex()}"
    print(f"{'  '*depth}GRUP 0x{pos:x}: label={label_str!r} type={gtype} size={gsize}")
    
    if depth >= max_depth:
        return pos + gsize
    
    inner = pos + 24
    inner_end = pos + gsize
    count = 0
    while inner < inner_end and count < max_records:
        if data[inner:inner+4] == b"GRUP":
            inner = dump_grup(inner, depth+1, max_depth, max_records)
        elif data[inner:inner+4].isalpha():
            sig, size, flags, formid = read_record_header(inner)
            print(f"{'  '*depth}  RECORD 0x{inner:x}: {sig} formid=0x{formid:08X} size={size} flags=0x{flags:08X}")
            inner += 16 + size
            count += 1
        else:
            inner += 1
    return pos + gsize


# Morrowind WRLD is at 0x7df88, its type-1 children GRUP at 0x7e0f9
print("=== WRLD Morrowind children (full tree) ===")
dump_grup(0x7e0f9, depth=0, max_depth=3, max_records=10)

# Also dump the first CELL subrecords
print("\n=== First CELL in Morrowind WRLD (0100E954) ===")
sig, size, flags, formid = read_record_header(0x7e111)
chunk = data[0x7e111+16:0x7e111+16+size]
decomp = decompress(flags, chunk)
subs = parse_subrecords(decomp or chunk)
for sr in subs:
    if sr["sig"] in ["EDID", "FULL", "XCLC", "XCLW", "DATA", "LTMP", "XLCN", "XCWT", "XOWN"]:
        text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in sr["data"][:min(sr["size"], 40)])
        print(f"  {sr['sig']} size={sr['size']}: {text}")
    elif sr["sig"] in ["NAME", "XLCN"]:
        val = struct.unpack("<I", sr["data"][:4])[0] if len(sr["data"]) >= 4 else 0
        print(f"  {sr['sig']} size={sr['size']}: formID=0x{val:08X}")

# Dump a few REFRs from the first type-4 GRUP
print("\n=== First few REFRs in type-4 children ===")
t4_pos = 0x7e3df
if data[t4_pos:t4_pos+4] == b"GRUP":
    gsize = struct.unpack("<I", data[t4_pos+4:t4_pos+8])[0]
    inner = t4_pos + 24
    inner_end = t4_pos + gsize
    count = 0
    while inner < inner_end and count < 3:
        if data[inner:inner+4].isalpha():
            sig, size, flags, formid = read_record_header(inner)
            chunk = data[inner+16:inner+16+size]
            decomp = decompress(flags, chunk)
            subs = parse_subrecords(decomp or chunk)
            print(f"REFR 0x{formid:08X} at 0x{inner:x}:")
            for sr in subs:
                if sr["sig"] in ["EDID", "NAME", "DATA", "XSCL", "XLCP"]:
                    if sr["sig"] == "NAME":
                        val = struct.unpack("<I", sr["data"][:4])[0] if len(sr["data"]) >= 4 else 0
                        print(f"  {sr['sig']}: 0x{val:08X}")
                    elif sr["sig"] == "DATA":
                        vals = struct.unpack("<ffffff", sr["data"])
                        print(f"  {sr['sig']}: pos={vals[:3]} rot={vals[3:]}")
                    else:
                        text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in sr["data"])
                        print(f"  {sr['sig']}: {text}")
            count += 1
            inner += 16 + size
        else:
            inner += 1
