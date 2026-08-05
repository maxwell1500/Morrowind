"""Verify our generated ESP structure by properly walking the GRUPs."""
import struct, zlib

def dump_bytes(data, start, length, label):
    chunk = data[start:start+length]
    print(f"{label} at 0x{start:x}: len={length} hex={chunk.hex()}")

with open(r"C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp", "rb") as f:
    data = f.read()

print(f"File size: {len(data)} bytes")

# TES4 header
print(f"\n=== TES4 at 0x00 ===")
print(f"sig={data[0:4].decode()} size={struct.unpack('<I', data[4:8])[0]} flags=0x{struct.unpack('<I', data[8:12])[0]:08X}")

# Walk top-level GRUPs
tes4_size = struct.unpack("<I", data[4:8])[0]
pos = 20 + tes4_size
print(f"\nTop-level GRUP starts at 0x{pos:x}")

while pos < len(data):
    if data[pos:pos+4] != b"GRUP":
        print(f"Expected GRUP at 0x{pos:x}, got {data[pos:pos+4]}")
        break
    gsize = struct.unpack("<I", data[pos+4:pos+8])[0]
    glabel = data[pos+8:pos+12]
    gtype = struct.unpack("<I", data[pos+12:pos+16])[0]
    try:
        glabel_str = glabel.decode("ascii")
    except:
        glabel_str = glabel.hex()
    print(f"GRUP at 0x{pos:x}: label={glabel_str!r} type={gtype} size={gsize}")
    pos += 8 + gsize

# Specifically parse the CELL GRUP contents
print("\n=== Detailed CELL GRUP walk ===")
grup_pos = 20 + tes4_size
if data[grup_pos:grup_pos+4] == b"GRUP":
    gsize = struct.unpack("<I", data[grup_pos+4:grup_pos+8])[0]
    content_start = grup_pos + 24
    content_end = grup_pos + 8 + gsize
    print(f"CELL GRUP content: 0x{content_start:x} - 0x{content_end:x}")
    
    # Block GRUP
    bpos = content_start
    bsize = struct.unpack("<I", data[bpos+4:bpos+8])[0]
    print(f"Block GRUP at 0x{bpos:x}: size={bsize}")
    bcontent_start = bpos + 24
    bcontent_end = bpos + 8 + bsize
    
    # Sub-block GRUP
    sbpos = bcontent_start
    sbsize = struct.unpack("<I", data[sbpos+4:sbpos+8])[0]
    print(f"Sub-block GRUP at 0x{sbpos:x}: size={sbsize}")
    sbcontent_start = sbpos + 24
    sbcontent_end = sbpos + 8 + sbsize
    
    # CELL record
    cell_pos = sbcontent_start
    cell_sig = data[cell_pos:cell_pos+4].decode()
    cell_size = struct.unpack("<I", data[cell_pos+4:cell_pos+8])[0]
    cell_flags = struct.unpack("<I", data[cell_pos+8:cell_pos+12])[0]
    cell_formid = struct.unpack("<I", data[cell_pos+12:cell_pos+16])[0]
    print(f"CELL at 0x{cell_pos:x}: sig={cell_sig} size={cell_size} flags=0x{cell_flags:08X} formid=0x{cell_formid:08X}")
    
    if cell_flags & 0x00040000:
        chunk = data[cell_pos+16:cell_pos+16+cell_size]
        uncomp_size = struct.unpack("<I", chunk[:4])[0]
        print(f"  uncompressed prefix: {uncomp_size}")
        print(f"  compressed data length: {len(chunk)-4}")
        try:
            decomp = zlib.decompress(chunk[4:])
            print(f"  decompressed OK, len={len(decomp)}")
            print("  subrecords:")
            p = 0
            while p < len(decomp) - 6:
                sig = decomp[p:p+4].decode("ascii", errors="replace")
                size = struct.unpack("<H", decomp[p+4:p+6])[0]
                print(f"    0x{p:x}: {sig} size={size}")
                p += 6 + size
                if p > len(decomp):
                    print("    WARNING: overran")
                    break
        except Exception as e:
            print(f"  decompress error: {e}")
    else:
        print("  not compressed")
    
    # Cell children GRUP should follow CELL record
    children_pos = cell_pos + 16 + cell_size
    print(f"\nExpected cell children GRUP at 0x{children_pos:x}")
    if data[children_pos:children_pos+4] == b"GRUP":
        csize = struct.unpack("<I", data[children_pos+4:children_pos+8])[0]
        clabel = struct.unpack("<I", data[children_pos+8:children_pos+12])[0]
        ctype = struct.unpack("<I", data[children_pos+12:children_pos+16])[0]
        print(f"  GRUP at 0x{children_pos:x}: label=0x{clabel:08X} type={ctype} size={csize}")
