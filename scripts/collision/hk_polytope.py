"""
Polytope helpers: construct full hknpConvexHull half-edge connectivity from
just (vertices, faces).

Inputs:
  vertices : list of (x, y, z) tuples
  faces    : list of vertex-index lists, in CCW order viewed from outside
Outputs (the dict shape consumed by hk_encode):
  vertices, planes, faces, indices, face_links, vertex_edges
"""
import math, struct

def _vec_sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def _vec_cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def _vec_dot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def _vec_len(a): return math.sqrt(_vec_dot(a, a))
def _vec_norm(a):
    L = _vec_len(a)
    if L == 0: return (0.0, 0.0, 0.0)
    return (a[0]/L, a[1]/L, a[2]/L)

def build_polytope(vertices, faces_v):
    """Convert (vertices, faces_v) -> full polytope dict ready for hk_encode.

    `faces_v` is a list of vertex-index lists (CCW from outside). All faces
    must reference the same vertex set.
    """
    n_verts = len(vertices)

    # --- 1. Flat indices array + face descriptors
    indices = []
    faces = []
    for fv in faces_v:
        if len(fv) < 3:
            raise ValueError("face needs >= 3 vertices")
        faces.append({"firstIndex": len(indices), "numIndices": len(fv), "minHalfAngle": 0})
        indices.extend(fv)

    n_he = len(indices)            # number of half-edges
    n_faces = len(faces)

    # --- 2. Plane equations from face vertices (CCW normal pointing outward)
    planes = []
    for fi, fv in enumerate(faces_v):
        v0 = vertices[fv[0]]
        v1 = vertices[fv[1]]
        v2 = vertices[fv[2]]
        n = _vec_norm(_vec_cross(_vec_sub(v1, v0), _vec_sub(v2, v0)))
        d = -_vec_dot(n, v0)
        planes.append((n[0], n[1], n[2], d))

    # --- 3. Half-edge twin map.
    # Each half-edge is identified by its position in `indices`.
    # The half-edge at position p represents v_from -> v_to where:
    #   v_from = indices[p]
    #   v_to   = indices[p + 1 within face]
    #
    # The "twin" of (v_from, v_to) is the half-edge (v_to, v_from) in the
    # adjacent face that shares this edge.
    he_at = {}  # (v_from, v_to) -> half_edge_index_in_indices
    he_face_pos = []  # for each half-edge: (face_idx, position_within_face)

    for face_idx, f in enumerate(faces):
        nv = f["numIndices"]
        first = f["firstIndex"]
        for k in range(nv):
            v_from = indices[first + k]
            v_to   = indices[first + (k + 1) % nv]
            if (v_from, v_to) in he_at:
                raise ValueError(f"duplicate directed edge {v_from}->{v_to} -- input not a manifold polytope")
            he_at[(v_from, v_to)] = first + k
            he_face_pos.append((face_idx, k))

    face_links = [None] * n_he
    for face_idx, f in enumerate(faces):
        nv = f["numIndices"]
        first = f["firstIndex"]
        for k in range(nv):
            v_from = indices[first + k]
            v_to   = indices[first + (k + 1) % nv]
            twin_he = he_at.get((v_to, v_from))
            if twin_he is None:
                raise ValueError(f"open edge {v_from}->{v_to} has no twin -- input has a boundary, not a closed polytope")
            twin_face_idx, twin_pos_in_face = he_face_pos[twin_he]
            face_links[first + k] = {
                "faceIndex": twin_face_idx,
                "edgeIndex": twin_pos_in_face,
                "padding": 1,    # the original file uses 1 for padding here
            }

    # --- 4. vertex_edges: for each vertex, one half-edge that starts at it.
    # Take the FIRST occurrence as we walk faces in order.
    vertex_edges = [None] * n_verts
    for face_idx, f in enumerate(faces):
        nv = f["numIndices"]
        first = f["firstIndex"]
        for k in range(nv):
            v = indices[first + k]
            if vertex_edges[v] is None:
                vertex_edges[v] = {
                    "faceIndex": face_idx,
                    "edgeIndex": k,
                    "padding": 1,
                }
    for v_i, ve in enumerate(vertex_edges):
        if ve is None:
            raise ValueError(f"vertex {v_i} not used by any face")

    return {
        "vertices": list(vertices),
        "planes": planes,
        "faces": faces,
        "indices": indices,
        "face_links": face_links,
        "vertex_edges": vertex_edges,
    }


# ----------------------------------------------------------------------------
# Built-in test polytope: a unit-ish tetrahedron at origin.

TETRAHEDRON_VERTICES = [
    ( 1.0,  1.0,  1.0),
    ( 1.0, -1.0, -1.0),
    (-1.0,  1.0, -1.0),
    (-1.0, -1.0,  1.0),
]
# Faces in CCW order viewed from outside.
TETRAHEDRON_FACES = [
    [0, 1, 2],   # face opposite v3
    [0, 3, 1],   # face opposite v2
    [0, 2, 3],   # face opposite v1
    [1, 3, 2],   # face opposite v0
]

if __name__ == "__main__":
    p = build_polytope(TETRAHEDRON_VERTICES, TETRAHEDRON_FACES)
    print("Tetrahedron polytope:")
    print(f"  vertices    : {len(p['vertices'])}")
    print(f"  planes      : {len(p['planes'])}")
    print(f"  faces       : {len(p['faces'])}")
    print(f"  indices     : {len(p['indices'])}")
    print(f"  face_links  : {len(p['face_links'])}")
    print(f"  vertex_edges: {len(p['vertex_edges'])}")
    print(f"  planes:")
    for pl in p["planes"]:
        print(f"    ({pl[0]:+.4f}, {pl[1]:+.4f}, {pl[2]:+.4f}, {pl[3]:+.4f})")
    print(f"  face_links: {p['face_links']}")
    print(f"  vertex_edges: {p['vertex_edges']}")
