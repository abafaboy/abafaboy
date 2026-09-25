"""Exact verification that n unit pieces cover a target.

A certificate (JSON) lists the target size as an exact rational and each piece
as an exact rational centroid (x, y) plus a rational rotation parameter t,
meaning the rotation with cos = (1 - t^2)/(1 + t^2), sin = 2t/(1 + t^2). The
verifier builds every piece itself from these numbers, so each piece is exactly
a unit square or an exactly unit equilateral triangle: square vertices are
rational, triangle vertices lie in Q(sqrt 3), and all arithmetic below is exact
in the field Q(sqrt 3). No floating point is used anywhere in the decision.

Method (vertical decomposition of the segment arrangement):
  * collect every piece edge (plus the square target's sides, or a bounding
    box for a disk target);
  * the x-coordinates of all endpoints and of all pairwise intersections cut
    the plane into vertical slabs; inside an open slab no two segments cross
    and no segment starts or ends, so consecutive segments bound open
    trapezoidal cells that no piece boundary passes through;
  * each such cell therefore lies entirely inside or entirely outside every
    (closed) piece, so testing one interior point decides it;
  * every cell that meets the target must contain a covered test point.
Because the union of finitely many closed pieces is closed and the open cells
are dense in the target, covering every cell covers the whole target.

usage: python verify.py CERT.json [CERT.json ...]
"""
import json
import sys
from fractions import Fraction as Q

try:  # gmpy2 is much faster if present; results are identical
    from gmpy2 import mpq as _mpq

    def Q(a, b=None):  # noqa: F811
        if isinstance(a, str):
            return _mpq(a)
        return _mpq(a) if b is None else _mpq(a, b)
except ImportError:  # pragma: no cover
    pass


class K:
    """Element a + b*sqrt(3) of Q(sqrt 3), a and b rational."""

    __slots__ = ("a", "b")

    def __init__(self, a, b=0):
        self.a = Q(a) if not isinstance(a, type(Q(0))) else a
        self.b = Q(b) if not isinstance(b, type(Q(0))) else b

    def __add__(s, o):
        o = _k(o); return K(s.a + o.a, s.b + o.b)
    __radd__ = __add__

    def __sub__(s, o):
        o = _k(o); return K(s.a - o.a, s.b - o.b)

    def __rsub__(s, o):
        return _k(o) - s

    def __neg__(s):
        return K(-s.a, -s.b)

    def __mul__(s, o):
        o = _k(o); return K(s.a * o.a + 3 * s.b * o.b, s.a * o.b + s.b * o.a)
    __rmul__ = __mul__

    def inv(s):
        d = s.a * s.a - 3 * s.b * s.b
        if d == 0:
            raise ZeroDivisionError
        return K(s.a / d, -s.b / d)

    def __truediv__(s, o):
        return s * _k(o).inv()

    def __rtruediv__(s, o):
        return _k(o) * s.inv()

    def sign(s):
        a, b = s.a, s.b
        sa = (a > 0) - (a < 0)
        sb = (b > 0) - (b < 0)
        if sa == 0:
            return sb
        if sb == 0 or sa == sb:
            return sa
        # opposite signs: compare a^2 with 3 b^2
        return sa if a * a > 3 * b * b else (sb if a * a < 3 * b * b else 0)

    def __lt__(s, o): return (s - o).sign() < 0
    def __le__(s, o): return (s - o).sign() <= 0
    def __gt__(s, o): return (s - o).sign() > 0
    def __ge__(s, o): return (s - o).sign() >= 0
    def __eq__(s, o): return (s - o).sign() == 0
    def __hash__(s): return hash((s.a, s.b))

    def __float__(s):
        return float(s.a) + float(s.b) * 3 ** 0.5

    def __repr__(s):
        return f"({s.a} + {s.b}*sqrt3)"


def _k(x):
    return x if isinstance(x, K) else K(x)


SQRT3 = K(0, 1)


def piece_vertices(kind, x, y, t):
    """Exact vertices (counter-clockwise) of the unit piece."""
    c = (1 - t * t) / (1 + t * t)
    s = 2 * t / (1 + t * t)
    if kind == "sq":
        h = Q(1, 2)
        offs = [(h, h), (-h, h), (-h, -h), (h, -h)]
        offs = [(K(u), K(v)) for u, v in offs]
    elif kind == "tri":
        # centroid at origin, side 1: top vertex (0, 1/sqrt3), others below
        offs = [(K(0), K(0, Q(1, 3))), (K(Q(-1, 2)), K(0, Q(-1, 6))), (K(Q(1, 2)), K(0, Q(-1, 6)))]
    else:
        raise ValueError(kind)
    return [(K(x) + u * c - v * s, K(y) + u * s + v * c) for u, v in offs]


def side_lengths_sq(verts):
    out = []
    for i in range(len(verts)):
        (x0, y0), (x1, y1) = verts[i], verts[(i + 1) % len(verts)]
        out.append((x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0))
    return out


def inside(verts, px, py):
    """Point in closed convex CCW polygon (exact)."""
    for i in range(len(verts)):
        (x0, y0), (x1, y1) = verts[i], verts[(i + 1) % len(verts)]
        if ((x1 - x0) * (py - y0) - (y1 - y0) * (px - x0)).sign() < 0:
            return False
    return True


def dist2_point_segment(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    L = dx * dx + dy * dy
    if L.sign() == 0:
        return wx * wx + wy * wy
    t = wx * dx + wy * dy
    if t.sign() <= 0:
        return wx * wx + wy * wy
    if (t - L).sign() >= 0:
        ux, uy = px - bx, py - by
        return ux * ux + uy * uy
    return wx * wx + wy * wy - t * t / L


def verify(cert, log=print):
    kind, target = cert["kind"], cert["target"]
    size = Q(cert["size"])
    pieces = []
    for p in cert["pieces"]:
        v = piece_vertices(kind, Q(p["x"]), Q(p["y"]), Q(p["t"]))
        for d2 in side_lengths_sq(v):
            assert d2 == K(1), "piece is not unit"
        pieces.append(v)
    n = len(pieces)
    assert n == cert["n"], "piece count mismatch"

    # target description
    if target == "square":
        h = K(size / 2)
        box = [(-h, -h), (h, -h), (h, h), (-h, h)]
        xlo, xhi = -h, h
    elif target == "triangle":
        # equilateral triangle of side `size`, centroid at the origin, apex up
        s_ = K(size)
        box = [(K(0), s_ * K(0, Q(1, 3))), (-s_ / 2, -s_ * K(0, Q(1, 6))), (s_ / 2, -s_ * K(0, Q(1, 6)))]
        xlo, xhi = -s_ / 2, s_ / 2
    elif target == "disk":
        r = K(size)
        r2 = r * r
        box = [(-r, -r), (r, -r), (r, r), (-r, r)]
        xlo, xhi = -r, r
    else:
        raise ValueError(target)

    segs = []
    for v in pieces + [box]:
        for i in range(len(v)):
            segs.append((v[i], v[(i + 1) % len(v)]))

    # critical x values
    xs = set()
    for (a, b) in segs:
        xs.add(a[0]); xs.add(b[0])
    for i in range(len(segs)):
        (ax, ay), (bx, by) = segs[i]
        for j in range(i + 1, len(segs)):
            (cx, cy), (dx, dy) = segs[j]
            den = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx)
            if den.sign() == 0:
                continue
            t = ((cx - ax) * (dy - cy) - (cy - ay) * (dx - cx)) / den
            u = ((cx - ax) * (by - ay) - (cy - ay) * (bx - ax)) / den
            if t.sign() >= 0 and (t - 1).sign() <= 0 and u.sign() >= 0 and (u - 1).sign() <= 0:
                xs.add(ax + t * (bx - ax))
    xs = _exact_sort([x for x in xs if xlo <= x <= xhi])

    cells = 0
    for x0, x1 in zip(xs, xs[1:]):
        if not (x0 < x1):
            continue
        xm = (x0 + x1) / 2
        ys = []
        for (a, b) in segs:
            (ax, ay), (bx, by) = a, b
            if ax == bx:
                continue
            lo, hi = (a, b) if ax < bx else (b, a)
            if lo[0] <= x0 and hi[0] >= x1:
                slope = (hi[1] - lo[1]) / (hi[0] - lo[0])
                ys.append((lo[1] + slope * (xm - lo[0]), lo, hi, slope))
        ys = _exact_sort_by(ys, key=lambda z: z[0])
        for (y0, l0, h0, s0), (y1, l1, h1, s1) in zip(ys, ys[1:]):
            if not (y0 < y1):
                continue
            px, py = xm, (y0 + y1) / 2
            if target == "square":
                if not (-h < py < h):
                    continue
            elif target == "triangle":
                # cell lies inside or outside the target (its sides are segments)
                if not inside(box, px, py):
                    continue
            else:
                # does this cell meet the open disk? cell corners at x0, x1
                c = [(x0, l0[1] + s0 * (x0 - l0[0])), (x1, l0[1] + s0 * (x1 - l0[0])),
                     (x1, l1[1] + s1 * (x1 - l1[0])), (x0, l1[1] + s1 * (x0 - l1[0]))]
                if inside_cell(c):
                    d2 = K(0)
                else:
                    d2 = _exact_min([dist2_point_segment(K(0), K(0), *c[i], *c[(i + 1) % 4]) for i in range(4)])
                if not (d2 < r2):
                    continue
            cells += 1
            if not any(inside(v, px, py) for v in pieces):
                log(f"UNCOVERED cell near ({float(px):.9f}, {float(py):.9f})")
                return False
    log(f"{kind} x{n} covers {target} of size {float(size):.12f}: OK ({len(segs)} segments, {len(xs)} slabs, {cells} cells checked exactly)")
    return True


def inside_cell(c):
    """Origin inside the closed convex quadrilateral c (CCW: bottom-left, bottom-right, top-right, top-left)."""
    for i in range(4):
        (x0, y0), (x1, y1) = c[i], c[(i + 1) % 4]
        if ((x1 - x0) * (0 - y0) - (y1 - y0) * (0 - x0)).sign() < 0:
            return False
    return True


def _exact_sort(v):
    import functools
    return sorted(v, key=functools.cmp_to_key(lambda p, q: (p - q).sign()))


def _exact_sort_by(v, key):
    import functools
    return sorted(v, key=functools.cmp_to_key(lambda p, q: (key(p) - key(q)).sign()))


def _exact_min(v):
    m = v[0]
    for z in v[1:]:
        if z < m:
            m = z
    return m


if __name__ == "__main__":
    ok = True
    for path in sys.argv[1:]:
        ok &= verify(json.load(open(path)))
    sys.exit(0 if ok else 1)
