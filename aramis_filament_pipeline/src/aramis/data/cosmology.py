"""Cosmology: project sky coordinates + redshift into comoving 3D geometry.

Used to turn (RA, dec, z) endpoints into a real metric axis along which a central
object is located. Requires astropy (the ``[data]`` extra); importing this module is
cheap but the functions raise an informative error if astropy is missing, so the
Stage-0 core never depends on it.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np


class AstropyUnavailable(RuntimeError):
    """Raised when astropy is required but not installed."""


def _require_astropy():
    try:
        import astropy.cosmology as cosmo  # noqa: F401
        import astropy.units as u  # noqa: F401
        from astropy.coordinates import SkyCoord  # noqa: F401

        return cosmo, u, SkyCoord
    except Exception as exc:  # pragma: no cover - exercised only without astropy
        raise AstropyUnavailable(
            "astropy is required for cosmology. Install with: pip install -e '.[data]'"
        ) from exc


def default_cosmology():
    """The default cosmology (Planck18). Override per run for catalog consistency."""
    cosmo, _, _ = _require_astropy()
    return cosmo.Planck18


def comoving_xyz(ra: float, dec: float, z: float, cosmo=None) -> np.ndarray:
    """Comoving Cartesian position (Mpc) for one (RA, dec, z) point."""
    cosmo_mod, u, SkyCoord = _require_astropy()
    if cosmo is None:
        cosmo = cosmo_mod.Planck18
    dist = cosmo.comoving_distance(z).to(u.Mpc).value
    c = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
    x = dist * np.cos(c.dec.radian) * np.cos(c.ra.radian)
    y = dist * np.cos(c.dec.radian) * np.sin(c.ra.radian)
    zc = dist * np.sin(c.dec.radian)
    return np.array([x, y, zc])


def axis_fraction_of_point(
    point: np.ndarray, ep1: np.ndarray, ep2: np.ndarray
) -> float:
    """Fractional projection of ``point`` onto the segment ``ep1 -> ep2`` (clamped)."""
    axis = ep2 - ep1
    denom = float(axis @ axis)
    if denom == 0:
        return 0.5
    t = float((point - ep1) @ axis) / denom
    return min(max(t, 0.0), 1.0)


def sky_samples_along_axis(
    ra1: float, dec1: float, ra2: float, dec2: float, n: int = 32
) -> List[Tuple[float, float, float]]:
    """``n`` great-circle sample points between two sky positions.

    Returns ``(axis_fraction, ra, dec)`` triples for sampling emission maps (Stage 2).
    """
    _, u, SkyCoord = _require_astropy()
    c1 = SkyCoord(ra=ra1 * u.deg, dec=dec1 * u.deg)
    c2 = SkyCoord(ra=ra2 * u.deg, dec=dec2 * u.deg)
    sep = c1.separation(c2)
    out: List[Tuple[float, float, float]] = []
    for i in range(n):
        f = i / (n - 1) if n > 1 else 0.0
        interp = c1.directional_offset_by(c1.position_angle(c2), sep * f)
        out.append((f, float(interp.ra.deg), float(interp.dec.deg)))
    return out
