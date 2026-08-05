"""Explore WRLD children and LCSR structure in Magnus.esm."""
import struct, zlib

PATH = r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm"

with open(PATH, "rb") as f:
    data = f.read()


def read_record(pos):
    sig = data[pos:pos+4].decode("ascii", errors="replace")
    size = struct.unpack("<I", data[pos+4:pos+8])[0]
    flags = struct.unpack("<I", data[pos+8:pos+12])[0]
    formid = struct.unpack("<I", data[pos+12:pos+16])[0]
    return sig, size, flags, formid, pos + 16 + size


def decompress_if_needed(sig, flags, chunk):
    if not (flags & 0x00040000):
        return chunk
    try:
        return zlib.decompress(chunk[12:])
    except Exception as e:
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
        result.append({
            "sig": sig,
            "size": sz,
            "data": chunk[pos+6:pos+6+sz]
        })
        pos += 6 + sz
        if pos > len(chunk):
            break
    return result


# Find WRLD 0200E1C8 and its children GRUPs
WRLD_FID = 0x0200E1C8
pos = 0
wrld_end = None
while pos < len(data) - 16:
    if data[pos:pos+4] == b"WRLD":
        sig, size, flags, formid, end = read_record(pos)
        if formid == WRLD_FID:
            wrld_end = end
            print(f"Found WRLD Morrowind at 0x{pos:x}, ends at 0x{wrld_end:x}")
            break
        pos = end
    else:
        pos += 1

if wrld_end:
    # Look for GRUPs immediately following the WRLD record
    pos = wrld_end
    count = 0
    while pos < len(data) and count < 10:
        if data[pos:pos+4] == b"GRUP":
            gsize = struct.unpack("<I", data[pos+4:pos+8])[0]
            label = data[pos+8:pos+12]
            gtype = struct.unpack("<I", data[pos+12:pos+16])[0]
            try:
                label_str = label.decode("ascii")
            except:
                label_str = label.hex()
            print(f"GRUP at 0x{pos:x}: label={label_str!r} type={gtype} size={gsize}")
            count += 1
            pos += gsize
        else:
            print(f"Non-GRUP at 0x{pos:x}: {data[pos:pos+4].hex()}")
            break

# Parse Morrowind_ID LCSR
print("\n=== Morrowind_ID LCSR data ===")
lctn_pos = 570597
sig, size, flags, formid, end = read_record(lctn_pos)
chunk = data[lctn_pos+16:lctn_pos+16+size]
decomp = decompress_if_needed(sig, flags, chunk)
subs = parse_subrecords(decomp or chunk)
for sr in subs:
    if sr["sig"] == "LCSR":
        print(f"LCSR size={sr['size']} hex={sr['data'].hex()}")
        # LCSR likely contains pairs: formID + ???
        d = sr["data"]
        for i in range(0, len(d) - 8, 8):
            a = struct.unpack("<I", d[i:i+4])[0]
            b = struct.unpack("<I", d[i+4:i+8])[0]
            print(f"  entry {i//8}: formID=0x{a:08X} unknown=0x{b:08X}")
        if len(d) % 8 == 4:
            a = struct.unpack("<I", d[-4:])[0]
            print(f"  trailing: 0x{a:08X}")

# Also find REFRs that reference WRLD 0200E1C8 or LCTN 0200E774
print("\n=== Searching for REFRs near WRLD children ===")
pos = 0
found = 0
while pos < len(data) - 16 and found < 5:
    if data[pos:pos+4] == b"REFR":
        sig, size, flags, formid, end = read_record(pos)
        chunk = data[pos+16:pos+16+size]
        decomp = decompress_if_needed(sig, flags, chunk)
        subs = parse_subrecords(decomp or chunk)
        # Check if any subrecord references Morrowind WRLD or LCTN
        interesting = False
        for sr in subs:
            if sr["sig"] == "XLCP" or sr["sig"] == "NAME":
                val = struct.unpack("<I", sr["data"][:4])[0] if len(sr["data"]) >= 4 else 0
                if val in [WRLD_FID, 0x0200E774]:
                    interesting = True
        if interesting:
            print(f"REFR 0x{formid:08X} at 0x{pos:x}")
            for sr in subs:
                text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in sr["data"][:min(sr["size"], 40)])
                print(f"  {sr['sig']} size={sr['size']} data={text}")
            found += 1
        pos = end
    else:
        pos += 1
