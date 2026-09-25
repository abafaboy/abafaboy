"""Turn a raw optimizer result into an exact certificate for verify.py.

The raw result is a configuration X (normalised target of size 1, pieces of
side F). Every target point p has min_i gauge_i(p) <= F, so growing the pieces
to F' = F(1 + eps) about their centroids leaves slack along every seam.
Scaling by 1/F' gives unit pieces covering a target of size 1/F'; we round the
size DOWN and the centroids/rotations to 1e-18, errors far below the slack.

usage: python make_cert.py RAW.json OUT.json [eps]
"""
import json
import math
import sys
from fractions import Fraction

from geom import PIECES

D = 10 ** 18


def rat(v):
    return Fraction(round(v * D), D)


def make(raw, eps=1e-9):
    kind, target, F = raw["kind"], raw["target"], raw["F"]
    Fp = F * (1 + eps)
    size = Fraction(math.floor(1 / Fp * 10 ** 12), 10 ** 12)
    sym = PIECES[kind]["sym"]
    pieces = []
    for x, y, th in raw["X"]:
        th = math.remainder(th, sym)            # into (-sym/2, sym/2]
        pieces.append(dict(x=str(rat(x / Fp)), y=str(rat(y / Fp)), t=str(rat(math.tan(th / 2)))))
    return dict(kind=kind, target=target, n=raw["n"], size=str(size), size_decimal=float(size),
                pieces=pieces)


if __name__ == "__main__":
    raw = json.load(open(sys.argv[1]))
    eps = float(sys.argv[3]) if len(sys.argv) > 3 else 1e-9
    json.dump(make(raw, eps), open(sys.argv[2], "w"), indent=1)
