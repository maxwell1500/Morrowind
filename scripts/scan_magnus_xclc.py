import struct, zlib
data = open(r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm", "rb").read()
grids = {}
pos = 0
while pos < len(data) - 20:
    if data[pos:pos+4] == b"XCLC":
        sln = struct.unpack("<H", data[pos+4:pos+6])[0]
        if sln >= 12:
            gx, gy, gz = struct.unpack("<iii", data[pos+6:pos+6+sln])
            if gx != 0x7FFFFFFF:  # skip persistent cell
                grids[(gx, gy)] = grids.get((gx, gy), 0) + 1
        pos += 6 + sln
    else:
        pos += 1
print("Occupied grids in Magnus.esm:")
for k, v in sorted(grids.items()):
    print("  %s: %d" % (k, v))
