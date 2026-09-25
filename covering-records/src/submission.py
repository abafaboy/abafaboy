"""Prepare pictures and values in the format Erich Friedman's Packing Center asks for.

Friedman's guidelines (packing/submit.html): a picture in the same orientation,
colours, pixel size, file type and name as the one it replaces (no border or
text), and the radius or side length to 5 decimal places.

usage: python submission.py FRIEDMAN_SITE_DIR   (a checkout of erich-friedman.github.io)
Writes ../submission/<page>/<name>.gif and ../submission/<page>/values.txt
"""
import glob
import json
import math
import os
import sys
from fractions import Fraction

from PIL import Image, ImageDraw

from geom import piece_vertices

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PAGE = {("sq", "disk"): ("sqcovcir", "scc"), ("tri", "disk"): ("tricovcir", "tcc"),
        ("tri", "square"): ("tricosqu", "tcs")}
GRAY, BLACK, WHITE = (206, 206, 206), (0, 0, 0), (255, 255, 255)


def draw(cert, W, H):
    kind, target = cert["kind"], cert["target"]
    size = float(Fraction(cert["size"]))
    polys = [piece_vertices(kind, float(Fraction(p["x"])), float(Fraction(p["y"])),
                            2 * math.atan(float(Fraction(p["t"])))) for p in cert["pieces"]]
    half = size / 2 if target == "square" else size
    xs = [x for P in polys for x, _ in P] + [-half, half]
    ys = [y for P in polys for _, y in P] + [-half, half]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    sc = min((W - 3) / (x1 - x0), (H - 3) / (y1 - y0))
    ox = (W - sc * (x1 - x0)) / 2
    oy = (H - sc * (y1 - y0)) / 2

    def T(x, y):
        return (ox + (x - x0) * sc, oy + (y1 - y) * sc)

    im = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(im)
    if target == "disk":
        (cx, cy) = T(0, 0)
        R = half * sc
        d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=GRAY)
    else:
        a, b = T(-half, half), T(half, -half)
        d.rectangle([a, b], fill=GRAY)
    for P in polys:
        pts = [T(x, y) for x, y in P]
        d.line(pts + [pts[0]], fill=BLACK, width=1)
    return im.convert("P", palette=Image.ADAPTIVE, colors=3)


def main(site):
    by_page = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "certificates", "*.json"))):
        cert = json.load(open(path))
        page, prefix = PAGE[(cert["kind"], cert["target"])]
        name = f"{prefix}{cert['n']}.gif"
        orig = os.path.join(site, "packing", page, name)
        W, H = Image.open(orig).size if os.path.exists(orig) else (220, 220)
        out = os.path.join(ROOT, "submission", page)
        os.makedirs(out, exist_ok=True)
        draw(cert, W, H).save(os.path.join(out, name))
        v = Fraction(cert["size"])
        by_page.setdefault(page, []).append(f"n = {cert['n']}: {math.floor(v * 10**5) / 10**5:.5f}  "
                                            f"(certified lower bound {float(v):.9f})")
    for page, lines in by_page.items():
        open(os.path.join(ROOT, "submission", page, "values.txt"), "w").write("\n".join(lines) + "\n")
        print(page, *lines, sep="\n  ")


if __name__ == "__main__":
    main(sys.argv[1])
