"""Best known values from Erich Friedman's Packing Center (as of 25 Sep 2026).

Source pages (git: github.com/erich-friedman/erich-friedman.github.io):
  packing/tricosqu/  Triangles Covering Squares  -> side s of the square
  packing/sqcovcir/  Squares Covering Circles    -> radius r of the circle
  packing/tricovcir/ Triangles Covering Circles  -> radius r of the circle
Pieces are unit equilateral triangles / unit squares. Values given on the page
only to three decimals ("1.028+") are stored as that truncated lower value.
"""
from math import sqrt

s3 = sqrt(3)

RECORDS = {
    ("tri", "square"): {
        1: (2 * s3 - 3, "Trivial"),
        2: (s3 - 1, "David Cantrell, Aug 2002"),
        3: (4 * s3 - 6, "David Cantrell, Aug 2002"),
        4: ((3 * s3 - 3) / 2, "Erich Friedman, Aug 2002"),
        5: ((15 * s3 - 21) / 4, "David Cantrell, Jul 2005"),
        6: ((107 * s3 - 85) / 71, "Maurizio Morandi, Apr 2009"),
        7: ((7 * s3 - 6) / 4, "Maurizio Morandi, Apr 2009"),
        8: ((12 - 5 * s3) / 2, "Maurizio Morandi, Apr 2009"),
        9: ((139 - 69 * s3) / 11, "Maurizio Morandi, Apr 2009"),
        10: (5 / s3 - 1, "Maurizio Morandi, Apr 2009"),
        11: (s3 + 0.25, "Maurizio Morandi, Apr 2009"),
        12: ((7 * s3 + 15) / 13, "Maurizio Morandi, Apr 2009"),
    },
    ("sq", "disk"): {
        1: (0.5, "Trivial"),
        2: (2 - sqrt(2), "Proved by Trevor Green, Aug 1999"),
        3: (0.794, "Proved by Trevor Green, Aug 1999"),
        4: (1.0, "Proved by Trevor Green, Aug 1999"),
        5: (1.028, "Maurizio Morandi, Apr 2009"),
        6: (1.126, "Erich Friedman, Aug 1999"),
        7: (1.239, "David Cantrell, Jul 2002"),
        8: (1.375, "Maurizio Morandi, Mar 2009"),
        9: (1.5, "Trivial"),
        10: (1.546, "Trevor Green, Aug 1999"),
        11: (1.608, "Maurizio Morandi, Mar 2009"),
        12: (1.701, "David Cantrell, Aug 2002"),
        13: (1.779, "Maurizio Morandi, Apr 2009"),
        14: (1.883, "David Cantrell, Jul 2002"),
        15: (1.991, "Maurizio Morandi, Apr 2009"),
        16: (2.007, "Maurizio Morandi, May 2009"),
        17: (2.042, "Maurizio Morandi, Jun 2009"),
        18: (2.116, "Maurizio Morandi, Jun 2009"),
    },
    ("tri", "disk"): {
        1: (s3 / 6, "Trivial"),
        2: (s3 / 4, "Erich Friedman, 1997"),
        3: ((38 * s3 - 9) / 109, "Maurizio Morandi, Jun 2009"),
        4: ((9 * s3 - 2 * sqrt(22)) / 10, "Trevor Green, Jul 1999"),
        5: ((79 * s3 - 3 * sqrt(79)) / 152, "Maurizio Morandi, Jun 2009"),
        6: (s3 / 2, "Trivial"),
        7: (0.892, "Maurizio Morandi, Jul 2009"),
        8: ((453 * s3 - 3 * sqrt(347)) / 752, "Maurizio Morandi, Jun 2009"),
        9: ((81 * s3 - 6 * sqrt(30)) / 106, "David Cantrell, Jul 2005"),
        10: ((31 * s3 - sqrt(103)) / 40, "David Cantrell, Jul 2005"),
        11: ((177 * s3 - 2 * sqrt(586)) / 226, "David Cantrell, Jul 2005"),
        12: ((7 * s3 - sqrt(7)) / 8, "David Cantrell, Jul 2005"),
        13: ((40 * s3 - sqrt(165)) / 45, "Maurizio Morandi, Aug 2009"),
        14: (1.290, "Maurizio Morandi, Aug 2009"),
        15: (1.343, "Maurizio Morandi, Aug 2009"),
        16: (1.392, "Maurizio Morandi, Aug 2009"),
        17: (1.434, "Maurizio Morandi, Aug 2009"),
        18: (1.475, "Maurizio Morandi, Aug 2009"),
    },
}

# Records the page gives only as a truncated decimal ("1.028+"): the true value
# lies in [v, v + 0.001), so a new value must reach v + 0.001 to be a sure gain.
TRUNCATED = {("sq", "disk"): {3, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18},
             ("tri", "disk"): {7, 14, 15, 16, 17, 18}}


def beats(kind, target, n, value):
    """True if `value` (side or radius) certainly beats the page's record."""
    rec = RECORDS[(kind, target)][n][0]
    step = TRUNC_STEP.get((kind, target, n), 0.001 if n in TRUNCATED.get((kind, target), ()) else 0.0)
    if (kind, target) == ("sq", "square"):
        bar = sqrt(rec * rec + step)        # truncation is in the printed AREA
    else:
        bar = rec + step
    return value > bar + 1e-12, bar


# Page values for the closed forms above, as printed, to catch transcription slips.
PRINTED = {
    ("tri", "square"): {1: .464, 2: .732, 3: .928, 4: 1.098, 5: 1.245, 6: 1.413, 7: 1.531,
                        8: 1.669, 9: 1.771, 10: 1.886, 11: 1.982, 12: 2.086},
    ("tri", "disk"): {1: .288, 2: .433, 3: .521, 4: .620, 5: .724, 6: .866, 8: .969,
                      9: 1.013, 10: 1.088, 11: 1.142, 12: 1.184, 13: 1.254},
}

if __name__ == "__main__":
    for key, tab in PRINTED.items():
        for n, v in tab.items():
            exact = RECORDS[key][n][0]
            assert v <= exact < v + 0.001 + 1e-12, (key, n, v, exact)
    print("closed forms match the printed truncations")


# ---------------------------------------------------------------------------
# Pages added later (same source, same date).
#   packing/squcotri/  Squares Covering Triangles  -> side s of the triangle
#   packing/tricovtri/ Triangles Covering Triangles -> side s of the triangle
#   packing/squcosqu/  Squares Covering Squares     -> AREA A of the square
# For squares covering squares we store the side sqrt(A); report.py shows A.
from math import floor

RECORDS[("sq", "triangle")] = {
    1: (sqrt(6) - sqrt(2), "Trivial"),
    2: (1.322, "Maurizio Morandi, Mar 2009"),
    3: (2.108, "David Cantrell, Aug 2002"),
    4: (4 / s3, "David Cantrell, Aug 2002"),
    5: (2.534, "Maurizio Morandi, Apr 2009"),
    6: (3.168, "David Cantrell, Aug 2002"),
    7: (3.327, "Maurizio Morandi, May 2009"),
    8: (3.495, "Maurizio Morandi, Apr 2009"),
    9: (3.711, "Maurizio Morandi, May 2009"),
    10: (4.197, "Maurizio Morandi, Apr 2009"),
    11: (4.35451, "Ryan Chi and d/dx, Sep 2026"),
    12: (2 * s3 + sqrt(6) - sqrt(2), "Maurizio Morandi, May 2009"),
}
TRUNCATED[("sq", "triangle")] = {2, 3, 5, 6, 7, 8, 9, 10}
TRUNC_STEP = {("sq", "triangle", 11): 1e-5}

_tct = {1: 1, 3: 1.5, 4: 2, 6: 7 / 3, 7: 2.5, 8: 8 / 3, 9: 3, 11: 3.25, 12: 10 / 3, 13: 3.5, 14: 11 / 3, 15: 3.75}
_tct_who = {1: "Trivial", 3: "Trivial", 4: "Trivial", 6: "David Cantrell, Aug 2002", 7: "Erich Friedman, 1999",
            8: "David Cantrell, Aug 2002", 9: "Trivial", 11: "Erich Friedman, 1999", 12: "Erich Friedman, 1999",
            13: "Erich Friedman, 1999", 14: "David Cantrell, Aug 2002", 15: "Erich Friedman, 1999"}
RECORDS[("tri", "triangle")] = {}
for _n in range(1, 16):
    _m = max(k for k in _tct if k <= _n)       # unlisted n: best known is the previous n's value
    RECORDS[("tri", "triangle")][_n] = (_tct[_m], _tct_who[_m] if _m == _n else f"same as n={_m} (not listed)")

_sqsq = {3: (0.5 + sqrt(5) / 2, "Dudeney, 1931"), 7: (11 / 4 + 3 / sqrt(2), "Trevor Green, Sep 2000"),
         8: (3 + 2 * sqrt(2), "Trevor Green, Sep 2000"), 12: (9.08195, "Ryan Chi, Sep 2026"),
         13: (5.5 + 3 * sqrt(2), "David Paterson, Jul 2002"), 14: (10.860, "Michael Kearney, Jul 2002"),
         15: (11.84721, "Ryan Chi, Sep 2026"), 21: (8.5 + 6 * sqrt(2), "David Paterson, Jul 2002"),
         22: (17.821, "David Cantrell, Aug 2002"), 23: (19.001, "David Cantrell, Jul 2002"),
         24: (20.008, "Maurizio Morandi, Oct 2010"), 31: (25.527, "David Paterson, Sep 2002"),
         32: (83 / 4 + 9 / sqrt(2), "David Paterson, Sep 2002"), 33: (27.988, "Maurizio Morandi, Oct 2010"),
         34: (18 + 8 * sqrt(2), "David Paterson, Sep 2002"), 35: (30.247, "Maurizio Morandi, Oct 2010"),
         43: (36.608, "David Paterson, Sep 2002"), 44: (20.5 + 12 * sqrt(2), "David Paterson, Sep 2002"),
         45: (39.042, "David Paterson, Sep 2002"), 46: (39.77036, "Ryan Chi and d/dx, Sep 2026"),
         47: (41.34484, "Ryan Chi and d/dx, Sep 2026"), 48: (42.61222, "Ryan Chi and d/dx, Sep 2026")}
SQSQ_AREA = {}
RECORDS[("sq", "square")] = {}
for _n in range(1, 49):
    if _n in _sqsq:
        A, who = _sqsq[_n]
    else:
        A, who = float(floor(sqrt(_n)) ** 2), "trivial covering (page: no tilted squares known)"
    SQSQ_AREA[_n] = A
    RECORDS[("sq", "square")][_n] = (sqrt(A), who)
TRUNCATED[("sq", "square")] = {14, 22, 23, 24, 31, 33, 35, 43, 45}
for _n in (12, 15, 46, 47, 48):
    TRUNC_STEP[("sq", "square", _n)] = 1e-5

# Closed forms as printed on the pages, for display.
FORMULA = {
    ("tri", "square"): {10: "5/√3 − 1", 11: "√3 + 1/4", 12: "(7√3 + 15)/13"},
    ("tri", "disk"): {9: "(81√3 − 6√30)/106", 11: "(177√3 − 2√586)/226", 12: "(7√3 − √7)/8"},
    ("sq", "triangle"): {1: "√6 − √2", 4: "4/√3", 12: "2√3 + √6 − √2"},
}

# Originality review (25 Sep 2026). Every certificate was compared with the
# picture of the record it beats, by independent reviewers using piece-by-piece
# matching under rotations and reflections (see docs/ORIGINALITY.md).
# REOPTIMISED: same arrangement as the current record, pieces moved slightly
#   (largest matched displacement 0.02-0.24 of a piece side); the value is a real
#   improvement but the design belongs to the original finder.
# NOT_SUBMITTED: re-optimisations whose gain is too small to be worth submitting.
REOPTIMISED = {("sq", "disk", 7), ("sq", "disk", 8), ("sq", "disk", 13), ("sq", "disk", 17),
               ("tri", "disk", 11), ("tri", "square", 10), ("tri", "square", 11),
               ("sq", "triangle", 10), ("sq", "triangle", 11),
               ("sq", "square", 12), ("sq", "square", 14), ("sq", "square", 15)}
NOT_SUBMITTED = {("sq", "square", 15)}
REFINEMENTS = REOPTIMISED      # backwards-compatible name
