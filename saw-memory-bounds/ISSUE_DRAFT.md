Draft issue for https://github.com/teorth/optimizationproblems (not posted).

---

**38a: best rigorous upper bound is 2.662343 (Couronnée 2022), not 2.679193**

The upper-bound table for the square-lattice SAW connective constant
(constants/38a.md) ends at 2.679193, attributed to Pönitz–Tittmann (2000) via
[FV2017]. A later preprint improves this:

- O. Couronnée, *New upper bound for the connective constant for square-lattice
  self-avoiding walks*, [arXiv:2211.16146](https://arxiv.org/abs/2211.16146)
  (Nov 2022). It modifies the Pönitz–Tittmann automaton, allowing several ways
  to shorten states that grow too large, and treats loops up to length 26. It
  reports μ(ℤ²) < 2.662342426.

As a side check, an independent implementation of the plain memory-22 automaton
gives λ₂₂ = 2.679192649, matching the Pönitz–Tittmann value
2.679192495 to about 1.5·10⁻⁷. Code:
https://github.com/abafaboy/abafaboy/tree/claude/new-session-nd3rcp/saw-memory-bounds

Couronnée's bound was not re-derived here: that paper could not be read from our
environment. It would need the usual verification before being marked as
confirmed.
