"""
reshape_collision.py: Stage 2 — Replace donor box collision with per-mesh
AABB box matching each object's dimensions.

Uses the same 8-vertex/6-face box structure as the donor, so bhkPhysicsSystem
block size stays identical — in-place DATA replacement only, no NIF rebuild.

Usage:
    python reshape_collision.py [--test nif_path] [--dry-run]
"""
import json, os, struct, sys, shutil
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib
import hk_polytope

PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
MESH_VERTICES = os.path.join(PROJECT_DIR, r"converted_assets\mapping\morrowind_mesh_verts.json")
TARGET_DIR = r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind"

# Donor box layout offsets within DATA body
DATA_VERTICES_OFF  = 0x230   # 8 vertices × 12B = 96B
DATA_PLANES_OFF    = 0x290   # 6 planes × 16B = 96B
DATA_FACES_OFF     = 0x2F0   # 6 faces × 4B = 24B
DATA_INDICES_OFF   = 0x310   # 24 indices × 1B = 24B
DATA_FACELINKS_OFF = 0x330   # 24 faceLinks × 4B = 96B
DATA_VERTEDGES_OFF = 0x390   # 8 vertexEdges × 4B = 32B
DATA_TRAILING_OFF  = 0x3B0   # trailing items start here


def le32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


def le16(buf, off):
    return struct.unpack_from("<H", buf, off)[0]


def find_header_offsets(buf):
    p = 0
    if buf[:38] != b"Gamebryo File Format, Version 20.2.0.7":
        raise ValueError("Not a Starfield NIF")
    p += 38
    p += 5 + 1 + 4
    num_blocks_off = p; p += 4
    p += 4
    aL = buf[p]; p += 1 + aL
    p += 4
    psL = buf[p]; p += 1 + psL
    u2L = buf[p]; p += 1 + u2L
    num_types_off = p; p += 2
    types_start = p
    for _ in range(le16(buf, num_types_off)):
        L = le32(buf, p); p += 4 + L
    types_end = p
    type_idx_start = p
    type_idx_end = p + le32(buf, num_blocks_off) * 2
    p = type_idx_end
    block_sz_start = p
    block_sz_end = p + le32(buf, num_blocks_off) * 4
    p = block_sz_end
    strings_start = p
    p += 4; p += 4
    for _ in range(le32(buf, p-8)):
        L = le32(buf, p); p += 4 + L
    p += 4
    groups_end = p
    return {
        "num_blocks": num_blocks_off,
        "num_types": num_types_off,
        "type_strings": (types_start, types_end - types_start),
        "type_indices": (type_idx_start, type_idx_end - type_idx_start),
        "block_sizes": (block_sz_start, block_sz_end - block_sz_start),
        "strings_region": (strings_start, groups_end - strings_start),
        "header_end": groups_end,
    }


def find_bhk_physics(data, offsets):
    num_blocks = le32(data, offsets["num_blocks"])
    ti_off, _ = offsets["type_indices"]
    bs_off, _ = offsets["block_sizes"]

    p, _ = offsets["type_strings"]
    num_types = le16(data, offsets["num_types"])
    blk_types = []
    pp = p
    for _ in range(num_types):
        L = le32(data, pp); pp += 4
        blk_types.append(data[pp:pp+L].decode("latin-1")); pp += L

    blk_ti = [le16(data, ti_off + i*2) for i in range(num_blocks)]
    phys_idx = next(i for i in range(num_blocks) if blk_types[blk_ti[i]] == "bhkPhysicsSystem")

    block_sizes = [le32(data, bs_off + i*4) for i in range(num_blocks)]
    blk_off = offsets["header_end"] + sum(block_sizes[:phys_idx])
    return phys_idx, blk_off, block_sizes[phys_idx]


def box_from_aabb(mins, maxs):
    """Create a box polytope from AABB. Returns (vertices, faces) for hk_polytope."""
    x0, y0, z0 = mins
    x1, y1, z1 = maxs

    vertices = [
        (x0, y0, z0),  # 0
        (x1, y0, z0),  # 1
        (x1, y1, z0),  # 2
        (x0, y1, z0),  # 3
        (x0, y0, z1),  # 4
        (x1, y0, z1),  # 5
        (x1, y1, z1),  # 6
        (x0, y1, z1),  # 7
    ]

    faces = [
        [0, 3, 2, 1],  # -Z
        [4, 5, 6, 7],  # +Z
        [0, 1, 5, 4],  # -Y
        [2, 3, 7, 6],  # +Y
        [0, 4, 7, 3],  # -X
        [1, 2, 6, 5],  # +X
    ]

    return vertices, faces


def reshape_nif(data, verts):
    """Replace box collision DATA in-place. Returns new bytes or None."""
    offsets = find_header_offsets(data)
    phys_idx, blk_off, _ = find_bhk_physics(data, offsets)

    # Compute AABB
    pts = np.array(verts, dtype=np.float64)
    mins = pts.min(axis=0)
    maxs = pts.max(axis=0)

    # Ensure minimum thickness
    extent = maxs - mins
    min_thick = 0.01
    for i in range(3):
        if extent[i] < min_thick:
            mid = (mins[i] + maxs[i]) / 2.0
            mins[i] = mid - min_thick / 2.0
            maxs[i] = mid + min_thick / 2.0

    # Build box polytope
    box_verts, box_faces = box_from_aabb(tuple(mins), tuple(maxs))
    polytope = hk_polytope.build_polytope(box_verts, box_faces)

    # Find DATA chunk body
    data_len = le32(data, blk_off)
    tag0_start = blk_off + 4
    chunks = lib.walk_tag0(data, tag0_start, tag0_start + data_len)
    by_fcc = {}
    def idx(c):
        by_fcc.setdefault(c.fourcc, []).append(c)
        for ch in c.children: idx(ch)
    for c in chunks: idx(c)
    data_c = by_fcc[b"DATA"][0]
    data_body_off = data_c.body_off

    # Build new DATA body (in-place replacement)
    new_data = bytearray(data)

    # Vertices at 0x230: 8 × 12 bytes
    off = data_body_off + DATA_VERTICES_OFF
    for v in polytope["vertices"]:
        struct.pack_into("<fff", new_data, off, v[0], v[1], v[2])
        off += 12

    # Planes at 0x290: 6 × 16 bytes
    off = data_body_off + DATA_PLANES_OFF
    for pl in polytope["planes"]:
        struct.pack_into("<ffff", new_data, off, pl[0], pl[1], pl[2], pl[3])
        off += 16

    # Faces at 0x2F0: 6 × 4 bytes
    off = data_body_off + DATA_FACES_OFF
    for f in polytope["faces"]:
        struct.pack_into("<HBB", new_data, off, f["firstIndex"], f["numIndices"], f["minHalfAngle"])
        off += 4

    # Indices at 0x310: 24 × 1 byte
    off = data_body_off + DATA_INDICES_OFF
    for idx_val in polytope["indices"]:
        new_data[off] = idx_val
        off += 1

    # FaceLinks at 0x330: 24 × 4 bytes
    off = data_body_off + DATA_FACELINKS_OFF
    for e in polytope["face_links"]:
        struct.pack_into("<HBB", new_data, off, e["faceIndex"], e["edgeIndex"], e["padding"])
        off += 4

    # VertexEdges at 0x390: 8 × 4 bytes
    off = data_body_off + DATA_VERTEDGES_OFF
    for e in polytope["vertex_edges"]:
        struct.pack_into("<HBB", new_data, off, e["faceIndex"], e["edgeIndex"], e["padding"])
        off += 4

    return bytes(new_data)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Reshape Havok collision to AABB boxes")
    ap.add_argument("--test", help="Process single NIF")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print(f"Loading vertex data from {MESH_VERTICES}...")
    with open(MESH_VERTICES, "r") as f:
        verts_by_mesh = {k.lower(): v for k, v in json.load(f).items()}
    print(f"  Loaded {len(verts_by_mesh)} meshes")

    if args.test:
        targets = [args.test]
    else:
        targets = sorted([
            os.path.join(TARGET_DIR, f)
            for f in os.listdir(TARGET_DIR)
            if f.lower().endswith(".nif") and not f.endswith(".bak")
        ])

    if not targets:
        print("No target NIFs found")
        return 1

    print(f"\nProcessing {len(targets)} target(s)...")
    ok = skip = fail = 0
    for tgt in targets:
        fname = os.path.basename(tgt)
        obj_id = fname[:-4].lower()
        print(f"  [{ok+skip+fail+1}/{len(targets)}] {fname}...", end="", flush=True)

        verts = verts_by_mesh.get(obj_id)
        if verts is None:
            print(" SKIP (no vertex data)")
            skip += 1
            continue

        with open(tgt, "rb") as f:
            data = f.read()

        try:
            new_data = reshape_nif(data, verts)
        except Exception as e:
            print(f" FAIL: {e}")
            import traceback; traceback.print_exc()
            fail += 1
            continue

        if new_data is None:
            print(" SKIP")
            skip += 1
            continue

        if args.dry_run:
            print(f" OK ({len(data)}B, same size)")
            ok += 1
            continue

        bak = tgt + ".bak3"
        if not os.path.exists(bak):
            shutil.copy2(tgt, bak)

        with open(tgt, "wb") as f:
            f.write(new_data)

        print(f" OK ({len(data)}B)")
        ok += 1

    print(f"\nDone: {ok} OK, {skip} skipped, {fail} failed")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
