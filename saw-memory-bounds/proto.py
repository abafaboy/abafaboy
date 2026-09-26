import sys, time
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigs

STEPS = [(1,0),(-1,0),(0,1),(0,-1)]
SYMS = [lambda x,y:(x,y), lambda x,y:(-x,y), lambda x,y:(x,-y), lambda x,y:(-x,-y),
        lambda x,y:(y,x), lambda x,y:(-y,x), lambda x,y:(y,-x), lambda x,y:(-y,-x)]

def norm(entries):
    out = []
    for (x,y),r in entries:
        d = abs(x)+abs(y)
        if d <= r:
            r -= (r-d) & 1
            out.append(((x,y),r))
    return out

def canon(entries):
    best = None
    for f in SYMS:
        t = tuple(sorted((f(x,y),r) for (x,y),r in entries))
        if best is None or t < best: best = t
    return best

def build(m):
    start = canon([])
    idx = {start: 0}; states=[start]; rows=[]; cols=[]
    q = 0
    while q < len(states):
        S = states[q]
        occ = {p:r for p,r in S}
        for s in STEPS:
            if s in occ and occ[s] >= 1: continue
            new = [((x-s[0],y-s[1]), r-1) for (x,y),r in S] + [((-s[0],-s[1]), m-1)]
            T = canon(norm(new))
            if T not in idx:
                idx[T] = len(states); states.append(T)
            rows.append(q); cols.append(idx[T])
        q += 1
    n = len(states)
    A = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n,n))
    return A, n

for m in range(int(sys.argv[2]) if len(sys.argv)>2 else 2, int(sys.argv[1])+1, 2):
    t=time.time()
    A,n = build(m)
    # power iteration
    v = np.ones(n)
    lam=0
    for it in range(3000):
        w = A @ v
        lam_new = w.sum()/v.sum()
        v = w / w.max()
        if abs(lam_new-lam) < 1e-13: break
        lam = lam_new
    print(f"m={m:2d} states={n:9d} lambda={lam_new:.9f}  ({time.time()-t:.1f}s)", flush=True)
