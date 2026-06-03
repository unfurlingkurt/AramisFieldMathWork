import random

from aramis.geometry.metric import (
    axiom_report,
    tension_additive,
    tension_multiplicative,
)
from aramis.geometry.ratio import Ratio


def _sample_ratios(n=12, seed=0):
    rng = random.Random(seed)
    return [Ratio(rng.randint(1, 12), rng.randint(1, 12)) for _ in range(n)]


def test_normalized_self_distance_is_zero():
    pts = _sample_ratios()
    for r in pts:
        assert tension_additive(r, r) == 0
        assert tension_multiplicative(r, r) == 0


def test_raw_self_tension_wart_is_pinned():
    # Regression guard: the *raw* cf_length self-value is 1, not 0 — which is
    # exactly why the public metrics normalize. If this ever changes, the
    # normalization rationale must be revisited.
    assert Ratio(1, 1).cf_length() == 1          # raw multiplicative self-value
    assert Ratio(0, 1).cf_length() == 1          # raw additive self-value (diff == 0)


def test_axioms_hold_for_default_metric():
    report = axiom_report(tension_additive, _sample_ratios(n=10, seed=1))
    assert report["identity"]
    assert report["symmetry"]
    assert report["non_negative"]


def test_multiplicative_is_quasimetric_not_symmetric():
    # compose(a,b) and compose(b,a) are reciprocals, so CF length can differ by one.
    # The multiplicative tension is therefore a *quasi*-metric, not symmetric. This
    # is a genuine property of the native geometry, documented here so the additive
    # metric remains the symmetric default.
    a, b = Ratio(2, 1), Ratio(1, 1)
    assert tension_multiplicative(a, b) != tension_multiplicative(b, a)


def test_additive_is_symmetric():
    pts = _sample_ratios(seed=2)
    for a in pts:
        for b in pts:
            assert tension_additive(a, b) == tension_additive(b, a)
