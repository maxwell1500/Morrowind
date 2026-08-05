"""
Create a new-format Havok physics system for a single static convex hull (wedge ramp).
This is a hand-built replacement for the bhkPhysicsSystem block used by clone_box.py.

Output is the raw bytes of a bhkPhysicsSystem block (including the 4-byte data length
prefix) that can be inserted into a NIF in place of the box-shaped donor system.
"""
import struct, math
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import hk_decode_lib as hklib

# We need a minimal type hierarchy.  Reuse the crate donor's type table but
# change the shape class from hknpBoxShape to hknpConvexShape.
#
# For simplicity, we clone the crate donor's bhkPhysicsSystem and only mutate:
#   - item 4 class (type_idx) from hknpBoxShape to hknpConvexShape
#   - shape data area to hold a hknpConvexShape (112 bytes) instead of hknpBoxShape (176)
#   - add convex hull data items after the existing items
#
# This requires rebuilding the TAG0 stream because offsets shift.
#
# Strategy: parse the crate donor completely, then programmatically rebuild DATA,
# TYPE, INDX sections with the new shape.

DONOR = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_CrewChest01.nif"

def parse_nif(path):
    with open(path, 'rb') as f: data = f.read()
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
    p += 4
    header_end = p
    return data, types, ti, sizes, header_end

def parse_physics(data, types, ti, sizes, header_end):
    phys_idx = next(i for i in range(len(ti)) if types[ti[i]] == 'bhkPhysicsSystem')
    blk_off = header_end + sum(sizes[:phys_idx])
    dlen = struct.unpack_from('<I', data, blk_off)[0]
    chunks = hklib.walk_tag0(data, blk_off+4, blk_off+4+dlen)
    by = {}
    def idx(c):
        by.setdefault(c.fourcc, []).append(c)
        for ch in c.children: idx(ch)
    for c in chunks: idx(c)
    return by, blk_off, dlen


def build_convex_hull_data(cx, cy, cz, hx, hy, hz):
    """
    Build a triangular prism (wedge) ramp aligned so:
      - bottom face is at z = cz - hz
      - top back edge is at z = cz + hz
      - slope runs along +Y
    The 6 vertices are:
      0: +hx, -hy, -hz   (bottom front right)
      1: -hx, -hy, -hz   (bottom front left)
      2: +hx, +hy, -hz   (bottom back right)
      3: -hx, +hy, -hz   (bottom back left)
      4: +hx, +hy, +hz   (top back right)
      5: -hx, +hy, +hz   (top back left)
    Faces (5):
      bottom:  0,1,3,2   normal (0,0,-1)
      top:     4,5,3,2    normal (0, sin, cos) sloped
      front:   0,1,5,4    normal (0,-1,0)
      right:   0,2,4      normal (1,0,0)
      left:    1,3,5      normal (-1,0,0)
    Actually a triangular prism has 5 faces: 2 triangles and 3 quads.
    """
    verts = [
        ( cx + hx, cy - hy, cz - hz ),
        ( cx - hx, cy - hy, cz - hz ),
        ( cx + hx, cy + hy, cz - hz ),
        ( cx - hx, cy + hy, cz - hz ),
        ( cx + hx, cy + hy, cz + hz ),
        ( cx - hx, cy + hy, cz + hz ),
    ]

    # Plane normals and d values (n·p + d = 0 => d = -n·p for a point on the plane)
    # Right face: points 0,2,4, normal +X, point 0 => d = -(cx+hx)
    # Left face: points 1,3,5, normal -X, point 1 => d = -(-(cx-hx)) = -(hx-cx) = cx-hx? Wait:
    #   plane -x + d = 0 contains x=cx-hx => -(cx-hx)+d=0 => d=cx-hx.
    # Front face: y=cy-hy, normal -Y => d = -( -(cy-hy)) = cy-hy
    # Bottom face: z=cz-hz, normal -Z => d = -( -(cz-hz)) = cz-hz
    # Back/slope face: contains points 2,3,4,5.  This is a sloped rectangle.
    #   normal = (0, -hz, 2*hy) ??? Let's compute.
    #   Edge v2->v4 = (0,0,2hz). Edge v2->v3 = (-2hx,0,0). Cross = (0, -? , 0)
    #   Actually the sloped face normal should have +Y and +Z components.
    #   Use points v2=(cx+hx, cy+hy, cz-hz), v3=(cx-hx, cy+hy, cz-hz), v4=(cx+hx, cy+hy, cz+hz).
    #   v2->v3 = (-2hx, 0, 0); v2->v4 = (0,0,2hz). Cross = (0, 4*hx*hz, 0). That's pure Y.
    #   Wait, those three points are not independent because v2 and v3 share same y,z, v4 shares y with v2 but different z.
    #   The face is planar? v2, v3, v4, v5: v5 = v3 + (0,0,2hz). So face is a rectangle in the plane y=cy+hy.
    #   Oh! The back face is vertical (parallel to YZ), at y=cy+hy. Its normal is +Y, not sloped.
    # The sloped surface is the diagonal face connecting front-bottom to back-top.
    # So the wedge has faces:
    #   bottom (z=cz-hz)
    #   back (y=cy+hy)
    #   front (y=cy-hy)
    #   right (x=cx+hx)
    #   left (x=cx-hx)
    #   sloped top connecting (front-bottom) to (back-top)
    # That's 6 faces. A triangular prism has 5 faces if the ends are triangles and sides are rectangles.
    # But our wedge has rectangular base, two triangular ends (left/right), rectangular back/front, and slanted top.
    # That's 6 faces.
    # Actually triangular prism: 2 triangle faces (left/right), 3 rectangle faces (bottom, back, top).
    # Here we want a wedge/ramp: bottom rectangle, back rectangle, front rectangle (or triangle?), left/right triangles, sloped top rectangle.
    # Hmm a ramp is a triangular prism lying on its side: the cross-section is a right triangle.
    # Cross-section in YZ plane: vertices (-hy,-hz), (+hy,-hz), (+hy,+hz). This is a right triangle.
    # Extruded along X from -hx to +hx.
    # Faces:
    #   two triangles at x=+hx and x=-hx (right/left)
    #   bottom rectangle (y from -hy to +hy, z=-hz)
    #   back vertical rectangle (y=+hy, z from -hz to +hz)
    #   sloped top rectangle connecting (-hy,-hz) to (+hy,-hz) to (+hy,+hz) to (-hy,+hz)?
    #   Wait the sloped side connects (-hy,-hz) to (+hy,+hz). The hypotenuse is the line from (-hy,-hz) to (+hy,+hz).
    #   The sloped face is a rectangle extruded along X, bounded by vertices:
    #     (+hx, -hy, -hz), (-hx, -hy, -hz), (-hx, +hy, +hz), (+hx, +hy, +hz)
    # So 5 faces total:
    #   bottom: 0,1,3,2 (actually the bottom is the rectangle at z=-hz: vertices 0,1,2,3)
    #   back: 2,3,5,4 (y=+hy)
    #   right triangle: 0,2,4 (x=+hx)
    #   left triangle: 1,3,5 (x=-hx)
    #   slope: 0,1,5,4

    planes = [
        # bottom: normal (0,0,-1), contains z=cz-hz => d=-(-(cz-hz))? n·p + d = 0 => d = -n·p = -(-(cz-hz)) = cz-hz
        (0.0, 0.0, -1.0, cz - hz),
        # back: normal (0,1,0), contains y=cy+hy => d = -(cy+hy)
        (0.0, 1.0, 0.0, -(cy + hy)),
        # front: normal (0,-1,0), contains y=cy-hy => d = -(-(cy-hy)) = cy-hy
        (0.0, -1.0, 0.0, cy - hy),
        # right: normal (1,0,0), contains x=cx+hx => d=-(cx+hx)
        (1.0, 0.0, 0.0, -(cx + hx)),
        # left: normal (-1,0,0), contains x=cx-hx => d = -(-(cx-hx)) = cx-hx
        (-1.0, 0.0, 0.0, cx - hx),
        # slope: normal computed from face 0,1,5,4
        # v0=(cx+hx, cy-hy, cz-hz), v1=(cx-hx, cy-hy, cz-hz), v5=(cx-hx, cy+hy, cz+hz)
        # v0->v1 = (-2hx,0,0), v0->v5 = (-2hx, 2hy, 2hz)
        # cross = (0 * 2hz - 0 * 2hy, 0 * (-2hx) - (-2hx)*2hz, (-2hx)*2hy - 0*(-2hx))
        #       = (0, 4*hx*hz, -4*hx*hy)
        # So normal = (0, hz, -hy) normalized. But it must point outward. For a point inside (cx,cy,cz),
        # n·inside = hz*cy - hy*cz... Wait normal should not depend on cx. Use normalized (0, hz, -hy) or (0, -hz, hy).
        # We want the ramp to be solid below the slope. The sloped face normal should point up and back-ish.
        # For a simple ramp from front-bottom to back-top, the normal points outward/up: (0, -hz, hy) or (0, hz, -hy).
        # Test with point inside: the ramp interior is below the slope line. For the line from (-hy,-hz) to (+hy,+hz),
        # the interior satisfies z < (hz/hy)*y + ... ? Let's derive slope line: z = (hz/hy)*y + (cz - ?). Actually in cross-section,
        # the line from (-hy, -hz) to (+hy, +hz) has slope m = (2hz)/(2hy) = hz/hy. Equation: z - (-hz) = (hz/hy)(y - (-hy))
        # => z + hz = (hz/hy)(y + hy) => z = (hz/hy)y + (hz/hy)hy - hz = (hz/hy)y.
        # Wait constant term: (hz/hy)*hy - hz = hz - hz = 0. So z = (hz/hy)*y.
        # The interior of the wedge is below this line and within the triangle: z <= (hz/hy)*y, and y between -hy and +hy, z >= -hz.
        # So the sloped plane in local coordinates: (hz/hy)y - z = 0, or normal proportional to (0, hz/hy, -1).
        # Normalized: (0, hz, -hy) / sqrt(hz^2 + hy^2).
        # For outward normal, we need it to point away from interior. At center (0,0,0), value = 0. Hmm center is on plane? For a wedge centered at origin, the sloped plane passes through origin.
        # Actually our wedge center is at (cx,cy,cz). The plane equation in world coords:
        #   n·(p - center) = 0 => n_x(x-cx) + n_y(y-cy) + n_z(z-cz) = 0
        # with n = (0, hz, -hy)/L.
        # => (hz/L)(y-cy) - (hy/L)(z-cz) = 0
        # => (hz/L)y - (hy/L)z + (-hz*cy + hy*cz)/L = 0
        # d = (hz*cy - hy*cz)/L
        (0.0, hz, -hy, hz*cy - hy*cz),  # not normalized yet
    ]
    # Normalize the slope plane
    L = math.sqrt(hz*hz + hy*hy)
    if L > 0:
        planes[-1] = (0.0, hz/L, -hy/L, (hz*cy - hy*cz)/L)

    faces = [
        # face 0 bottom: vertices 0,1,3,2
        {'first': 0, 'num': 4, 'indices': [0, 1, 3, 2]},
        # face 1 back: vertices 2,3,5,4
        {'first': 4, 'num': 4, 'indices': [2, 3, 5, 4]},
        # face 2 front: vertices 0,1,5,4 (sloped top face)
        {'first': 8, 'num': 4, 'indices': [0, 1, 5, 4]},
        # face 3 right triangle: 0,2,4
        {'first': 12, 'num': 3, 'indices': [0, 2, 4]},
        # face 4 left triangle: 1,3,5
        {'first': 15, 'num': 3, 'indices': [1, 3, 5]},
    ]

    # Build flat index list
    indices = []
    for f in faces:
        indices.extend(f['indices'])
        f['firstIndex'] = len(indices) - len(f['indices'])

    # faceLinks and vertexEdges are adjacency info used by Havok for edge queries.
    # For a simple convex hull, we can leave them zero or minimal. The engine may still work.
    # Each edge has (faceIndex, edgeIndex). For each face, each edge is shared with another face.
    # Let's compute a simple mapping.
    num_edges = sum(f['num'] for f in faces)
    # Create edge list: (v_from, v_to, face)
    edges = []
    edge_map = {}
    for fi, f in enumerate(faces):
        idxs = f['indices']
        n = len(idxs)
        for ei in range(n):
            v0 = idxs[ei]
            v1 = idxs[(ei+1) % n]
            key = tuple(sorted((v0, v1)))
            if key in edge_map:
                edge_map[key].append((fi, ei))
            else:
                edge_map[key] = [(fi, ei)]
            edges.append((v0, v1, fi, ei))

    # faceLinks: per face edge, the opposite (faceIndex, edgeIndex)
    faceLinks = [0] * num_edges  # uint16 faceIndex, uint8 edgeIndex, uint8 padding
    pos = 0
    for fi, f in enumerate(faces):
        n = f['num']
        for ei in range(n):
            idxs = f['indices']
            v0 = idxs[ei]
            v1 = idxs[(ei+1) % n]
            key = tuple(sorted((v0, v1)))
            others = [x for x in edge_map[key] if x[0] != fi]
            if others:
                opp_f, opp_e = others[0]
            else:
                opp_f, opp_e = fi, ei
            faceLinks[pos] = (opp_f, opp_e)
            pos += 1

    # vertexEdges: per vertex, one incident edge index
    vertexEdges = [0xFFFF] * len(verts)
    for ei, (v0, v1, fi, eidx) in enumerate(edges):
        if vertexEdges[v0] == 0xFFFF:
            vertexEdges[v0] = ei
        if vertexEdges[v1] == 0xFFFF:
            vertexEdges[v1] = ei

    return {
        'verts': verts,
        'planes': planes,
        'faces': faces,
        'indices': indices,
        'faceLinks': faceLinks,
        'vertexEdges': vertexEdges,
    }


if __name__ == '__main__':
    # Quick test output
    hull = build_convex_hull_data(0, 0, 0, 1.0, 1.0, 2.0)
    print('verts', hull['verts'])
    print('planes', hull['planes'])
    print('indices', hull['indices'])
    print('faceLinks', hull['faceLinks'])
    print('vertexEdges', hull['vertexEdges'])
