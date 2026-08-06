"""
clone_box.py: Inject static box-shaped Havok collision from Starborn_CrewChest01.nif
into Morrowind NIFs, scaled per-mesh to its AABB.

This uses the crate's hknpBoxShape (proper box) instead of the kitchenette's
compressed mesh, avoiding the Aabb4BytesCodec tree rebuild problem.
"""
import os, sys, struct, shutil, json

sys.path.insert(0, os.path.dirname(__file__))
import clone_static as cs

DONOR = r"C:\XboxGames\Starfield\Content\Content\Data\meshes\FurnishedStarborn\Starborn_CrewChest01.nif"
TARGET_DIRS = [
    r"C:\Users\max\Projects\Morrowind\converted_assets\meshes",
    r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind",
]
TARGET_DIR = TARGET_DIRS[1]
BOUNDS_PATH = r"C:\Users\max\Projects\Morrowind\converted_assets\mapping\morrowind_mesh_bounds.json"

# Box shape offsets within bhkPhysicsSystem DATA
# Determined from decode_box_shape.py
OBB_OFF = 0x180 + 112
VERTS_ITEM = 6
VERTS_OFF = 0x230
PLANES_ITEM = 7
PLANES_OFF = 0x290
CONVEX_RADIUS_OFF = 0x180 + 32


def load_bounds():
    with open(BOUNDS_PATH, "r") as f:
        return json.load(f)


def get_bounds_for_nif(name_lower, bounds):
    # keys are lowercased object IDs; strip extension
    base = name_lower.lower().replace(".nif", "")
    if base in bounds:
        return bounds[base]
    return None


def scale_box(phys_raw, bounds, name):
    """Return scaled bhkPhysicsSystem bytes based on mesh AABB."""
    phys = bytearray(phys_raw)
    mn = bounds["min"]
    mx = bounds["max"]
    cx = (mn[0] + mx[0]) / 2.0
    cy = (mn[1] + mx[1]) / 2.0
    cz = (mn[2] + mx[2]) / 2.0
    hx = (mx[0] - mn[0]) / 2.0
    hy = (mx[1] - mn[1]) / 2.0
    hz = (mx[2] - mn[2]) / 2.0

    # Avoid zero-extent in any axis (thin meshes)
    min_ext = 0.001
    if hx < min_ext: hx = min_ext
    if hy < min_ext: hy = min_ext
    if hz < min_ext: hz = min_ext

    # Update OBB transform: rotation columns are half-extents on diagonal, translation is center
    # Rotation matrix layout in file (hkRotationf): 3 columns of hkVector4f
    # col0 = (hx, 0, 0, ?)
    # col1 = (0, hy, 0, ?)
    # col2 = (0, 0, hz, ?)
    # translation = (cx, cy, cz, ?)
    # The 4th component seems to be the same as the extent (w component) in donor; preserve pattern
    struct.pack_into("<ffff", phys, OBB_OFF + 0,  hx, 0.0, 0.0, hx)
    struct.pack_into("<ffff", phys, OBB_OFF + 16, 0.0, hy, 0.0, hy)
    struct.pack_into("<ffff", phys, OBB_OFF + 32, 0.0, 0.0, hz, hz)
    struct.pack_into("<ffff", phys, OBB_OFF + 48, cx, cy, cz, 0.5)

    # Update 8 vertices
    corners = [
        ( hx,  hy,  hz),
        (-hx,  hy,  hz),
        ( hx, -hy,  hz),
        (-hx, -hy,  hz),
        ( hx,  hy, -hz),
        (-hx,  hy, -hz),
        ( hx, -hy, -hz),
        (-hx, -hy, -hz),
    ]
    for i, (x, y, z) in enumerate(corners):
        # vertices are relative to center? In donor they are absolute world coords with center offset
        # Donor vertices: +/-0.241 in x/y, z 0.008..0.491. Center is (0,0,0.25), half-extents (0.241,0.241,0.241)
        # So vertices are center + corner_offset
        struct.pack_into("<fff", phys, VERTS_OFF + i*12,
                         cx + x, cy + y, cz + z)

    # Update 6 planes (ax+by+cz+d=0); d is -distance from origin along normal
    planes = [
        (1.0, 0.0, 0.0, -hx),
        (-1.0, 0.0, 0.0, -hx),
        (0.0, 1.0, 0.0, -hy),
        (0.0, -1.0, 0.0, -hy),
        (0.0, 0.0, 1.0, -hz),
        (0.0, 0.0, -1.0, -hz),
    ]
    # Wait donor planes use absolute z values? Actually donor planes:
    # (1,0,0,-0.241), (-1,0,0,-0.241), (0,1,0,-0.241), (0,-1,0,-0.241), (0,0,1,-0.491), (0,0,-1,0.008)
    # These are in object space with center offset. For an axis-aligned box centered at (cx,cy,cz)
    # plane equations should be: x = cx +/- hx -> nx*x+ny*y+nz*z + d = 0
    # For normal (1,0,0), plane x = cx+hx => x - (cx+hx) = 0 => d = -(cx+hx)
    # For normal (-1,0,0), plane x = cx-hx => -x + (cx-hx) = 0 => d = -(cx-hx)
    # The 4th component of hkVector4 is ignored? It's 0 in donor planes.
    for i, (nx, ny, nz) in enumerate([(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]):
        d = -(nx*cx + ny*cy + nz*cz + abs(nx)*hx + abs(ny)*hy + abs(nz)*hz)
        # Actually compute exact d for each face
        if nx == 1: d = -(cx + hx)
        elif nx == -1: d = -(-cx + hx)  # plane x = cx - hx -> -x + cx - hx = 0 => d = cx - hx; wait sign
        # General: nx*x + ny*y + nz*z + d = 0 => d = - (nx*x0 + ny*y0 + nz*z0) for the face point
        # For normal (1,0,0), face at cx+hx: d = -(cx+hx)
        # For normal (-1,0,0), face at cx-hx: d = -(-(cx-hx)) = cx-hx
        # Use formula with sign
        sign = 1 if nx + ny + nz > 0 else -1
        dist = nx*cx + ny*cy + nz*cz + (abs(nx)*hx + abs(ny)*hy + abs(nz)*hz)
        # Actually dist = dot(normal, face_center)
        # d = -dist
        # Recompute simply:
        pass
    # Simpler: compute planes based on face centers
    faces = [
        (1,0,0, cx+hx),
        (-1,0,0, cx-hx),
        (0,1,0, cy+hy),
        (0,-1,0, cy-hy),
        (0,0,1, cz+hz),
        (0,0,-1, cz-hz),
    ]
    for i, (nx, ny, nz, fc) in enumerate(faces):
        d = -(nx*fc + ny*fc + nz*fc)  # no, just d = -dot(normal, face_center)
        d = -(nx*fc + ny*fc + nz*fc) if False else -(nx*fc + ny*fc + nz*fc)
        d = -(nx*fc + ny*fc + nz*fc)
        # Correct: normal is (nx,ny,nz). Plane contains point (fc,?,?) or (?,fc,?) etc. Actually face center has one coordinate = fc, others = center.
        # For x face: center = (fc, cy, cz). dot = nx*fc + ny*cy + nz*cz = fc (since ny=nz=0). d = -fc.
        # So d = -(nx*fc + ny*cy + nz*cz) works because for x faces ny=nz=0.
        # For y faces: nx=nz=0, d = -(ny*fc) = -fc (since fc = cy +/- hy)
        # For z faces: d = -(nz*fc) = -fc
        struct.pack_into("<ffff", phys, PLANES_OFF + i*16, nx, ny, nz, 0.0)
        # Replace d with -fc
        struct.pack_into("<f", phys, PLANES_OFF + i*16 + 12, -fc)

    # convexRadius: keep small relative to smallest half-extent, but at least 0.001
    cr = min(hx, hy, hz) * 0.01
    if cr < 0.001: cr = 0.001
    if cr > 0.05: cr = 0.05
    struct.pack_into("<f", phys, CONVEX_RADIUS_OFF, cr)

    return bytes(phys)


def inject_box(target_path, donor_blocks, bounds_map, dry_run=False):
    name = os.path.basename(target_path)
    base = name.lower().replace(".nif", "")
    bounds = bounds_map.get(base)
    if not bounds:
        raise ValueError(f"No bounds for {name}")

    # Scale the donor physics system to this mesh
    scaled_phys = scale_box(donor_blocks["bhkphys_raw"], bounds, name)

    # Reuse clone_static's injection but with our scaled physics
    with open(target_path, "rb") as f:
        data = bytearray(f.read())
    offs = cs.find_header_offsets(data)
    nb = cs.le32(data, offs["num_blocks"])
    nt = cs.le16(data, offs["num_types"])
    ts_off, _ = offs["type_strings"]
    ti_off, _ = offs["type_indices"]
    bs_off, _ = offs["block_sizes"]

    types = []
    p = ts_off
    for _ in range(nt):
        L = cs.le32(data, p); p += 4
        types.append(data[p:p+L].decode("latin-1")); p += L
    blk_ti = [cs.le16(data, ti_off + i*2) for i in range(nb)]
    blk_sizes = [cs.le32(data, bs_off + i*4) for i in range(nb)]
    block_data = []
    cur = offs["header_end"]
    for i in range(nb):
        block_data.append(bytes(data[cur:cur+blk_sizes[i]]))
        cur += blk_sizes[i]
    footer = bytes(data[cur:])
    raw_prefix = bytes(data[:offs["num_types"]])
    raw_strings_region = bytes(data[offs["strings_region"][0]:offs["strings_region"][0]+offs["strings_region"][1]])

    remove_idxs = set()
    for i in range(nb):
        tn = types[blk_ti[i]]
        if tn in cs.OLD_HAVOK_TYPES:
            remove_idxs.add(i)
    kept_indices = [i for i in range(nb) if i not in remove_idxs]

    new_types = list(types)
    new_blk_ti_kept = [blk_ti[i] for i in kept_indices]
    new_blk_sizes_kept = [blk_sizes[i] for i in kept_indices]
    new_block_data_kept = [block_data[i] for i in kept_indices]

    bhknp_name = "bhkNPCollisionObject"
    bhkphys_name = "bhkPhysicsSystem"
    bhknp_ti = next((i for i, t in enumerate(new_types) if t == bhknp_name), None)
    bhkphys_ti = next((i for i, t in enumerate(new_types) if t == bhkphys_name), None)
    if bhknp_ti is None:
        bhknp_ti = len(new_types); new_types.append(bhknp_name)
    if bhkphys_ti is None:
        bhkphys_ti = len(new_types); new_types.append(bhkphys_name)

    bhknp_block_idx = len(new_blk_ti_kept)
    bhkphys_block_idx = len(new_blk_ti_kept) + 1
    new_blk_ti_kept.append(bhknp_ti)
    new_blk_ti_kept.append(bhkphys_ti)
    new_blk_sizes_kept.append(len(donor_blocks["bhknp_raw"]))
    new_blk_sizes_kept.append(len(scaled_phys))

    bhknp_fixed = cs.patch_bhknp_refs(donor_blocks["bhknp_raw"], 0, bhkphys_block_idx)
    new_block_data_kept.append(bhknp_fixed)
    new_block_data_kept.append(scaled_phys)

    ni_data = bytearray(new_block_data_kept[0])
    ni_num_extra = cs.le32(ni_data, 4)
    coll_off = 8 + 4 * ni_num_extra + 60
    struct.pack_into("<I", ni_data, coll_off, bhknp_block_idx)
    new_block_data_kept[0] = bytes(ni_data)

    for i in range(len(new_blk_ti_kept)):
        tn = new_types[new_blk_ti_kept[i]]
        if tn == "BSXFlags":
            bd = bytearray(new_block_data_kept[i])
            struct.pack_into("<I", bd, 4, 0x02)
            new_block_data_kept[i] = bytes(bd)
            break

    out = bytearray()
    out += raw_prefix
    out += struct.pack("<H", len(new_types))
    for t in new_types:
        b = t.encode("latin-1")
        out += struct.pack("<I", len(b)) + b
    out += struct.pack("<" + "H" * len(new_blk_ti_kept), *new_blk_ti_kept)
    out += struct.pack("<" + "I" * len(new_blk_sizes_kept), *new_blk_sizes_kept)
    out += raw_strings_region
    for bd in new_block_data_kept:
        out += bd
    out += footer
    struct.pack_into("<I", out, offs["num_blocks"], len(new_blk_sizes_kept))
    new_data = bytes(out)

    if dry_run:
        print(f"  Would write {len(new_data)} bytes (was {len(data)})")
        return

    bak = target_path + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(target_path, bak)
    with open(target_path, "wb") as f:
        f.write(new_data)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", help="Process single NIF")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()

    if args.restore:
        count = 0
        for f in sorted(os.listdir(TARGET_DIR)):
            if f.endswith(".bak"):
                src = os.path.join(TARGET_DIR, f)
                dst = os.path.join(TARGET_DIR, f[:-4])
                shutil.copy2(src, dst)
                count += 1
        print(f"Restored {count} .bak files")
        return

    bounds_map = load_bounds()
    bsx_raw, bhknp_raw, bhkphys_raw, bhknp_str, bhkphys_str = cs.read_donor_blocks(DONOR)
    if bhknp_raw is None or bhkphys_raw is None:
        print("ERROR: donor missing Havok blocks")
        return 1
    donor_blocks = {
        "bsxflags_raw": bsx_raw,
        "bhknp_raw": bhknp_raw,
        "bhkphys_raw": bhkphys_raw,
    }

    if args.test:
        targets = [args.test]
    else:
        targets = sorted([
            os.path.join(TARGET_DIR, f)
            for f in os.listdir(TARGET_DIR)
            if f.lower().endswith(".nif") and not f.endswith(".bak") and not f.endswith(".bak2")
        ])

    print(f"\nProcessing {len(targets)} target(s)...")
    ok = fail = 0
    for tgt in targets:
        fname = os.path.basename(tgt)
        print(f"  [{ok+fail+1}/{len(targets)}] {fname}...", end="", flush=True)
        try:
            inject_box(tgt, donor_blocks, bounds_map, dry_run=args.dry_run)
            print(" OK" if not args.dry_run else "")
            ok += 1
        except Exception as e:
            print(f" FAIL: {e}")
            import traceback; traceback.print_exc()
            fail += 1
    print(f"\nDone: {ok} OK, {fail} failed")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())