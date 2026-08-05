import struct, zlib
data = open(r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm", "rb").read()
pos = 0
while pos < len(data) - 20:
    if data[pos:pos+4] == b"XCLC":
        sln = struct.unpack("<H", data[pos+4:pos+6])[0]
        if sln >= 12:
            gx, gy, gz = struct.unpack("<iii", data[pos+6:pos+6+sln])
            if (gx, gy) == (-2, -9):
                # Found XCLC, look back for CELL
                for back in range(0, 2000, 1):
                    if data[pos-back:pos-back+4] == b"CELL":
                        size = struct.unpack("<I", data[pos-back+4:pos-back+8])[0]
                        fid = struct.unpack("<I", data[pos-back+12:pos-back+16])[0]
                        print("Grid (-2,-9): CELL 0x%08X at offset %d" % (fid, pos-back))
                        break
                break
        pos += 6 + sln
    else:
        pos += 1
