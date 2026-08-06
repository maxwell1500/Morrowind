"""
reshape_static.py: Scale the cloned kitchenette collision geometry to match
each Morrowind mesh's AABB.

The kitchenette's collision shape has:
  - Section domain: min=(1.176, -1.909, 0.0), max=(1.965, 1.094, 2.048)
    Center=(1.57, -0.41, 1.024), HalfExtent=(0.789, 1.502, 1.024)
  - SimdTree nodes: 8 nodes × 4 children, each child has float min/max AABBs
  - Packed vertices: quantized relative to section domain (auto-rescale)
  - Aabb4BytesCodec nodes: quantized relative to tree domain

Strategy: Scale all FLOAT AABBs from kitchenette domain to mesh AABB.
  For each float coordinate c in collision data:
    c_new = mesh_center + (c - kitchenette_center) * scale
  where scale = mesh_halfextent / kitchenette_halfextent

We modify:
  1. Section domain (DATA+0x370 min, DATA+0x380 max) — 32 bytes
  2. SimdTree node AABBs (DATA+0x4a0, 8 nodes × 128B, AABBs at offset 0-95 per node) — 8×96 bytes
  3. The Aabb4 tree domain (need to find its location)

We do NOT modify:
  - Packed vertices (quantized, auto-rescale with section domain)
  - Primitives (vertex indices)
  - Aabb4BytesCodec compressed nodes (quantized, auto-rescale with tree domain)
"""
import json, os, struct, sys, shutil
import numpy as np

PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
MESH_VERTICES = os.path.join(PROJECT_DIR, r"converted_assets\mapping\morrowind_mesh_verts.json")
TARGET_DIRS = [
    r"C:\Users\max\Projects\Morrowind\converted_assets\meshes",
    r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind",
]
TARGET_DIR = TARGET_DIRS[1]

# Kitchenette collision domain (from Section at DATA+0x360, offset 16-47)
KITCH_DOMAIN_MIN = (1.176, -1.909, 0.0)    # (1.1759... -1.909... 0.0)
KITCH_DOMAIN_MAX = (1.965, 1.094, 2.048)   # (1.9648... 1.0943... 2.0480...)
KITCH_CENTER = tuple((a+b)/2 for a,b in zip(KITCH_DOMAIN_MIN, KITCH_DOMAIN_MAX))
KITCH_HALFEXT = tuple((b-a)/2 for a,b in zip(KITCH_DOMAIN_MIN, KITCH_DOMAIN_MAX))

# Offsets within DATA body
SECTION_OFF = 0x360
SECTION_DOMAIN_MIN_OFF = SECTION_OFF + 16   # 3 floats + 1 pad
SECTION_DOMAIN_MAX_OFF = SECTION_OFF + 32   # 3 floats + 1 pad
SIMDTREE_OFF = 0x4a0
SIMDTREE_NODE_SIZE = 128
SIMDTREE_NODE_COUNT = 8
# Each SimdTree node: 4 children × (min 3 floats + max 3 floats) = 24 bytes per child
# Children data at offset 0-95 in each node (4 × 24 = 96)


def le32(buf, off): return struct.unpack_from("<I", buf, off)[0]


def find_header_offsets(buf):
    p = 38 + 5 + 1 + 4
    num_blocks_off = p; p += 4 + 4
    aL = buf[p]; p += 1 + aL + 4
    psL = buf[p]; p += 1 + psL
    u2L = buf[p]; p += 1 + u2L
    num_types_off = p; p += 2
    types_start = p
    for _ in range(le16(buf, num_types_off)):
        L = le32(buf, p); p += 4 + L
    types_end = p
    type_idx_end = p + le32(buf, num_blocks_off) * 2
    p = type_idx_end
    block_sz_end = p + le32(buf, num_blocks_off) * 4
    p = block_sz_end
    strings_start = p
    ns = le32(buf, p); p += 4 + 4
    for _ in range(ns):
        L = le32(buf, p); p += 4 + L
    p += 4
    return {
        "num_blocks": num_blocks_off,
        "num_types": num_types_off,
        "type_strings": (types_start, types_end - types_start),
        "type_indices": (p, 0),
        "block_sizes": (block_sz_end - le32(buf, num_blocks_off)*4, block_sz_end - (block_sz_end - le32(buf, num_blocks_off)*4)),
        "header_end": p,
    }


def find_bhk_physics(data):
    p = 38+5+1+4
    nb = struct.unpack_from("<I", data, p)[0]; p += 4+4
    aL = data[p]; p += 1+aL+4
    psL = data[p]; p += 1+psL
    u2L = data[p]; p += 1+u2L
    nt = struct.unpack_from("<H", data, p)[0]; p += 2
    types = []
    for _ in range(nt):
        L = struct.unpack_from('<I', data, p)[0]; p += 4
        types.append(data[p:p+L].decode("latin-1")); p += L
    ti = [struct.unpack_from('<H', data, p+i*2)[0] for i in range(nb)]; p += nb*2
    sizes = [struct.unpack_from('<I', data, p+i*4)[0] for i in range(nb)]; p += nb*4
    ns = struct.unpack_from('<I', data, p)[0]; p += 4+4
    for _ in range(ns):
        L = struct.unpack_from('<I', data, p)[0]; p += 4+L
    p += 4
    he = p

    phys_idx = next(i for i in range(nb) if types[ti[i]] == "bhkPhysicsSystem")
    blk_off = he + sum(sizes[:phys_idx])
    return phys_idx, blk_off, sizes[phys_idx]


def find_data_body_off(data, blk_off):
    """Find the DATA chunk body offset within the bhkPhysicsSystem block."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    import hk_decode_lib as lib
    dlen = le32(data, blk_off)
    tag0 = blk_off + 4
    chunks = lib.walk_tag0(data, tag0, tag0 + dlen)
    by_fcc = {}
    def idx(c):
        by_fcc.setdefault(c.fourcc, []).append(c)
        for ch in c.children: idx(ch)
    for c in chunks: idx(c)
    data_c = by_fcc[b"DATA"][0]
    return data_c.body_off


def scale_coord(val, axis, mesh_min, mesh_max):
    """Scale a float coordinate from kitchenette domain to mesh domain."""
    k_center = KITCH_CENTER[axis]
    k_half = KITCH_HALFEXT[axis]
    m_center = (mesh_min[axis] + mesh_max[axis]) / 2.0
    m_half = (mesh_max[axis] - mesh_min[axis]) / 2.0
    if k_half == 0:
        return m_center
    scale = m_half / k_half
    return m_center + (val - k_center) * scale


def reshape_nif(data, mesh_min, mesh_max):
    """Scale the kitchenette collision geometry to mesh AABB. In-place DATA patch."""
    phys_idx, blk_off, _ = find_bhk_physics(data)
    data_body_off = find_data_body_off(data, blk_off)

    out = bytearray(data)

    # 1. Scale section domain (min at +16, max at +32, each 3 floats + pad)
    for axis in range(3):
        # min
        old_min = struct.unpack_from("<f", data, data_body_off + SECTION_DOMAIN_MIN_OFF + axis*4)[0]
        new_min = scale_coord(old_min, axis, mesh_min, mesh_max)
        struct.pack_into("<f", out, data_body_off + SECTION_DOMAIN_MIN_OFF + axis*4, new_min)
        # max
        old_max = struct.unpack_from("<f", data, data_body_off + SECTION_DOMAIN_MAX_OFF + axis*4)[0]
        new_max = scale_coord(old_max, axis, mesh_min, mesh_max)
        struct.pack_into("<f", out, data_body_off + SECTION_DOMAIN_MAX_OFF + axis*4, new_max)

    # 2. Scale SimdTree node AABBs
    for node_i in range(SIMDTREE_NODE_COUNT):
        node_off = data_body_off + SIMDTREE_OFF + node_i * SIMDTREE_NODE_SIZE
        for child_i in range(4):
            child_off = node_off + child_i * 24
            # min 3 floats at child_off, max 3 floats at child_off+12
            for axis in range(3):
                old_min = struct.unpack_from("<f", data, child_off + axis*4)[0]
                new_min = scale_coord(old_min, axis, mesh_min, mesh_max)
                struct.pack_into("<f", out, child_off + axis*4, new_min)
                old_max = struct.unpack_from("<f", data, child_off + 12 + axis*4)[0]
                new_max = scale_coord(old_max, axis, mesh_min, mesh_max)
                struct.pack_into("<f", out, child_off + 12 + axis*4, new_max)

    return bytes(out)


def main():
    import argparse
    ap = argparse.ArgumentParser()
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

        # Compute AABB
        pts = np.array(verts, dtype=np.float64)
        mesh_min = pts.min(axis=0)
        mesh_max = pts.max(axis=0)

        # Ensure minimum thickness
        extent = mesh_max - mesh_min
        min_thick = 0.01
        for i in range(3):
            if extent[i] < min_thick:
                mid = (mesh_min[i] + mesh_max[i]) / 2.0
                mesh_min[i] = mid - min_thick / 2.0
                mesh_max[i] = mid + min_thick / 2.0

        try:
            new_data = reshape_nif(data, mesh_min, mesh_max)
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
            print(f" OK (AABB {mesh_min[0]:.1f},{mesh_min[1]:.1f},{mesh_min[2]:.1f} to {mesh_max[0]:.1f},{mesh_max[1]:.1f},{mesh_max[2]:.1f})")
            ok += 1
            continue

        bak = tgt + ".bak2"
        if not os.path.exists(bak):
            shutil.copy2(tgt, bak)

        with open(tgt, "wb") as f:
            f.write(new_data)

        print(f" OK")
        ok += 1

    print(f"\nDone: {ok} OK, {skip} skipped, {fail} failed")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())