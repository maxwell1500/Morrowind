"""
Build a static Havok physics system for a single hknpConvexShape wedge ramp.

This script creates a complete bhkPhysicsSystem raw block (including 4-byte
length prefix) that can be used as donor collision for stair meshes.

It clones the structure of the crate donor (Starborn_CrewChest01.nif) but
replaces the hknpBoxShape with an hknpConvexShape whose hull is a right-
triangular prism ramp.
"""
import struct, math, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as lib

DONOR = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_CrewChest01.nif"

def parse_donor_physics():
    with open(DONOR, 'rb') as f: data = f.read()
    p = 38+5+1+4
    nb = struct.unpack_from('<I', data, p)[0]; p += 4+4
    aL = data[p]; p += 1+aL+4
    psL = data[p]; p += 1+psL
    u2L = data[p]; p += 1+u2L
    nt = struct.unpack_from('<H', data, p)[0]; p += 2
    types = []
    for _ in range(nt):
        L = struct.unpack_from('<I', data, p)[0]; p += 4
        types.append(data[p:p+L].decode('latin-1')); p += L
    ti = [struct.unpack_from('<H', data, p+i*2)[0] for i in range(nb)]; p += nb*2
    sizes = [struct.unpack_from('<I', data, p+i*4)[0] for i in range(nb)]; p += nb*4
    ns = struct.unpack_from('<I', data, p)[0]; p += 4+4
    for _ in range(ns):
        L = struct.unpack_from('<I', data, p)[0]; p += 4+L
    p += 4; he = p
    phys_idx = next(i for i in range(nb) if types[ti[i]] == 'bhkPhysicsSystem')
    blk_off = he + sum(sizes[:phys_idx])
    dlen = struct.unpack_from('<I', data, blk_off)[0]
    raw = data[blk_off:blk_off+4+dlen]
    return raw


def build_ramp_hull(cx, cy, cz, hx, hy, hz):
    """
    Right-triangular prism ramp. Cross-section in YZ plane:
        (-hy, -hz)  -- bottom front
        (+hy, -hz)  -- bottom back
        (+hy, +hz)  -- top back
    Extruded along X from -hx to +hx.
    """
    verts = [
        (cx + hx, cy - hy, cz - hz),   # 0 bottom front right
        (cx - hx, cy - hy, cz - hz),   # 1 bottom front left
        (cx + hx, cy + hy, cz - hz),   # 2 bottom back right
        (cx - hx, cy + hy, cz - hz),   # 3 bottom back left
        (cx + hx, cy + hy, cz + hz),   # 4 top back right
        (cx - hx, cy + hy, cz + hz),   # 5 top back left
    ]

    # Face indices
    faces = [
        (0, 1, 3, 2),   # bottom
        (2, 3, 5, 4),   # back vertical
        (0, 1, 5, 4),   # sloped top
        (0, 2, 4),      # right triangle
        (1, 3, 5),      # left triangle
    ]

    # Build normals per face
    def face_normal(idxs):
        # Newell method
        nx = ny = nz = 0.0
        n = len(idxs)
        for i in range(n):
            v0 = verts[idxs[i]]
            v1 = verts[idxs[(i+1)%n]]
            nx += (v0[1] - v1[1]) * (v0[2] + v1[2])
            ny += (v0[2] - v1[2]) * (v0[0] + v1[0])
            nz += (v0[0] - v1[0]) * (v0[1] + v1[1])
        L = math.sqrt(nx*nx + ny*ny + nz*nz)
        if L == 0: return (0,0,0)
        return (nx/L, ny/L, nz/L)

    planes = []
    for idxs in faces:
        nx, ny, nz = face_normal(idxs)
        # d = -n·p for any vertex in face
        vx, vy, vz = verts[idxs[0]]
        d = -(nx*vx + ny*vy + nz*vz)
        planes.append((nx, ny, nz, d))

    # flatten indices
    flat_indices = []
    face_records = []
    for idxs in faces:
        face_records.append({'first': len(flat_indices), 'num': len(idxs)})
        flat_indices.extend(idxs)

    # Build edge adjacency (simplified: just link to self if not found)
    edge_map = {}
    edges = []
    for fi, idxs in enumerate(faces):
        n = len(idxs)
        for ei in range(n):
            a = idxs[ei]
            b = idxs[(ei+1)%n]
            key = tuple(sorted((a,b)))
            entry = (fi, ei)
            if key not in edge_map:
                edge_map[key] = []
            edge_map[key].append(entry)
            edges.append((fi, ei))

    faceLinks = []
    for fi, ei in edges:
        idxs = faces[fi]
        a = idxs[ei]
        b = idxs[(ei+1)%len(idxs)]
        key = tuple(sorted((a,b)))
        others = [x for x in edge_map[key] if x != (fi, ei)]
        if others:
            faceLinks.append(others[0])
        else:
            faceLinks.append((fi, ei))

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


def pack_varuint(value):
    """Encode a Havok varuint (big-endian prefix scheme)."""
    if value < 0x80:
        return bytes([value])
    elif value < 0x4000:
        return bytes([0x80 | (value >> 8), value & 0xff])
    elif value < 0x200000:
        return bytes([0xc0 | (value >> 16), (value >> 8) & 0xff, value & 0xff])
    elif value < 0x10000000:
        return bytes([0xe0 | (value >> 24), (value >> 16) & 0xff, (value >> 8) & 0xff, value & 0xff])
    else:
        raise ValueError('varuint too large')


def build_physics_system(cx, cy, cz, hx, hy, hz):
    """
    Build a complete bhkPhysicsSystem raw block for a static convex ramp.
    """
    hull = build_ramp_hull(cx, cy, cz, hx, hy, hz)

    # We will build DATA, TYPE, INDX sections from scratch using the crate
    # donor's type/class structure but with the shape swapped to hknpConvexShape.
    # For simplicity, we will hard-code the TYPE/TBDY bytes based on the crate
    # donor and only change the shape class definition.
    #
    # Instead of fully rebuilding TYPE/TBDY, we take a shortcut: use the donor's
    # raw TAG0 stream, parse its sections, and replace the shape item data.
    # But the shape item size changes (176 -> 112) so offsets shift. That
    # requires full rebuild.
    #
    # To minimize risk, we copy the stair NIF's existing physics system and
    # patch item 4 from hknpBoxShape to hknpConvexShape, adding hull data after
    # the existing items.
    raise NotImplementedError('full builder not yet implemented')


if __name__ == '__main__':
    raw = parse_donor_physics()
    print(f"Donor physics system raw block: {len(raw)} bytes")
    hull = build_ramp_hull(0, 0, 0, 1.0, 1.0, 2.0)
    print('Hull:')
    print(' verts', hull['verts'])
    print(' planes', hull['planes'])
    print(' faces', hull['faces'])
    print(' indices', hull['indices'])
    print(' faceLinks', hull['faceLinks'])
    print(' vertexEdges', hull['vertexEdges'])
