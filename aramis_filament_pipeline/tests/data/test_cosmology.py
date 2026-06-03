"""Cosmology tests — skipped cleanly if astropy (the [data] extra) is absent."""

import numpy as np
import pytest

from aramis.data.cosmology import (
    AstropyUnavailable,
    axis_fraction_of_point,
    comoving_xyz,
)


def _astropy_or_skip():
    try:
        comoving_xyz(0.0, 0.0, 0.1)
    except AstropyUnavailable:
        pytest.skip("astropy not installed (pip install -e '.[data]')")


def test_comoving_distance_monotonic_in_redshift():
    _astropy_or_skip()
    r1 = np.linalg.norm(comoving_xyz(10.0, 5.0, 0.1))
    r2 = np.linalg.norm(comoving_xyz(10.0, 5.0, 0.3))
    assert r2 > r1 > 0


def test_axis_fraction_projection():
    ep1 = np.array([0.0, 0.0, 0.0])
    ep2 = np.array([10.0, 0.0, 0.0])
    assert abs(axis_fraction_of_point(np.array([3.0, 1.0, 0.0]), ep1, ep2) - 0.3) < 1e-9
    # Clamped to [0, 1].
    assert axis_fraction_of_point(np.array([-5.0, 0.0, 0.0]), ep1, ep2) == 0.0
    assert axis_fraction_of_point(np.array([50.0, 0.0, 0.0]), ep1, ep2) == 1.0
