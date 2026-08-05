"""Dump structure of our generated ESP."""
import struct

with open(r"C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp", "rb") as f:
    data = f.read()

print(f"File size: {len(data)} bytes")
print(f"Header: {data[0:4].decode()}")

record_size = struct.unpack("<I", data[4:8])[0]
print(f"TES4 size: {record_size}")

pos = 20 + record_size
print(f"First GRUP at 0x{pos:x}")
while pos < len(data):
    if data[pos:pos+4] == b"GRUP":
        size = struct.unpack("<I", data[pos+4:pos+8])[0]
        label_hex = data[pos+8:pos+12].hex()
        try:
            label_str = data[pos+8:pos+12].decode("ascii")
        except:
            label_str = "?"
        gtype = struct.unpack("<I", data[pos+12:pos+16])[0]
        print(f"GRUP at 0x{pos:x}: label_hex={label_hex} label_str={label_str!r} type={gtype} size={size}")
        pos += size + 8
    else:
        print(f"Unexpected byte at 0x{pos:x}: {data[pos]:02x} {data[pos:pos+4]}")
        pos += 1
