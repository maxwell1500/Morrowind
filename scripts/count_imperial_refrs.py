import struct, zlib

data = open(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm", "rb").read()

def walk(data, start, end, depth=0):
    pos = start
    refr_count = 0
    while pos < end:
        sig = data[pos:pos+4]
        if sig == b"GRUP":
            size = struct.unpack("<I", data[pos+4:pos+8])[0]
            refr_count += walk(data, pos+24, pos+size, depth+1)
            pos += size
        elif sig == b"REFR":
            refr_count += 1
            pos += 24 + struct.unpack("<I", data[pos+4:pos+8])[0]
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
            while sub < len(body) - 6:
                ssig = body[sub:sub+4].decode("ascii", errors="replace")
                sln = struct.unpack("<H", body[sub+4:sub+6])[0]
                if sub + 6 + sln > len(body):
                    break
                if ssig == "XCLC":
                    xclc = struct.unpack("<iii", body[sub+6:sub+6+sln])
                sub += 6 + sln
            if xclc and xclc[:2] == (2147483647, 2147483647):
                print("Persistent cell 0x%08X" % fid)
                # Count REFRs in children
                children_start = pos + 24 + size
                children_end = pos + 24 + size + 0  # need to find children group
                # Actually the children are in GRUP after the cell
                # Let me just scan the rest of the WRLD children
            pos += 24 + size
        else:
            pos += 24 + struct.unpack("<I", data[pos+4:pos+8])[0]
    return refr_count

# Find WRLD group and scan
pos = 24 + struct.unpack("<I", data[4:8])[0]
while pos < len(data) - 24:
    sig = data[pos:pos+4]
    if sig == b"GRUP":
        gtype = struct.unpack("<I", data[pos+12:pos+16])[0]
        label = data[pos+8:pos+12]
        size = struct.unpack("<I", data[pos+4:pos+8])[0]
        if gtype == 0 and label == b"WRLD":
            walk(data, pos+24, pos+size)
            break
        pos += size
    else:
        pos += 24 + struct.unpack("<I", data[pos+4:pos+8])[0]
