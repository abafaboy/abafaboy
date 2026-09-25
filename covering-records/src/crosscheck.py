"""Independent floating-point cross-check of certificates with Shapely/GEOS.

This does not share code with verify.py: it rebuilds the pieces with floats,
unions them with GEOS and asks whether the union contains the target. The disk
is replaced by a circumscribed 20000-gon of radius r(1 - 1e-7) (a superset of
that slightly smaller disk), and the square by a square shrunk by 1e-7, so this
check is slightly weaker than the exact one, but it is a genuinely separate
implementation.

usage: python crosscheck.py CERT.json [...]
"""
import json
import math
import sys
from fractions import Fraction

from shapely.geometry import Polygon
from shapely.ops import unary_union


def piece(kind, x, y, th):
    if kind == "sq":
        offs = [(0.5, 0.5), (-0.5, 0.5), (-0.5, -0.5), (0.5, -0.5)]
    else:
        s3 = math.sqrt(3)
        offs = [(0, 1 / s3), (-0.5, -0.5 / s3), (0.5, -0.5 / s3)]
    c, s = math.cos(th), math.sin(th)
    return Polygon([(x + u * c - v * s, y + u * s + v * c) for u, v in offs])


def check(cert):
    kind, target = cert["kind"], cert["target"]
    size = float(Fraction(cert["size"]))
    polys = []
    for p in cert["pieces"]:
        t = float(Fraction(p["t"]))
        polys.append(piece(kind, float(Fraction(p["x"])), float(Fraction(p["y"])), 2 * math.atan(t)))
    for P in polys:
        side = math.dist(*list(P.exterior.coords)[:2])
        assert abs(side - 1) < 1e-12
    U = unary_union(polys)
    if target == "square":
        h = size / 2 * (1 - 1e-7)
        T = Polygon([(-h, -h), (h, -h), (h, h), (-h, h)])
    else:
        N = 20000
        R = size * (1 - 1e-7) / math.cos(math.pi / N)
        T = Polygon([(R * math.cos(2 * math.pi * i / N), R * math.sin(2 * math.pi * i / N)) for i in range(N)])
    missing = T.difference(U).area
    ok = U.contains(T)
    print(f"{kind} x{cert['n']} -> {target} {size:.9f}: shapely contains={ok} uncovered area={missing:.2e}")
    return ok


if __name__ == "__main__":
    ok = all([check(json.load(open(p))) for p in sys.argv[1:]])
    sys.exit(0 if ok else 1)
