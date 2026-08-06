"""
encode_static_box.py: Build proper AABB box collision for each mesh.

Encodes 8 box corners as packed vertices (uint16×3) + shared vertices (21-bit×3),
and 12 triangles referencing them. Updates section domain, counts, SimdTree AABBs.

Format details (reverse-engineered from kitchenette):
  - Packed vertices (item 14): 8 bytes each = 3×uint16 (0..65535) + 2 pad bytes
    Dequant: coord = domain_min + (uint16/65535) * (domain_max - domain_min)
  - Shared vertices (item 15): 8 bytes each = u64 with 3×21-bit values + 1 flag bit
    Dequant: coord = domain_min + (val21/2097151) * (domain_max - domain_min)
  - Primitives (item 12): 4 bytes each = 3×uint8 vertex indices + 1 byte (material?)
    Indices 0..N-1 = packed vertices, N..N+M-1 = shared vertices (via sharedVerticesIndex)
  - sharedVerticesIndex (item 13): uint16 array mapping shared slot i to shared vertex i
    (For a box: just 0,1,2,3,4,5)
  - Section domain (offset 16-47): min(3 floats) + max(3 floats) = mesh AABB
  - SimdTree nodes: 8×128B, each has 4 children with float AABBs, scaled to mesh AABB

Usage:
    python encode_static_box.py [--test nif_path] [--dry-run]
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

sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib

# DATA body offsets (from kitchenette analysis)
SECTION_OFF = 0x360
SECTION_DOMAIN_MIN_OFF = SECTION_OFF + 16
SECTION_DOMAIN_MAX_OFF = SECTION_OFF + 32
SECTION_NUM_PACKED_VERTS_OFF = SECTION_OFF + 88
SECTION_NUM_PRIMITIVES_OFF = SECTION_OFF + 89

PRIMITIVES_OFF = 0x3c0       # item 12, 18 × 4B
SHARED_VERTS_INDEX_OFF = 0x410  # item 13, 6 × 2B (uint16)
PACKED_VERTS_OFF = 0x420     # item 14, 14 × 8B
SHARED_VERTS_OFF = 0x460     # item 15, 6 × 8B (u64)
SIMDTREE_OFF = 0x4a0         # item 17, 8 × 128B

NUM_PACKED_VERTS = 8   # box corners
NUM_SHARED_VERTS = 6  # additional unique vertices needed by tree
NUM_PRIMITIVES = 12    # box triangles
NUM_SHARED_VERTS_INDEX = 6  # sharedVerticesIndex entries

# 8 box corners: (x_bit, y_bit, z_bit)
BOX_CORNERS = [
    (0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0),
    (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1),
]

# 12 box triangles (CCW from outside), vertex indices 0-7
BOX_TRIANGLES = [
    (0, 1, 3), (0, 3, 2),   # -Z
    (4, 6, 7), (4, 7, 5),   # +Z
    (0, 4, 5), (0, 5, 1),   # -Y
    (2, 3, 7), (2, 7, 6),   # +Y
    (0, 2, 6), (0, 6, 4),   # -X
    (1, 5, 7), (1, 7, 3),   # +X
]

# 6 shared vertices — we'll use 6 more box edge points
# These satisfy the tree structure. We'll place them at box edge midpoints.
# The kitchenette uses 6 shared verts at specific positions. We'll use:
# shared vertex 0 = (max_x, max_y, min_z)  -- corner 3
# shared vertex 1 = (mid_x, min_y, min_z) -- edge midpoint
# etc. Actually, let's just use 6 of the 8 box corners that the tree needs.
# The kitchenette's SimdTree leaves reference primitives 0-34, where
# primitives 12-17 use shared vertices. We need those 6 triangles to
# reference valid box vertices.

# Simplest: make shared vertices = 6 of the 8 box corners (duplicates of packed)
# This way triangles referencing shared verts 14-19 still hit box corners.
SHARED_VERT_AS_BOX_CORNERS = [0, 1, 2, 3, 5, 7]  # which box corner each shared vert duplicates


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
    p += le32(buf, num_blocks_off) * 2  # type indices
    p += le32(buf, num_blocks_off) * 4  # block sizes
    ns = le32(buf, p); p += 4 + 4
    for _ in range(ns):
        L = le32(buf, p); p += 4 + L
    p += 4
    return {"num_blocks": num_blocks_off, "header_end": p}


def find_bhk_physics(data):
    p = 38+5+1+4
    nb = struct.unpack_from("<I", data, p)[0]; p += 4+4
    aL = data[p]; p += 1+aL+4
    psL = data[p]; p += 1+psL
    u2L = data[p]; p += 1+u2L
    nt = struct.unpack_from('<H', data, p)[0]; p += 2
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
    return blk_off


def find_data_body_off(data, blk_off):
    dlen = le32(data, blk_off)
    chunks = lib.walk_tag0(data, blk_off + 4, blk_off + 4 + dlen)
    by_fcc = {}
    def idx(c):
        by_fcc.setdefault(c.fourcc, []).append(c)
        for ch in c.children: idx(ch)
    for c in chunks: idx(c)
    return by_fcc[b"DATA"][0].body_off


def encode_uint16(val, dmin, dmax):
    """Quantize a float coordinate to uint16 (0..65535) for domain dequant."""
    if dmax == dmin:
        return 0
    return int((val - dmin) / (dmax - dmin) * 65535)


def encode_u21(val, dmin, dmax):
    """Quantize a float coordinate to 21-bit (0..2097151) for shared vertices."""
    if dmax == dmin:
        return 0
    return int((val - dmin) / (dmax - dmin) * 2097151)


def encode_box_nif(data, mesh_min, mesh_max):
    """Replace kitchenette geometry with an AABB box."""
    blk_off = find_bhk_physics(data)
    db = find_data_body_off(data, blk_off)
    out = bytearray(data)

    dmin = list(mesh_min)
    dmax = list(mesh_max)

    # 1. Section domain = mesh AABB
    for axis in range(3):
        struct.pack_into("<f", out, db + SECTION_DOMAIN_MIN_OFF + axis*4, dmin[axis])
        struct.pack_into("<f", out, db + SECTION_DOMAIN_MAX_OFF + axis*4, dmax[axis])

    # 2. Packed vertices: 8 box corners (uint16×3 + 2 pad)
    for i, (bx, by, bz) in enumerate(BOX_CORNERS):
        off = db + PACKED_VERTS_OFF + i * 8
        x = dmin[0] if not bx else dmax[0]
        y = dmin[1] if not by else dmax[1]
        z = dmin[2] if not bz else dmax[2]
        u16x = encode_uint16(x, dmin[0], dmax[0])
        u16y = encode_uint16(y, dmin[1], dmax[1])
        u16z = encode_uint16(z, dmin[2], dmax[2])
        struct.pack_into("<HHH", out, off, u16x, u16y, u16z)
        struct.pack_into("<H", out, off + 6, 0)
    # Zero remaining packed verts (14 - 8 = 6 slots)
    for i in range(8, 14):
        off = db + PACKED_VERTS_OFF + i * 8
        for j in range(8):
            out[off + j] = 0

    # 3. Shared vertices: 6 entries (u64 with 3×21-bit)
    for i in range(NUM_SHARED_VERTS):
        corner_idx = SHARED_VERT_AS_BOX_CORNERS[i]
        bx, by, bz = BOX_CORNERS[corner_idx]
        x = dmin[0] if not bx else dmax[0]
        y = dmin[1] if not by else dmax[1]
        z = dmin[2] if not bz else dmax[2]
        x21 = encode_u21(x, dmin[0], dmax[0])
        y21 = encode_u21(y, dmin[1], dmax[1])
        z21 = encode_u21(z, dmin[2], dmax[2])
        val64 = x21 | (y21 << 21) | (z21 << 42)
        off = db + SHARED_VERTS_OFF + i * 8
        struct.pack_into("<Q", out, off, val64)

    # 4. sharedVerticesIndex: 0,1,2,3,4,5 (identity mapping)
    for i in range(NUM_SHARED_VERTS_INDEX):
        off = db + SHARED_VERTS_INDEX_OFF + i * 2
        struct.pack_into("<H", out, off, i)

    # 5. Primitives: 12 box triangles (4 bytes each: 3 uint8 indices + 1 byte)
    for i, tri in enumerate(BOX_TRIANGLES):
        off = db + PRIMITIVES_OFF + i * 4
        out[off] = tri[0]
        out[off+1] = tri[1]
        out[off+2] = tri[2]
        out[off+3] = 0
    # Zero remaining 6 primitives + 8 bytes padding
    for i in range(12, 18):
        off = db + PRIMITIVES_OFF + i * 4
        for j in range(4):
            out[off + j] = 0
    for j in range(8):
        out[db + PRIMITIVES_OFF + 72 + j] = 0

    # 6. Section counts
    out[db + SECTION_NUM_PACKED_VERTS_OFF] = NUM_PACKED_VERTS
    out[db + SECTION_NUM_PRIMITIVES_OFF] = NUM_PRIMITIVES

    # 7. SimdTree: scale float AABBs from kitchenette domain to mesh AABB
    KITCH_DMIN = (1.17037034034729, -1.9087656736373901, 0.0)
    KITCH_DMAX = (1.999778389930725, 1.0799816846847534, 2.047852039337158)
    k_center = tuple((a+b)/2 for a,b in zip(KITCH_DMIN, KITCH_DMAX))
    k_half = tuple((b-a)/2 for a,b in zip(KITCH_DMIN, KITCH_DMAX))
    m_center = tuple((mesh_min[i]+mesh_max[i])/2 for i in range(3))
    m_half = tuple((mesh_max[i]-mesh_min[i])/2 for i in range(3))

    def scale_val(val, axis):
        if abs(val) > 1e30:
            return val
        if k_half[axis] == 0:
            return m_center[axis]
        return m_center[axis] + (val - k_center[axis]) * (m_half[axis] / k_half[axis])

    for node_i in range(8):
        node_off = db + SIMDTREE_OFF + node_i * 128
        for child_i in range(4):
            child_off = node_off + child_i * 24
            for axis in range(3):
                old_min = struct.unpack_from("<f", data, child_off + axis*4)[0]
                struct.pack_into("<f", out, child_off + axis*4, scale_val(old_min, axis))
                old_max = struct.unpack_from("<f", data, child_off + 12 + axis*4)[0]
                struct.pack_into("<f", out, child_off + 12 + axis*4, scale_val(old_max, axis))

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

        pts = np.array(verts, dtype=np.float64)
        mesh_min = pts.min(axis=0)
        mesh_max = pts.max(axis=0)

        extent = mesh_max - mesh_min
        min_thick = 0.01
        for i in range(3):
            if extent[i] < min_thick:
                mid = (mesh_min[i] + mesh_max[i]) / 2.0
                mesh_min[i] = mid - min_thick / 2.0
                mesh_max[i] = mid + min_thick / 2.0

        try:
            new_data = encode_box_nif(data, mesh_min, mesh_max)
        except Exception as e:
            print(f" FAIL: {e}")
            fail += 1
            continue

        if args.dry_run:
            print(f" OK")
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