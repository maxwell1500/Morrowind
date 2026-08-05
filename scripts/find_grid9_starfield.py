import struct
data = open(r"C:\XboxGames\Starfield\Content\Data\Starfield.esm", "rb").read()
target = bytes.fromhex("58434c430c000000f6fffffff7ffffff00000000")
pos = 0
while True:
    pos = data.find(target, pos)
    if pos < 0:
        break
    print("Found XCLC at offset %d" % pos)
    for back in range(0, 2000, 1):
        if data[pos-back:pos-back+4] == b"CELL":
            size = struct.unpack("<I", data[pos-back+4:pos-back+8])[0]
            fid = struct.unpack("<I", data[pos-back+12:pos-back+16])[0]
            print("  CELL 0x%08X at offset %d" % (fid, pos-back))
            break
    pos += 1
