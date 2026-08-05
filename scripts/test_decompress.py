"""Test decompressing our CELL record."""
import zlib, struct
with open(r"C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp", "rb") as f:
    data = f.read()

offset = 0xec
rec_size = struct.unpack("<I", data[offset+4:offset+8])[0]
chunk = data[offset+16:offset+16+rec_size]
print(f"record size: {rec_size}")
print(f"chunk length: {len(chunk)}")
print(f"uncompressed prefix: {struct.unpack('<I', chunk[:4])[0]}")
try:
    decomp = zlib.decompress(chunk[4:])
    print(f"decompressed length: {len(decomp)}")
    print("OK")
except Exception as e:
    print(f"decompress error: {e}")
