import struct, zlib, io

def write_subrecord(buf, sig, data):
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<H", len(data)))
    buf.write(data)

def write_record(buf, sig, formid, flags, subrecords):
    sub_data = subrecords.getvalue() if hasattr(subrecords, "getvalue") else subrecords
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<I", len(sub_data)))
    buf.write(struct.pack("<I", flags))
    buf.write(struct.pack("<I", formid))
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", 0x00000240))
    buf.write(sub_data)

def write_compressed_record(buf, sig, formid, flags, subrecords):
    sub_data = subrecords.getvalue() if hasattr(subrecords, "getvalue") else subrecords
    compressed = zlib.compress(sub_data)
    content = struct.pack("<I", len(sub_data)) + compressed
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<I", len(content)))
    buf.write(struct.pack("<I", flags | 0x00040000))
    buf.write(struct.pack("<I", formid))
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", 0x00000240))
    buf.write(content)

def write_grup(buf, label, grup_type, content):
    data = content.getvalue() if hasattr(content, "getvalue") else content
    buf.write(b"GRUP")
    buf.write(struct.pack("<I", len(data) + 24))
    if isinstance(label, str):
        label_bytes = label.encode("ascii")[:4].ljust(4, b"\x00")
    else:
        label_bytes = struct.pack("<I", label)
    buf.write(label_bytes)
    buf.write(struct.pack("<I", grup_type))
    buf.write(b"\x00" * 8)
    buf.write(data)

def extract_wrld_body(master_path, wrld_formid):
    data = open(master_path, 'rb').read()
    pos = 0
    while pos < len(data) - 24:
        if data[pos:pos+4] == b"WRLD":
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            formid = struct.unpack('<I', data[pos+12:pos+16])[0]
            if formid == wrld_formid:
                rec = data[pos+24:pos+24+size]
                if rec[:8] == b"\x00\x00\x00\x00@\x02\x00\x00":
                    return rec[8:]
                return rec
            pos += 24 + size
        else:
            pos += 1
    raise RuntimeError(f"WRLD {wrld_formid:08X} not found")

buf = io.BytesIO()
buf.write(b"TES4")
data_size_pos = buf.tell()
buf.write(struct.pack("<I", 0))
buf.write(struct.pack("<I", 0x00000101))
buf.write(struct.pack("<I", 0))
buf.write(struct.pack("<I", 0))
buf.write(struct.pack("<I", 0))
subrecord_start = buf.tell()
write_subrecord(buf, "HEDR", struct.pack("<fII", 0.96, 4, 0xFE000D55))
write_subrecord(buf, "CNAM", b"Seyda Neen Test Huge Coord\x00")
write_subrecord(buf, "MAST", b"Starfield.esm\x00")
write_subrecord(buf, "MAST", b"The Elder Star System - Magnus.esm\x00")
write_subrecord(buf, "BNAM", b"Main\x00")
write_subrecord(buf, "INCC", struct.pack("<I", 0))
data_size = buf.tell() - subrecord_start
buf.seek(data_size_pos)
buf.write(struct.pack("<I", data_size))
buf.seek(0, 2)

stat_sub = io.BytesIO()
write_subrecord(stat_sub, "EDID", b"test_marker\x00")
write_subrecord(stat_sub, "OBND", struct.pack("<ffffff", -1.0, -1.0, -1.0, 1.0, 1.0, 1.0))
write_subrecord(stat_sub, "ODTY", struct.pack("<I", 0))
write_subrecord(stat_sub, "BFCB", b"BGSKeywordForm_Component\x00")
write_subrecord(stat_sub, "BFCE", b"")
write_subrecord(stat_sub, "MODL", b"morrowind\\active_de_bed_30.nif\x00")
stat_grup = io.BytesIO()
write_record(stat_grup, "STAT", 0xFE000800, 0x00000000, stat_sub)
write_grup(buf, "STAT", 0, stat_grup.getvalue())

interior_fid = 0xFE0008F1
cell_sub = io.BytesIO()
write_subrecord(cell_sub, "EDID", b"TestInterior\x00")
write_subrecord(cell_sub, "FULL", b"Test Interior\x00")
write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00010025))
cell_buf = io.BytesIO()
write_compressed_record(cell_buf, "CELL", interior_fid, 0x00000000, cell_sub)
children = io.BytesIO()
write_grup(children, interior_fid, 6, b"")
subblock = io.BytesIO()
subblock.write(cell_buf.getvalue())
subblock.write(children.getvalue())
block = io.BytesIO()
write_grup(block, 0, 3, subblock.getvalue())
top = io.BytesIO()
write_grup(top, 0, 2, block.getvalue())
write_grup(buf, "CELL", 0, top.getvalue())

exterior_fid = 0xFE0008F2
cell_sub = io.BytesIO()
write_subrecord(cell_sub, "EDID", b"TestExterior\x00")
write_subrecord(cell_sub, "FULL", b"Test Exterior\x00")
write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00000002))
write_subrecord(cell_sub, "XCLC", struct.pack("<iii", -11, -1, 0))
write_subrecord(cell_sub, "LTMP", struct.pack("<I", 0))
write_subrecord(cell_sub, "XCLW", struct.pack("<f", 0.0))
cell_buf = io.BytesIO()
write_compressed_record(cell_buf, "CELL", exterior_fid, 0x00000000, cell_sub)

# One REFR at huge coordinate
persistent = io.BytesIO()
refr_sub = io.BytesIO()
write_subrecord(refr_sub, "NAME", struct.pack("<I", 0xFE000800))
write_subrecord(refr_sub, "DATA", struct.pack("<ffffff", -637230.9, -3548683.9999999995, -10576.49, 0.0, 0.0, 4.482020447387695))
write_record(persistent, "REFR", 0xFE000B23, 0x00010400, refr_sub)

persistent_grup = io.BytesIO()
write_grup(persistent_grup, exterior_fid, 8, persistent.getvalue())
cell_children = io.BytesIO()
write_grup(cell_children, exterior_fid, 6, persistent_grup.getvalue())

subblock = io.BytesIO()
subblock.write(cell_buf.getvalue())
subblock.write(cell_children.getvalue())
exterior_block = io.BytesIO()
write_grup(exterior_block, 0, 2, subblock.getvalue())
wrld_children = io.BytesIO()
write_grup(wrld_children, 0x0100E1C8, 1, exterior_block.getvalue())
wrld_body = extract_wrld_body(r'C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm', 0x0100E1C8)
wrld_override = io.BytesIO()
write_record(wrld_override, "WRLD", 0x0100E1C8, 0x00000004, wrld_body)
wrld_top = io.BytesIO()
wrld_top.write(wrld_override.getvalue())
wrld_top.write(wrld_children.getvalue())
write_grup(buf, "WRLD", 0, wrld_top.getvalue())

open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen_test_huge_refr.esp', 'wb').write(buf.getvalue())
print('Created test ESP with single REFR at huge coordinate')
