import struct, zlib
data = open(r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm", "rb").read()
pos = 0
while pos < len(data) - 24:
    if data[pos:pos+4] == b"CELL":
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
        while sub < len(body) - 6:
            ssig = body[sub:sub+4].decode("ascii", errors="replace")
            sln = struct.unpack("<H", body[sub+4:sub+6])[0]
            if sub + 6 + sln > len(body):
                break
            if ssig == "XCLC":
                xclc = struct.unpack("<iii", body[sub+6:sub+6+sln])
            sub += 6 + sln
        if xclc and xclc[:2] == (-2, -9):
            print("Found CELL 0x%08X at grid (-2,-9)" % fid)
            break
        pos += 24 + size
    elif data[pos:pos+4] == b"GRUP":
        pos += struct.unpack("<I", data[pos+4:pos+8])[0]
    else:
        pos += 24 + struct.unpack("<I", data[pos+4:pos+8])[0]
else:
    print("Grid (-2,-9) not found in Magnus.esm")
