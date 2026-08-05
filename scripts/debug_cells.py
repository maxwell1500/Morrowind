import struct
import zlib

data = open(r"C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp", "rb").read()
count = 0
pos = 24 + struct.unpack("<I", data[4:8])[0]
while pos < len(data) - 24:
    sig = data[pos:pos + 4].decode("ascii", errors="replace")
    if sig == "CELL":
        size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        flags = struct.unpack("<I", data[pos + 8:pos + 12])[0]
        formid = struct.unpack("<I", data[pos + 12:pos + 16])[0]
        body = data[pos + 24:pos + 24 + size]
        if flags & 0x00040000:
            body = zlib.decompress(body[4:])
        sub = 0
        xclc = None
        edid = None
        data_val = None
        while sub < len(body):
            ssig = body[sub:sub + 4].decode("ascii", errors="replace")
            sln = struct.unpack("<H", body[sub + 4:sub + 6])[0]
            sdata = body[sub + 6:sub + 6 + sln]
            if ssig == "XCLC":
                xclc = struct.unpack("<iii", sdata)
            elif ssig == "EDID":
                edid = sdata.rstrip(b"\x00").decode("ascii", errors="replace")
            elif ssig == "DATA":
                data_val = struct.unpack("<I", sdata)[0] if sln == 4 else None
            sub += 6 + sln
        count += 1
        edid_str = edid or "???"
        if xclc:
            print("CELL %d: fid=0x%08X edid=%s grid=%s DATA=%08x" % (count, formid, edid_str, xclc[:2], data_val))
        else:
            print("CELL %d: fid=0x%08X edid=%s no XCLC DATA=%08x" % (count, formid, edid_str, data_val))
        pos += 24 + size
    elif sig == "GRUP":
        pos += struct.unpack("<I", data[pos + 4:pos + 8])[0]
    else:
        pos += 24 + struct.unpack("<I", data[pos + 4:pos + 8])[0]

print("Total CELL records: %d" % count)
