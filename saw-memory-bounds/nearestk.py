"""Automaton: remember the K visited sites nearest the endpoint (L1), any age.
Also drop sites farther than RMAX. Compare growth vs states with memory-m."""
import sys, time
import numpy as np
from scipy.sparse import csr_matrix
STEPS=[(1,0),(-1,0),(0,1),(0,-1)]
SYMS=[lambda x,y:(x,y),lambda x,y:(-x,y),lambda x,y:(x,-y),lambda x,y:(-x,-y),
      lambda x,y:(y,x),lambda x,y:(-y,x),lambda x,y:(y,-x),lambda x,y:(-y,-x)]
def canon(S): return min(tuple(sorted(f(x,y) for x,y in S)) for f in SYMS)
def shrink(S,K,RMAX):
    S=[p for p in S if abs(p[0])+abs(p[1])<=RMAX]
    if len(S)>K:
        S=sorted(S,key=lambda p:(abs(p[0])+abs(p[1]),p))[:K]
    return S
def build(K,RMAX,cap=2_500_000):
    start=canon([]); idx={start:0}; states=[start]; rows=[]; cols=[]; q=0
    while q<len(states):
        S=states[q]; occ=set(S)
        for s in STEPS:
            if s in occ: continue
            new=[(x-s[0],y-s[1]) for x,y in S]+[(-s[0],-s[1])]
            T=canon(shrink(new,K,RMAX))
            if T not in idx:
                idx[T]=len(states); states.append(T)
            rows.append(q); cols.append(idx[T])
        q+=1
        if len(states)>cap: return None,len(states)
    n=len(states); return csr_matrix((np.ones(len(rows)),(rows,cols)),shape=(n,n)),n
def lam(A,n):
    v=np.ones(n); l=0
    for it in range(20000):
        w=A@v; ln=w.sum()/v.sum(); v=w/w.max()
        if abs(ln-l)<1e-12: break
        l=ln
    return ln
RMAX=int(sys.argv[1])
for K in range(4, 40, 2):
    t=time.time(); A,n=build(K,RMAX)
    if A is None: print(f"RMAX={RMAX} K={K}: >{n} states"); break
    print(f"RMAX={RMAX} K={K:2d} states={n:8d} lambda={lam(A,n):.9f} ({time.time()-t:.0f}s)",flush=True)
