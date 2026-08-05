"""
M4: OBJ loader + convex hull.

Loads vertices from a .obj file and builds a convex polytope (using scipy's
ConvexHull / qhull). The result feeds directly into hk_polytope.build_polytope.

Note: Only vertices are read from the OBJ (face data is ignored — we always
take the convex hull). This means the input mesh can be non-convex; the tool
will silently use its hull.
"""
import sys
import numpy as np
from scipy.spatial import ConvexHull


def load_obj_vertices(path):
    """Read vertex coordinates from an OBJ file. Returns Nx3 numpy array."""
    verts = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if parts[0] == "v":
                # OBJ vertex line: v x y z [w]
                if len(parts) < 4:
                    raise ValueError(f"malformed vertex line: {line!r}")
                verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
    if len(verts) < 4:
        raise ValueError(f"need at least 4 non-coplanar vertices, got {len(verts)}")
    return np.array(verts, dtype=np.float64)


def hull_to_polytope_inputs(points):
    """Run convex hull and produce (vertices, faces) for hk_polytope.build_polytope.

    scipy returns triangular faces. We keep them as triangles (no coplanar
    merging) — Havok handles arbitrary convex polytopes, and triangulation just
    means a few extra (parallel) planes which are still correct.

    Faces returned in CCW order from outside. scipy doesn't guarantee winding,
    so we orient each triangle outward by checking the signed volume against
    the hull centroid.
    """
    hull = ConvexHull(points)

    # hull.vertices = indices into `points` of the hull's vertices.
    # hull.simplices = (n_facets x 3) array of point-indices into `points`.
    # We reindex into a smaller hull-only vertex array.
    used_idx = sorted(set(hull.vertices.tolist()))
    remap = {old: new for new, old in enumerate(used_idx)}
    hull_verts = points[used_idx]

    # Centroid for orientation check
    centroid = hull_verts.mean(axis=0)

    faces = []
    for tri in hull.simplices:
        a, b, c = remap[tri[0]], remap[tri[1]], remap[tri[2]]
        v0, v1, v2 = hull_verts[a], hull_verts[b], hull_verts[c]
        n = np.cross(v1 - v0, v2 - v0)
        # If normal points toward centroid (away from outside), flip.
        if np.dot(n, v0 - centroid) < 0:
            faces.append([a, c, b])
        else:
            faces.append([a, b, c])

    verts_list = [tuple(map(float, v)) for v in hull_verts]
    return verts_list, faces


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: hk_obj.py <mesh.obj>")
        sys.exit(2)
    pts = load_obj_vertices(sys.argv[1])
    print(f"loaded {len(pts)} vertices from {sys.argv[1]}")
    verts, faces = hull_to_polytope_inputs(pts)
    print(f"convex hull: {len(verts)} vertices, {len(faces)} triangular faces")
    bbox_min = np.min(verts, axis=0); bbox_max = np.max(verts, axis=0)
    print(f"bounding box: min={bbox_min} max={bbox_max} extent={bbox_max-bbox_min}")
