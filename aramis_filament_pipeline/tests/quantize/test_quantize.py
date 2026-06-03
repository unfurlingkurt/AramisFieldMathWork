from aramis.quantize.project import (
    axis_anchors,
    fraction_to_ratio,
    pair_mass_ratio,
)
from aramis.quantize.scale import ScaleSpec


def test_linear_quantize_roundtrip():
    spec = ScaleSpec(name="t", kind="linear", denom=1000, ref=1.0)
    for v in (0.5, 1.0, 2.0, 7.3):
        r = spec.quantize(v)
        assert abs(spec.inverse(r) - v) < (1.0 / spec.denom) + 1e-9


def test_quantize_is_monotonic():
    spec = ScaleSpec(name="t", kind="linear", denom=1000, ref=1.0)
    assert spec.quantize_int(1.0) < spec.quantize_int(2.0) < spec.quantize_int(5.0)


def test_quantize_floor_on_nonpositive():
    spec = ScaleSpec(name="t", denom=1000, floor=1)
    assert spec.quantize_int(0.0) == 1
    assert spec.quantize_int(-3.0) == 1


def test_pair_mass_ratio_reflects_asymmetry():
    spec = ScaleSpec(name="t", kind="linear", denom=1000, ref=1.0)
    sym = pair_mass_ratio(1.0, 1.0, spec)
    skew = pair_mass_ratio(8.0, 1.0, spec)
    assert sym.axis_fraction() == 0.5
    assert skew.axis_fraction() > 0.5


def test_fraction_to_ratio_inverts_axis_fraction():
    for s in (0.2, 0.5, 0.75):
        r = fraction_to_ratio(s, denom=1000)
        assert abs(r.axis_fraction() - s) < 1e-3


def test_axis_anchors_bracket():
    spec = ScaleSpec(name="t", kind="linear", denom=1000, ref=1.0)
    mr = pair_mass_ratio(3.0, 1.0, spec)
    left, right = axis_anchors(mr)
    assert left.axis_fraction() != right.axis_fraction()
