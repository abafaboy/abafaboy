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
    rec = RECORDS[(kind, target)][n][0]
    bar = rec + 0.001 if n in TRUNCATED.get((kind, target), ()) else rec
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

# Closed forms as printed on the pages, for display.
FORMULA = {
    ("tri", "square"): {10: "5/√3 − 1", 11: "√3 + 1/4", 12: "(7√3 + 15)/13"},
    ("tri", "disk"): {9: "(81√3 − 6√30)/106", 11: "(177√3 − 2√586)/226", 12: "(7√3 − √7)/8"},
}
