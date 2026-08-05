"""Generate SeydaNeen.esp as an ESL attached to Magnus's Morrowind WRLD."""
import os
import struct
import io
import zlib

OUTPUT_DIR = r"C:\Users\max\Projects\Morrowind\Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "SeydaNeen.esp")

# Plugin configuration: ESL (light master)
PLUGIN_FLAGS = 0x00000100  # ESL / light master

# FormID allocation in ESL space (0xFE prefix, object IDs 0x800+)
# ESL object IDs must be < 0x1000 (4096). We start at 0x800 to leave room.
FID_CELL       = 0xFE000800
FID_REFR       = 0xFE000801
FID_STAT       = 0xFE000802
FID_NEXT       = 0xFE000803

# Magnus Morrowind worldspace formID (as stored in Magnus.esm; resolves to 0x0200E1C8 at load time)
FID_MORROWIND_WRLD = 0x0100E1C8

# Seyda Neen cell grid coordinates in Magnus Morrowind worldspace
CELL_GRID_X = -10
CELL_GRID_Y = -1

# 8-byte prefix that appears before subrecords in Starfield records
RECORD_PREFIX = struct.pack("<II", 0, 0x00000240)


def write_subrecord(buf, sig, data):
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<H", len(data)))
    buf.write(data)


def write_record(buf, sig, formid, flags, subrecords):
    """Write a Starfield record (uncompressed) with 8-byte prefix."""
    sub_data = subrecords.getvalue() if hasattr(subrecords, 'getvalue') else subrecords
    content = RECORD_PREFIX + sub_data
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<I", len(content)))
    buf.write(struct.pack("<I", flags))
    buf.write(struct.pack("<I", formid))
    buf.write(content)


def write_compressed_record(buf, sig, formid, flags, subrecords):
    """Write a Starfield record with zlib-compressed subrecords."""
    sub_data = subrecords.getvalue() if hasattr(subrecords, 'getvalue') else subrecords
    compressed = zlib.compress(sub_data)
    content = RECORD_PREFIX + struct.pack("<I", len(sub_data)) + compressed
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<I", len(content)))
    buf.write(struct.pack("<I", flags | 0x00040000))  # compressed flag
    buf.write(struct.pack("<I", formid))
    buf.write(content)


def write_grup(buf, label, grup_type, content):
    data = content.getvalue() if hasattr(content, 'getvalue') else content
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


def main():
    buf = io.BytesIO()
    
    # ===== TES4 Header (24 bytes) =====
    # ImperialCity layout: flags, padding, version/timestamp 0x240 at 0x14
    buf.write(b"TES4")
    data_size_pos = buf.tell()
    buf.write(struct.pack("<I", 0))            # size of subrecord data
    buf.write(struct.pack("<I", PLUGIN_FLAGS)) # flags (ESL)
    buf.write(struct.pack("<I", 0))            # padding
    buf.write(struct.pack("<I", 0))            # padding
    buf.write(struct.pack("<I", 0x00000240))    # version/timestamp
    
    subrecord_start = buf.tell()
    
    write_subrecord(buf, "HEDR", struct.pack("<fII", 0.96, 3, FID_NEXT))
    write_subrecord(buf, "CNAM", b"Seyda Neen Mod\x00")
    write_subrecord(buf, "MAST", b"Starfield.esm\x00")
    write_subrecord(buf, "MAST", b"The Elder Star System - Magnus.esm\x00")
    write_subrecord(buf, "BNAM", b"Main\x00")
    write_subrecord(buf, "INCC", struct.pack("<I", 0))
    
    data_size = buf.tell() - subrecord_start
    buf.seek(data_size_pos)
    buf.write(struct.pack("<I", data_size))
    buf.seek(0, 2)
    
    # ===== STAT record for ex_nord_house_01 =====
    stat_sub = io.BytesIO()
    write_subrecord(stat_sub, "EDID", b"ex_nord_house_01\x00")
    write_subrecord(stat_sub, "OBND", struct.pack("<ffffff",
        -1.0, -1.0, -1.0, 1.0, 1.0, 1.0))
    write_subrecord(stat_sub, "ODTY", struct.pack("<I", 0))
    write_subrecord(stat_sub, "BFCB", b"BGSKeywordForm_Component\x00")
    write_subrecord(stat_sub, "BFCE", b"")
    write_subrecord(stat_sub, "MODL", b"morrowind\\ex_nord_house_01.nif\x00")
    write_subrecord(stat_sub, "FLLD", struct.pack("<I", 1))
    
    stat_buf = io.BytesIO()
    write_record(stat_buf, "STAT", FID_STAT, 0x00000000, stat_sub)
    
    # ===== CELL record inside Morrowind WRLD =====
    cell_sub = io.BytesIO()
    write_subrecord(cell_sub, "EDID", b"Seyda Neen\x00")
    write_subrecord(cell_sub, "FULL", b"Seyda Neen\x00")
    write_subrecord(cell_sub, "XCLC", struct.pack("<ii", CELL_GRID_X, CELL_GRID_Y))
    write_subrecord(cell_sub, "XCLW", struct.pack("<f", 0.0))
    write_subrecord(cell_sub, "CNAM", struct.pack("<B", 1))
    
    cell_buf = io.BytesIO()
    write_compressed_record(cell_buf, "CELL", FID_CELL, 0x00000000, cell_sub)
    
    # ===== REFR record =====
    refr_sub = io.BytesIO()
    write_subrecord(refr_sub, "EDID", b"ex_nord_house_01\x00")
    write_subrecord(refr_sub, "NAME", struct.pack("<I", FID_STAT))
    write_subrecord(refr_sub, "DATA", struct.pack("<ffffff",
        -546730.7, -3512590.5, 19693.95,
        0.0, 0.0, 42.99999894818919))
    write_subrecord(refr_sub, "XSCL", struct.pack("<f", 1.0))
    
    refr_buf = io.BytesIO()
    write_record(refr_buf, "REFR", FID_REFR, 0x00000400, refr_sub)
    
    # ===== WRLD children hierarchy =====
    persistent = io.BytesIO()
    write_grup(persistent, FID_CELL, 8, refr_buf.getvalue())
    
    cell_children = io.BytesIO()
    write_grup(cell_children, FID_CELL, 6, persistent.getvalue())
    
    cell_with_children = io.BytesIO()
    cell_with_children.write(cell_buf.getvalue())
    cell_with_children.write(cell_children.getvalue())
    
    # Worldspace children GRUP type=1, label = Morrowind WRLD formID
    wrld_children = io.BytesIO()
    write_grup(wrld_children, FID_MORROWIND_WRLD, 1, cell_with_children.getvalue())
    
    wrld_grup = io.BytesIO()
    write_grup(wrld_grup, "WRLD", 0, wrld_children.getvalue())
    
    # ===== Top-level groups: STAT first, then WRLD =====
    write_grup(buf, "STAT", 0, stat_buf.getvalue())
    write_grup(buf, "WRLD", 0, wrld_grup.getvalue())
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "wb") as f:
        f.write(buf.getvalue())
    
    print(f"Created {OUTPUT_FILE}")
    print(f"Size: {buf.tell()} bytes")

if __name__ == "__main__":
    main()
