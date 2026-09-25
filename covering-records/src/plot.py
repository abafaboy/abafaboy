"""Draw a certificate as a standalone SVG.

usage: python plot.py CERT.json OUT.svg
"""
import json
import math
import sys
from fractions import Fraction

from geom import piece_vertices

COLORS = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948",
          "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac"]


def svg(cert, px=520):
    kind, target = cert["kind"], cert["target"]
    size = float(Fraction(cert["size"]))
    polys = []
    for p in cert["pieces"]:
        t = float(Fraction(p["t"]))
        th = 2 * math.atan(t)
        polys.append(piece_vertices(kind, float(Fraction(p["x"])), float(Fraction(p["y"])), th))
    xs = [x for P in polys for x, _ in P]
    ys = [y for P in polys for _, y in P]
    half = size / 2 if target == "square" else size
    lo = min(min(xs), min(ys), -half) - 0.05
    hi = max(max(xs), max(ys), half) + 0.05
    sc = px / (hi - lo)

    def T(x, y):
        return (x - lo) * sc, (hi - y) * sc

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{px}" height="{px}" viewBox="0 0 {px} {px}">',
           f'<rect width="{px}" height="{px}" fill="white"/>']
    for i, P in enumerate(polys):
        pts = " ".join(f"{a:.2f},{b:.2f}" for a, b in (T(x, y) for x, y in P))
        out.append(f'<polygon points="{pts}" fill="{COLORS[i % len(COLORS)]}" fill-opacity="0.55" '
                   f'stroke="#333" stroke-width="1"/>')
    if target == "square":
        x0, y0 = T(-half, half)
        out.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{2*half*sc:.2f}" height="{2*half*sc:.2f}" '
                   f'fill="none" stroke="black" stroke-width="2.5"/>')
    else:
        cx, cy = T(0, 0)
        out.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{half*sc:.2f}" fill="none" stroke="black" stroke-width="2.5"/>')
    label = {"square": "s", "disk": "r"}[target]
    out.append(f'<text x="8" y="{px-10}" font-family="sans-serif" font-size="15">n = {cert["n"]}, '
               f'{label} = {size:.9f}</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    open(sys.argv[2], "w").write(svg(json.load(open(sys.argv[1]))))
