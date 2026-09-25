"""Tests for the exact verifier: arithmetic, known coverings, negative controls.

run: python -m pytest tests   (or: python tests/test_verify.py)
"""
import glob
import json
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

import verify  # noqa: E402
from verify import K  # noqa: E402

CERTS = sorted(glob.glob(os.path.join(HERE, "..", "certificates", "*.json")))
quiet = dict(log=lambda *a: None)


def test_sign_in_q_sqrt3():
    assert K(2, -1).sign() == 1          # 2 - sqrt3 > 0
    assert K(1, -1).sign() == -1         # 1 - sqrt3 < 0
    assert K(-7, 4).sign() == -1         # -7 + 4 sqrt3 = -0.0718 < 0
    assert K(-6, 4).sign() == 1          # -6 + 4 sqrt3 = 0.928 > 0
    assert K(0, 0).sign() == 0
    x = K(Fraction(3, 7), Fraction(-2, 5))
    assert (x * x.inv() - 1).sign() == 0


def test_unit_pieces():
    for kind in ("sq", "tri"):
        v = verify.piece_vertices(kind, Fraction(1, 3), Fraction(-2, 9), Fraction(5, 17))
        assert all(d == K(1) for d in verify.side_lengths_sq(v))


def _trivial(kind, target, size, pieces):
    return dict(kind=kind, target=target, n=len(pieces), size=str(size),
                pieces=[dict(x=str(x), y=str(y), t=str(t)) for x, y, t in pieces])


def test_known_exact_coverings():
    # one unit square covers the disk of radius 1/2 (touching), not radius 1/2 + tiny
    assert verify.verify(_trivial("sq", "disk", Fraction(1, 2), [(0, 0, 0)]), **quiet)
    assert not verify.verify(_trivial("sq", "disk", Fraction(1, 2) + Fraction(1, 10**12), [(0, 0, 0)]), **quiet)
    # four unit squares in a 2x2 block cover the disk of radius 1 exactly
    block = [(Fraction(a, 2), Fraction(b, 2), 0) for a in (-1, 1) for b in (-1, 1)]
    assert verify.verify(_trivial("sq", "disk", 1, block), **quiet)
    assert not verify.verify(_trivial("sq", "disk", 1 + Fraction(1, 10**12), block), **quiet)
    # the 2x2 block also covers the square of side 2 but not side 2 + tiny
    assert verify.verify(_trivial("sq", "square", 2, block), **quiet)
    assert not verify.verify(_trivial("sq", "square", 2 + Fraction(1, 10**12), block), **quiet)
    # a gap between two squares is found
    apart = [(Fraction(-1, 2) - Fraction(1, 10**9), 0, 0), (Fraction(1, 2), 0, 0)]
    assert not verify.verify(_trivial("sq", "square", Fraction(1, 2), apart), **quiet)


def test_rejects_bad_input():
    one = [(0, 0, 0)]
    assert not verify.verify(_trivial("sq", "disk", -1, one), **quiet)          # negative size
    assert not verify.verify(_trivial("sq", "square", 0, one), **quiet)         # zero size
    assert not verify.verify(_trivial("sq", "disk", Fraction(1, 4), []), **quiet)  # no pieces
    bad = _trivial("sq", "disk", Fraction(1, 4), one); bad["n"] = 7
    assert not verify.verify(bad, **quiet)                                      # n mismatch


def test_certificates_pass_and_controls_fail():
    assert CERTS, "no certificates found"
    for path in CERTS:
        cert = json.load(open(path))
        assert verify.verify(cert, **quiet), path
        bad = dict(cert, size=str(Fraction(cert["size"]) * Fraction(1000001, 1000000)))
        assert not verify.verify(bad, **quiet), path + " (enlarged target must fail)"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
