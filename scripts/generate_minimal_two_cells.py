import os
import struct
import io
import csv
import zlib
import math

OUTPUT_DIR = r"C:\Users\max\Projects\Morrowind\Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "SeydaNeen_minimal_two_cells.esp")
MASTER_PATH = r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm"

PLUGIN_FLAGS = 0x00000101
FID_MORROWIND_WRLD = 0x0100E1C8
MW_CELL_SIZE = 8192.0


def extract_wrld_body(master_path, wrld_formid):
    with open(master_path, "rb") as f:
        data = f.read()
    pos = 0
    while pos < len(data) - 16:
        if data[pos:pos + 4] == b"WRLD":
            size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
            formid = struct.unpack("<I", data[pos + 12:pos + 16])[0]
            if formid == wrld_formid:
                rec = data[pos + 16:pos + 16 + size]
                if rec[:8] == b"\x00\x00\x00\x00@\x02\x00\x00":
                    return rec[8:]
                return rec
            pos += 16 + size
        else:
            pos += 1
    raise RuntimeError("WRLD %08X not found" % wrld_formid)


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


def main():
    next_formid = 0x00000800

    def alloc():
        nonlocal next_formid
        fid = 0xFE000000 | next_formid
        next_formid += 1
        return fid

    stat_fid = alloc()
    stat_sub = io.BytesIO()
    write_subrecord(stat_sub, "EDID", b"test_marker\x00")
    write_subrecord(stat_sub, "OBND", struct.pack("<ffffff", -1.0, -1.0, -1.0, 1.0, 1.0, 1.0))
    write_subrecord(stat_sub, "ODTY", struct.pack("<I", 0))
    write_subrecord(stat_sub, "BFCB", b"BGSKeywordForm_Component\x00")
    write_subrecord(stat_sub, "BFCE", b"")
    write_subrecord(stat_sub, "MODL", b"morrowind\\active_de_bed_30.nif\x00")

    buf = io.BytesIO()
    buf.write(b"TES4")
    data_size_pos = buf.tell()
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", PLUGIN_FLAGS))
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", 0))
    buf.write(struct.pack("<I", 0x00000240))
    subrecord_start = buf.tell()
    num_records = 5  # STAT + 2 CELL + 2 REFR + 1 WRLD
    write_subrecord(buf, "HEDR", struct.pack("<fII", 0.96, num_records, 0xFE000000 | next_formid))
    write_subrecord(buf, "CNAM", b"Minimal Two Cells\x00")
    write_subrecord(buf, "MAST", b"Starfield.esm\x00")
    write_subrecord(buf, "MAST", b"The Elder Star System - Magnus.esm\x00")
    write_subrecord(buf, "BNAM", b"Main\x00")
    write_subrecord(buf, "INCC", struct.pack("<I", 0))
    data_size = buf.tell() - subrecord_start
    buf.seek(data_size_pos)
    buf.write(struct.pack("<I", data_size))
    buf.seek(0, 2)

    stat_group = io.BytesIO()
    write_record(stat_group, "STAT", stat_fid, 0x00000000, stat_sub)
    write_grup(buf, "STAT", 0, stat_group.getvalue())

    # Interior dummy cell to avoid empty CELL group issues
    interior_fid = alloc()
    cell_sub = io.BytesIO()
    write_subrecord(cell_sub, "EDID", b"DummyInterior\x00")
    write_subrecord(cell_sub, "FULL", b"Dummy\x00")
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

    # Exterior cells at (-2,-10) and (-2,-9) each with one REFR at origin
    exterior_block = io.BytesIO()
    for grid_x, grid_y in [(-2, -10), (-2, -9)]:
        cell_fid = alloc()
        cell_sub = io.BytesIO()
        edid = ("Seyda_Neen_Exterior_%d_%d" % (grid_x, grid_y)).encode("ascii")
        write_subrecord(cell_sub, "EDID", edid + b"\x00")
        write_subrecord(cell_sub, "FULL", b"Seyda Neen\x00")
        write_subrecord(cell_sub, "DATA", struct.pack("<I", 0x00000002))
        write_subrecord(cell_sub, "XCLC", struct.pack("<iii", grid_x, grid_y, 0))
        write_subrecord(cell_sub, "LTMP", struct.pack("<I", 0))
        write_subrecord(cell_sub, "XCLW", struct.pack("<f", 0.0))
        cell_buf = io.BytesIO()
        write_compressed_record(cell_buf, "CELL", cell_fid, 0x00000000, cell_sub)

        refr_fid = alloc()
        refr_sub = io.BytesIO()
        write_subrecord(refr_sub, "NAME", struct.pack("<I", stat_fid))
        write_subrecord(refr_sub, "DATA", struct.pack("<ffffff", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        persistent = io.BytesIO()
        write_record(persistent, "REFR", refr_fid, 0x00010400, refr_sub)

        persistent_grup = io.BytesIO()
        write_grup(persistent_grup, cell_fid, 8, persistent.getvalue())
        cell_children = io.BytesIO()
        write_grup(cell_children, cell_fid, 6, persistent_grup.getvalue())

        subblock = io.BytesIO()
        subblock.write(cell_buf.getvalue())
        subblock.write(cell_children.getvalue())
        write_grup(exterior_block, 0, 3, subblock.getvalue())

    exterior_top_block = io.BytesIO()
    write_grup(exterior_top_block, 0, 2, exterior_block.getvalue())

    wrld_children = io.BytesIO()
    write_grup(wrld_children, FID_MORROWIND_WRLD, 1, exterior_top_block.getvalue())

    wrld_override_subrecords = extract_wrld_body(MASTER_PATH, FID_MORROWIND_WRLD)
    wrld_override = io.BytesIO()
    write_record(wrld_override, "WRLD", FID_MORROWIND_WRLD, 0x00000004, wrld_override_subrecords)

    wrld_group_content = io.BytesIO()
    wrld_group_content.write(wrld_override.getvalue())
    wrld_group_content.write(wrld_children.getvalue())
    write_grup(buf, "WRLD", 0, wrld_group_content.getvalue())

    with open(OUTPUT_FILE, "wb") as f:
        f.write(buf.getvalue())
    print("Created %s size=%d" % (OUTPUT_FILE, buf.tell()))


if __name__ == "__main__":
    main()
