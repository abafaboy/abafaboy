"""Search for coverings of a square or disk by n equal regular polygons.

Formulation. The target (square of side 1, or disk of radius 1) is fixed and
the n pieces are placed by centroid and angle. For a configuration X let

    F(X) = max_{p in target} min_i g_i(p),

where g_i is the gauge of piece i about its centroid (see geom.py). Scaling
every piece by F(X) about its own centroid makes the pieces cover the target,
so unit pieces cover a target of size 1/F(X). We minimise F.

F is a max-min of piecewise-linear functions, so its value is attained at a
finite set of candidate points (ties of three linear pieces, ties of two on
the target boundary, target corners, ...). `exact_F` enumerates them. The
global search minimises a smoothed version of F on sample points; the local
polish is a sequential minimax (SLSQP) over the near-active candidates.
"""
import itertools
import math
import sys
import time

import numpy as np
from scipy.optimize import minimize

import jax
import jax.numpy as jnp

jax.config.update("jax_enable_x64", True)

from geom import PIECES  # noqa: E402

SQ_EDGES = [((1.0, 0.0), 0.5), ((-1.0, 0.0), 0.5), ((0.0, 1.0), 0.5), ((0.0, -1.0), 0.5)]
SQ_CORNERS = [(0.5, 0.5), (-0.5, 0.5), (-0.5, -0.5), (0.5, -0.5)]


# ----------------------------------------------------------------------------
# linear pieces of the gauges
# ----------------------------------------------------------------------------
def lin_np(kind, X):
    P = PIECES[kind]
    phi = np.asarray(P["normals"])
    ang = X[:, 2:3] + phi[None, :]                      # (n, k)
    ax = np.cos(ang) / P["h"]
    ay = np.sin(ang) / P["h"]
    b = -(ax * X[:, 0:1] + ay * X[:, 1:2])
    return np.stack([ax.ravel(), ay.ravel()], 1), b.ravel()


def lin_jnp(kind, X):
    P = PIECES[kind]
    phi = jnp.asarray(P["normals"])
    ang = X[:, 2:3] + phi[None, :]
    ax = jnp.cos(ang) / P["h"]
    ay = jnp.sin(ang) / P["h"]
    b = -(ax * X[:, 0:1] + ay * X[:, 1:2])
    return jnp.stack([ax.ravel(), ay.ravel()], 1), b.ravel()


def G_np(kind, X, pts):
    a, b = lin_np(kind, X)
    k = len(PIECES[kind]["normals"])
    L = pts @ a.T + b[None, :]                           # (N, m)
    L = L.reshape(len(pts), -1, k)
    return L.max(2).min(1)


# ----------------------------------------------------------------------------
# exact evaluation of F by candidate enumeration
# ----------------------------------------------------------------------------
_TRIPLE_CACHE = {}


def _triples(n, k):
    key = (n, k)
    if key not in _TRIPLE_CACHE:
        m = n * k
        T = np.array(list(itertools.combinations(range(m), 3)), dtype=np.int64)
        piece = T // k
        keep = ~((piece[:, 0] == piece[:, 1]) & (piece[:, 1] == piece[:, 2]))
        _TRIPLE_CACHE[key] = T[keep]
    return _TRIPLE_CACHE[key]


class _Meta:
    """Lazy list of (type, index-tuple) built from vectorised blocks."""

    def __init__(self):
        self.blocks, self.offsets, self.total = [], [], 0

    def add(self, typ, idx):
        idx = np.asarray(idx, dtype=np.int64).reshape(len(idx), -1)
        self.blocks.append((typ, idx)); self.offsets.append(self.total)
        self.total += len(idx)

    def __len__(self):
        return self.total

    def __getitem__(self, j):
        b = int(np.searchsorted(self.offsets, j, side="right")) - 1
        typ, idx = self.blocks[b]
        return typ, tuple(int(v) for v in idx[j - self.offsets[b]])


_PAIR_CACHE = {}


def _pairs(m):
    if m not in _PAIR_CACHE:
        _PAIR_CACHE[m] = np.array(list(itertools.combinations(range(m), 2)), dtype=np.int64)
    return _PAIR_CACHE[m]


def candidates(kind, target, X):
    """Return (points, meta): every point where the maximum of G may sit."""
    n = len(X)
    k = len(PIECES[kind]["normals"])
    m = n * k
    a, b = lin_np(kind, X)
    out_pts, meta = [], _Meta()

    # interior points where three linear pieces tie
    T = _triples(n, k)
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    M00 = a[A, 0] - a[B, 0]; M01 = a[A, 1] - a[B, 1]
    M10 = a[A, 0] - a[C, 0]; M11 = a[A, 1] - a[C, 1]
    r0 = b[B] - b[A]; r1 = b[C] - b[A]
    det = M00 * M11 - M01 * M10
    ok = np.abs(det) > 1e-12
    dsafe = np.where(ok, det, 1)
    px = (r0 * M11 - r1 * M01) / dsafe
    py = (M00 * r1 - M10 * r0) / dsafe
    if target == "square":
        inside = ok & (np.abs(px) <= 0.5 + 1e-12) & (np.abs(py) <= 0.5 + 1e-12)
    else:
        inside = ok & (px * px + py * py <= 1 + 1e-12)
    out_pts.append(np.stack([px[inside], py[inside]], 1)); meta.add("tri", T[inside])

    pairs = _pairs(m)
    PA, PB = pairs[:, 0], pairs[:, 1]
    d = a[PA] - a[PB]
    e = b[PB] - b[PA]
    if target == "square":
        # ties of two linear pieces on each side of the square, and the corners
        for ei, (u, w) in enumerate(SQ_EDGES):
            det = d[:, 0] * u[1] - d[:, 1] * u[0]
            ok = np.abs(det) > 1e-12
            dsafe = np.where(ok, det, 1)
            px = (e * u[1] - w * d[:, 1]) / dsafe
            py = (d[:, 0] * w - u[0] * e) / dsafe
            inside = ok & (np.abs(px) <= 0.5 + 1e-12) & (np.abs(py) <= 0.5 + 1e-12)
            out_pts.append(np.stack([px[inside], py[inside]], 1))
            sel = pairs[inside]
            meta.add("edge", np.hstack([sel, np.full((len(sel), 1), ei)]))
        out_pts.append(np.array(SQ_CORNERS)); meta.add("corner", np.arange(4)[:, None])
    else:
        # ties of two linear pieces on the circle, and each linear piece's
        # maximum over the circle
        dd = (d * d).sum(1)
        ok = dd > 1e-18
        dsafe = np.where(ok, dd, 1)
        base = (e / dsafe)[:, None] * d
        disc = 1 - e * e / dsafe
        ok &= disc >= 0
        perp = np.stack([-d[:, 1], d[:, 0]], 1) / np.sqrt(dsafe)[:, None]
        sq = np.sqrt(np.where(ok, disc, 0))[:, None]
        for sgn in (1, -1):
            Pp = base + sgn * sq * perp
            out_pts.append(Pp[ok]); sel = pairs[ok]
            meta.add("dpair", np.hstack([sel, np.full((len(sel), 1), sgn)]))
        na = np.sqrt((a * a).sum(1))
        out_pts.append(a / na[:, None]); meta.add("dsingle", np.arange(m)[:, None])
    return np.concatenate(out_pts), meta


def exact_F(kind, target, X, return_cands=False):
    pts, meta = candidates(kind, target, X)
    g = G_np(kind, X, pts)
    j = int(np.argmax(g))
    if return_cands:
        return float(g[j]), pts, meta, g
    return float(g[j])


# ----------------------------------------------------------------------------
# smoothed objective for global search
# ----------------------------------------------------------------------------
def sample_points(target, K):
    if target == "square":
        u = np.linspace(-0.5, 0.5, K)
        xx, yy = np.meshgrid(u, u)
        return np.stack([xx.ravel(), yy.ravel()], 1)
    pts = [np.zeros((1, 2))]
    rings = K // 2
    for r in np.linspace(1.0 / rings, 1.0, rings):
        cnt = max(6, int(round(2 * math.pi * r * K / 2 * 1.6)))
        th = np.linspace(0, 2 * math.pi, cnt, endpoint=False) + r
        pts.append(np.stack([r * np.cos(th), r * np.sin(th)], 1))
    return np.concatenate(pts)


def make_smooth(kind, n, pts):
    k = len(PIECES[kind]["normals"])
    pts = jnp.asarray(pts)

    def f(x, tau, tau2):
        X = x.reshape(n, 3)
        a, b = lin_jnp(kind, X)
        L = (pts @ a.T + b[None, :]).reshape(pts.shape[0], n, k)
        g = L.max(2)                                     # gauges (N, n)
        G = -tau * jax.scipy.special.logsumexp(-g / tau, axis=1)
        return tau2 * jax.scipy.special.logsumexp(G / tau2)

    return jax.jit(jax.value_and_grad(f))


def smooth_opt(vg, x0, schedule):
    x = x0.copy()
    for tau, tau2, iters in schedule:
        def fun(z):
            v, g = vg(z, tau, tau2)
            return float(v), np.asarray(g, dtype=np.float64)
        res = minimize(fun, x, jac=True, method="L-BFGS-B", options=dict(maxiter=iters))
        x = res.x
    return x


# ----------------------------------------------------------------------------
# local polish: sequential minimax over near-active candidates
# ----------------------------------------------------------------------------
def lin_batch(kind, Xb):
    """Xb: (B, n, 3) real or complex -> a (B, m, 2), b (B, m)."""
    P = PIECES[kind]
    phi = np.asarray(P["normals"])
    ang = Xb[:, :, 2:3] + phi[None, None, :]
    ax = np.cos(ang) / P["h"]
    ay = np.sin(ang) / P["h"]
    b = -(ax * Xb[:, :, 0:1] + ay * Xb[:, :, 1:2])
    B = Xb.shape[0]
    return np.stack([ax.reshape(B, -1), ay.reshape(B, -1)], 2), b.reshape(B, -1)


def make_vals(kind, target, n, meta_list):
    """Return f(xb) -> (B, c) candidate values for frozen combinatorics.

    Written with plain numpy ufuncs only, so it accepts complex input and the
    Jacobian can be taken exactly by the complex-step method."""
    k = len(PIECES[kind]["normals"])
    groups = {}
    for typ, idx in meta_list:
        groups.setdefault(typ, []).append(idx)
    G = {t: np.array(v) for t, v in groups.items()}

    def vals(xb):
        Bn = xb.shape[0]
        a, b = lin_batch(kind, xb.reshape(Bn, n, 3))
        ax, ay = a[:, :, 0], a[:, :, 1]
        outs = []
        if "tri" in G:
            A, B_, C = G["tri"][:, 0], G["tri"][:, 1], G["tri"][:, 2]
            M00 = ax[:, A] - ax[:, B_]; M01 = ay[:, A] - ay[:, B_]
            M10 = ax[:, A] - ax[:, C]; M11 = ay[:, A] - ay[:, C]
            r0 = b[:, B_] - b[:, A]; r1 = b[:, C] - b[:, A]
            det = M00 * M11 - M01 * M10
            px = (r0 * M11 - r1 * M01) / det
            py = (M00 * r1 - M10 * r0) / det
            outs.append(ax[:, A] * px + ay[:, A] * py + b[:, A])
        if "edge" in G:
            A, B_, E = G["edge"][:, 0], G["edge"][:, 1], G["edge"][:, 2]
            U = np.array([SQ_EDGES[e][0] for e in E]); W = np.array([SQ_EDGES[e][1] for e in E])
            d0 = ax[:, A] - ax[:, B_]; d1 = ay[:, A] - ay[:, B_]; e_ = b[:, B_] - b[:, A]
            det = d0 * U[:, 1] - d1 * U[:, 0]
            px = (e_ * U[:, 1] - W * d1) / det
            py = (d0 * W - U[:, 0] * e_) / det
            outs.append(ax[:, A] * px + ay[:, A] * py + b[:, A])
        if "corner" in G:
            Q = np.array([SQ_CORNERS[c] for c in G["corner"][:, 0]])
            F_ = G["corner"][:, 1]           # index of active linear function
            outs.append(ax[:, F_] * Q[:, 0] + ay[:, F_] * Q[:, 1] + b[:, F_])
        if "dpair" in G:
            A, B_, S = G["dpair"][:, 0], G["dpair"][:, 1], G["dpair"][:, 2].astype(np.float64)
            d0 = ax[:, A] - ax[:, B_]; d1 = ay[:, A] - ay[:, B_]; e_ = b[:, B_] - b[:, A]
            dd = d0 * d0 + d1 * d1
            disc = np.sqrt(1 - e_ * e_ / dd)
            sd = np.sqrt(dd)
            px = e_ / dd * d0 - S * disc * d1 / sd
            py = e_ / dd * d1 + S * disc * d0 / sd
            outs.append(ax[:, A] * px + ay[:, A] * py + b[:, A])
        if "dsingle" in G:
            I = G["dsingle"][:, 0]
            outs.append(np.sqrt(ax[:, I] ** 2 + ay[:, I] ** 2) + b[:, I])
        return np.concatenate(outs, 1)

    return vals


def jac_cs(vals, x):
    """Exact Jacobian by complex step, batched over all coordinates."""
    d = len(x)
    h = 1e-40
    xb = np.tile(x.astype(np.complex128), (d, 1))
    xb[np.arange(d), np.arange(d)] += 1j * h
    return (vals(xb).imag / h).T                         # (c, d)


def active_set(kind, target, x, n, tol):
    k = len(PIECES[kind]["normals"])
    Fc, pts, meta, g = exact_F(kind, target, x.reshape(n, 3), return_cands=True)
    sel = np.nonzero(g >= Fc - tol)[0]
    a, b = lin_np(kind, x.reshape(n, 3))
    chosen = []
    for j in sel:
        typ, idx = meta[j]
        p = pts[j]
        L = (a @ p + b).reshape(n, k)
        gp = L.max(1)
        if typ in ("tri", "edge", "dpair"):
            fs = idx[:3] if typ == "tri" else idx[:2]
            if any(abs(a[f] @ p + b[f] - gp[f // k]) > 1e-9 for f in fs):
                continue
            if any(abs(gp[f // k] - g[j]) > 1e-9 for f in fs):
                continue
        elif typ == "dsingle":
            f = idx[0]
            if abs(a[f] @ p + b[f] - g[j]) > 1e-9:
                continue
        elif typ == "corner":
            i = int(np.argmin(gp))
            chosen.append(("corner", (idx[0], i * k + int(np.argmax(L[i])))))
            continue
        chosen.append(meta[j])
    return Fc, chosen


def polish(kind, target, X, rounds=200, tol=None, verbose=False):
    n = len(X)
    x = X.ravel().copy()
    step = 0.02
    Fc = exact_F(kind, target, X)
    for it in range(rounds):
        tl = tol if tol is not None else max(5e-3 * Fc, 1e-9)
        Fc, chosen = active_set(kind, target, x, n, max(tl, 50 * step * Fc))
        vals = make_vals(kind, target, n, chosen)
        x0 = x.copy()

        def cons(z):
            return z[-1] - vals(z[None, :-1])[0].real

        def consj(z):
            J = jac_cs(vals, z[:-1])
            return np.hstack([-J, np.ones((J.shape[0], 1))])

        z0 = np.append(x0, Fc)
        bounds = [(v - step, v + step) for v in x0] + [(None, None)]
        try:
            with np.errstate(all="ignore"):
                res = minimize(lambda z: z[-1], z0, jac=lambda z: np.eye(len(z))[-1],
                               method="SLSQP", bounds=bounds,
                               constraints=[dict(type="ineq", fun=cons, jac=consj)],
                               options=dict(maxiter=100, ftol=1e-16))
            xn = res.x[:-1]
            Fn = exact_F(kind, target, xn.reshape(n, 3))
        except Exception as ex:  # degenerate geometry
            if verbose:
                print("slsqp fail", ex)
            Fn = np.inf
        if Fn < Fc - 1e-16:
            x = xn
            if verbose:
                print(f"  polish {it}: 1/F={1/Fn:.13f} step={step:.2e} cons={len(chosen)}")
            step = min(step * 2, 0.05)
        else:
            step *= 0.3
            if step < 1e-11:
                break
    return x.reshape(n, 3), exact_F(kind, target, x.reshape(n, 3))


# ----------------------------------------------------------------------------
# driver
# ----------------------------------------------------------------------------
def random_start(rng, target, n, lam_guess):
    if target == "square":
        c = rng.uniform(-0.5, 0.5, size=(n, 2))
    else:
        r = np.sqrt(rng.uniform(0, 1, n)); th = rng.uniform(0, 2 * math.pi, n)
        c = np.stack([r * np.cos(th), r * np.sin(th)], 1)
    t = rng.uniform(0, 2 * math.pi, size=(n, 1))
    return np.hstack([c, t])


def search(kind, target, n, restarts=50, seed=0, K=48, verbose=True, polish_top=5):
    rng = np.random.default_rng(seed)
    pts = sample_points(target, K)
    vg = make_smooth(kind, n, pts)
    schedule = [(0.05, 0.05, 300), (0.02, 0.02, 300), (0.008, 0.008, 400),
                (0.003, 0.003, 500), (0.001, 0.001, 600)]
    results = []
    t0 = time.time()
    for r in range(restarts):
        X0 = random_start(rng, target, n, None)
        x = smooth_opt(vg, X0.ravel(), schedule)
        X = x.reshape(n, 3)
        F = exact_F(kind, target, X)
        results.append((F, X))
        if verbose:
            best = min(results, key=lambda z: z[0])[0]
            print(f"[{kind}->{target} n={n}] restart {r}: 1/F={1/F:.6f}  best={1/best:.6f}  ({time.time()-t0:.0f}s)", flush=True)
    results.sort(key=lambda z: z[0])
    polished = []
    for F, X in results[:polish_top]:
        Xp, Fp = polish(kind, target, X)
        polished.append((Fp, Xp))
        if verbose:
            print(f"  polished {1/F:.6f} -> {1/Fp:.9f}", flush=True)
    polished.sort(key=lambda z: z[0])
    return polished


if __name__ == "__main__":
    kind, target, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    restarts = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    res = search(kind, target, n, restarts=restarts)
    F, X = res[0]
    print("BEST", 1 / F)
    np.save(f"best_{kind}_{target}_{n}.npy", X)
