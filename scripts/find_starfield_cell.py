import struct, zlib
data = open(r"C:\XboxGames\Starfield\Content\Data\Starfield.esm", "rb").read()
target = 0x010488FA
pos = 0
while pos < len(data) - 24:
    if data[pos:pos+4] == b"CELL":
        size = struct.unpack("<I", data[pos+4:pos+8])[0]
        fid = struct.unpack("<I", data[pos+12:pos+16])[0]
        if fid == target:
            print("Found CELL 0x%08X in Starfield.esm at offset %d" % (fid, pos))
            flags = struct.unpack("<I", data[pos+8:pos+12])[0]
            body = data[pos+24:pos+24+size]
            if flags & 0x00040000:
                try:
                    body = zlib.decompress(body[4:])
                except Exception as e:
                    print("Decompress error: %s" % e)
                    body = b""
            sub = 0
            while sub < len(body) - 6:
                ssig = body[sub:sub+4].decode("ascii", errors="replace")
                sln = struct.unpack("<H", body[sub+4:sub+6])[0]
                print("  %s len=%d" % (ssig, sln))
                sub += 6 + sln
            break
        pos += 24 + size
    elif data[pos:pos+4] == b"GRUP":
        pos += struct.unpack("<I", data[pos+4:pos+8])[0]
    else:
        pos += 24 + struct.unpack("<I", data[pos+4:pos+8])[0]
