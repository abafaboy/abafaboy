"""Write the plain-text submission email for Erich Friedman from the certificates.

Part 1 lists configurations judged to be new arrangements; part 2 lists
re-optimised versions of the current record arrangements, labelled as such.

usage: python email_body.py > ../submission/email.txt
"""
import glob
import json
import math
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from records import FORMULA, NOT_SUBMITTED, REOPTIMISED, RECORDS, TRUNC_STEP, TRUNCATED  # noqa: E402

ROOT = os.path.join(HERE, "..")
PAGES = [(("sq", "disk"), "Squares Covering Circles", "sqcovcir", "scc", "r"),
         (("tri", "disk"), "Triangles Covering Circles", "tricovcir", "tcc", "r"),
         (("tri", "square"), "Triangles Covering Squares", "tricosqu", "tcs", "s"),
         (("sq", "triangle"), "Squares Covering Triangles", "squcotri", "sct", "s"),
         (("tri", "triangle"), "Triangles Covering Triangles", "tricovtri", "tct", "s"),
         (("sq", "square"), "Squares Covering Squares", "squcosqu", "scs", "A")]
REPO = "https://github.com/abafaboy/abafaboy/tree/claude/new-session-nd3rcp/covering-records"


def trunc5(v):
    return f"{math.floor(v * 10 ** 5) / 10 ** 5:.5f}"


def old_str(key, n):
    rec, who = RECORDS[key][n]
    if key == ("sq", "square"):
        rec = rec * rec
    if n in FORMULA.get(key, {}):
        val = f"{FORMULA[key][n]} = {trunc5(rec)}+"
    elif (key[0], key[1], n) in TRUNC_STEP:
        val = f"{rec:.5f}+"
    elif n in TRUNCATED.get(key, ()):
        val = f"{rec:.3f}+"
    else:
        val = f"{trunc5(rec)}+"
    return f"{val}, {who}"


def section(certs, want_reopt):
    out = []
    for key, title, page, prefix, sym in PAGES:
        rows = [c for c in certs.get(key, []) if ((key[0], key[1], c["n"]) in REOPTIMISED) == want_reopt]
        if not rows:
            continue
        out.append("")
        out.append(f"{title} (folder {page}, pictures {prefix}N.gif)")
        for c in sorted(rows, key=lambda c: c["n"]):
            v = Fraction(c["size"])
            if key == ("sq", "square"):
                v = v * v
            out.append(f"  n = {c['n']}: {sym} = {trunc5(float(v))}   [current: {old_str(key, c['n'])}]")
    return out


def main():
    certs = {}
    for p in glob.glob(os.path.join(ROOT, "certificates", "*.json")):
        c = json.load(open(p))
        if (c["kind"], c["target"], c["n"]) in NOT_SUBMITTED:
            continue
        certs.setdefault((c["kind"], c["target"]), []).append(c)
    n_new = sum(1 for k, v in certs.items() for c in v if (k[0], k[1], c["n"]) not in REOPTIMISED)
    n_re = sum(1 for k, v in certs.items() for c in v if (k[0], k[1], c["n"]) in REOPTIMISED)
    out = ["Hi Erich,", ""]
    out.append(f"I would like to submit improved coverings for {len(certs)} of the covering pages: {n_new} new "
               f"configurations, and {n_re} better-optimised versions of configurations already on the pages. "
               "Pictures are attached as one zip per page, each holding a folder named after the page; every "
               "picture has the same file name, size and colours as the one it replaces. Values are truncated "
               "(not rounded) to 5 decimal places.")
    out.append("")
    out.append("PART 1. New configurations. Each is a different arrangement from the current picture, not a "
               "re-optimised copy of it.")
    out += section(certs, False)
    out.append("")
    out.append("PART 2. Better-optimised versions of the current configurations. I compared each one piece by "
               "piece with the current picture, allowing rotations and reflections of the whole figure. Each is "
               "the SAME arrangement with the pieces moved slightly, so the design belongs to the original "
               "finder, and I am not claiming these as new configurations. They do cover a larger target, so you "
               "may want the improved values. Please credit them however you think is fair.")
    out += section(certs, True)
    out.append("")
    out.append("How they were found: a computer search that I ran with Claude Code (an AI coding assistant), which "
               "wrote and ran the optimisation code. Each configuration is scored by the largest factor by which "
               "the pieces must grow (about their own centres) to cover the target, and that score is minimised "
               "with random starts, a smoothed gradient phase, an exact minimax polish and basin hopping. The same "
               "search re-finds most of the existing records on these pages.")
    out.append("")
    out.append("How they were checked: every value is a certified lower bound. Each configuration is stored with "
               "rational centres and rational rotations, so the squares are exactly unit squares and the "
               "triangles exactly unit triangles. An exact-arithmetic program (rationals and sqrt 3, no floating "
               "point) proves that the target of the stated size is completely covered. A second, independently "
               "written exact checker and a floating-point check with Shapely agree. Enlarging any target by one "
               "part in a million makes the checks fail.")
    out.append("")
    out.append(f"Exact coordinates, certificates and code: {REPO}")
    out.append("")
    out.append("Name for attribution (for part 1): Abdulfayyod Mukhamedov")
    out.append("")
    out.append("Best regards,")
    out.append("Abdulfayyod Mukhamedov")
    print("\n".join(out))


if __name__ == "__main__":
    main()
