"""Explore The Elder Star System - Magnus.esm structure."""
import struct, zlib, json

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
    # Starfield: 8-byte prefix, 4-byte uncomp size, zlib
    try:
        return zlib.decompress(chunk[12:])
    except Exception as e:
        return None


def parse_subrecords(chunk, has_prefix=True):
    """Parse subrecords from record data chunk."""
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
            "offset": pos,
            "data": chunk[pos+6:pos+6+sz]
        })
        pos += 6 + sz
        if pos > len(chunk):
            break
    return result


def find_record_by_formid(target_fid):
    pos = 0
    while pos < len(data) - 16:
        if data[pos:pos+4].isalpha():
            sig, size, flags, formid, end = read_record(pos)
            if formid == target_fid:
                chunk = data[pos+16:pos+16+size]
                decomp = decompress_if_needed(sig, flags, chunk)
                return {
                    "pos": pos,
                    "sig": sig,
                    "size": size,
                    "flags": flags,
                    "formid": formid,
                    "chunk": chunk,
                    "decomp": decomp,
                    "subrecords": parse_subrecords(decomp or chunk)
                }
            pos = end
        else:
            pos += 1
    return None


def find_records_by_type(sig_filter, max_results=20):
    pos = 0
    found = []
    while pos < len(data) - 16 and len(found) < max_results:
        if data[pos:pos+4] == sig_filter.encode():
            sig, size, flags, formid, end = read_record(pos)
            chunk = data[pos+16:pos+16+size]
            decomp = decompress_if_needed(sig, flags, chunk)
            found.append({
                "pos": pos,
                "sig": sig,
                "formid": hex(formid),
                "size": size,
                "chunk_prefix": chunk[:8].hex(),
                "decomp_size": len(decomp) if decomp else None,
                "subrecords": [
                    {"sig": s["sig"], "size": s["size"], "text": s["data"].decode("ascii", errors="replace")[:30]}
                    for s in parse_subrecords(decomp or chunk)
                ]
            })
            pos = end
        else:
            pos += 1
    return found


print("=== Magnus WRLD records ===")
wrlds = find_records_by_type("WRLD", 5)
for w in wrlds:
    print(json.dumps(w, indent=2))

print("\n=== Magnus LCTN records ===")
lctns = find_records_by_type("LCTN", 10)
for l in lctns:
    print(json.dumps(l, indent=2))

print("\n=== Looking for Morrowind_ID LCTN ===")
morrowind_lctn = None
for l in lctns:
    for sr in l["subrecords"]:
        if "Morrowind" in sr.get("text", "") or "morrowind" in sr.get("text", "").lower():
            morrowind_lctn = l
            print(json.dumps(l, indent=2))
            break
    if morrowind_lctn:
        break

print("\n=== Searching for CELLs ===")
cells = find_records_by_type("CELL", 20)
for c in cells:
    print(f"CELL {c['formid']} at 0x{c['pos']:x}: subrecords={c['subrecords'][:3]}")
