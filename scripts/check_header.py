"""Check TES4 header size calculation."""
with open(r"C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp", "rb") as f:
    data = f.read()

sig = data[0:4].decode()
record_size = int.from_bytes(data[4:8], "little")
flags = int.from_bytes(data[8:12], "little")
print(f"TES4 sig={sig} record_size={record_size} flags=0x{flags:08X}")
print(f"TES4 header is 20 bytes (4 sig + 4 size + 4 flags + 8 padding)")
print(f"Subrecords start at 0x14")
grup_pos = data.find(b"GRUP")
print(f"First GRUP at 0x{grup_pos:x}")
print(f"Actual subrecord data size: 0x{grup_pos - 0x14:x} = {grup_pos - 0x14}")
print(f"But header says size: {record_size}")
