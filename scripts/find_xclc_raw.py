import struct
data = open(r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm", "rb").read()
# XCLC subrecord for (-2,-10): X C L C len=12 f6 ff ff ff f6 ff ff ff 00 00 00 00
# XCLC = 58434c43, len=0c000000, data = f6ffffff f6ffffff 00000000
target = bytes.fromhex("58434c430c000000f6fffffff6ffffff00000000")
pos = data.find(target)
if pos >= 0:
    print("Found XCLC at offset %d" % pos)
    # Look back for CELL header
    for back in range(0, 1000, 1):
        if data[pos-back:pos-back+4] == b"CELL":
            size = struct.unpack("<I", data[pos-back+4:pos-back+8])[0]
            fid = struct.unpack("<I", data[pos-back+12:pos-back+16])[0]
            print("CELL at offset %d, fid=0x%08X, size=%d" % (pos-back, fid, size))
            break
else:
    print("Not found in Magnus.esm")
    # Try ImperialCity.esm
    data = open(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm", "rb").read()
    pos = data.find(target)
    if pos >= 0:
        print("Found in ImperialCity.esm at offset %d" % pos)
    else:
        print("Not found in ImperialCity.esm either")
