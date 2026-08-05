"""Dump NIF block structure + bhk blocks for any Starfield NIF."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib


def le32(buf, off): return struct.unpack_from("<I", buf, off)[0]
def le16(buf, off): return struct.unpack_from("<H", buf, off)[0]


def dump(path, max_bhkphys_dump=4096):
    with open(path, "rb") as f:
        data = f.read()
    # header
    p = 38 + 5 + 1 + 4
    nb = le32(data, p); p += 4
    bsver = le32(data, p); p += 4
    aL = data[p]; p += 1 + aL + 4
    psL = data[p]; p += 1 + psL
    u2L = data[p]; p += 1 + u2L
    nt = le16(data, p); p += 2
    types = []
    for _ in range(nt):
        L = le32(data, p); p += 4
        types.append(data[p:p+L].decode("latin-1")); p += L
    ti = [le16(data, p + i*2) for i in range(nb)]; p += nb*2
    sizes = [le32(data, p + i*4) for i in range(nb)]; p += nb*4
    p += 4; ns = le32(data, p); p += 4
    for _ in range(ns):
        L = le32(data, p); p += 4 + L
    p += 4
    he = p

    print(f"=== {os.path.basename(path)} ({len(data)}B) ===")
    print(f"Blocks: {nb}, types: {nt}")
    cur = he
    block_offs = []
    for i in range(nb):
        tn = types[ti[i]]
        block_offs.append(cur)
        if tn in ("NiNode", "BSXFlags", "bhkNPCollisionObject", "bhkPhysicsSystem"):
            print(f"  [{i}] {tn} off=0x{cur:x} size={sizes[i]}")
        cur += sizes[i]

    # Show BSXFlags value
    for i in range(nb):
        tn = types[ti[i]]
        if tn == "BSXFlags":
            off = block_offs[i]
            raw = data[off:off+sizes[i]]
            print(f"  BSXFlags raw: {raw.hex()}  (flags=0x{le32(raw,4):08x})")

    # Show bhkNPCollisionObject
    for i in range(nb):
        tn = types[ti[i]]
        if tn == "bhkNPCollisionObject":
            off = block_offs[i]
            raw = data[off:off+sizes[i]]
            print(f"  bhkNPCollisionObject raw ({sizes[i]}B): {raw.hex()}")
            # decode: target_ref(u32), flags(u16), padding(u16)?, phys_ref(u32), body_id(u32)
            if sizes[i] >= 14:
                tgt = le32(raw, 0)
                flags = le16(raw, 4)
                phys = le32(raw, 6)
                body_id = le32(raw, 10)
                print(f"    target_ref={tgt}, flags=0x{flags:04x}, phys_ref={phys}, body_id={body_id}")

    # Walk TAG0 in bhkPhysicsSystem
    for i in range(nb):
        tn = types[ti[i]]
        if tn == "bhkPhysicsSystem":
            off = block_offs[i]
            dlen = le32(data, off)
            tag0_start = off + 4
            chunks = lib.walk_tag0(data, tag0_start, tag0_start + dlen)
            by_fcc = {}
            def idx(c):
                by_fcc.setdefault(c.fourcc, []).append(c)
                for ch in c.children: idx(ch)
            for c in chunks: idx(c)

            print(f"  bhkPhysicsSystem TAG0 tree (data_len={dlen}):")
            def show(c, d=0):
                print(f"{'  '*(d+2)}{c.fourcc.decode()} @0x{c.abs_off:x} size={c.size}")
                for ch in c.children: show(ch, d+1)
            for c in chunks: show(c)

            # items
            if b"ITEM" in by_fcc:
                items = lib.parse_item(data, by_fcc[b"ITEM"][0].body_off, by_fcc[b"ITEM"][0].body_end)
                print(f"  ITEMS ({len(items)}):")
                for it in items:
                    print(f"    [{it['i']}] type_idx={it['type_idx']} data_off=0x{it['data_off']:x} count={it['count']} flags={it['flags']}")

            # DATA size
            if b"DATA" in by_fcc:
                dc = by_fcc[b"DATA"][0]
                print(f"  DATA body_size={dc.size-8}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        dump(p)