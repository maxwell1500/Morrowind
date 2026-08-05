"""
hk_decode_lib: pure-function library for parsing Starfield NIF files
and the embedded Havok TAG0 stream. No side effects on import.

This is the importable subset of hk_decode.py — extracted so the CLI driver
(injectcollision.py) can use the parsers without triggering an end-to-end
demo on import.
"""
import struct

# ---------------------------------------------------------------------------
# Endian helpers

def be32(buf, off): return struct.unpack_from(">I", buf, off)[0]
def le32(buf, off): return struct.unpack_from("<I", buf, off)[0]
def le_u16(buf, off): return struct.unpack_from("<H", buf, off)[0]
def le_u8(buf, off): return buf[off]
def le_f32(buf, off): return struct.unpack_from("<f", buf, off)[0]

# ---------------------------------------------------------------------------
# Havok varuint (matches utils::hk::hkVarUInt_info)

_VARUINT_TABLE = [
    (0b10000000, 7,  1, 0b00000000),
    (0b11000000, 14, 2, 0b10000000),
    (0b11100000, 21, 3, 0b11000000),
    (0b11111000, 27, 4, 0b11100000),
    (0b11111000, 35, 5, 0b11101000),
    (0b11111111, 40, 6, 0b11111000),
    (0b11111000, 59, 8, 0b11110000),
    (0b11111111, 64, 9, 0b11111001),
]

def read_varuint_be(buf, pos):
    prefix = buf[pos]
    for (mask, bits, nbytes, pfx) in _VARUINT_TABLE:
        if (prefix & mask) == pfx:
            break
    else:
        raise ValueError(f"Bad varuint prefix 0x{prefix:02x} at pos {pos}")
    if nbytes == 1:
        return prefix, pos + 1
    value = (prefix & (~mask & 0xFF))
    for i in range(1, nbytes):
        value = (value << 8) | buf[pos + i]
    return value, pos + nbytes

# ---------------------------------------------------------------------------
# NIF header

def _parse_nif_header(buf):
    p = 0
    if buf[:38] != b"Gamebryo File Format, Version 20.2.0.7":
        raise SystemExit("Not a Starfield NIF (header magic mismatch)")
    p += 38
    p += 5 + 1 + 4   # version[5] + endian + user_ver
    num_blocks = le32(buf, p); p += 4
    p += 4           # bs_version
    aL = buf[p]; p += 1 + aL
    p += 4           # unk1
    psL = buf[p]; p += 1 + psL
    u2L = buf[p]; p += 1 + u2L
    num_types = le_u16(buf, p); p += 2
    block_types = []
    for _ in range(num_types):
        L = le32(buf, p); p += 4
        block_types.append(buf[p:p+L].decode("latin-1")); p += L
    block_type_indices = []
    for _ in range(num_blocks):
        block_type_indices.append(le_u16(buf, p)); p += 2
    block_sizes = []
    for _ in range(num_blocks):
        block_sizes.append(le32(buf, p)); p += 4
    num_strings = le32(buf, p); p += 4
    p += 4
    strings = []
    for _ in range(num_strings):
        L = le32(buf, p); p += 4
        strings.append(buf[p:p+L].decode("latin-1")); p += L
    p += 4   # num_groups
    return p, block_type_indices, block_sizes, block_types, strings

# ---------------------------------------------------------------------------
# Havok TAG0 chunk walker

class Chunk:
    __slots__ = ("fourcc", "abs_off", "decorator", "size", "body_off", "body_end", "children", "parent")
    def __init__(self, fourcc, abs_off, decorator, total_size, parent=None):
        self.fourcc = fourcc
        self.abs_off = abs_off
        self.decorator = decorator
        self.size = total_size
        self.body_off = abs_off + 8
        self.body_end = abs_off + total_size
        self.children = []
        self.parent = parent

def walk_tag0(buf, base, end, parent=None):
    pos = base
    chunks = []
    while pos + 8 <= end:
        sz_be = be32(buf, pos)
        decorator = sz_be >> 24
        size = sz_be & 0x00FFFFFF
        fourcc = bytes(buf[pos+4:pos+8])
        c = Chunk(fourcc, pos, decorator, size, parent)
        if fourcc in (b"TAG0", b"TYPE", b"INDX"):
            c.children = walk_tag0(buf, pos + 8, pos + size, c)
        chunks.append(c)
        pos += size
    return chunks

# ---------------------------------------------------------------------------
# Per-chunk decoders

class HkClass:
    def __init__(self):
        self.name = ""
        self.parent = None
        self.template_args = []
        self.optionals = 0
        self.format = None
        self.sub_type = None
        self.version = None
        self.size = None
        self.alignment = None
        self.type_flags = None
        self.fields = []
        self.kind = None
        self.nested_parent = None
        self.nested_classes = []

OPT_FORMAT     = 1 << 0
OPT_SUBTYPE    = 1 << 1
OPT_VERSION    = 1 << 2
OPT_SIZEALIGN  = 1 << 3
OPT_FLAGS      = 1 << 4
OPT_MEMBERS    = 1 << 5
OPT_INTERFACES = 1 << 6
OPT_ATTRIBUTES = 1 << 7
FIELD_FLAG_ADDITIONAL_UNK_VALUE = 1 << 7

def parse_tst1(buf, body_off, body_end):
    out = []
    p = body_off
    cur = bytearray()
    while p < body_end:
        b = buf[p]; p += 1
        if b == 0:
            if cur:
                out.append(cur.decode("latin-1", "replace"))
                cur = bytearray()
        else:
            cur.append(b)
    if cur: out.append(cur.decode("latin-1", "replace"))
    return out

def parse_fst1(buf, body_off, body_end):
    return parse_tst1(buf, body_off, body_end)

def parse_tna1(buf, body_off, body_end, type_names):
    p = body_off
    n, p = read_varuint_be(buf, p)
    classes = [HkClass() for _ in range(n)]
    for i in range(1, n):
        c = classes[i]
        ni, p = read_varuint_be(buf, p)
        c.name = type_names[ni] if ni < len(type_names) else f"<bad:{ni}>"
        n_args, p = read_varuint_be(buf, p)
        for _ in range(n_args):
            param_ni, p = read_varuint_be(buf, p)
            param_value, p = read_varuint_be(buf, p)
            param_type = type_names[param_ni] if param_ni < len(type_names) else f"<bad:{param_ni}>"
            if param_type and param_type[0] == 't':
                ref = classes[param_value] if param_value < len(classes) else None
                c.template_args.append((param_type, ref))
            else:
                c.template_args.append((param_type, param_value))
    return classes

def parse_tbdy(buf, body_off, body_end, classes, field_names):
    p = body_off
    while p < body_end:
        tid, p = read_varuint_be(buf, p)
        if tid == 0:
            break
        c = classes[tid]
        parent_tid, p = read_varuint_be(buf, p)
        if parent_tid > 0:
            c.parent = classes[parent_tid]
        opt, p = read_varuint_be(buf, p)
        c.optionals = opt
        if opt & OPT_FORMAT:
            c.format, p = read_varuint_be(buf, p)
            c.kind = c.format & 0xF
        if opt & OPT_SUBTYPE:
            sub_idx, p = read_varuint_be(buf, p)
            c.sub_type = classes[sub_idx]
        if opt & OPT_VERSION:
            c.version, p = read_varuint_be(buf, p)
        if opt & OPT_SIZEALIGN:
            c.size, p = read_varuint_be(buf, p)
            c.alignment, p = read_varuint_be(buf, p)
        if opt & OPT_FLAGS:
            c.type_flags, p = read_varuint_be(buf, p)
        if opt & OPT_MEMBERS:
            num_members, p = read_varuint_be(buf, p)
            num_fields = num_members & 0xFFFF
            num_props = (num_members >> 16) & 0xFFFF
            if num_props != 0:
                raise NotImplementedError("class properties (num_props != 0)")
            for _ in range(num_fields):
                fld = {}
                fname_idx, p = read_varuint_be(buf, p)
                fld["name"] = field_names[fname_idx] if fname_idx < len(field_names) else f"<bad:{fname_idx}>"
                fflags, p = read_varuint_be(buf, p)
                fld["flags"] = fflags
                if fflags & FIELD_FLAG_ADDITIONAL_UNK_VALUE:
                    unk, p = read_varuint_be(buf, p)
                    fld["unk_value"] = unk
                offs, p = read_varuint_be(buf, p)
                fld["offset"] = offs
                tref, p = read_varuint_be(buf, p)
                fld["type"] = classes[tref] if tref < len(classes) else None
                c.fields.append(fld)
        if opt & OPT_INTERFACES:
            n_if, p = read_varuint_be(buf, p)
            for _ in range(n_if):
                read_varuint_be(buf, p)
                read_varuint_be(buf, p)
        if opt & OPT_ATTRIBUTES:
            raise NotImplementedError("attributes")

def parse_item(buf, body_off, body_end):
    items = []
    p = body_off
    i = 0
    while p + 12 <= body_end:
        tflags = le32(buf, p)
        type_idx = tflags & 0x00FFFFFF
        flags    = (tflags >> 24) & 0xFF
        data_off = le32(buf, p + 4)
        count    = le32(buf, p + 8)
        items.append({"i": i, "type_idx": type_idx, "flags": flags,
                      "data_off": data_off, "count": count})
        p += 12; i += 1
    return items

def parse_ptch(buf, body_off, body_end):
    out = []
    p = body_off
    while p + 8 <= body_end:
        tidx = le32(buf, p); p += 4
        npat = le32(buf, p); p += 4
        offsets = []
        for _ in range(npat):
            offsets.append(le32(buf, p)); p += 4
        out.append({"type_idx": tidx, "offsets": offsets})
    return out
