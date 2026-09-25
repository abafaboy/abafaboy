"""Second, independently written exact coverage checker.

Written during the pre-submission audit by a separate reviewer agent that did not
reuse verify.py: it uses horizontal instead of vertical slabs, its own Q(sqrt 3)
arithmetic on plain Fractions, and computes piece orientation instead of
assuming it. Run on the certificates: python verify_independent.py ../certificates/*.json
"""
import sys, json
from fractions import Fraction as Fr
from functools import cmp_to_key

# elements of Q(sqrt3) as tuples (a, b) meaning a + b*sqrt3
def A(x): return (Fr(x), Fr(0))
def add(p, q): return (p[0] + q[0], p[1] + q[1])
def sub(p, q): return (p[0] - q[0], p[1] - q[1])
def mul(p, q): return (p[0]*q[0] + 3*p[1]*q[1], p[0]*q[1] + p[1]*q[0])
def div(p, q):
    n = q[0]*q[0] - 3*q[1]*q[1]
    assert n != 0
    return mul(p, (q[0]/n, -q[1]/n))
def sgn(p):
    a, b = p
    # sign of a + b sqrt3 via: if a,b same sign or one zero trivial, else compare a^2 vs 3 b^2
    if b == 0: return (a > 0) - (a < 0)
    if a == 0: return (b > 0) - (b < 0)
    if (a > 0) == (b > 0): return 1 if a > 0 else -1
    d = a*a - 3*b*b
    return ((a > 0) - (a < 0)) if d > 0 else ((b > 0) - (b < 0))
def cmp(p, q): return sgn(sub(p, q))
HALF = A(Fr(1, 2))

def piece(kind, x, y, t):
    c = (1 - t*t) / (1 + t*t); s = 2*t / (1 + t*t)
    if kind == 'sq':
        loc = [(A(Fr(1, 2)), A(Fr(1, 2))), (A(Fr(-1, 2)), A(Fr(1, 2))), (A(Fr(-1, 2)), A(Fr(-1, 2))), (A(Fr(1, 2)), A(Fr(-1, 2)))]
    else:
        loc = [((Fr(0), Fr(0)), (Fr(0), Fr(1, 3))), (A(Fr(-1, 2)), (Fr(0), Fr(-1, 6))), (A(Fr(1, 2)), (Fr(0), Fr(-1, 6)))]
    C, S = A(c), A(s)
    return [(add(A(x), sub(mul(u, C), mul(v, S))), add(A(y), add(mul(u, S), mul(v, C)))) for u, v in loc]

def cross(o, a, b):
    return sub(mul(sub(a[0], o[0]), sub(b[1], o[1])), mul(sub(a[1], o[1]), sub(b[0], o[0])))

def orient(P):
    s = (Fr(0), Fr(0))
    for i in range(len(P)):
        s = add(s, cross((A(0), A(0)), P[i], P[(i+1) % len(P)]))
    return sgn(s)

def contains(P, q):
    o = orient(P); assert o != 0
    return all(sgn(cross(P[i], P[(i+1) % len(P)], q)) * o >= 0 for i in range(len(P)))

def d2_seg(p, a, b):
    d = sub(b, a) if False else (sub(b[0], a[0]), sub(b[1], a[1]))
    w = (sub(p[0], a[0]), sub(p[1], a[1]))
    L = add(mul(d[0], d[0]), mul(d[1], d[1]))
    ww = add(mul(w[0], w[0]), mul(w[1], w[1]))
    if sgn(L) == 0: return ww
    t = add(mul(w[0], d[0]), mul(w[1], d[1]))
    if sgn(t) <= 0: return ww
    if cmp(t, L) >= 0:
        u = (sub(p[0], b[0]), sub(p[1], b[1])); return add(mul(u[0], u[0]), mul(u[1], u[1]))
    return sub(ww, div(mul(t, t), L))

def check(cert):
    kind, target = cert['kind'], cert['target']
    size = Fr(cert['size']); assert size > 0
    pcs = [piece(kind, Fr(p['x']), Fr(p['y']), Fr(p['t'])) for p in cert['pieces']]
    assert len(pcs) == cert['n']
    S = A(size)
    if target == 'square':
        h = A(size / 2); T = [(sub(A(0), h), sub(A(0), h)), (h, sub(A(0), h)), (h, h), (sub(A(0), h), h)]
    elif target == 'triangle':
        T = [(A(0), (Fr(0), size / 3)), (A(-size / 2), (Fr(0), -size / 6)), (A(size / 2), (Fr(0), -size / 6))]
    else:
        T = [(A(-size), A(-size)), (A(size), A(-size)), (A(size), A(size)), (A(-size), A(size))]
    ylo = min((v[1] for v in T), key=cmp_to_key(cmp)); yhi = max((v[1] for v in T), key=cmp_to_key(cmp))
    segs = [(P[i], P[(i+1) % len(P)]) for P in pcs + [T] for i in range(len(P))]
    ys = set()
    for a, b in segs: ys.add(a[1]); ys.add(b[1])
    for i in range(len(segs)):
        p, p2 = segs[i]; r = (sub(p2[0], p[0]), sub(p2[1], p[1]))
        for j in range(i):
            q, q2 = segs[j]; s = (sub(q2[0], q[0]), sub(q2[1], q[1]))
            den = sub(mul(r[0], s[1]), mul(r[1], s[0]))
            if sgn(den) == 0: continue
            qp = (sub(q[0], p[0]), sub(q[1], p[1]))
            tt = div(sub(mul(qp[0], s[1]), mul(qp[1], s[0])), den)
            uu = div(sub(mul(qp[0], r[1]), mul(qp[1], r[0])), den)
            if sgn(tt) >= 0 and cmp(tt, A(1)) <= 0 and sgn(uu) >= 0 and cmp(uu, A(1)) <= 0:
                ys.add(add(p[1], mul(tt, r[1])))
    ys = sorted([y for y in ys if cmp(y, ylo) >= 0 and cmp(y, yhi) <= 0], key=cmp_to_key(cmp))
    ncell = 0
    R2 = mul(S, S)
    for y0, y1 in zip(ys, ys[1:]):
        if cmp(y0, y1) >= 0: continue
        ym = mul(add(y0, y1), HALF)
        xs = []
        for a, b in segs:
            if cmp(a[1], b[1]) == 0: continue
            lo, hi = (a, b) if cmp(a[1], b[1]) < 0 else (b, a)
            if cmp(lo[1], y0) <= 0 and cmp(hi[1], y1) >= 0:
                inv = div(sub(hi[0], lo[0]), sub(hi[1], lo[1]))
                xat = lambda yy, lo=lo, inv=inv: add(lo[0], mul(inv, sub(yy, lo[1])))
                xs.append((xat(ym), xat))
        xs.sort(key=cmp_to_key(lambda u, v: cmp(u[0], v[0])))
        for (xa, fa), (xb, fb) in zip(xs, xs[1:]):
            if cmp(xa, xb) >= 0: continue
            q = (mul(add(xa, xb), HALF), ym)
            if target in ('square', 'triangle'):
                if not contains(T, q): continue
            else:
                corners = [(fa(y0), y0), (fb(y0), y0), (fb(y1), y1), (fa(y1), y1)]
                O = (A(0), A(0))
                # origin in closed trapezoid? (test with each edge, orientation-agnostic via nonzero-area check)
                sides = [sgn(cross(corners[i], corners[(i+1) % 4], O)) for i in range(4)
                         if not (cmp(corners[i][0], corners[(i+1) % 4][0]) == 0 and cmp(corners[i][1], corners[(i+1) % 4][1]) == 0)]
                if all(s_ >= 0 for s_ in sides) or all(s_ <= 0 for s_ in sides):
                    d2 = A(0)
                else:
                    d2 = min((d2_seg(O, corners[i], corners[(i+1) % 4]) for i in range(4)), key=cmp_to_key(cmp))
                if cmp(d2, R2) >= 0: continue
            ncell += 1
            if not any(contains(P, q) for P in pcs):
                return False, ncell
    return True, ncell

if __name__ == '__main__':
    allok = True
    for path in sys.argv[1:]:
        ok, n = check(json.load(open(path)))
        allok &= ok
        print(path.split('/')[-1], 'INDEPENDENT', 'OK' if ok else 'FAIL', n, 'cells')
    sys.exit(0 if allok else 1)
