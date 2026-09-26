# Method

## The problems

Three pages of Erich Friedman's
[Packing Center](https://erich-friedman.github.io/packing/) ask the same kind of
question: with *n* unit copies of a piece, allowed to overlap and to stick out,
what is the largest target you can cover completely?

| page | pieces | target | value |
|---|---|---|---|
| Squares Covering Circles | unit squares | disk | radius *r* |
| Triangles Covering Circles | unit equilateral triangles | disk | radius *r* |
| Triangles Covering Squares | unit equilateral triangles | square | side *s* |

Most of the records on these pages were set between 1997 and 2009 by hand or
with small programs. Several values are given only to three decimals
("1.239+").

## Turning covering into minimising one number

Fix the target at size 1: the square of side 1, or the disk of radius 1. Place
*n* pieces by centroid and angle. For a point *p*, the **gauge** of piece *i*

    g_i(p) = max over edges e of  (rotated normal of e) . (p - centroid_i) / inradius

is the factor by which piece *i* must be scaled about its centroid to reach *p*.
It is piecewise linear in *p*. Let

    F(X) = max over target points p of  min over pieces i of  g_i(p).

If every piece is scaled by F(X) about its own centroid, the pieces cover the
target, and no smaller common factor does. Scaling the whole picture by 1/F(X)
gives **unit** pieces covering a target of size **1/F(X)**. So the problem is to
minimise F.

### Evaluating F exactly

min_i g_i is a continuous piecewise-linear function, so its maximum over the
target is attained at a vertex of its linear pieces. Every such vertex is one
of:

* a point where three linear functions (from at least two pieces) are equal;
* square target: a point on a side where two of them are equal, or a corner;
* disk target: a point on the circle where two of them are equal, or the point
  of the circle where a single linear function is largest.

`src/opt.py:candidates` enumerates all of these (tens of thousands for n = 18),
and F is the largest value of min_i g_i among them. This is exact up to float
rounding. The certificates below remove the rounding.

## Search

1. **Smoothed global phase.** Replace the max over target points by a
   log-sum-exp over a grid of about 2,300 sample points, and the min over pieces
   by a soft-min. Minimise with L-BFGS (gradients from JAX), sharpening the
   smoothing in five stages. Start from uniformly random centroids and angles.
2. **Exact local polish.** Take every candidate vertex within a small tolerance
   of the current maximum, freeze which linear functions define it, and solve
   the minimax problem "minimise t subject to value_j(X) <= t" with SLSQP inside
   a trust region. Recompute F exactly, accept only improvements, and repeat.
   Jacobians use the complex-step method, which is exact to machine precision.
   Each round takes a few milliseconds.
3. **Basin hopping.** Perturb the best few configurations (jiggle all pieces,
   re-seat one or two pieces randomly, or rotate a few), then polish again.
   Four worker processes run with different seeds.

The same code reproduces the known records it should, for example
(7√3 − 6)/4 for seven triangles covering a square, r = 1 for four squares, and
r = √3/2 for six triangles. See the README for the full list.

## Exact certificates

`src/make_cert.py` turns a configuration into a certificate. Each piece is given
as a rational centroid and a rational t, meaning the rotation with
cos = (1−t²)/(1+t²) and sin = 2t/(1+t²). The target size is a rational slightly
*below* 1/F. The verifier rebuilds every piece from those numbers, so each
piece is exactly unit-sized:

* square vertices are rational;
* triangle vertices lie in the field Q(√3).

The verifier asserts that every side has squared length exactly 1.

Why the rounding is safe: F is a strict maximum over the target, so enlarging
all pieces by the factor 1 + 10⁻⁹ leaves overlap along every seam. Rounding
coordinates to 10⁻¹⁸ is far below that overlap.

`src/verify.py` then decides coverage with **no floating point**:

1. Collect every piece edge, plus the square's sides or a bounding box of the
   disk.
2. The x-coordinates of all endpoints and all pairwise edge intersections cut
   the plane into vertical slabs. Inside an open slab no edges cross and none
   start or end. So consecutive edges bound open trapezoids that no piece
   boundary passes through.
3. Each trapezoid lies wholly inside or wholly outside every closed piece, so
   testing one interior point decides it.
4. Every trapezoid that meets the target (for the disk: exact squared distance
   to the centre is below r²) must contain a covered test point.

The union of finitely many closed pieces is closed and the open trapezoids are
dense, so this proves the whole closed target is covered. All comparisons are
exact sign tests in Q(√3): for a + b√3 with opposite signs, compare a² with 3b².

`src/crosscheck.py` is a second, independent check. It builds the pieces in
floating point, unions them with GEOS (Shapely), and tests containment of the
target shrunk by 10⁻⁷.

**Negative controls.** Enlarging any certified target by a factor of 1 + 10⁻⁶
makes the exact verifier find an uncovered cell, and makes the Shapely check
fail. So neither check passes vacuously. `tests/test_verify.py` runs these
controls.
