import struct
import zlib


def indent(depth):
    return "  " * depth


def parse_esp(data, pos=0, depth=0, max_depth=10):
    if depth > max_depth or pos >= len(data) - 24:
        return None
    sig = data[pos:pos + 4].decode("ascii", errors="replace")
    size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
    if sig == "TES4":
        print("%sTES4 size=%d" % (indent(depth), size))
        parse_esp(data, pos + 24 + size, depth)
        return None
    elif sig == "GRUP":
        gtype = struct.unpack("<I", data[pos + 12:pos + 16])[0]
        label = data[pos + 8:pos + 12]
        print("%sGRUP type=%d label=%s size=%d" % (indent(depth), gtype, label, size))
        inner = pos + 24
        end = pos + size
        while inner < end:
            inner = parse_esp(data, inner, depth + 1, max_depth)
            if inner is None:
                break
        return end
    else:
        flags = struct.unpack("<I", data[pos + 8:pos + 12])[0]
        fid = struct.unpack("<I", data[pos + 12:pos + 16])[0]
        print("%s%s fid=0x%08X size=%d flags=%08x" % (indent(depth), sig, fid, size, flags))
        return pos + 24 + size


data = open(r"C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp", "rb").read()
parse_esp(data)
