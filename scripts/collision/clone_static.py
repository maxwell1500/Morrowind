"""
clone_static.py: Inject Starfield static Havok collision into Morrowind NIFs.

REMOVES old-format Havok blocks (bhkConvexVerticesShape, bhkCollisionObject,
bhkRigidBody) that SGB exported (these are ignored by Starfield's CK — F4
shows no collision wireframe), and INJECTS new Starfield static blocks
(bhkNPCollisionObject + bhkPhysicsSystem) cloned from a native static NIF.

Donor: Starborn_BuiltInKitchenette01.nif — uses hknpCompressedMeshShape with
motionType=0 (STATIC), flags=0x0080, no motion/mass/drag properties.

Usage:
    python clone_static.py [--test nif_path] [--dry-run] [--restore]
"""
import os, sys, struct, shutil

sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as dec

DONOR = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif"
TARGET_DIR = r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind"

# Old SGB-exported Havok block types to REMOVE
OLD_HAVOK_TYPES = {
    "bhkConvexVerticesShape",
    "bhkCollisionObject",
    "bhkRigidBody",
}

# ---------------------------------------------------------------------------
# Helpers

def le32(buf, off): return struct.unpack_from("<I", buf, off)[0]
def le16(buf, off): return struct.unpack_from("<H", buf, off)[0]


def find_header_offsets(buf):
    p = 0
    if buf[:38] != b"Gamebryo File Format, Version 20.2.0.7":
        raise ValueError("Not a Starfield NIF")
    p += 38 + 5 + 1 + 4
    num_blocks_off = p; p += 4
    p += 4  # bs_version
    aL = buf[p]; p += 1 + aL
    p += 4  # unk1
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
    ns = le32(buf, p); p += 4
    p += 4  # max_strlen
    for _ in range(ns):
        L = le32(buf, p); p += 4 + L
    p += 4  # num_groups
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


def parse_nif(buf):
    """Parse NIF header, return dict with block types, indices, sizes, data, header_end."""
    offs = find_header_offsets(buf)
    nb = le32(buf, offs["num_blocks"])
    nt = le16(buf, offs["num_types"])
    ts_off, _ = offs["type_strings"]
    types = []
    p = ts_off
    for _ in range(nt):
        L = le32(buf, p); p += 4
        types.append(buf[p:p+L].decode("latin-1")); p += L
    ti_off, _ = offs["type_indices"]
    blk_ti = [le16(buf, ti_off + i*2) for i in range(nb)]
    bs_off, _ = offs["block_sizes"]
    blk_sizes = [le32(buf, bs_off + i*4) for i in range(nb)]
    # Extract block data
    block_data = []
    cur = offs["header_end"]
    for i in range(nb):
        block_data.append(buf[cur:cur+blk_sizes[i]])
        cur += blk_sizes[i]
    footer = buf[cur:]
    return {
        "offsets": offs,
        "num_blocks": nb,
        "num_types": nt,
        "types": types,
        "blk_ti": blk_ti,
        "blk_sizes": blk_sizes,
        "block_data": block_data,
        "footer": footer,
    }


def build_nif(parsed, new_types, new_blk_ti, new_blk_sizes, new_block_data):
    """Rebuild NIF bytes from parsed structure with modified block list."""
    offs = parsed["offsets"]
    num_blk_off = offs["num_blocks"]
    num_typ_off = offs["num_types"]
    ts_off, ts_sz = offs["type_strings"]
    sr_off, sr_sz = offs["strings_region"]

    prefix = bytearray(parsed["raw_prefix"] if "raw_prefix" in parsed else b"")
    if not prefix:
        # Build prefix from original buffer up to num_types
        # We need the original buffer; store it in parsed
        raise RuntimeError("raw_prefix not stored")

    type_strs = bytearray()
    for t in new_types:
        b = t.encode("latin-1")
        type_strs += struct.pack("<I", len(b)) + b
    type_idx_bytes = struct.pack("<" + "H" * len(new_blk_ti), *new_blk_ti)
    blk_sz_bytes = struct.pack("<" + "I" * len(new_blk_sizes), *new_blk_sizes)
    strings_region = parsed["raw_strings_region"]

    out = bytearray()
    out += prefix
    out += struct.pack("<H", len(new_types))
    out += type_strs
    out += type_idx_bytes
    out += blk_sz_bytes
    out += strings_region
    for bd in new_block_data:
        out += bd
    out += parsed["footer"]
    struct.pack_into("<I", out, num_blk_off, len(new_blk_sizes))
    return bytes(out)


def read_donor_blocks(donor_path):
    """Extract BSXFlags, bhkNPCollisionObject, bhkPhysicsSystem from donor."""
    with open(donor_path, "rb") as f:
        data = f.read()
    parsed = parse_nif(data)
    found = {}
    for i in range(parsed["num_blocks"]):
        tn = parsed["types"][parsed["blk_ti"][i]]
        if tn in ("BSXFlags", "bhkNPCollisionObject", "bhkPhysicsSystem"):
            found[tn] = parsed["block_data"][i]

    def type_name_bytes(name):
        b = name.encode("latin-1")
        return struct.pack("<I", len(b)) + b

    return (found.get("BSXFlags"), found.get("bhkNPCollisionObject"),
            found.get("bhkPhysicsSystem"),
            type_name_bytes("bhkNPCollisionObject"),
            type_name_bytes("bhkPhysicsSystem"))


def patch_bhknp_refs(bhknp_raw, target_block_idx, phys_block_idx):
    """Patch bhkNPCollisionObject: target_ref, phys_ref, body_id. Preserve flags=0x0080."""
    out = bytearray(bhknp_raw)
    struct.pack_into("<I", out, 0, target_block_idx)
    # DO NOT touch offset 4-5 (flags)
    struct.pack_into("<I", out, 6, phys_block_idx)
    struct.pack_into("<I", out, 10, 0)
    return bytes(out)


def inject_into_target(target_path, donor_blocks, dry_run=False):
    with open(target_path, "rb") as f:
        data = bytearray(f.read())

    offs = find_header_offsets(data)
    nb = le32(data, offs["num_blocks"])
    nt = le16(data, offs["num_types"])
    ts_off, _ = offs["type_strings"]
    ti_off, _ = offs["type_indices"]
    bs_off, _ = offs["block_sizes"]

    types = []
    p = ts_off
    for _ in range(nt):
        L = le32(data, p); p += 4
        types.append(data[p:p+L].decode("latin-1")); p += L
    blk_ti = [le16(data, ti_off + i*2) for i in range(nb)]
    blk_sizes = [le32(data, bs_off + i*4) for i in range(nb)]
    block_data = []
    cur = offs["header_end"]
    for i in range(nb):
        block_data.append(bytes(data[cur:cur+blk_sizes[i]]))
        cur += blk_sizes[i]
    footer = bytes(data[cur:])

    # Store raw prefix (everything up to num_types field) and strings region
    raw_prefix = bytes(data[:offs["num_types"]])
    raw_strings_region = bytes(data[offs["strings_region"][0]:offs["strings_region"][0]+offs["strings_region"][1]])

    # Identify old Havok blocks to remove
    remove_idxs = set()
    for i in range(nb):
        tn = types[blk_ti[i]]
        if tn in OLD_HAVOK_TYPES:
            remove_idxs.add(i)

    # Build new block list (keeping order, excluding removed)
    kept_indices = [i for i in range(nb) if i not in remove_idxs]
    # Map old block idx -> new block idx
    old_to_new = {}
    for new_idx, old_idx in enumerate(kept_indices):
        old_to_new[old_idx] = new_idx

    new_types = list(types)
    new_blk_ti_kept = [blk_ti[i] for i in kept_indices]
    new_blk_sizes_kept = [blk_sizes[i] for i in kept_indices]
    new_block_data_kept = [block_data[i] for i in kept_indices]

    # Add new bhkNP types if not present
    bhknp_name = "bhkNPCollisionObject"
    bhkphys_name = "bhkPhysicsSystem"
    bhknp_ti = None
    bhkphys_ti = None
    for i, t in enumerate(new_types):
        if t == bhknp_name: bhknp_ti = i
        if t == bhkphys_name: bhkphys_ti = i

    if bhknp_ti is None:
        bhknp_ti = len(new_types)
        new_types.append(bhknp_name)
    if bhkphys_ti is None:
        bhkphys_ti = len(new_types)
        new_types.append(bhkphys_name)

    # Append new blocks
    bhknp_block_idx = len(new_blk_ti_kept)
    bhkphys_block_idx = len(new_blk_ti_kept) + 1
    new_blk_ti_kept.append(bhknp_ti)
    new_blk_ti_kept.append(bhkphys_ti)
    new_blk_sizes_kept.append(len(donor_blocks["bhknp_raw"]))
    new_blk_sizes_kept.append(len(donor_blocks["bhkphys_raw"]))

    bhknp_fixed = patch_bhknp_refs(donor_blocks["bhknp_raw"], 0, bhkphys_block_idx)
    new_block_data_kept.append(bhknp_fixed)
    new_block_data_kept.append(donor_blocks["bhkphys_raw"])

    # Patch NiNode (block 0, now still index 0) collision_object ref
    # NiNode is block 0 in kept list (it's never removed)
    ni_data = bytearray(new_block_data_kept[0])
    ni_num_extra = le32(ni_data, 4)
    coll_off = 8 + 4 * ni_num_extra + 60
    struct.pack_into("<I", ni_data, coll_off, bhknp_block_idx)
    new_block_data_kept[0] = bytes(ni_data)

    # Patch BSXFlags flags -> 0x02
    for i in range(len(new_blk_ti_kept)):
        tn = new_types[new_blk_ti_kept[i]]
        if tn == "BSXFlags":
            bd = bytearray(new_block_data_kept[i])
            struct.pack_into("<I", bd, 4, 0x02)
            new_block_data_kept[i] = bytes(bd)
            break

    # Rebuild NIF
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
        print(f"  Removed {len(remove_idxs)} old Havok blocks, added 2 new")
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
    ap.add_argument("--restore", action="store_true", help="Restore .bak files")
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

    print(f"Reading donor: {DONOR}")
    bsx_raw, bhknp_raw, bhkphys_raw, bhknp_str, bhkphys_str = read_donor_blocks(DONOR)
    if bhknp_raw is None or bhkphys_raw is None:
        print("ERROR: donor missing Havok blocks")
        return 1
    print(f"  BSXFlags: {len(bsx_raw)}B, bhkNP: {len(bhknp_raw)}B, bhkPhys: {len(bhkphys_raw)}B")

    donor_blocks = {
        "bsxflags_raw": bsx_raw,
        "bhknp_raw": bhknp_raw,
        "bhkphys_raw": bhkphys_raw,
        "bhknp_str": bhknp_str,
        "bhkphys_str": bhkphys_str,
    }

    if args.test:
        targets = [args.test]
    else:
        targets = sorted([
            os.path.join(TARGET_DIR, f)
            for f in os.listdir(TARGET_DIR)
            if f.lower().endswith(".nif") and not f.endswith(".bak")
        ])

    print(f"\nProcessing {len(targets)} target(s)...")
    ok = fail = 0
    for tgt in targets:
        fname = os.path.basename(tgt)
        print(f"  [{ok+fail+1}/{len(targets)}] {fname}...", end="", flush=True)
        try:
            inject_into_target(tgt, donor_blocks, dry_run=args.dry_run)
            print(" OK")
            ok += 1
        except Exception as e:
            print(f" FAIL: {e}")
            import traceback; traceback.print_exc()
            fail += 1

    print(f"\nDone: {ok} OK, {fail} failed")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())