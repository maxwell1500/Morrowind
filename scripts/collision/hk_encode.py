"""
M2: Encoder for bhkPhysicsSystem block. Round-trip test:
    decode polytope from atsd_Sherpa.nif -> encode it back -> diff vs original.

The substitution path (M3) reuses this same encoder with new geometry.

Encoding strategy ("replace-in-place"):
  - SDKV chunk: bytes spliced verbatim from the input NIF.
  - TYPE chunk + all its children (TPTR/TST1/TNA1/FST1/TBDY/THSH/TPAD): verbatim.
    (We do NOT re-encode TBDY varints. The TYPE table is identical to the input.)
  - DATA chunk: re-built. Bytes 0..495 are the system metadata, copied verbatim.
    Bytes 496..607 are the hknpConvexShape, copied verbatim except the 6 hkRelArray
    fields at +556..+603 which get the (possibly new) ITEM indices.
    Bytes 608+ are the polytope arrays + trailing instances, each starting at a
    16-byte-aligned offset.
  - INDX chunk: ITEM and PTCH re-emitted with possibly-shifted offsets.
"""
import struct, sys, os
import hk_decode_lib as _lib  # silent helpers (no side effects)

# ---------------------------------------------------------------------------
# Helpers

def align_up(n, a):
    return (n + a - 1) & ~(a - 1)

def be_size_and_flags(decorator, size_with_header):
    return struct.pack(">I", ((decorator & 0xFF) << 24) | (size_with_header & 0x00FFFFFF))

def pack_chunk(fourcc4, decorator, body_bytes):
    """Wrap body in an 8-byte TAG0-style header. fourcc4 must be 4 bytes."""
    total = 8 + len(body_bytes)
    return be_size_and_flags(decorator, total) + fourcc4 + body_bytes

LEAF = 0x40
PARENT = 0x00

# ---------------------------------------------------------------------------
# DATA layout
#
# Convex polytope arrays (between the convex shape and the mass-distribution
# block). Order is fixed because the hkRelArray fields in hknpConvexHull
# reference them by item index.

POLY_ARRAY_KEYS = [
    # (item_idx, name,         element_size, alignment)
    (8,  "vertices",     12, 4),
    (9,  "planes",       16, 16),
    (10, "faces",         4, 2),
    (11, "indices",       1, 1),
    (12, "faceLinks",     4, 2),
    (13, "vertexEdges",   4, 2),
]

# Trailing instance items (shifted when polytope grows/shrinks).
TRAILING_ITEMS = [
    # (item_idx, size, alignment)
    (6,  80, 16),   # hknpRefMassDistribution
    (7,  40, 8),    # hkRefCountedProperties
    (14, 16, 8),    # hkRefCountedProperties::Entry
    (15, 56, 8),    # hknpShapeMassProperties
]

# ---------------------------------------------------------------------------
def encode_bhk_physics_system(input_data, polytope, items_in, patches_in,
                              type_chunk_abs_off, type_chunk_size,
                              sdkv_abs_off, sdkv_size,
                              data_chunk_abs_off, data_chunk_size,
                              tag0_abs_off):
    """Re-encode a bhkPhysicsSystem block given a polytope and the original
    items/patches/TYPE bytes. Returns the new block bytes (data_length-prefixed)."""

    # --- 1. Build the new DATA bytes
    #
    # Bytes 0..607 are the fixed prefix (system data + hknpConvexShape).
    # The hknpConvexShape's hkRelArray fields at +556..+603 get the ITEM indices
    # for items 8..13 written into them (offset_field = item_idx, size_field = 0).
    # For round-trip these are the same indices already in the file.

    DATA_BASE = data_chunk_abs_off + 8
    fixed_prefix = bytearray(input_data[DATA_BASE : DATA_BASE + 608])

    # Patch the 6 hkRelArray fields with the (round-trip identical) item indices.
    # Field offsets in DATA: 556, 564, 572, 580, 588, 596.
    rel_field_offsets = [556 + i*8 for i in range(6)]
    for (rel_off, (item_idx, _name, _es, _aln)) in zip(rel_field_offsets, POLY_ARRAY_KEYS):
        struct.pack_into("<i", fixed_prefix, rel_off, item_idx)
        struct.pack_into("<i", fixed_prefix, rel_off + 4, 0)

    # --- 2. Lay out polytope arrays starting from offset 608, each 16-aligned
    new_data = bytearray(fixed_prefix)
    new_items = [dict(it) for it in items_in]   # copy, will overwrite data_off/count for changed items

    # We need access to the original DATA bytes for the constant prefix only.
    # The polytope arrays come from the polytope dict; the trailing instances
    # come from the original bytes (their content is unchanged).
    orig_DATA = input_data[DATA_BASE : DATA_BASE + data_chunk_size - 8]

    cur = 608
    # vertices: list of (x,y,z) floats
    cur = align_up(cur, 16)
    new_items[8]["data_off"]  = cur
    new_items[8]["count"]     = len(polytope["vertices"])
    for (x, y, z) in polytope["vertices"]:
        new_data.extend(struct.pack("<fff", x, y, z))
    cur = len(new_data)

    # planes: list of (a,b,c,d) floats — 16 bytes each, must be 16-aligned
    pad = align_up(cur, 16) - cur
    new_data.extend(b"\x00" * pad); cur += pad
    new_items[9]["data_off"]  = cur
    new_items[9]["count"]     = len(polytope["planes"])
    for (a, b, c, d) in polytope["planes"]:
        new_data.extend(struct.pack("<ffff", a, b, c, d))
    cur = len(new_data)

    # faces: list of {firstIndex, numIndices, minHalfAngle} — 4 bytes
    pad = align_up(cur, 16) - cur
    new_data.extend(b"\x00" * pad); cur += pad
    new_items[10]["data_off"] = cur
    new_items[10]["count"]    = len(polytope["faces"])
    for f in polytope["faces"]:
        new_data.extend(struct.pack("<HBB", f["firstIndex"], f["numIndices"], f["minHalfAngle"]))
    cur = len(new_data)

    # indices: list of uint8s
    pad = align_up(cur, 16) - cur
    new_data.extend(b"\x00" * pad); cur += pad
    new_items[11]["data_off"] = cur
    new_items[11]["count"]    = len(polytope["indices"])
    new_data.extend(bytes(polytope["indices"]))
    cur = len(new_data)

    # faceLinks: 124 Edges (4 bytes each)
    pad = align_up(cur, 16) - cur
    new_data.extend(b"\x00" * pad); cur += pad
    new_items[12]["data_off"] = cur
    new_items[12]["count"]    = len(polytope["face_links"])
    for e in polytope["face_links"]:
        new_data.extend(struct.pack("<HBB", e["faceIndex"], e["edgeIndex"], e["padding"]))
    cur = len(new_data)

    # vertexEdges: 28 Edges
    pad = align_up(cur, 16) - cur
    new_data.extend(b"\x00" * pad); cur += pad
    new_items[13]["data_off"] = cur
    new_items[13]["count"]    = len(polytope["vertex_edges"])
    for e in polytope["vertex_edges"]:
        new_data.extend(struct.pack("<HBB", e["faceIndex"], e["edgeIndex"], e["padding"]))
    cur = len(new_data)

    # --- 3. Trailing instance items (unchanged content, shifted positions)
    #     We copy them from the original DATA at their original offsets.
    orig_items_by_idx = {it["i"]: it for it in items_in}
    for (item_idx, size, aln) in TRAILING_ITEMS:
        pad = align_up(cur, 16) - cur
        new_data.extend(b"\x00" * pad); cur += pad
        old_off = orig_items_by_idx[item_idx]["data_off"]
        new_items[item_idx]["data_off"] = cur
        new_data.extend(orig_DATA[old_off : old_off + size])
        cur = len(new_data)

    # --- 4. Trailing padding — pad DATA payload to 16
    pad = align_up(cur, 16) - cur
    new_data.extend(b"\x00" * pad); cur += pad

    # --- 5. Adjust PTCH for items that moved
    #     PTCH offsets that target offsets within items 7 or 14 need to be
    #     shifted by (new_data_off - old_data_off) for those items.
    delta_item7  = new_items[7]["data_off"]  - orig_items_by_idx[7]["data_off"]
    delta_item14 = new_items[14]["data_off"] - orig_items_by_idx[14]["data_off"]
    new_patches = []
    for p in patches_in:
        out_offsets = []
        for off in p["offsets"]:
            old_item7  = orig_items_by_idx[7]["data_off"]
            old_item14 = orig_items_by_idx[14]["data_off"]
            if old_item7 <= off < old_item7 + 40:
                out_offsets.append(off + delta_item7)
            elif old_item14 <= off < old_item14 + 16:
                out_offsets.append(off + delta_item14)
            else:
                out_offsets.append(off)
        new_patches.append({"type_idx": p["type_idx"], "offsets": out_offsets})

    # --- 6. Encode chunks
    # SDKV: verbatim
    sdkv_bytes = input_data[sdkv_abs_off : sdkv_abs_off + sdkv_size]

    # DATA: leaf chunk wrapping new_data
    data_bytes = pack_chunk(b"DATA", LEAF, bytes(new_data))

    # TYPE: verbatim
    type_bytes = input_data[type_chunk_abs_off : type_chunk_abs_off + type_chunk_size]

    # ITEM body
    item_body = bytearray()
    for it in new_items:
        tflags = (it["type_idx"] & 0x00FFFFFF) | ((it["flags"] & 0xFF) << 24)
        item_body.extend(struct.pack("<III", tflags, it["data_off"], it["count"]))
    item_bytes = pack_chunk(b"ITEM", LEAF, bytes(item_body))

    # PTCH body
    patch_body = bytearray()
    for p in new_patches:
        patch_body.extend(struct.pack("<i", p["type_idx"]))
        patch_body.extend(struct.pack("<i", len(p["offsets"])))
        for off in p["offsets"]:
            patch_body.extend(struct.pack("<I", off))
    patch_bytes = pack_chunk(b"PTCH", LEAF, bytes(patch_body))

    # INDX = ITEM + PTCH (parent chunk)
    indx_body = item_bytes + patch_bytes
    indx_bytes = pack_chunk(b"INDX", PARENT, indx_body)

    # TAG0 = SDKV + DATA + TYPE + INDX
    tag0_body = sdkv_bytes + data_bytes + type_bytes + indx_bytes
    tag0_bytes = pack_chunk(b"TAG0", PARENT, tag0_body)

    # bhkPhysicsSystem block payload = u32 data_length + tag0_bytes
    block_payload = struct.pack("<I", len(tag0_bytes)) + tag0_bytes
    return block_payload, new_items, new_patches


# ---------------------------------------------------------------------------
# M2: round-trip test

def main():
    # M2 self-test: parse the same NIF the decoder demo uses, encode it back,
    # diff bytes. Only runs when this module is executed directly.
    import hk_decode as dec
    nif_path = dec.NIF_PATH
    data_in  = dec.data
    items    = dec.items
    patches  = dec.patches

    type_chunk = dec.chunks_by_fourcc[b"TYPE"][0]
    sdkv_chunk = dec.chunks_by_fourcc[b"SDKV"][0]
    data_chunk = dec.chunks_by_fourcc[b"DATA"][0]
    tag0_chunk = dec.chunks_by_fourcc[b"TAG0"][0]

    polytope = {
        "vertices":     dec.verts,
        "planes":       dec.planes,
        "faces":        dec.faces,
        "indices":      dec.indices,
        "face_links":   dec.face_links,
        "vertex_edges": dec.vertex_edges,
    }

    new_block, _new_items, _new_patches = encode_bhk_physics_system(
        data_in, polytope, items, patches,
        type_chunk_abs_off=type_chunk.abs_off, type_chunk_size=type_chunk.size,
        sdkv_abs_off=sdkv_chunk.abs_off, sdkv_size=sdkv_chunk.size,
        data_chunk_abs_off=data_chunk.abs_off, data_chunk_size=data_chunk.size,
        tag0_abs_off=tag0_chunk.abs_off,
    )

    # Compare against the original block
    block_off = dec.phys_blk_off
    block_size = dec.phys_blk_size
    orig_block = data_in[block_off : block_off + block_size]

    print(f"\n=== M2 round-trip diff ===")
    print(f"original block size: {len(orig_block)}")
    print(f"new block size:      {len(new_block)}")
    if len(new_block) != len(orig_block):
        print(f"!!! sizes differ by {len(new_block) - len(orig_block)} bytes")

    # Byte-by-byte diff with offsets in absolute file coordinates
    diffs = []
    for i, (a, b) in enumerate(zip(orig_block, new_block)):
        if a != b:
            diffs.append((i, a, b))
    print(f"differing bytes: {len(diffs)}")
    if diffs:
        print(f"first 32 diffs:")
        for (i, a, b) in diffs[:32]:
            abs_off = block_off + i
            print(f"  block+0x{i:04x} (file 0x{abs_off:04x}): orig 0x{a:02x}  new 0x{b:02x}")
    else:
        print("PASS: byte-identical round-trip")

    # Also write the full new NIF (with header block_size patched if needed) to /tmp
    new_full = bytearray(data_in)
    # Replace the bhkPhysicsSystem block contents
    new_full[block_off : block_off + block_size] = new_block
    # If size changed, update header.block_sizes[3] and shift everything after.
    # For round-trip this should be a no-op.
    if len(new_block) != block_size:
        # Header block_sizes[3] is at file 0x00FE (block_sizes start 0x00F2 + 3*4)
        struct.pack_into("<I", new_full, 0x00F2 + 3*4, len(new_block))
        # Recompute trailing data... For now just report.
        print(f"!!! block size changed; would need to shift trailing blocks by {len(new_block) - block_size} bytes")
    out_path = r"c:\tmp\sf\atsd_Sherpa.roundtrip.nif"
    open(out_path, "wb").write(bytes(new_full))
    print(f"wrote {out_path} ({len(new_full)} bytes)")

if __name__ == "__main__":
    main()
