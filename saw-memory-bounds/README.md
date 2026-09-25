# saw-memory-bounds

**Rigorous upper bounds on the square-lattice self-avoiding walk (SAW) connective
constant μ ≈ 2.63816, from finite-memory walks.** This folder records an attempt that
did **not** beat the best known bound. It is kept because it reproduces a published
number independently, and because the numbers and failed variants may save
someone time.

## Background

Every self-avoiding walk is also a *memory-m walk*: a walk with no loop of length
≤ m. The growth rate λ_m of memory-m walks is the Perron root of a finite automaton,
so μ ≤ λ_m for every m. Known rigorous upper bounds on μ(ℤ²):

| bound | source | method |
|---|---|---|
| 2.69576 | Alm (1993) | transfer matrices between SAW windows |
| 2.6939 | Noonan (1998) | Goulden–Jackson cluster method |
| 2.679192495 | Pönitz & Tittmann (2000) | automata for walks without loops of length ≤ 22 |
| **2.662343** | Couronnée (2022), [arXiv:2211.16146](https://arxiv.org/abs/2211.16146) | modified Pönitz–Tittmann automaton with several ways to shorten large states, loops up to 26 |

Note: [Tao's optimization-constants repository](https://teorth.github.io/optimizationproblems/constants/38a.html)
(checked 25 Sep 2026) lists 2.679193 as the best upper bound. It does not yet include
Couronnée's 2.662343.

## What was computed here

`mem.cpp` builds the memory-m automaton directly. A state is the set of past sites
relative to the endpoint, each with the number of steps for which it is still
forbidden. Sites that are too far away to be reached in that time are dropped, and
the lifetime is reduced to the parity of the distance. States are reduced by the 8
lattice symmetries. Power iteration gives Collatz–Wielandt bounds, min_i (Av)_i/v_i ≤
λ ≤ max_i (Av)_i/v_i, and the table gives both ends.

| m | states (÷ symmetry) | λ_m (upper end of the bracket) |
|---|---|---|
| 12 | 1,907 | 2.711252339 |
| 14 | 10,397 | 2.701374268 |
| 16 | 58,411 | 2.693848922 |
| 18 | 336,168 | 2.687924410 |
| 20 | 1,973,511 | 2.683138866 |
| 22 | 11,778,632 | **2.679192649** |

λ₂₂ agrees with Pönitz–Tittmann's 2.679192495 to 1.5·10⁻⁷, an independent
reproduction of their bound. We do not know where the last digits differ; it may be
a small difference in the automaton. Build and run with
`g++ -O3 -march=native -fopenmp -o mem mem.cpp && ./mem 22` (about 90 s and 2 GB).

## Why this does not beat 2.662343

The data fit λ_m − μ ≈ C·m^(−0.96) very closely. The fit predicts λ₂₆ ≈ 2.673, and it
would take m ≈ 40 to reach 2.662. The automaton grows by about 5.6× for every
increase of m by 2, so m = 40 would need around 10¹³ states. Plain memory-m cannot
compete with Couronnée's automaton.

Three alternative automata were tried. Each remembers a different subset of the past;
any such subset gives a valid upper bound. At equal state counts, none beat plain
time-memory:

| variant | file | result |
|---|---|---|
| remember every visited site within L1 radius R | `radius.py` | R=6: 1.37M states, λ=2.68978 (memory-20: 1.97M states, λ=2.68314) |
| remember the K visited sites nearest the endpoint | `nearestk.py` | K=12: 431k states, λ=2.69060 (worse than memory at the same size) |
| memory-m, plus keep old sites while they stay within distance D | `memd.cpp` | small gain in λ, but it costs more states than simply raising m |
| memory-m, plus reject moves that seal the walk into a pocket (valid because *endless* walks also grow at rate μ) | `memt.cpp` | λ₂₀ drops only from 2.683139 to 2.683038 |

We could not access Couronnée's paper from this environment, so his automaton was
not reimplemented. Doing that, then extending it to longer loops, is the natural next
step.
