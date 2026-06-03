"""Stage 2 map-sampling tests against an in-memory HEALPix map (no download).

Skipped cleanly if healpy (the [maps] extra) is unavailable.
"""

import numpy as np
import pytest

from aramis.data.schema import Sample
from aramis.maps.healpix_sampling import HealpyUnavailable, sample_along_sky
from aramis.maps.profiles import clean_profile, has_signal


def _healpy_or_skip():
    try:
        import healpy as hp  # noqa: F401

        return hp
    except Exception:
        pytest.skip("healpy not installed (pip install -e '.[maps]')")


def test_sample_along_sky_reads_map_values():
    hp = _healpy_or_skip()
    nside = 16
    npix = hp.nside2npix(nside)
    m = np.zeros(npix)
    # Plant a bright pixel at a known direction and sample there.
    ra, dec = 45.0, 10.0
    theta, phi = np.radians(90 - dec), np.radians(ra)
    bright_pix = hp.ang2pix(nside, theta, phi)
    m[bright_pix] = 100.0
    samples = sample_along_sky(m, [(0.5, ra, dec), (0.1, 200.0, -30.0)])
    assert samples[0].intensity == 100.0
    assert samples[1].intensity == 0.0


def test_clean_profile_makes_positive_weights():
    raw = [Sample(s=0.0, intensity=5.0), Sample(s=0.5, intensity=20.0),
           Sample(s=1.0, intensity=4.0)]
    cleaned = clean_profile(raw, background="median")
    assert all(s.intensity >= 0 for s in cleaned)
    # Peak sample retains the most weight.
    assert max(cleaned, key=lambda s: s.intensity).s == 0.5
    assert has_signal(cleaned)


def test_disc_averaging_runs():
    hp = _healpy_or_skip()
    nside = 16
    m = np.arange(hp.nside2npix(nside), dtype=float)
    samples = sample_along_sky(m, [(0.5, 30.0, 0.0)], radius_arcmin=120.0)
    assert np.isfinite(samples[0].intensity)
