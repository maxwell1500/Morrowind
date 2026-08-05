"""
clone_collision.py: Stage 1 — Clone Havok collision skeleton from donor NIF
into target NIFs. Adds bhkNPCollisionObject + bhkPhysicsSystem blocks,
patches NiNode collision ref and BSXFlags.

Usage:
    python clone_collision.py [--test nif_path] [--dry-run]
"""
import os, sys, struct, shutil

sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as dec

DONOR = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_CrewChest01.nif"
TARGET_DIR = r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind"

# ---------------------------------------------------------------------------
# Low-level helpers

def le32(buf, off): return struct.unpack_from("<I", buf, off)[0]
def le16(buf, off): return struct.unpack_from("<H", buf, off)[0]


def find_header_offsets(buf):
    """Return offsets of every field in the NIF header.
    Dict values are (offset, size) for each region.
    Based on hk_decode_lib._parse_nif_header logic.
    """
    p = 0
    if buf[:38] != b"Gamebryo File Format, Version 20.2.0.7":
        raise ValueError("Not a Starfield NIF")
    p += 38                                  # 0: magic
    p += 5 + 1 + 4                            # 38: version, endian, user_ver
    num_blocks_off = p; p += 4               # 48: num_blocks
    bs_ver_off = p; p += 4                   # 52: bs_version
    aL = buf[p]; auth_off = p; p += 1 + aL   # 56: author_len + author
    unk1_off = p; p += 4                     # after author: unk1
    psL = buf[p]; ps_off = p; p += 1 + psL  # process_script
    u2L = buf[p]; u2_off = p; p += 1 + u2L  # unk2
    num_types_off = p; p += 2               # num_types uint16
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
    strings_start = p                        # num_strings
    num_strings = le32(buf, p); p += 4
    max_sl = le32(buf, p); p += 4
    for _ in range(num_strings):
        L = le32(buf, p); p += 4 + L
    strings_end = p
    num_groups = le32(buf, p); p += 4
    groups_end = p                           # header_end
    return {
        "magic": (0, 38),
        "version": (38, 10),
        "num_blocks": num_blocks_off,
        "bs_version": bs_ver_off,
        "author": (auth_off, 1 + aL),
        "unk1": unk1_off,
        "process_script": (ps_off, 1 + psL),
        "unk2": (u2_off, 1 + u2L),
        "num_types": num_types_off,
        "type_strings": (types_start, types_end - types_start),
        "type_indices": (type_idx_start, type_idx_end - type_idx_start),
        "block_sizes": (block_sz_start, block_sz_end - block_sz_start),
        "strings_region": (strings_start, groups_end - strings_start),
        "header_end": groups_end,
    }


def rebuild_nif(src_buf, offsets, new_num_blocks, new_num_types,
                new_type_strings, new_type_indices, new_block_sizes,
                appended_block_data):
    """Rebuild a NIF with modified header fields.
    
    Extracts invariant header prefix, replaces variable-length arrays,
    then appends original block data + new block data + footer.
    Returns new file bytes.
    """
    fmt = "<IH"
    num_blk_off = offsets["num_blocks"]
    num_typ_off = offsets["num_types"]
    ti_off, ti_sz = offsets["type_indices"]
    bs_off, bs_sz = offsets["block_sizes"]
    ts_off, ts_sz = offsets["type_strings"]
    sr_off, sr_sz = offsets["strings_region"]

    # Build sections
    # 1. Prefix: up to num_types (inclusive)
    prefix = bytearray(src_buf[:num_typ_off])
    prefix += struct.pack("<H", new_num_types)
    # 2. Type strings: old + new
    type_strs = bytearray(src_buf[ts_off:ts_off + ts_sz])
    type_strs += new_type_strings
    # 3. Block type indices (uint16 list)
    type_idx_bytes = struct.pack("<" + "H" * len(new_type_indices), *new_type_indices)
    # 4. Block sizes (uint32 list)
    blk_sz_bytes = struct.pack("<" + "I" * len(new_block_sizes), *new_block_sizes)
    # 5. Strings region (num_strings, max_strlen, strings, num_groups)
    strings_region = src_buf[sr_off:sr_off + sr_sz]
    # 6. Original block data (all bytes from old header_end to before footer)
    old_block_data = src_buf[offsets["header_end"]:-8]
    # 7. Footer
    footer = src_buf[-8:]

    # Assemble
    out = bytearray()
    out += prefix
    out += type_strs
    out += type_idx_bytes
    out += blk_sz_bytes
    out += strings_region
    out += old_block_data
    out += appended_block_data
    out += footer

    # Patch num_blocks in prefix
    struct.pack_into("<I", out, num_blk_off, new_num_blocks)
    # Patch bs_version in prefix (carried over from src)
    return bytes(out)


def read_donor_blocks(donor_path):
    """Extract BSXFlags, bhkNPCollisionObject, bhkPhysicsSystem from donor.
    Returns (bsxflags_raw, bhknp_raw, bhkphys_raw, bhknp_type_str, bhkphys_type_str)."""
    with open(donor_path, "rb") as f:
        data = f.read()
    offs = find_header_offsets(data)
    num_blocks = le32(data, offs["num_blocks"])
    # Read block type indices
    ti_off, ti_sz = offs["type_indices"]
    blk_ti = [le16(data, ti_off + i*2) for i in range(num_blocks)]
    # Read block types
    nt_off = offs["num_types"]
    num_types = le16(data, nt_off)
    ts_off, _ = offs["type_strings"]
    blk_types = []
    p = ts_off
    for _ in range(num_types):
        L = le32(data, p); p += 4
        blk_types.append(data[p:p+L].decode("latin-1")); p += L
    # Read block sizes
    bs_off, _ = offs["block_sizes"]
    blk_sizes = [le32(data, bs_off + i*4) for i in range(num_blocks)]

    # Locate blocks
    cur = offs["header_end"]
    found = {}
    for i in range(num_blocks):
        tn = blk_types[blk_ti[i]]
        sz = blk_sizes[i]
        if tn in ("BSXFlags", "bhkNPCollisionObject", "bhkPhysicsSystem"):
            found[tn] = data[cur:cur+sz]
        cur += sz

    # Get type name strings for new types
    def type_name_bytes(name):
        b = name.encode("latin-1")
        return struct.pack("<I", len(b)) + b

    bhknp_str = type_name_bytes("bhkNPCollisionObject")
    bhkphys_str = type_name_bytes("bhkPhysicsSystem")

    return (found.get("BSXFlags"), found.get("bhkNPCollisionObject"),
            found.get("bhkPhysicsSystem"), bhknp_str, bhkphys_str)


def patch_bhknp_refs(bhknp_raw, target_block_idx, phys_block_idx):
    """Fix bhkNPCollisionObject: target_ref=0, physics_system_ref=new phys block."""
    out = bytearray(bhknp_raw)
    struct.pack_into("<I", out, 0, target_block_idx)   # target_ref = NiNode block
    struct.pack_into("<I", out, 6, phys_block_idx)     # physics_system_ref
    struct.pack_into("<I", out, 10, 0)                  # body_id = 0
    return bytes(out)


def inject_into_target(target_path, donor_blocks, dry_run=False):
    """Inject collision skeleton into a single target NIF."""
    with open(target_path, "rb") as f:
        data = bytearray(f.read())

    offs = find_header_offsets(data)
    old_num_blocks = le32(data, offs["num_blocks"])
    old_num_types = le16(data, offs["num_types"])

    # Read existing block types and indices
    ts_off, ts_sz = offs["type_strings"]
    ti_off, ti_sz = offs["type_indices"]
    blk_types = []
    p = ts_off
    for _ in range(old_num_types):
        L = le32(data, p); p += 4
        blk_types.append(data[p:p+L].decode("latin-1")); p += L
    
    blk_ti = [le16(data, ti_off + i*2) for i in range(old_num_blocks)]

    # Find or create type indices for Havok types
    bhknp_str = donor_blocks["bhknp_str"]
    bhkphys_str = donor_blocks["bhkphys_str"]
    bhknp_name = "bhkNPCollisionObject"
    bhkphys_name = "bhkPhysicsSystem"

    new_type_strs = bytearray()
    new_num_types = old_num_types

    bhknp_ti = None
    bhkphys_ti = None
    for i, t in enumerate(blk_types):
        if t == bhknp_name: bhknp_ti = i
        if t == bhkphys_name: bhkphys_ti = i

    if bhknp_ti is None:
        bhknp_ti = new_num_types
        new_num_types += 1
        new_type_strs += bhknp_str
        blk_types.append(bhknp_name)

    if bhkphys_ti is None:
        bhkphys_ti = new_num_types
        new_num_types += 1
        new_type_strs += bhkphys_str
        blk_types.append(bhkphys_name)

    # New block type indices + sizes
    new_blk_ti = list(blk_ti)
    new_blk_sizes = [le32(data, offs["block_sizes"][0] + i*4) for i in range(old_num_blocks)]

    bhknp_block_idx = old_num_blocks          # first new block
    bhkphys_block_idx = old_num_blocks + 1    # second new block

    new_blk_ti.append(bhknp_ti)
    new_blk_ti.append(bhkphys_ti)
    new_blk_sizes.append(len(donor_blocks["bhknp_raw"]))
    new_blk_sizes.append(len(donor_blocks["bhkphys_raw"]))

    new_num_blocks = old_num_blocks + 2

    # Patch NiNode's collision_object field
    ni_off = offs["header_end"]
    ni_num_extra = le32(data, ni_off + 4)
    coll_obj_field_off = ni_off + 8 + 4 * ni_num_extra + 60
    struct.pack_into("<I", data, coll_obj_field_off, bhknp_block_idx)

    # Patch BSXFlags flags → 0x42 (Havok | Dynamic)
    cur = offs["header_end"]
    for i in range(old_num_blocks):
        tn = blk_types[blk_ti[i]]
        sz = new_blk_sizes[i]
        if tn == "BSXFlags":
            struct.pack_into("<I", data, cur + 4, 0x42)
            break
        cur += sz

    # Fix bhkNPCollisionObject refs
    bhknp_fixed = patch_bhknp_refs(donor_blocks["bhknp_raw"], bhknp_block_idx, bhkphys_block_idx)

    # Build appended block data
    appended = bhknp_fixed + donor_blocks["bhkphys_raw"]

    # Rebuild file
    new_data = rebuild_nif(data, offs, new_num_blocks, new_num_types,
                           new_type_strs, new_blk_ti, new_blk_sizes, appended)

    if dry_run:
        print(f"  Would write {len(new_data)} bytes (was {len(data)})")
        return

    # Backup
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

    # Handle restore
    if args.restore:
        tdir = TARGET_DIR
        count = 0
        for f in sorted(os.listdir(tdir)):
            if f.endswith(".bak"):
                src = os.path.join(tdir, f)
                dst = os.path.join(tdir, f[:-4])
                shutil.copy2(src, dst)
                count += 1
        print(f"Restored {count} .bak files")
        return

    # Load donor blocks
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

    # Determine targets
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
