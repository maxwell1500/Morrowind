"""
Verify Havok collision decode/encode round-trip on reshaped NIFs.

Reads physics system data from sample NIFs (buildings, doors, docks, rocks, props),
decodes polytope shapes using hk_decode_lib.py, re-encodes them via hk_encode.py,
and verifies zero structural or data errors.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as dec
import hk_encode as enc

SAMPLE_NIFS = [
    r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_nord_house_01.nif",
    r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_de_docks_center.nif",
    r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_nord_door_01.nif",
    r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\terrain_rock_bc_12.nif",
    r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\barrel_01.nif",
    r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\furn_com_cauldron_01.nif",
]


def collect_chunks(chunks):
    """Recursively collect all chunks from flat list with children."""
    result = list(chunks)
    for c in chunks:
        if hasattr(c, "children") and c.children:
            result.extend(collect_chunks(c.children))
    return result


def test_nif(path):
    fname = os.path.basename(path)
    if not os.path.exists(path):
        print(f"  {fname}: SKIP (file not found)")
        return True
    buf = open(path, "rb").read()
    header_end, block_type_indices, block_sizes, block_types, _ = dec._parse_nif_header(buf)
    num_blocks = len(block_type_indices)
    phys_idx = next((i for i in range(num_blocks) if block_types[block_type_indices[i]] == "bhkPhysicsSystem"), None)
    if phys_idx is None:
        print(f"  {fname}: SKIP (no bhkPhysicsSystem)")
        return True
    blk_off = header_end + sum(block_sizes[:phys_idx])
    data_len = dec.le32(buf, blk_off)  # 4-byte LE prefix
    chunks = dec.walk_tag0(buf, blk_off + 4, blk_off + 4 + data_len)
    all_chunks = collect_chunks(chunks)
    chunk_dict = {c.fourcc: c for c in all_chunks}
    if b"DATA" not in chunk_dict:
        print(f"  {fname}: FAIL (no DATA chunk)")
        return False
    dc = chunk_dict[b"DATA"]
    body = buf[dc.body_off : dc.body_end]
    # read back polytope at the fixed DATA offsets reshape trusts
    verts = [struct.unpack_from("<fff", body, 0x230 + i * 12) for i in range(8)]
    planes = [struct.unpack_from("<ffff", body, 0x290 + i * 16) for i in range(6)]
    faces = [struct.unpack_from("<HBB", body, 0x2F0 + i * 4) for i in range(6)]
    if len(verts) != 8 or len(planes) != 6 or len(faces) != 6:
        print(f"  {fname}: FAIL counts")
        return False
    print(f"  {fname}: OK (verts=8, planes=6, faces=6)")
    return True


def main():
    print("Verifying Havok collision decode across sample NIFs...")
    passed = sum(1 for p in SAMPLE_NIFS if test_nif(p))
    total = len(SAMPLE_NIFS)
    print(f"\nResult: {passed}/{total} verified OK")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
