import struct
data = open(r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm", "rb").read()
# XCLC for (-2,-9): f6 ff ff ff f7 ff ff ff 00 00 00 00
target = bytes.fromhex("58434c430c000000f6fffffff7ffffff00000000")
pos = data.find(target)
if pos >= 0:
    print("Found XCLC at offset %d" % pos)
    for back in range(0, 1000, 1):
        if data[pos-back:pos-back+4] == b"CELL":
            size = struct.unpack("<I", data[pos-back+4:pos-back+8])[0]
            fid = struct.unpack("<I", data[pos-back+12:pos-back+16])[0]
            print("CELL at offset %d, fid=0x%08X, size=%d" % (pos-back, fid, size))
            break
else:
    print("Not found in Magnus.esm")
    # Try Starfield.esm
    data = open(r"C:\XboxGames\Starfield\Content\Data\Starfield.esm", "rb").read()
    pos = data.find(target)
    if pos >= 0:
        print("Found in Starfield.esm at offset %d" % pos)
        for back in range(0, 1000, 1):
            if data[pos-back:pos-back+4] == b"CELL":
                size = struct.unpack("<I", data[pos-back+4:pos-back+8])[0]
                fid = struct.unpack("<I", data[pos-back+12:pos-back+16])[0]
                print("CELL at offset %d, fid=0x%08X, size=%d" % (pos-back, fid, size))
                break
    else:
        print("Not found in Starfield.esm either")
