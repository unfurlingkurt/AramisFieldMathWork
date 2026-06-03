import numpy as np

from aramis.data.loaders.synthetic import make_synthetic
from aramis.stats.bootstrap import bootstrap_ci, cohen_d, permutation_p_value
from aramis.stats.nulls import (
    null_random_sky_pairs,
    null_rotated_axes,
    null_same_mass_controls,
    null_shuffled_masses,
    observed_center_emission,
    run_null_battery,
)
from aramis.systems import EuclideanMidpoint, FareyMedoid, ForceBalancePoint


def test_same_mass_control_collapses_force_balance():
    fils = make_synthetic(n=10, seed=1)
    controlled = null_same_mass_controls(fils)
    fb = ForceBalancePoint()
    assert all(abs(fb.locate(f).t - 0.5) < 1e-9 for f in controlled)


def test_shuffled_masses_preserves_mass_multiset():
    fils = make_synthetic(n=15, seed=2)
    shuffled = null_shuffled_masses(fils, seed=0)
    before = sorted([f.mass1 for f in fils] + [f.mass2 for f in fils])
    after = sorted([f.mass1 for f in shuffled] + [f.mass2 for f in shuffled])
    assert np.allclose(before, after)


def test_random_sky_pairs_preserves_count():
    fils = make_synthetic(n=12, seed=3)
    assert len(null_random_sky_pairs(fils, seed=0)) == len(fils)


def test_rotated_axes_changes_sample_positions():
    fils = make_synthetic(n=5, seed=4)
    rotated = null_rotated_axes(fils, seed=0)
    orig = [s.s for s in fils[0].samples]
    new = [s.s for s in rotated[0].samples]
    assert orig != new


def test_emission_center_tracks_peak():
    fils = make_synthetic(n=8, seed=5)
    for f in fils:
        # intensity-weighted center should be near the planted peak
        assert abs(observed_center_emission(f) - f.meta["planted_center"]) < 0.1


def test_battery_structure_and_rotated_null_kills_signal():
    fils = make_synthetic(n=40, seed=0)
    result = run_null_battery(
        fils, FareyMedoid(), EuclideanMidpoint(), n_null=15, seed=0
    )
    assert result["improvement_mean"] > 0  # medoid closer than midpoint on real signal
    assert "shuffled_masses" in result["nulls"]
    assert "same_mass_control" in result["nulls"]
    # Scrambling the emission axis should erase the medoid's advantage.
    rotated = null_rotated_axes(fils, seed=1)
    rot_med = np.mean([abs(FareyMedoid().locate(f).t - f.meta["planted_center"]) for f in rotated])
    real_med = result["medoid_mean_err"]
    assert rot_med > real_med


def test_bootstrap_and_effect_size():
    rng = np.random.default_rng(0)
    a = rng.normal(1.0, 0.1, 200)
    b = rng.normal(0.0, 0.1, 200)
    lo, mid, hi = bootstrap_ci(a - b, seed=0)
    assert lo < mid < hi
    assert cohen_d(a, b) > 2.0
    assert 0.0 <= permutation_p_value(0.5, [0.0, 0.1, 0.2]) <= 1.0
