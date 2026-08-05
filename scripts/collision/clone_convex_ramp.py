"""
clone_convex_ramp.py: Build a static convex-hull ramp from the Starborn ship model
pedestal donor and inject it into Morrowind stair NIFs.

The pedestal donor uses hknpConvexShape with a real convex hull (vertices, planes,
faces, indices, faceLinks, vertexEdges).  We replace its hull with a right-
triangular prism ramp aligned to the stair bounds.
"""
import os, sys, struct, shutil, json, math

sys.path.insert(0, os.path.dirname(__file__))
import clone_static as cs
import hk_decode_lib as hklib

DONOR = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_ShipModelPedestal01.nif"
TARGET_DIR = r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind"
BOUNDS_PATH = r"C:\Users\max\Projects\Morrowind\converted_assets\mapping\morrowind_mesh_bounds.json"

STAIR_NAMES = {
    'in_c_stair_plain_tall_01',
    'in_c_stair_plain_tall_02',
    'in_c_plain_stair_short',
}


def load_bounds():
    with open(BOUNDS_PATH) as f:
        return json.load(f)


def find_data_body_off(phys_raw):
    dlen = struct.unpack_from("<I", phys_raw, 0)[0]
    chunks = hklib.walk_tag0(phys_raw, 4, 4 + dlen)
    by_fcc = {}
    def idx(c):
        by_fcc.setdefault(c.fourcc, []).append(c)
        for ch in c.children: idx(ch)
    for c in chunks: idx(c)
    return by_fcc[b"DATA"][0].body_off - 0


def build_ramp_hull(cx, cy, cz, hx, hy, hz):
    """
    Right-triangular prism ramp. Cross-section in YZ plane:
        (-hy, -hz)  bottom front
        (+hy, -hz)  bottom back
        (+hy, +hz)  top back
    Extruded along X from -hx to +hx.
    """
    verts = [
        (cx + hx, cy - hy, cz - hz),   # 0
        (cx - hx, cy - hy, cz - hz),   # 1
        (cx + hx, cy + hy, cz - hz),   # 2
        (cx - hx, cy + hy, cz - hz),   # 3
        (cx + hx, cy + hy, cz + hz),   # 4
        (cx - hx, cy + hy, cz + hz),   # 5
    ]

    faces = [
        (0, 1, 3, 2),   # bottom
        (2, 3, 5, 4),   # back vertical
        (0, 1, 5, 4),   # sloped top
        (0, 2, 4),      # right triangle
        (1, 3, 5),      # left triangle
    ]

    def face_normal(idxs):
        nx = ny = nz = 0.0
        n = len(idxs)
        for i in range(n):
            v0 = verts[idxs[i]]
            v1 = verts[idxs[(i+1)%n]]
            nx += (v0[1] - v1[1]) * (v0[2] + v1[2])
            ny += (v0[2] - v1[2]) * (v0[0] + v1[0])
            nz += (v0[0] - v1[0]) * (v0[1] + v1[1])
        L = math.sqrt(nx*nx + ny*ny + nz*nz)
        if L == 0:
            return (0.0, 0.0, 0.0)
        return (nx/L, ny/L, nz/L)

    planes = []
    for idxs in faces:
        nx, ny, nz = face_normal(idxs)
        vx, vy, vz = verts[idxs[0]]
        d = -(nx*vx + ny*vy + nz*vz)
        planes.append((nx, ny, nz, d))

    flat_indices = []
    face_records = []
    for idxs in faces:
        face_records.append({'first': len(flat_indices), 'num': len(idxs)})
        flat_indices.extend(idxs)

    edges = []
    edge_map = {}
    for fi, idxs in enumerate(faces):
        n = len(idxs)
        for ei in range(n):
            a = idxs[ei]
            b = idxs[(ei+1)%n]
            key = tuple(sorted((a, b)))
            entry = (fi, ei)
            edge_map.setdefault(key, []).append(entry)
            edges.append((fi, ei))

    faceLinks = []
    for fi, ei in edges:
        idxs = faces[fi]
        a = idxs[ei]
        b = idxs[(ei+1)%len(idxs)]
        key = tuple(sorted((a, b)))
        others = [x for x in edge_map[key] if x != (fi, ei)]
        faceLinks.append(others[0] if others else (fi, ei))

    vertexEdges = [0xFFFF] * len(verts)
    for ei, (fi, _) in enumerate(edges):
        idxs = faces[fi]
        for v in idxs:
            if vertexEdges[v] == 0xFFFF:
                vertexEdges[v] = ei

    return {
        'verts': verts,
        'planes': planes,
        'faces': face_records,
        'indices': flat_indices,
        'faceLinks': faceLinks,
        'vertexEdges': vertexEdges,
    }


def encode_half16(val):
    """Encode float as Havok half16 (int16). Simple clamped version."""
    # Havok half is 16-bit float: 1 sign, 5 exp, 10 mantissa
    # Use Python's struct float16? Not available. Use simple int16 clamp.
    # Actually maxAllowedPenetration can just be copied from donor.
    return 0


def scale_convex_donor(phys_raw, bounds, name):
    """Replace donor convex hull with a ramp matching the mesh AABB."""
    mn = bounds['min']
    mx = bounds['max']
    cx = (mn[0] + mx[0]) / 2.0
    cy = (mn[1] + mx[1]) / 2.0
    cz = (mn[2] + mx[2]) / 2.0
    hx = (mx[0] - mn[0]) / 2.0
    hy = (mx[1] - mn[1]) / 2.0
    hz = (mx[2] - mn[2]) / 2.0

    min_ext = 0.001
    if hx < min_ext: hx = min_ext
    if hy < min_ext: hy = min_ext
    if hz < min_ext: hz = min_ext

    db = find_data_body_off(phys_raw)

    # Parse donor items to find shape and hull data offsets
    chunks = hklib.walk_tag0(phys_raw, 4, 4 + len(phys_raw) - 4)
    by_fcc = {}
    def idx(c):
        by_fcc.setdefault(c.fourcc, []).append(c)
        for ch in c.children: idx(ch)
    for c in chunks: idx(c)
    items = hklib.parse_item(phys_raw, by_fcc[b'ITEM'][0].body_off, by_fcc[b'ITEM'][0].body_end)

    # Identify shape item (the hknpConvexShape). It should be the one with type_idx
    # matching class 59 (hknpConvexShape). We don't know class idx here, so look for
    # an item whose data contains hull relarrays (non-zero rel offsets with sizes).
    shape_item = None
    for it in items:
        if it['count'] == 1 and it['data_off'] > 0:
            off = db + it['data_off']
            # Check hull relarray at +60: should have non-zero rel offsets
            rels = [struct.unpack_from('<i', phys_raw, off + 60 + i*8)[0] for i in range(6)]
            sizes = [struct.unpack_from('<i', phys_raw, off + 60 + i*8 + 4)[0] for i in range(6)]
            if all(r > 0 for r in rels) and sum(sizes) > 0:
                shape_item = it
                break
    if shape_item is None:
        raise ValueError("Could not find convex shape item in donor")

    shape_off = db + shape_item['data_off']

    # Read hull relarrays
    hull_off = shape_off + 60
    rels = {}
    for name, off in [('verts', 0), ('planes', 8), ('faces', 16), ('indices', 24),
                       ('faceLinks', 32), ('vertexEdges', 40)]:
        rel = struct.unpack_from('<i', phys_raw, hull_off + off)[0]
        sz = struct.unpack_from('<i', phys_raw, hull_off + off + 4)[0]
        rels[name] = (rel, sz)

    # Find absolute data offsets of each hull array (relative to shape start? or DATA start?)
    # In pedestal, rel offsets were small numbers 8,9,10... and item offsets matched them relative to DATA? No,
    # the relarray offsets in hull were 8,9,10,11,12,13. The items were at data_off 0x260, 0x390, 0x610, etc.
    # It seems rel offsets are item indices, not byte offsets. Let's verify.
    # Actually relarray stores offset to data from start of the containing item? Or from DATA body?
    # For pedestal, hull rel for vertices = 8, and item 8 was hkFloat3 at 0x260. So rel = item index!
    # Similarly planes rel=9, item 9 is hkVector4 at 0x390. faces=10, item 10 is faces at 0x610.
    # indices=11, item 11 is hkUint8 at 0x6b0. faceLinks=12, item 12 is hknpConvexHull::Edge at 0x730.
    # vertexEdges=13, item 13 is hknpConvexHull::Edge at 0x930.
    # So the hull relarray references item indices in the ITEM table. That makes sense.
    #
    # Therefore we need to build new ITEM entries for our hull arrays and update the relarray numbers.

    hull = build_ramp_hull(cx, cy, cz, hx, hy, hz)

    # Build new DATA body. We keep all donor items up to the shape, then replace the
    # hull-array items after the shape with our own. For simplicity, we keep the
    # material, properties, mass props items as-is.
    #
    # We'll construct a new data body from scratch with all items.

    # First, figure out the current donor item list and which items are hull arrays.
    # We'll replace items that the hull references with new counts, and adjust offsets.

    # Identify which items are hull arrays by checking if their type_idx matches the relarray numbers.
    # In pedestal, hull rels were 8..13, so those items are replaced.
    hull_item_indices = set(rels[name][0] for name in rels)

    # New item counts
    new_counts = {}
    for name, (rel_idx, _) in rels.items():
        if name == 'verts':
            new_counts[rel_idx] = len(hull['verts'])
        elif name == 'planes':
            new_counts[rel_idx] = len(hull['planes'])
        elif name == 'faces':
            new_counts[rel_idx] = len(hull['faces'])
        elif name == 'indices':
            new_counts[rel_idx] = len(hull['indices'])
        elif name == 'faceLinks':
            new_counts[rel_idx] = len(hull['faceLinks'])
        elif name == 'vertexEdges':
            new_counts[rel_idx] = len(hull['vertexEdges'])

    # Compute sizes of each item based on type. We need to know type sizes.
    # For the hull arrays:
    #   verts: hkFloat3 = 12 bytes each
    #   planes: hkVector4 = 16 bytes each
    #   faces: hknpConvexHull::Face = 4 bytes each
    #   indices: hkUint8 = 1 byte each
    #   faceLinks: hknpConvexHull::Edge = 4 bytes each
    #   vertexEdges: hknpConvexHull::Edge = 4 bytes each
    # But the ITEM type_idx values for these in the pedestal are 76,49,79,13,82,82.
    # We need the class sizes. We can parse the donor's TBDY to get them.

    tna1 = hklib.parse_tna1(phys_raw, by_fcc[b'TNA1'][0].body_off, by_fcc[b'TNA1'][0].body_end,
                            hklib.parse_tst1(phys_raw, by_fcc[b'TST1'][0].body_off, by_fcc[b'TST1'][0].body_end))
    fst1 = hklib.parse_fst1(phys_raw, by_fcc[b'FST1'][0].body_off, by_fcc[b'FST1'][0].body_end)
    hklib.parse_tbdy(phys_raw, by_fcc[b'TBDY'][0].body_off, by_fcc[b'TBDY'][0].body_end, tna1, fst1)

    type_size = {}
    for i, c in enumerate(tna1):
        if c.size is not None:
            type_size[i] = c.size

    # Item alignment: each item starts at offset rounded up to class alignment? For arrays,
    # offsets in donor are not necessarily aligned. We just lay them out sequentially.
    # Donor layout suggests fixed offsets chosen at build time. We'll lay out items in order
    # with no padding, matching donor style.

    # Rebuild DATA body
    new_data_body = bytearray()
    new_item_offsets = {}

    # Copy items before shape item unchanged
    for it in items:
        if it['i'] == shape_item['i']:
            break
        if it['count'] == 0:
            new_item_offsets[it['i']] = 0
            continue
        off = len(new_data_body)
        new_item_offsets[it['i']] = off
        start = db + it['data_off']
        size = it['count'] * type_size.get(it['type_idx'], 1)
        new_data_body += phys_raw[start:start + size]

    # Add shape item (convex shape) - keep same size (112 bytes) but update hull relarray indices
    shape_new_off = len(new_data_body)
    new_item_offsets[shape_item['i']] = shape_new_off
    shape_data = bytearray(phys_raw[shape_off:shape_off + type_size[shape_item['type_idx']]])
    # Update hull relarray item indices. New hull items will be placed immediately after shape.
    next_idx = shape_item['i'] + 1
    struct.pack_into('<i', shape_data, 60 + 0, next_idx + 0)   # verts
    struct.pack_into('<i', shape_data, 60 + 8, next_idx + 1)   # planes
    struct.pack_into('<i', shape_data, 60 + 16, next_idx + 2)  # faces
    struct.pack_into('<i', shape_data, 60 + 24, next_idx + 3)  # indices
    struct.pack_into('<i', shape_data, 60 + 32, next_idx + 4)  # faceLinks
    struct.pack_into('<i', shape_data, 60 + 40, next_idx + 5)  # vertexEdges
    # clear sizes (will be set via new_counts)
    for off in [60+4, 60+12, 60+20, 60+28, 60+36, 60+44]:
        struct.pack_into('<i', shape_data, off, 0)
    new_data_body += shape_data

    # Add new hull array items
    item_idx = next_idx
    # verts
    verts_off = len(new_data_body)
    for v in hull['verts']:
        new_data_body += struct.pack('<fff', *v)
    new_item_offsets[item_idx] = verts_off
    item_idx += 1
    # planes
    planes_off = len(new_data_body)
    for p in hull['planes']:
        new_data_body += struct.pack('<ffff', *p)
    new_item_offsets[item_idx] = planes_off
    item_idx += 1
    # faces
    faces_off = len(new_data_body)
    for f in hull['faces']:
        new_data_body += struct.pack('<HBB', f['first'], f['num'], 0)
    new_item_offsets[item_idx] = faces_off
    item_idx += 1
    # indices
    indices_off = len(new_data_body)
    for idx in hull['indices']:
        new_data_body += bytes([idx])
    new_item_offsets[item_idx] = indices_off
    item_idx += 1
    # faceLinks
    fl_off = len(new_data_body)
    for fi, ei in hull['faceLinks']:
        new_data_body += struct.pack('<HB', fi, ei) + bytes([0])
    new_item_offsets[item_idx] = fl_off
    item_idx += 1
    # vertexEdges
    ve_off = len(new_data_body)
    for ei in hull['vertexEdges']:
        new_data_body += struct.pack('<HBB', ei, 0, 0)
    new_item_offsets[item_idx] = ve_off
    item_idx += 1

    # Skip old hull items in donor
    for it in items:
        if it['i'] <= shape_item['i']:
            continue
        if it['i'] in hull_item_indices:
            continue
        if it['count'] == 0:
            new_item_offsets[it['i']] = 0
            continue
        off = len(new_data_body)
        new_item_offsets[it['i']] = off
        start = db + it['data_off']
        size = it['count'] * type_size.get(it['type_idx'], 1)
        new_data_body += phys_raw[start:start + size]

    # Rebuild ITEM table
    new_items = []
    for it in items:
        new_items.append({
            'i': it['i'],
            'type_idx': it['type_idx'],
            'flags': it['flags'],
            'data_off': new_item_offsets[it['i']],
            'count': new_counts.get(it['i'], it['count']),
        })

    # Rebuild ITEM bytes
    item_bytes = bytearray()
    for it in new_items:
        tflags = (it['flags'] << 24) | it['type_idx']
        item_bytes += struct.pack('<III', tflags, it['data_off'], it['count'])

    # Rebuild PTCH
    # Each patch: type_idx (4) + n_offsets (4) + offsets (4 each)
    # We need to patch all pointer fields. For changed hull relarrays, the offsets changed.
    # For simplicity, parse donor patches and adjust by offset delta for items that moved.
    # We also need to patch the shape's hull relarrays? No, those are encoded in shape data.
    # But ITEM table offsets are patched too.
    patches = hklib.parse_ptch(phys_raw, by_fcc[b'PTCH'][0].body_off, by_fcc[b'PTCH'][0].body_end)
    patch_bytes = bytearray()
    for pt in patches:
        tidx = pt['type_idx']
        # compute offset delta for this type's items
        # For patches that target a specific item, the offset is the item data offset.
        # We can find which item has type_idx and use its offset delta.
        matching_items = [it for it in new_items if it['type_idx'] == tidx]
        if matching_items:
            # assume all items of same type moved by same delta (not always true)
            old_off = items[matching_items[0]['i']]['data_off']
            new_off = matching_items[0]['data_off']
            delta = new_off - old_off
        else:
            delta = 0
        new_offsets = [o + delta for o in pt['offsets']]
        patch_bytes += struct.pack('<II', tidx, len(new_offsets))
        for o in new_offsets:
            patch_bytes += struct.pack('<I', o)

    # Rebuild TYPE section (copy unchanged)
    type_section = phys_raw[by_fcc[b'TYPE'][0].abs_off:by_fcc[b'TYPE'][0].body_end]

    # Rebuild SDKV (copy)
    sdkv_section = phys_raw[by_fcc[b'SDKV'][0].abs_off:by_fcc[b'SDKV'][0].body_end]

    # Rebuild INDX: just ITEM + PTCH
    indx_body = item_bytes + patch_bytes
    indx_size = 8 + len(indx_body)
    indx_section = b'INDX' + struct.pack('<I', indx_size - 8) + indx_body

    # Rebuild DATA: header + new body
    data_size = 8 + len(new_data_body)
    data_section = b'DATA' + struct.pack('<I', data_size - 8) + bytes(new_data_body)

    # Rebuild TYPE with DATA size update? TYPE doesn't know DATA size.
    # Assemble TAG0 body
    tag0_body = sdkv_section + data_section + type_section + indx_section
    tag0_size = 8 + len(tag0_body)
    tag0_section = b'TAG0' + struct.pack('<I', tag0_size - 8) + tag0_body

    new_phys = struct.pack('<I', len(tag0_section)) + tag0_section
    return new_phys


def inject_convex_ramp(target_path, donor_raw, bounds_map, dry_run=False):
    name = os.path.basename(target_path)
    base = name.lower().replace('.nif', '')
    bounds = bounds_map.get(base)
    if not bounds:
        # case-insensitive fallback
        for k, v in bounds_map.items():
            if k.lower() == base:
                bounds = v
                break
    if not bounds:
        if dry_run:
            print(f"  SKIP (no bounds)")
        return

    scaled_phys = scale_convex_donor(donor_raw, bounds, name)

    # Use clone_static injection with our custom physics system
    with open(target_path, 'rb') as f:
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
        if tn in cs.OLD_HAVOK_TYPES or tn in ("bhkNPCollisionObject", "bhkPhysicsSystem"):
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
    new_blk_sizes_kept.append(len(cs.read_donor_blocks(DONOR)[1]))
    new_blk_sizes_kept.append(len(scaled_phys))

    # Donor bhkNPCollisionObject raw (we'll patch target_ref)
    donor_bsx, donor_bhknp, _, _, _ = cs.read_donor_blocks(DONOR)
    bhknp_fixed = cs.patch_bhknp_refs(donor_bhknp, 0, bhkphys_block_idx)
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

    if dry_run:
        print(f"  Would write {len(out)} bytes (was {len(data)})")
        return

    bak = target_path + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(target_path, bak)
    with open(target_path, "wb") as f:
        f.write(bytes(out))


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
    donor_raw = parse_donor_physics(DONOR)

    if args.test:
        targets = [args.test]
    else:
        targets = sorted([
            os.path.join(TARGET_DIR, f)
            for f in os.listdir(TARGET_DIR)
            if f.lower().endswith(".nif") and not f.endswith(".bak") and not f.endswith(".bak2")
               and f.lower().replace(".nif", "") in STAIR_NAMES
        ])

    print(f"\nProcessing {len(targets)} stair target(s)...")
    ok = fail = 0
    for tgt in targets:
        fname = os.path.basename(tgt)
        print(f"  [{ok+fail+1}/{len(targets)}] {fname}...", end="", flush=True)
        try:
            inject_convex_ramp(tgt, donor_raw, bounds_map, dry_run=args.dry_run)
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
