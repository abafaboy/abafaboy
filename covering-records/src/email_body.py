"""Write the plain-text submission email for Erich Friedman from the certificates.

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
from records import FORMULA, RECORDS, TRUNC_STEP, TRUNCATED  # noqa: E402

ROOT = os.path.join(HERE, "..")
PAGES = [(("sq", "disk"), "Squares Covering Circles", "sqcovcir", "scc", "r"),
         (("tri", "disk"), "Triangles Covering Circles", "tricovcir", "tcc", "r"),
         (("tri", "square"), "Triangles Covering Squares", "tricosqu", "tcs", "s"),
         (("sq", "triangle"), "Squares Covering Triangles", "squcotri", "sct", "s"),
         (("tri", "triangle"), "Triangles Covering Triangles", "tricovtri", "tct", "s"),
         (("sq", "square"), "Squares Covering Squares", "squcosqu", "scs", "A")]
REPO = "https://github.com/abafaboy/abafaboy/tree/claude/new-session-nd3rcp/covering-records"
ZIP = "https://github.com/abafaboy/abafaboy/raw/claude/new-session-nd3rcp/covering-records/submission/submission.zip"


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


def main():
    certs = {}
    for p in glob.glob(os.path.join(ROOT, "certificates", "*.json")):
        c = json.load(open(p))
        certs.setdefault((c["kind"], c["target"]), []).append(c)
    total = sum(len(v) for v in certs.values())
    npages = len(certs)
    out = []
    out.append("Hi Erich,")
    out.append("")
    out.append(f"I would like to submit {total} improved configurations for {npages} of the covering pages. "
               "One picture is included for each, with the same file name, size and colours as the picture "
               "it replaces. They are in the attached submission.zip, one folder per page (the same zip is "
               f"also at {ZIP} ). Values are truncated (not rounded) to 5 decimal places.")
    for key, title, page, prefix, sym in PAGES:
        if key not in certs:
            continue
        out.append("")
        out.append(f"{title} ({prefix}N.gif)")
        for c in sorted(certs[key], key=lambda c: c["n"]):
            v = Fraction(c["size"])
            if key == ("sq", "square"):
                v = v * v
            out.append(f"  n = {c['n']}: {sym} = {trunc5(float(v))}   [previous: {old_str(key, c['n'])}]")
    out.append("")
    out.append("How they were found: a computer search. Each configuration is scored by the largest factor "
               "by which the pieces must grow (about their own centres) to cover the target. That score is "
               "minimised with random starts, a smoothed gradient phase, an exact minimax polish (SLSQP) and "
               "basin hopping. The same search re-finds the existing records on these pages; the "
               "improvements above are the cases where it went further.")
    out.append("")
    out.append("How they were checked: every value is a certified lower bound. Each configuration is stored "
               "with rational centres and rational rotations, so the squares are exactly unit squares and the "
               "triangles exactly unit triangles, with coordinates in Q(sqrt 3). An exact-arithmetic program "
               "then proves that the target of the stated size is completely covered. A separate floating-point "
               "check with Shapely agrees. Enlarging any target by one part in a million makes both checks "
               "fail.")
    out.append("")
    out.append(f"Code, exact coordinates and certificates: {REPO}")
    out.append("")
    out.append("Name for attribution: Abdulfayyod Mukhamedov (found with Claude Code)")
    out.append("")
    out.append("Best regards,")
    out.append("Abdulfayyod Mukhamedov")
    print("\n".join(out))


if __name__ == "__main__":
    main()
