"""Automaton: remember visited sites within L1 distance R of the endpoint (any age).
Optionally also drop sites older than T steps (T=None: no age limit)."""
import sys, time
import numpy as np
from scipy.sparse import csr_matrix

STEPS = [(1,0),(-1,0),(0,1),(0,-1)]
SYMS = [lambda x,y:(x,y), lambda x,y:(-x,y), lambda x,y:(x,-y), lambda x,y:(-x,-y),
        lambda x,y:(y,x), lambda x,y:(-y,x), lambda x,y:(y,-x), lambda x,y:(-y,-x)]

def canon(S):
    return min(tuple(sorted(f(x,y) for x,y in S)) for f in SYMS)

def build(R):
    start = canon([])
    idx = {start:0}; states=[start]; rows=[]; cols=[]
    q=0
    while q < len(states):
        S = states[q]; occ=set(S)
        for s in STEPS:
            if s in occ: continue
            new = [(x-s[0],y-s[1]) for x,y in S] + [(-s[0],-s[1])]
            new = [(x,y) for x,y in new if abs(x)+abs(y) <= R]
            T = canon(new)
            if T not in idx:
                idx[T]=len(states); states.append(T)
            rows.append(q); cols.append(idx[T])
        q+=1
        if len(states) > 3_000_000: return None, len(states)
    n=len(states)
    return csr_matrix((np.ones(len(rows)),(rows,cols)),shape=(n,n)), n

for R in range(1, int(sys.argv[1])+1):
    t=time.time(); A,n = build(R)
    if A is None: print(f"R={R}: >{n} states, stop"); break
    v=np.ones(n); lam=0
    for it in range(5000):
        w=A@v; ln=w.sum()/v.sum(); v=w/w.max()
        if abs(ln-lam)<1e-13: break
        lam=ln
    print(f"R={R} states={n:9d} lambda={ln:.9f} ({time.time()-t:.1f}s)", flush=True)
