"""Assert the native Ratio agrees with the repo's canonical Rational.

Skips cleanly if the canonical module (which imports matplotlib) is unavailable.
"""

import random

import pytest

from aramis.geometry.canonical_bridge import (
    CanonicalUnavailable,
    assert_cf_agrees,
    assert_mediant_agrees,
    load_canonical_rational,
)
from aramis.geometry.ratio import Ratio


@pytest.fixture(scope="module")
def Rational():
    try:
        return load_canonical_rational()
    except CanonicalUnavailable as exc:
        pytest.skip(f"canonical Rational unavailable: {exc}")


def test_mediant_agrees_with_canonical(Rational):
    rng = random.Random(0)
    for _ in range(2000):
        a = Ratio(rng.randint(0, 50), rng.randint(1, 50))
        b = Ratio(rng.randint(0, 50), rng.randint(1, 50))
        assert_mediant_agrees(a, b, Rational)


def test_continued_fraction_agrees_with_canonical(Rational):
    rng = random.Random(1)
    for _ in range(2000):
        r = Ratio(rng.randint(0, 200), rng.randint(1, 200))
        assert_cf_agrees(r, Rational)
