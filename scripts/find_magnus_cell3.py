import struct, zlib, io

# Read Magnus.esm and extract the cell body for 0x010488FA
data = open(r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm", "rb").read()
target = 0x010488FA
pos = 0
cell_body = None
while pos < len(data) - 24:
    if data[pos:pos+4] == b"CELL":
        size = struct.unpack("<I", data[pos+4:pos+8])[0]
        fid = struct.unpack("<I", data[pos+12:pos+16])[0]
        if fid == target:
            flags = struct.unpack("<I", data[pos+8:pos+12])[0]
            body = data[pos+24:pos+24+size]
            if flags & 0x00040000:
                try:
                    body = zlib.decompress(body[4:])
                except Exception as e:
                    print("Decompress error: %s" % e)
            cell_body = body
            print("Found cell body, len=%d" % len(body))
            break
        pos += 24 + size
    elif data[pos:pos+4] == b"GRUP":
        pos += struct.unpack("<I", data[pos+4:pos+8])[0]
    else:
        pos += 24 + struct.unpack("<I", data[pos+4:pos+8])[0]

if cell_body is None:
    print("Cell not found in Magnus.esm, trying ImperialCity.esm")
    data = open(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm", "rb").read()
    pos = 0
    while pos < len(data) - 24:
        if data[pos:pos+4] == b"CELL":
            size = struct.unpack("<I", data[pos+4:pos+8])[0]
            fid = struct.unpack("<I", data[pos+12:pos+16])[0]
            if fid == target:
                flags = struct.unpack("<I", data[pos+8:pos+12])[0]
                body = data[pos+24:pos+24+size]
                if flags & 0x00040000:
                    try:
                        body = zlib.decompress(body[4:])
                    except Exception as e:
                        print("Decompress error: %s" % e)
                cell_body = body
                print("Found in ImperialCity.esm, len=%d" % len(body))
                break
            pos += 24 + size
        elif data[pos:pos+4] == b"GRUP":
            pos += struct.unpack("<I", data[pos+4:pos+8])[0]
        else:
            pos += 24 + struct.unpack("<I", data[pos+4:pos+8])[0]

if cell_body:
    print("Subrecords:")
    sub = 0
    while sub < len(cell_body) - 6:
        ssig = cell_body[sub:sub+4].decode("ascii", errors="replace")
        sln = struct.unpack("<H", cell_body[sub+4:sub+6])[0]
        print("  %s len=%d" % (ssig, sln))
        sub += 6 + sln
