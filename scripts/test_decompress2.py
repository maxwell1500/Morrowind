"""Extract exact compressed bytes and try variants."""
import zlib, struct

with open(r"C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp", "rb") as f:
    data = f.read()

offset = 0xec
rec_size = struct.unpack("<I", data[offset+4:offset+8])[0]
chunk = data[offset+16:offset+16+rec_size]
uncomp_len = struct.unpack("<I", chunk[:4])[0]
comp = chunk[4:]

print(f"record size: {rec_size}")
print(f"chunk length: {len(chunk)}")
print(f"uncompressed prefix: {uncomp_len}")
print(f"compressed length: {len(comp)}")
print(f"compressed hex: {comp.hex()}")

# Try standard zlib
for name, fn in [("zlib.decompress", zlib.decompress)]:
    try:
        d = fn(comp)
        print(f"{name}: OK len={len(d)}")
    except Exception as e:
        print(f"{name}: {e}")

# Try raw deflate (wbits=-15)
import zlib as z
for wbits in [-15, 15, 31, -8, 8, 24, 40, 47]:
    try:
        d = z.decompress(comp, wbits=wbits)
        print(f"wbits={wbits}: OK len={len(d)}")
    except Exception as e:
        pass
