"""Generate a MINIMAL test ESP with our own WRLD, 1 CELL, 1 REFR.
This is to test if our own WRLD works without overriding Magnus.
"""
import os
import struct
import io
import zlib
import math

OUTPUT_FILE = r"C:\Users\max\Projects\Morrowind\Data\test_minimal.esp"

PLUGIN_FLAGS = 0x00000100  # ESL only (not master - not depending on Magnus)

# Our own WRLD formIDs (ESL range, no conflict with Magnus)
OUR_WRLD_FID = 0xFE002000
OUR_PNDT_FID = 0xFE002001
OUR_LCTN_FID = 0xFE002002
OUR_CELL_FID = 0xFE002003  # New cell, not Magnus's
OUR_PERSISTENT_CELL_FID = 0xFE002004
OUR_REFR_FID = 0xFE002005
OUR_STAT_FID = 0xFE002006

MW_CELL_SIZE = 8192.0
DEG2RAD = math.pi / 180.0


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
    if isinstance(label, (bytes, bytearray)):
        label_bytes = label[:4].ljust(4, b"\x00")
    elif isinstance(label, str):
        label_bytes = label.encode("ascii")[:4].ljust(4, b"\x00")
    else:
        label_bytes = struct.pack("<I", label & 0xFFFFFFFF)
    buf.write(label_bytes)
    buf.write(struct.pack("<I", grup_type))
    buf.write(b"\x00" * 8)
    buf.write(data)


def main():
    buf = io.BytesIO()
    # TES4 header
    buf.write(b"TES4")
    data_size_pos = buf.tell()
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", PLUGIN_FLAGS))
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", 0x00000240))
    subrecord_start = buf.tell()
    # HEDR
    num_records = 8  # rough estimate
    write_subrecord(buf, "HEDR", struct.pack("<fII", 0.96, num_records, OUR_REFR_FID + 10))
    write_subrecord(buf, "CNAM", b"Vvardenfell Test\x00")
    data_size = buf.tell() - subrecord_start
    buf.seek(data_size_pos)
    buf.write(struct.pack("<I", data_size))
    buf.seek(0, 2)

    # STAT record
    stat_sub = io.BytesIO()
    write_subrecord(stat_sub, "EDID", b"TestCrate\x00")
    write_subrecord(stat_sub, "OBND", struct.pack("<ffffff", -1, -1, -1, 1, 1, 1))
    write_subrecord(stat_sub, "ODTY", struct.pack("<I", 0))
    write_subrecord(stat_sub, "BFCB", b"BGSKeywordForm_Component\x00")
    write_subrecord(stat_sub, "BFCE", b"")
    write_subrecord(stat_sub, "MODL", b"morrowind\\flora_bc_tree_02.nif\x00")
    write_subrecord(stat_sub, "FLLD", struct.pack("<I", 1))
    write_subrecord(stat_sub, "XFLG", b"\x02")
    write_subrecord(stat_sub, "DNAM", struct.pack("<ff", 1.0, 1.0))
    stat_buf = io.BytesIO()
    write_record(stat_buf, "STAT", OUR_STAT_FID, 0, stat_sub)
    stat_group = io.BytesIO()
    stat_group.write(stat_buf.getvalue())
    write_grup(buf, "STAT", 0, stat_group.getvalue())

    # WRLD - our own, NEW worldspace
    wrld_sub = io.BytesIO()
    write_subrecord(wrld_sub, "EDID", b"VvardenfellTest\x00")
    write_subrecord(wrld_sub, "FULL", b"Vvardenfell Test\x00")
    write_subrecord(wrld_sub, "BFCB", b"BGSWorldSpaceOverlay_Component\x00")
    write_subrecord(wrld_sub, "BFCE", b"")
    # World bounds - small, centered on origin
    # DNAM: terrain min as 2 floats (x, y)
    write_subrecord(wrld_sub, "DNAM", struct.pack("<ff", -4096.0, -4096.0))
    # MNAM: 4 floats (offset, scale?)
    write_subrecord(wrld_sub, "MNAM", struct.pack("<ffff", 0.0, 0.0, 0.0, 0.0))
    # ONAM: 4 floats (orientation)
    write_subrecord(wrld_sub, "ONAM", struct.pack("<ffff", 1.0, 0.0, 0.0, 0.0))
    # NAM0: outer NW corner
    write_subrecord(wrld_sub, "NAM0", struct.pack("<ff", -4096.0, -4096.0))
    # NAM9: outer SE corner
    write_subrecord(wrld_sub, "NAM9", struct.pack("<ff", 4096.0, 4096.0))
    # DATA
    write_subrecord(wrld_sub, "DATA", b"\x00")
    wrld_buf = io.BytesIO()
    write_record(wrld_buf, "WRLD", OUR_WRLD_FID, 0, wrld_sub)

    # WRLD children
    wrld_children = io.BytesIO()

    # Persistent cell
    persistent_cell_sub = io.BytesIO()
    write_subrecord(persistent_cell_sub, "EDID", b"VvardenfellTestPersistent\x00")
    write_subrecord(persistent_cell_sub, "DATA", struct.pack("<I", 0x00000002))
    write_subrecord(persistent_cell_sub, "XCLC", struct.pack("<iii", 0x7FFFFFFF, 0x7FFFFFFF, 0))
    write_subrecord(persistent_cell_sub, "LTMP", struct.pack("<I", 0))
    write_subrecord(persistent_cell_sub, "XCLW", struct.pack("<f", 0.0))
    write_subrecord(persistent_cell_sub, "XILS", struct.pack("<f", 1.0))
    persistent_cell_buf = io.BytesIO()
    write_compressed_record(persistent_cell_buf, "CELL", OUR_PERSISTENT_CELL_FID, 0, persistent_cell_sub)
    persistent_grup = io.BytesIO()
    write_grup(persistent_grup, OUR_PERSISTENT_CELL_FID, 8, b"")
    persistent_children = io.BytesIO()
    write_grup(persistent_children, OUR_PERSISTENT_CELL_FID, 6, persistent_grup.getvalue())
    wrld_children.write(persistent_children.getvalue())

    # Exterior cell at (0, 0) with 1 REFR
    cell_sub = io.BytesIO()
    write_subrecord(cell_sub, "EDID", b"VvardenfellTestCell00\x00")
    write_subrecord(cell_sub, "FULL", b"Vvardenfell Test Cell 0,0\x00")
    write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00000202))
    write_subrecord(cell_sub, "XCLC", struct.pack("<iii", 0, 0, 0))
    write_subrecord(cell_sub, "LTMP", struct.pack("<I", 0))
    write_subrecord(cell_sub, "XCLW", struct.pack("<f", 0.0))
    write_subrecord(cell_sub, "XILS", struct.pack("<f", 1.0))
    cell_buf = io.BytesIO()
    write_record(cell_buf, "CELL", OUR_CELL_FID, 0, cell_sub)

    # REFR
    refr_sub = io.BytesIO()
    write_subrecord(refr_sub, "NAME", struct.pack("<I", OUR_STAT_FID))
    write_subrecord(refr_sub, "DATA", struct.pack("<ffffff", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    refr_buf = io.BytesIO()
    write_record(refr_buf, "REFR", OUR_REFR_FID, 0x00010400, refr_sub)
    refr_grup_inner = io.BytesIO()
    refr_grup_inner.write(refr_buf.getvalue())
    refr_grup = io.BytesIO()
    write_grup(refr_grup, OUR_CELL_FID, 9, refr_grup_inner.getvalue())
    cell_children = io.BytesIO()
    write_grup(cell_children, OUR_CELL_FID, 6, refr_grup.getvalue())

    # Block/sub-block for cell (0, 0)
    subblock = io.BytesIO()
    subblock.write(cell_buf.getvalue())
    subblock.write(cell_children.getvalue())
    cell_block = io.BytesIO()
    write_grup(cell_block, struct.pack("<hh", 0, 0), 5, subblock.getvalue())
    block = io.BytesIO()
    write_grup(block, struct.pack("<hh", 0, 0), 4, cell_block.getvalue())
    wrld_children.write(block.getvalue())

    wrld_children_grup = io.BytesIO()
    write_grup(wrld_children_grup, OUR_WRLD_FID, 1, wrld_children.getvalue())

    wrld_group_content = io.BytesIO()
    wrld_group_content.write(wrld_buf.getvalue())
    wrld_group_content.write(wrld_children_grup.getvalue())
    write_grup(buf, "WRLD", 0, wrld_group_content.getvalue())

    # PNDT
    pndt_sub = io.BytesIO()
    write_subrecord(pndt_sub, "EDID", b"VvardenfellTestPNDT\x00")
    write_subrecord(pndt_sub, "FULL", b"Vvardenfell Test\x00")
    pndt_buf = io.BytesIO()
    write_record(pndt_buf, "PNDT", OUR_PNDT_FID, 0, pndt_sub)
    pndt_group = io.BytesIO()
    pndt_group.write(pndt_buf.getvalue())
    write_grup(buf, "PNDT", 0, pndt_group.getvalue())

    # LCTN
    lctn_sub = io.BytesIO()
    write_subrecord(lctn_sub, "EDID", b"VvardenfellTestLCTN\x00")
    write_subrecord(lctn_sub, "FULL", b"Vvardenfell Test Location\x00")
    lctn_buf = io.BytesIO()
    write_record(lctn_buf, "LCTN", OUR_LCTN_FID, 0, lctn_sub)
    lctn_group = io.BytesIO()
    lctn_group.write(lctn_buf.getvalue())
    write_grup(buf, "LCTN", 0, lctn_group.getvalue())

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "wb") as f:
        f.write(buf.getvalue())
    print(f"Created {OUTPUT_FILE}")
    print(f"Size: {buf.tell()} bytes")
    print(f"WRLD formID: 0x{OUR_WRLD_FID:08X}")
    print(f"Cell formID: 0x{OUR_CELL_FID:08X}")
    print(f"REFR formID: 0x{OUR_REFR_FID:08X}")


if __name__ == "__main__":
    main()
