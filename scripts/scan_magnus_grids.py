import struct, zlib

data = open(r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm", "rb").read()
grids = {}

def scan(data, start, end):
    pos = start
    while pos < end:
        sig = data[pos:pos+4]
        if sig == b"GRUP":
            size = struct.unpack("<I", data[pos+4:pos+8])[0]
            scan(data, pos+24, pos+size)
            pos += size
        elif sig == b"CELL":
            size = struct.unpack("<I", data[pos+4:pos+8])[0]
            flags = struct.unpack("<I", data[pos+8:pos+12])[0]
            fid = struct.unpack("<I", data[pos+12:pos+16])[0]
            body = data[pos+24:pos+24+size]
            if flags & 0x00040000:
                try:
                    body = zlib.decompress(body[4:])
                except Exception:
                    body = b""
            sub = 0
            xclc = None
            while sub < len(body):
                ssig = body[sub:sub+4].decode("ascii", errors="replace")
                sln = struct.unpack("<H", body[sub+4:sub+6])[0]
                sdata = body[sub+6:sub+6+sln]
                if ssig == "XCLC":
                    xclc = struct.unpack("<iii", sdata)
                sub += 6 + sln
            if xclc:
                grids[xclc[:2]] = fid
            pos += 24 + size
        else:
            pos += 24 + struct.unpack("<I", data[pos+4:pos+8])[0]

tes4_size = struct.unpack("<I", data[4:8])[0]
scan(data, 24 + tes4_size, len(data))
print("Occupied grids in Magnus.esm:")
for k, v in sorted(grids.items()):
    print("  %s: 0x%08X" % (k, v))
