"""Debug generate_esp.py by simulating its buffer building."""
import struct, io, zlib

def write_subrecord(buf, sig, data):
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<H", len(data)))
    buf.write(data)

def write_compressed_record(buf, sig, formid, flags, subrecords):
    sub_data = subrecords.getvalue() if hasattr(subrecords, 'getvalue') else subrecords
    compressed = zlib.compress(sub_data)
    print(f"  write_compressed_record: sub_data len={len(sub_data)}, compressed len={len(compressed)}, total record size={16 + 4 + len(compressed)}")
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<I", 4 + len(compressed)))
    buf.write(struct.pack("<I", flags | 0x00040000))
    buf.write(struct.pack("<I", formid))
    buf.write(struct.pack("<I", len(sub_data)))
    buf.write(compressed)

def write_record(buf, sig, formid, flags, subrecords):
    sub_data = subrecords.getvalue() if hasattr(subrecords, 'getvalue') else subrecords
    print(f"  write_record: sub_data len={len(sub_data)}, total record size={16 + len(sub_data)}")
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<I", len(sub_data)))
    buf.write(struct.pack("<I", flags))
    buf.write(struct.pack("<I", formid))
    buf.write(sub_data)

def write_grup(buf, label, grup_type, content):
    data = content.getvalue() if hasattr(content, 'getvalue') else content
    print(f"  write_grup: type={grup_type} data len={len(data)} total size={len(data)+24}")
    buf.write(b"GRUP")
    buf.write(struct.pack("<I", len(data) + 24))
    if isinstance(label, str):
        label_bytes = label.encode("ascii")[:4].ljust(4, b'\x00')
    else:
        label_bytes = struct.pack("<I", label)
    buf.write(label_bytes)
    buf.write(struct.pack("<I", grup_type))
    buf.write(b"\x00" * 8)
    buf.write(data)

# CELL subrecords
print("=== Building CELL subrecords ===")
cell_sub = io.BytesIO()
write_subrecord(cell_sub, "EDID", b"Seyda Neen\x00")
write_subrecord(cell_sub, "FULL", b"Seyda Neen\x00")
write_subrecord(cell_sub, "XCLC", struct.pack("<ii", 0, 0))
write_subrecord(cell_sub, "XCLW", struct.pack("<f", 0.0))
write_subrecord(cell_sub, "CNAM", struct.pack("<B", 1))
print(f"cell_sub len={len(cell_sub.getvalue())}")

cell_buf = io.BytesIO()
write_compressed_record(cell_buf, "CELL", 0x00010000, 0x00000000, cell_sub)
print(f"cell_buf len={len(cell_buf.getvalue())}, first 4 bytes={cell_buf.getvalue()[:4]}")

# REFR
print("\n=== Building REFR ===")
refr_sub = io.BytesIO()
write_subrecord(refr_sub, "EDID", b"ex_nord_house_01\x00")
write_subrecord(refr_sub, "NAME", struct.pack("<I", 0x00000000))
write_subrecord(refr_sub, "DATA", struct.pack("<ffffff",
    -546730.7, -3512590.5, 19693.95,
    0.0, 0.0, 42.99999894818919))
write_subrecord(refr_sub, "XSCL", struct.pack("<f", 1.0))
print(f"refr_sub len={len(refr_sub.getvalue())}")

refr_buf = io.BytesIO()
write_record(refr_buf, "REFR", 0x00020000, 0x00000400, refr_sub)
print(f"refr_buf len={len(refr_buf.getvalue())}, first 4 bytes={refr_buf.getvalue()[:4]}")

# GRUPs
print("\n=== Building GRUPs ===")
persistent = io.BytesIO()
write_grup(persistent, 0x00010000, 8, refr_buf.getvalue())
print(f"persistent len={len(persistent.getvalue())}")

cell_children = io.BytesIO()
write_grup(cell_children, 0x00010000, 6, persistent.getvalue())
print(f"cell_children len={len(cell_children.getvalue())}")

cell_with_children = io.BytesIO()
cell_with_children.write(cell_buf.getvalue())
cell_with_children.write(cell_children.getvalue())
print(f"cell_with_children len={len(cell_with_children.getvalue())}, first 8 bytes={cell_with_children.getvalue()[:8].hex()}")

subblock_grup = io.BytesIO()
write_grup(subblock_grup, 0x00000000, 3, cell_with_children.getvalue())
print(f"subblock_grup len={len(subblock_grup.getvalue())}")

block_grup = io.BytesIO()
write_grup(block_grup, 0x00000000, 2, subblock_grup.getvalue())
print(f"block_grup len={len(block_grup.getvalue())}")

cell_grup = io.BytesIO()
write_grup(cell_grup, "CELL", 0, block_grup.getvalue())
print(f"cell_grup len={len(cell_grup.getvalue())}")
