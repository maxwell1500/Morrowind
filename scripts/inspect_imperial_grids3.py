import struct
import zlib

data = open(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm", "rb").read()
grids = {}
count = 0
pos = 24 + struct.unpack("<I", data[4:8])[0]
while pos < len(data) - 24:
    sig = data[pos:pos + 4]
    if sig == b"CELL":
        size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        flags = struct.unpack("<I", data[pos + 8:pos + 12])[0]
        body = data[pos + 24:pos + 24 + size]
        if flags & 0x00040000:
            unc_len = struct.unpack("<I", body[:4])[0]
            try:
                body = zlib.decompress(body[4:])
            except Exception:
                pass
        sub = 0
        xclc = None
        edid = None
        data_val = None
        while sub < len(body) - 8:
            ssig = body[sub:sub + 4]
            sln = struct.unpack("<H", body[sub + 4:sub + 6])[0]
            sdata = body[sub + 6:sub + 6 + sln]
            if ssig == b"XCLC":
                xclc = struct.unpack("<iii", sdata)
            elif ssig == b"EDID":
                edid = sdata.rstrip(b"\x00").decode("ascii", errors="replace")
            elif ssig == b"DATA":
                data_val = struct.unpack("<I", sdata)[0] if sln == 4 else None
            sub += 6 + sln
        if xclc:
            grids[xclc[:2]] = grids.get(xclc[:2], 0) + 1
            count += 1
            edid_str = edid or "???"
            print("  %s: grid=%s DATA=%08x" % (edid_str, xclc[:2], data_val))
        pos += 24 + size
    elif sig == b"GRUP":
        pos += struct.unpack("<I", data[pos + 4:pos + 8])[0]
    else:
        pos += 24 + struct.unpack("<I", data[pos + 4:pos + 8])[0]

print("Total exterior cells: %d" % count)
print("Summary grids:")
for k, v in sorted(grids.items()):
    print("  %s: %d" % (k, v))
