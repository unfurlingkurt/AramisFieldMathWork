import random

import pytest

from aramis.geometry.ratio import Ratio


def test_reduction_and_sign():
    assert (Ratio(2, 4).p, Ratio(2, 4).q) == (1, 2)
    r = Ratio(1, -2)
    assert (r.p, r.q) == (-1, 2)  # denominator kept positive


def test_zero_zero_rejected():
    with pytest.raises(ValueError):
        Ratio(0, 0)


def test_infinity_anchor():
    inf = Ratio(1, 0)
    assert inf.is_infinite()
    assert Ratio(5, 0) == inf  # any q==0 canonicalizes to 1:0
    assert inf.as_float() == float("inf")
    assert inf.axis_fraction() == 1.0


def test_mediant():
    assert Ratio(0, 1).mediant(Ratio(1, 0)) == Ratio(1, 1)
    assert Ratio(0, 1).mediant(Ratio(1, 1)) == Ratio(1, 2)


def test_compose_is_quotient_with_right_identity():
    # compose(a, b) == a_val / b_val as a ratio; right identity 1:1; NOT associative.
    identity = Ratio(1, 1)
    rng = random.Random(0)
    pts = [Ratio(rng.randint(1, 9), rng.randint(1, 9)) for _ in range(8)]
    for a in pts:
        assert a.compose(identity) == a
        for b in pts:
            assert abs(a.compose(b).as_float() - a.as_float() / b.as_float()) < 1e-9
    # Demonstrate non-associativity explicitly (it is division).
    a, b, c = Ratio(2, 1), Ratio(3, 1), Ratio(5, 1)
    assert a.compose(b).compose(c) != a.compose(b.compose(c))


def test_continued_fraction():
    # 7/3 = 2 + 1/(3) -> [2, 3]
    assert Ratio(7, 3).cf() == (2, 3)
    assert Ratio(1, 1).cf_length() == 1
    assert Ratio(0, 1).cf_length() == 1


def test_axis_fraction_corresponds_to_value():
    # A ratio at axis fraction s has value s/(1-s); check the mapping is consistent.
    r = Ratio(1, 2)  # value 0.5, axis fraction 1/3
    assert abs(r.axis_fraction() - 1 / 3) < 1e-9
    assert abs(r.as_float() - 0.5) < 1e-9
