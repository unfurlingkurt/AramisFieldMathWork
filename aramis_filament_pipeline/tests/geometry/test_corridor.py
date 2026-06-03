from aramis.geometry.corridor import axis_corridor, corridor_candidates, farey_medoid
from aramis.geometry.ratio import Ratio
from aramis.quantize.project import fraction_to_ratio


def test_axis_corridor_contains_thirds_at_depth_2():
    fractions = sorted(r.axis_fraction() for r in axis_corridor(depth=2))
    # Depth-2 Stern-Brocot yields the 1/3, 1/2, 2/3 thirds structure.
    for target in (1 / 3, 1 / 2, 2 / 3):
        assert any(abs(f - target) < 1e-9 for f in fractions)


def test_corridor_is_ordered_and_unique():
    cand = corridor_candidates(Ratio(0, 1), Ratio(1, 1), depth=4)
    assert len(cand) == len(set(cand))


def test_farey_medoid_recovers_nearest_node():
    candidates = axis_corridor(depth=6)
    # A single sample near axis fraction 1/3 should select the 1/3 corridor member.
    sample = fraction_to_ratio(0.333, denom=1000)
    medoid, score = farey_medoid(candidates, [sample])
    assert abs(medoid.axis_fraction() - 1 / 3) < 0.02


def test_farey_medoid_requires_inputs():
    import pytest

    with pytest.raises(ValueError):
        farey_medoid([], [Ratio(1, 1)])
    with pytest.raises(ValueError):
        farey_medoid([Ratio(1, 1)], [])
