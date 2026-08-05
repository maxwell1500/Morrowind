import struct
data = open(r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm", "rb").read()
target = 0x010488FA
pos = 0
while pos < len(data) - 24:
    sig = data[pos:pos+4]
    if sig in (b"CELL", b"WRLD", b"REFR", b"STAT", b"GRUP"):
        size = struct.unpack("<I", data[pos+4:pos+8])[0]
        if sig != b"GRUP":
            fid = struct.unpack("<I", data[pos+12:pos+16])[0]
            if fid == target:
                print("Found %s 0x%08X at offset %d size=%d" % (sig.decode(), fid, pos, size))
                break
        pos += 24 + size if sig != b"GRUP" else size
    else:
        pos += 1
else:
    print("Not found in Magnus.esm")
