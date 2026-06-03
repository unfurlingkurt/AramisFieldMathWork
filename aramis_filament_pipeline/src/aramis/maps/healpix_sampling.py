"""Sample HEALPix emission maps along filament axes (Stage 2).

Turns real sky maps (ROSAT X-ray, GLEAM radio, Planck-y SZ) into the emission
samples the Farey medoid consumes. ``healpy`` is the optional ``[maps]`` extra, so
this module imports lazily and the Stage-0/1 core never depends on it.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Tuple

import numpy as np

from ..data.schema import Sample


class HealpyUnavailable(RuntimeError):
    """Raised when healpy is required but not installed."""


def _require_healpy():
    try:
        import healpy as hp  # noqa: F401

        return hp
    except Exception as exc:  # pragma: no cover - only without healpy
        raise HealpyUnavailable(
            "healpy is required for map sampling. Install with: pip install -e '.[maps]'"
        ) from exc


def load_healpix_map(path: str | Path):
    """Read a HEALPix map; returns ``(map_array, nside)``."""
    hp = _require_healpy()
    m = hp.read_map(str(path))
    return m, hp.get_nside(m)


def sample_along_sky(
    map_array: np.ndarray,
    sky_points: Sequence[Tuple[float, float, float]],
    radius_arcmin: float | None = None,
) -> List[Sample]:
    """Sample ``map_array`` at each ``(axis_fraction, ra, dec)`` sky point.

    If ``radius_arcmin`` is given, average the map over a disc of that radius around
    each point (robust to pixel noise); otherwise read the nearest pixel.
    """
    hp = _require_healpy()
    nside = hp.get_nside(map_array)
    out: List[Sample] = []
    for frac, ra, dec in sky_points:
        theta = np.radians(90.0 - dec)
        phi = np.radians(ra)
        if radius_arcmin:
            vec = hp.ang2vec(theta, phi)
            pix = hp.query_disc(nside, vec, np.radians(radius_arcmin / 60.0))
            value = float(np.mean(map_array[pix])) if len(pix) else float("nan")
        else:
            value = float(map_array[hp.ang2pix(nside, theta, phi)])
        out.append(Sample(s=float(frac), intensity=value, ra=float(ra), dec=float(dec)))
    return out
