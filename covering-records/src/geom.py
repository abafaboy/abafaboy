"""Piece and target geometry shared by the optimizer and the plots.

Pieces are regular polygons of side 1 (equilateral triangle or square),
described by their centroid (x, y) and rotation angle t. A piece is the set
    { c + R(t) v : n_e . v <= h  for every edge e }
where n_e are the outward unit normals of the unrotated piece and h is its
inradius. Its gauge (Minkowski functional about the centroid) is
    g(p) = max_e  (R(t) n_e) . (p - c) / h,
so a point p lies in the piece scaled by lam about its centroid iff g(p) <= lam.
"""
import math

SQRT3 = math.sqrt(3.0)

PIECES = {
    # normal angles (radians), inradius, vertex angles, circumradius
    "tri": dict(normals=[-math.pi / 2, math.pi / 6, 5 * math.pi / 6],
                h=1 / (2 * SQRT3),
                verts=[math.pi / 2, 7 * math.pi / 6, 11 * math.pi / 6],
                R=1 / SQRT3,
                sym=2 * math.pi / 3),
    "sq": dict(normals=[0.0, math.pi / 2, math.pi, 3 * math.pi / 2],
               h=0.5,
               verts=[math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4],
               R=1 / math.sqrt(2),
               sym=math.pi / 2),
}

# Targets are normalised to size 1: the square [-1/2, 1/2]^2 (side 1) or the
# unit disk (radius 1). A configuration needing piece scale lam therefore
# certifies a target of size 1/lam covered by unit pieces.
TARGETS = ("square", "disk")


def piece_vertices(kind, x, y, t, scale=1.0):
    P = PIECES[kind]
    return [(x + scale * P["R"] * math.cos(a + t), y + scale * P["R"] * math.sin(a + t))
            for a in P["verts"]]
