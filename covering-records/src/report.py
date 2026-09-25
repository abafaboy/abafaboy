"""Build certificates, verify them exactly, draw them, and write the results table.

usage: python report.py            (reads ../results/raw/*.json)
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import make_cert  # noqa: E402
import plot  # noqa: E402
import verify  # noqa: E402
from records import FORMULA, REFINEMENTS, RECORDS, TRUNC_STEP, beats  # noqa: E402

ROOT = os.path.join(HERE, "..")
NAMES = {("tri", "square"): "Triangles covering squares (side s)",
         ("sq", "disk"): "Squares covering circles (radius r)",
         ("tri", "disk"): "Triangles covering circles (radius r)",
         ("sq", "triangle"): "Squares covering triangles (side s)",
         ("tri", "triangle"): "Triangles covering triangles (side s)",
         ("sq", "square"): "Squares covering squares (area A)"}


def trunc_str(x, digits):
    """Truncate (never round up): certified values are lower bounds."""
    import math
    return f"{math.floor(x * 10 ** digits) / 10 ** digits:.{digits}f}"


def floor_fmt(x, digits=4):
    """Round DOWN, with more digits for small gains, so gains are never overstated."""
    import math
    while digits < 8 and x < 10 ** (1 - digits):
        digits += 1
    return f"{math.floor(x * 10 ** digits) / 10 ** digits:.{digits}f}"


def disp(key, v):
    """Displayed quantity: area for squares covering squares, else side/radius."""
    return v * v if key == ("sq", "square") else v


def rec_str(key, n, digits=6):
    rec, _ = RECORDS[key][n]
    _, bar = beats(key[0], key[1], n, rec)
    step = TRUNC_STEP.get((key[0], key[1], n))
    if n in FORMULA.get(key, {}):
        return f"{FORMULA[key][n]} = {disp(key, rec):.{digits}f}", False
    if step:
        return f"{disp(key, rec):.5f}+", True
    if bar != rec:
        return f"{disp(key, rec):.3f}+", True
    return f"{disp(key, rec):.{digits}f}", False


def main():
    rows = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "results", "raw", "*.json"))):
        raw = json.load(open(path))
        key = (raw["kind"], raw["target"])
        n = raw["n"]
        better, bar = beats(raw["kind"], raw["target"], n, raw["value"])
        if not better:
            rows.setdefault(key, {})[n] = (raw["value"], None, False)
            continue
        cert = make_cert.make(raw)
        base = f"{raw['kind']}_{raw['target']}_{n:02d}"
        cpath = os.path.join(ROOT, "certificates", base + ".json")
        os.makedirs(os.path.dirname(cpath), exist_ok=True)
        json.dump(cert, open(cpath, "w"), indent=1)
        ok = verify.verify(cert)
        assert ok, cpath
        spath = os.path.join(ROOT, "figures", base + ".svg")
        os.makedirs(os.path.dirname(spath), exist_ok=True)
        open(spath, "w").write(plot.svg(cert))
        rows.setdefault(key, {})[n] = (cert["size_decimal"], base, True)

    lines = []
    refined = []
    for key, name in NAMES.items():
        if key not in rows:
            continue
        # re-optimised rows are collected for every page, even one with no new record
        if any(v[2] and (key[0], key[1], n) not in REFINEMENTS for n, v in rows[key].items()):
            lines.append(f"### {name}\n")
            lines.append("| n | previous record | holder | new value (verified) | improvement | files |")
            lines.append("|---|---|---|---|---|---|")
        for n in sorted(rows[key]):
            val, base, new = rows[key][n]
            rec, who = RECORDS[key][n]
            if not new:
                continue
            _, bar = beats(key[0], key[1], n, val)
            recs, trunc = rec_str(key, n)
            if (key[0], key[1], n) in REFINEMENTS:
                dv, db = disp(key, val), disp(key, bar)
                refined.append(f"| {name.split(' (')[0]} | {n} | {recs} | {who} | {trunc_str(dv, 9)} | "
                               f"[svg](figures/{base}.svg) · [cert](certificates/{base}.json) |")
                continue
            dv, dr, db = disp(key, val), disp(key, rec), disp(key, bar)
            gain = f"≥ +{floor_fmt(dv - db)}" if trunc else f"+{floor_fmt(dv - dr, 6)}"
            lines.append(f"| {n} | {recs} | {who} | **{trunc_str(dv, 9)}** | {gain} | "
                         f"[svg](figures/{base}.svg) · [cert](certificates/{base}.json) |")
        if lines and lines[-1] != "":
            lines.append("")
    if refined:
        lines.append("### Re-optimised versions of the current record arrangements\n")
        lines.append("Each of these beats the current value, and is verified exactly like the new records above. But "
                     "independent reviewers, matching pieces one-to-one under rotations and reflections, found each "
                     "configuration to be the same arrangement as the current record's picture with the pieces moved "
                     "slightly. The design belongs to the original finder, so these are reported as re-optimisations, "
                     "not as new configurations (see docs/ORIGINALITY.md).\n")
        lines.append("| problem | n | current record | holder | re-optimised value (verified) | files |")
        lines.append("|---|---|---|---|---|---|")
        lines.extend(refined)
        lines.append("")
    open(os.path.join(ROOT, "results", "table.md"), "w").write("\n".join(lines))
    print("\n".join(lines))
    write_all(rows)
    inject_readme("\n".join(lines), sum(1 for key, r in rows.items() for n, v in r.items()
                                        if v[2] and (key[0], key[1], n) not in REFINEMENTS))


def inject_readme(table, count):
    import re
    path = os.path.join(ROOT, "README.md")
    s = open(path).read()
    s = re.sub(r"<!-- TABLE -->.*?<!-- /TABLE -->", lambda m: "<!-- TABLE -->\n" + table + "\n<!-- /TABLE -->", s, flags=re.S)
    s = re.sub(r"<!-- COUNT -->.*?<!-- /COUNT -->", f"<!-- COUNT -->{count}<!-- /COUNT -->", s)
    open(path, "w").write(s)


def write_all(rows):
    """Every instance searched, with how the search result compares."""
    out = ["| problem | n | record on the page | best found here | status |", "|---|---|---|---|---|"]
    for key, name in NAMES.items():
        for n in sorted(rows.get(key, {})):
            val, _, new = rows[key][n]
            rec, who = RECORDS[key][n]
            _, bar = beats(key[0], key[1], n, val)
            trunc = bar != rec
            recs, _t = rec_str(key, n, 7)
            if new and (key[0], key[1], n) in REFINEMENTS:
                status = "re-optimised version of the current record's arrangement (verified)"
            elif new:
                status = "**new record** (exactly verified)"
            elif (trunc and rec <= val < bar) or (not trunc and abs(val - rec) < 1e-7):
                status = "consistent with record (page gives a truncated decimal)" if trunc else "matches record"
            elif val < rec:
                status = f"below record by {disp(key, rec) - disp(key, val):.4f}"
            else:
                status = "above printed value, not by a certain margin"
            out.append(f"| {name.split(' (')[0]} | {n} | {recs} | {trunc_str(disp(key, val), 7)} | {status} |")
    open(os.path.join(ROOT, "results", "all.md"), "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
