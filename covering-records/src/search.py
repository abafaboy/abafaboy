"""Parallel multi-start + basin-hopping search.

usage: python search.py KIND TARGET N [--restarts R] [--hops H] [--workers W]
Writes the best configuration found to ../results/raw/KIND_TARGET_N.json
(only if it beats what is already stored there).
"""
import argparse
import json
import os
import sys
import time

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1")

import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "results", "raw")


def worker(args):
    kind, target, n, seed, restarts, hops = args
    import opt
    from records import RECORDS
    rng = np.random.default_rng(seed)
    pts = opt.sample_points(target, 48)
    vg = opt.make_smooth(kind, n, pts)
    sched = [(0.05, 0.05, 300), (0.02, 0.02, 300), (0.008, 0.008, 400),
             (0.003, 0.003, 500), (0.001, 0.001, 600)]
    pool = []
    for r in range(restarts):
        X0 = opt.random_start(rng, target, n, None)
        try:
            x = opt.smooth_opt(vg, X0.ravel(), sched)
            X, F = opt.polish(kind, target, x.reshape(n, 3))
        except Exception:
            continue
        pool.append((F, X))
    pool.sort(key=lambda z: z[0])
    pool = pool[:4]
    # basin hopping on the best few
    for h in range(hops):
        F0, X0 = pool[rng.integers(len(pool))] if rng.random() < 0.3 else pool[0]
        X = X0.copy()
        mode = rng.integers(3)
        if mode == 0:       # jiggle everything
            X[:, :2] += rng.normal(0, rng.choice([0.01, 0.03, 0.08]), size=(n, 2))
            X[:, 2] += rng.normal(0, rng.choice([0.03, 0.1, 0.3]), size=n)
        elif mode == 1:     # relocate one or two pieces
            for i in rng.choice(n, size=min(n, rng.integers(1, 3)), replace=False):
                X[i] = opt.random_start(rng, target, 1, None)[0]
        else:               # rotate a few pieces by a symmetry-breaking amount
            for i in rng.choice(n, size=min(n, rng.integers(1, 4)), replace=False):
                X[i, 2] += rng.uniform(-0.6, 0.6)
                X[i, :2] += rng.normal(0, 0.05, 2)
        try:
            if mode == 1:
                x = opt.smooth_opt(vg, X.ravel(), sched[2:])
                X = x.reshape(n, 3)
            Xp, Fp = opt.polish(kind, target, X)
        except Exception:
            continue
        if Fp < pool[-1][0] - 1e-12:
            pool.append((Fp, Xp))
            pool.sort(key=lambda z: z[0])
            # drop near-duplicates by value
            ded = []
            for F, Xc in pool:
                if not ded or abs(F - ded[-1][0]) > 1e-10:
                    ded.append((F, Xc))
            pool = ded[:4]
    return [(float(F), X.tolist()) for F, X in pool]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind"); ap.add_argument("target"); ap.add_argument("n", type=int)
    ap.add_argument("--restarts", type=int, default=12)
    ap.add_argument("--hops", type=int, default=150)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    from records import RECORDS
    from multiprocessing import Pool
    t0 = time.time()
    jobs = [(a.kind, a.target, a.n, a.seed * 1000 + w, a.restarts, a.hops) for w in range(a.workers)]
    with Pool(a.workers) as p:
        outs = p.map(worker, jobs)
    allres = sorted([r for o in outs for r in o], key=lambda z: z[0])
    F, X = allres[0]
    from records import beats
    rec = RECORDS[(a.kind, a.target)][a.n][0]
    val = 1 / F
    better, bar = beats(a.kind, a.target, a.n, val)
    print(f"{a.kind}->{a.target} n={a.n}: found {val:.10f}  record {rec:.6f} (bar {bar:.6f})  "
          f"{'IMPROVED' if better else ''}  ({time.time()-t0:.0f}s)", flush=True)
    os.makedirs(RAW, exist_ok=True)
    path = os.path.join(RAW, f"{a.kind}_{a.target}_{a.n}.json")
    old = json.load(open(path)) if os.path.exists(path) else None
    if old is None or val > old["value"] + 1e-13:
        json.dump(dict(kind=a.kind, target=a.target, n=a.n, value=val, F=F, X=X,
                       note="target normalised to size 1; pieces have side F"), open(path, "w"), indent=1)


if __name__ == "__main__":
    main()
