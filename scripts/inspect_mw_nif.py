"""
Read Morrowind NIF and identify collision structure.
Morrowind NIF format: NetImmerse 4.0.0.0 (NetImmerse File Format)
"""
import struct
import sys

def read_uint32(f):
    return struct.unpack('<I', f.read(4))[0]

def read_uint16(f):
    return struct.unpack('<H', f.read(2))[0]

def read_int32(f):
    return struct.unpack('<i', f.read(4))[0]

def read_float(f):
    return struct.unpack('<f', f.read(4))[0]

def read_string(f, max_len=256):
    length = read_uint32(f)
    if length == 0:
        return ""
    raw = f.read(length)
    return raw.decode('utf-8', errors='replace').rstrip('\x00')

def read_ref(f):
    return read_uint32(f)

def read_ninode(f, indent=0, parent_name=""):
    name = read_string(f)
    extra_data_size = read_uint32(f)
    extra_data_ref = read_ref(f)
    controller_ref = read_ref(f)
    # In NIF 4.0, NiNode has: name, extraDataSize, extraDataRef, controllerRef, numProperties, propertiesRef[], numChildren, childrenRef[]
    num_properties = read_uint32(f)
    for _ in range(num_properties):
        read_ref(f)
    num_children = read_uint32(f)
    children = []
    for _ in range(num_children):
        children.append(read_ref(f))

    print(f"{'  '*indent}NiNode: name={name!r}, extraDataSize={extra_data_size}, extraDataRef={extra_data_ref}, ctrlRef={controller_ref}, props={num_properties}, children={num_children}")
    return name, extra_data_ref, num_children, children

def read_nitrishape(f, indent=0):
    name = read_string(f)
    extra_data_size = read_uint32(f)
    extra_data_ref = read_ref(f)

    num_triangles = read_uint16(f)
    num_vertices = read_uint16(f)

    has_uvs = read_uint32(f)  # bool in Nif
    has_normals = read_uint32(f)  # bool in Nif
    has_vertex_colors = read_uint32(f)
    has_uv2 = read_uint32(f)  # Nif-specific

    # bounding sphere center
    cx = read_float(f)
    cy = read_float(f)
    cz = read_float(f)
    r = read_float(f)

    # vertices
    for _ in range(num_vertices):
        vx = read_float(f)
        vy = read_float(f)
        vz = read_float(f)
    if has_normals:
        for _ in range(num_vertices):
            nx = read_float(f)
            ny = read_float(f)
            nz = read_float(f)
    if has_uvs:
        for _ in range(num_vertices):
            u = read_float(f)
            v = read_float(f)
    if has_vertex_colors:
        for _ in range(num_vertices):
            r = read_uint32(f)
            g = read_uint32(f)
            b = read_uint32(f)
            a = read_uint32(f)

    # triangles
    for _ in range(num_triangles):
        v1 = read_uint16(f)
        v2 = read_uint16(f)
        v3 = read_uint16(f)

    # num match groups
    num_match_groups = read_uint16(f)
    for _ in range(num_match_groups):
        mg_size = read_uint16(f)
        for _ in range(mg_size):
            read_uint16(f)

    # properties
    num_properties = read_uint32(f)
    for _ in range(num_properties):
        read_ref(f)

    print(f"{'  '*indent}NiTriShape: name={name!r}, tris={num_triangles}, verts={num_vertices}, hasUVs={has_uvs}, hasN={has_normals}, props={num_properties}")
    return name

def read_block(f, block_type, indent=0):
    if block_type == "NiNode":
        return read_ninode(f, indent)
    elif block_type == "NiTriShape":
        return read_nitrishape(f, indent)
    else:
        print(f"{'  '*indent}Skipping {block_type} ({f.tell()})")
        return None

def read_nif(path):
    with open(path, 'rb') as f:
        # Header
        version = read_uint32(f)
        v_str = f"{version >> 24}.{(version >> 16) & 0xFF}.{(version >> 8) & 0xFF}.{version & 0xFF}"
        print(f"Version: {v_str}")

        num_blocks = read_uint32(f)
        print(f"Num blocks: {num_blocks}")

        # Read block types
        block_types = []
        block_sizes = []
        for i in range(num_blocks):
            tname_len = read_uint32(f)
            tname = f.read(tname_len).decode('utf-8', errors='replace').rstrip('\x00')
            tsize = read_uint32(f)
            block_types.append(tname)
            block_sizes.append(tsize)
            if tname in ("NiNode", "NiTriShape", "RootCollisionNode"):
                print(f"  Block {i}: {tname}, size={tsize}")

        # Read string table (NIF 4.0.0.0)
        maxstrlen = read_uint32(f)
        strlen = read_uint32(f)
        str_data = f.read(strlen)
        # Position in file after header

        # Read each block
        for i, (bt, bs) in enumerate(zip(block_types, block_sizes)):
            start = f.tell()
            print(f"\nBlock {i}: {bt} at offset {start}, size {bs}")
            if bt in ("NiNode", "RootCollisionNode"):
                read_ninode(f)
            elif bt == "NiTriShape":
                read_nitrishape(f)
            else:
                f.read(bs)
                print(f"  (skipped)")

if __name__ == "__main__":
    nif_path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\max\Projects\Morrowind\raw_assets\Morrowind_Full\meshes\x\ex_nord_house_03.nif"
    read_nif(nif_path)
