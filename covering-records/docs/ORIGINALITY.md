# Originality review

A value that beats the record is not automatically a new design. The optimizer
starts from random configurations, but it can still converge to the same
arrangement as a record found by hand years ago, only better optimized. Before
anything was submitted, each covering was compared with the picture of the record
it beats (Friedman's site, commit `cd143d9` and later, 25 September 2026).

## How the comparison was done

Each comparison used independent reviewer agents, and none of them saw another's
answer.

1. **Picture review.** Three judges per borderline case, and one per remaining
   case, looked at the old and new pictures side by side.
2. **Quantitative matching.** Two further reviewers per case each used a
   different method.
   - The first located every piece in the old GIF by template matching. It took
     the new pieces exactly from the certificate, searched all rotations and
     reflections of the whole figure, and matched pieces one to one (Hungarian
     algorithm). It reports the largest displacement of a matched pair, in piece
     sides.
   - The second rendered the certificate at the old picture's scale and scored
     outline overlap under every rotation and reflection.

**Classification rule.** A covering is the *same arrangement, re-optimised* if,
under the best rotation or reflection, every piece matches a piece of the same
orientation class moved by clearly less than half a side. It is *same family,
different arrangement* if the design is similar but the piece counts per
orientation, or which pieces touch which, clearly differ. Otherwise it is a *new
arrangement*.

## Verdicts

| covering | verdict | largest matched displacement (sides) | votes |
|---|---|---|---|
| squares covering circles, n = 12 | same family, different arrangement | 0.15 | 2 quantitative + 1 picture review ("new") |
| squares covering circles, n = 18 | same family, different arrangement | 0.60 | 3 picture + 2 quantitative |
| triangles covering circles, n = 9 | same family, different arrangement | 0.17–0.19 (6 of 9 pieces turned 23–37°) | 1 picture + 2 quantitative |
| triangles covering circles, n = 12 | same family, different arrangement | 0.55–0.72 | 1 picture + 2 quantitative |
| squares covering triangles, n = 12 | same family, different arrangement | 0.43–0.44 | 2 quantitative vs 1 picture ("same") |
| squares covering circles, n = 7 | same arrangement, re-optimised | 0.06 | all 3 |
| squares covering circles, n = 8 | same arrangement, re-optimised | 0.02 | all 3 |
| squares covering circles, n = 13 | same arrangement, re-optimised | 0.14–0.17 | all 3 |
| squares covering circles, n = 17 | same arrangement, re-optimised | 0.055 | 2 quantitative vs 1 picture ("new") |
| triangles covering circles, n = 11 | same arrangement, re-optimised | 0.05–0.06 (figure turned 30°) | all 3 |
| triangles covering squares, n = 10 | same arrangement, re-optimised | 0.23 (figure reflected) | all 3 |
| triangles covering squares, n = 11 | same arrangement, re-optimised | 0.11 (figure turned 90°) | all 3 |
| squares covering triangles, n = 10 | same arrangement, re-optimised | – | 3 picture reviews |
| squares covering triangles, n = 11 | same arrangement, re-optimised | – | 3 picture reviews |
| squares covering squares, n = 12 | same arrangement, re-optimised | – | 3 picture reviews |
| squares covering squares, n = 14 | same arrangement, re-optimised | 0.10 (figure reflected) | all 3 |
| squares covering squares, n = 15 | same arrangement, re-optimised | – | 3 picture reviews, plus the per-record auditor |

Several of these were first judged "new" by eye. The quantitative matching
showed they were the old figure turned or reflected.

## What this means for the claims

- The **five different arrangements** are the only coverings presented as new
  configurations.
- The **eleven re-optimisations** still cover larger targets than the records,
  because the hand-made 2002–2009 configurations were not fully optimized. They
  are reported as better-optimized versions of the existing arrangements. The
  design belongs to the original finder, and credit is left to the site's
  maintainer.
- **Squares covering squares, n = 15** is not submitted at all. Its gain over
  Ryan Chi's September 2026 value is only 8 × 10⁻⁵ in area.

None of the covering values found here appears anywhere else. An audit searched
papers, repositories, forums and other record tables for each page; the only
published values are those on Friedman's pages, and ours beat them.
