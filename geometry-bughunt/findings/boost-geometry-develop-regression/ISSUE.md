# Regression since 1.87: `within()` returns true and `intersection()` returns all of A for two triangles with nearly coincident vertices (bisected to 9c4d7529b)

## Summary

For two valid triangles that share a nearly coincident vertex (1 to 2 ulps apart), Boost.Geometry 1.87.0 through 1.92.0 and current `develop` return:

- `within(A, B) == true` and `relation(A, B) == "2FF10F212"`;
- `intersection(A, B)` equal to all of A (area 3.63, while area(B) is only 0.27);
- `union_(A, B)` equal to B alone.

The two triangles overlap in a small triangle of area about 0.078, which is not a sliver. So the correct answers are `within == false`, `overlaps == true`, intersection area ≈ 0.078 and union area ≈ 3.82. Boost 1.83 through 1.86 return these correct answers.

I bisected the change to 9c4d7529b, "fix: add condition to handle_as_touch" (fixes #1288). In a local experiment, disabling only that added condition on `develop` gives the correct answer for this input.

## Minimal reproduction

The polygons use the default types (clockwise, closed), and the rings are written clockwise. `bg::is_valid` accepts both inputs.

```cpp
#include <boost/geometry.hpp>
#include <iomanip>
#include <iostream>
namespace bg = boost::geometry;
using point_t = bg::model::d2::point_xy<double>;
using polygon_t = bg::model::polygon<point_t>;
using mpolygon_t = bg::model::multi_polygon<polygon_t>;

int main()
{
    polygon_t a, b;
    bg::read_wkt("POLYGON((-0.6 3,2 -1,-1.7 1.9,-0.6 3))", a);
    bg::read_wkt("POLYGON((-1.6999999999999997 1.9000000000000004,-1 2,-2.6 1,"
                 "-1.6999999999999997 1.9000000000000004))", b);
    mpolygon_t i, u, d;
    bg::intersection(a, b, i);
    bg::union_(a, b, u);
    bg::difference(a, b, d);
    std::cout << std::setprecision(17) << std::boolalpha
              << bg::is_valid(a) << " " << bg::is_valid(b) << "\n"
              << bg::relation(a, b).str() << " within=" << bg::within(a, b) << "\n"
              << "area A=" << bg::area(a) << " B=" << bg::area(b) << "\n"
              << "intersection=" << bg::area(i) << " union=" << bg::area(u)
              << " difference=" << bg::area(d) << "\n";
}
```

The full program is `repro.cpp`. It also runs the original case in which this was found: two unit squares, with B equal to A shifted by one edge vector.

Geometry, for checking by hand:

- A = (-0.6, 3), (2, -1), (-1.7, 1.9).
- B's first vertex is (-1.7, 1.9) moved by +1 ulp in x and +2 ulps in y.
- A's edge from (-0.6, 3) to (-1.7, 1.9) and B's edge to (-2.6, 1) both lie on the line y = x + 3.6 in decimal arithmetic.
- B's vertex (-1, 2) is strictly inside A. So the interiors overlap near (-1, 2), and A's vertex (2, -1) is far outside B.

## Expected

These values come from exact rational arithmetic on the exact double inputs. Two independent exact implementations agree.

| | value |
|---|---|
| is_valid(A), is_valid(B) | true, true |
| relation(A,B) | 212101212 (interiors intersect) |
| within(A,B), covered_by(A,B) | false, false |
| overlaps(A,B) | true |
| area(A), area(B) | 3.63, 0.27 |
| area(intersection) | 0.077697841726618824 |
| area(union) | 3.8223021582733816 |
| area(difference A−B) | 3.5523021582733811 |

## Actual

Output of `repro.cpp`, identical on develop 196d04c, 1.92.0 and 1.87.0:

```
relation(A,B) = 2FF10F212
within(A,B) = true   covered_by(A,B) = true   overlaps(A,B) = false
area(intersection) = 3.6299999999999994
area(union)        = 0.27000000000000024
area(difference)   = 3.5523021582733816
intersection = MULTIPOLYGON(((-1.7 1.8999999999999999,-0.59999999999999998 3,2 -1,-1.7 1.8999999999999999)))
```

The results are also inconsistent with each other: `difference` is correct (3.55), `intersection` returns all of A (3.63), and together they add up to about twice area(A).

On 1.83, 1.85/1.86, and on the parent commit of 9c4d7529b, the output is `212101212`, `within=false`, `overlaps=true`, intersection 0.0776978…, union 3.8223….

## Versions

| Boost.Geometry | minimal case | original case (unit squares) |
|---|---|---|
| 1.83.0, 1.84.0, 1.85.0/1.86.0 | correct | correct |
| 754695969 (parent of 9c4d7529b) | correct | correct |
| 9c4d7529b "fix: add condition to handle_as_touch" | wrong | wrong |
| 1.87.0, 1.88.0 | wrong | wrong (union area 0) |
| 1.89.0, 1.90.0, 1.91.0, 1.92.0 | wrong | wrong |
| develop 196d04c (2026-08-17, current HEAD) | wrong | wrong |

Test setup:

- g++ 13.3, `-std=c++17 -O2`, on x86-64 Ubuntu 24.04. The results are the same with `-O0`, with `-march=native`, and with clang++.
- Each Boost.Geometry version's headers were placed in front of the system Boost 1.83. Versions from 1.84 on also needed a one-line shim for `<boost/core/invoke_swap.hpp>`.
- `BOOST_GEOMETRY_DEFAULT_STRATEGY_SIDE_USE_SIDE_ROBUST` does not change the result.

## Analysis

These points are based on bisection, on a trace of the values involved, and on one local experiment. They are not a proposed fix.

1. **Bisection.** `git bisect` between boost-1.86.0 and boost-1.87.0 points to 9c4d7529b. That commit added this early return to `touch_interior::handle_as_touch` (develop: `include/boost/geometry/algorithms/detail/overlay/get_turn_info.hpp:366-378`):

   ```cpp
   if (has_k
       && (same(side.pj_wrt_q1(), side.qj_wrt_p2())
        || same(side.pj_wrt_q2(), side.qj_wrt_p1())))
   {
       return false;
   }
   ```

2. **Trace for this input.** `handle_as_touch` is reached from `get_turn_info` (get_turn_info.hpp:1481-1510) with P = B's segment (-2.6, 1) → B0 and Q = A's segment (2, -1) → (-1.7, 1.9). So pj = B0 and qj = A1, which are 5e-16 apart.
   - `pj_wrt_q1` and `qj_wrt_p2` are both -1. Checked with exact arithmetic, both signs are correct: B0 lies just outside A, and A1 lies just inside B.
   - `pj_wrt_q2` and `qj_wrt_p1` are 0. `side_by_triangle` classifies them as collinear, although the exact values are +1 and -1 (the determinants are about 2e-16).
   - The new condition therefore returns `false`, and the intersection is processed as a `touch_interior` turn.

3. **Experiment.** With only that `if` disabled on develop (`experiment_disable_condition.diff`), the same calls reach the existing distance test at get_turn_info.hpp:410-412. That test gives `dm = 8.9e-31`, so the intersection is handled as a touch. The final results are then correct for both the minimal case and the original case: relation 212101212, intersection area 0.0776978…, union 3.8223….
   - The inputs added with 9c4d7529b for #1288 and #1222 still give the expected areas with the condition disabled on develop. The parent commit fails #1288 (multi/poly difference returns 0).
   - Upstream tests run with the condition disabled: see "Upstream tests" below.
   - This suggests the condition catches configurations with nearly coincident pj/qj, where the "segments cross or touch in the middle" reasoning in its comment does not hold. I have not worked out a fix that keeps #1288 fixed in all its variants.

4. Both relate (`within`/`relation`) and overlay change together, which fits a change in the shared turn computation (`get_turn_info`) rather than in traversal.

## Upstream tests (develop, with and without the condition)

UPSTREAM_TESTS_PLACEHOLDER

## Related issues

- #1288: the issue fixed by 9c4d7529b.
- #1360 (open): "Buffer (or other overlays) fail because arrival is not handled correctly". It concerns arrival handling for nearly collinear touching segments in `get_turn_info`, the same area of the code but a different block.
- #1487 (open): "No intersection for polygons with close boundaries". In my builds its test case starts failing in 1.89.0, not 1.87.0, and disabling the condition does not fix it. So it looks like a separate regression.
- #1201 (open): intersection returns the second polygon for a nearly coincident vertex. It fails from 1.83 on and is not affected by the experiment.

## How it was found

Found by differential testing against an exact rational-arithmetic oracle. The oracle computes predicates and overlay areas exactly for the exact double inputs, and a second, independently written exact implementation cross-checks it. The minimal case was reduced automatically from the original case. The reduction kept the requirements that develop is wrong while 1.83, 1.86, and develop with the condition disabled are all correct.
