"""Tempel et al. (2014) SDSS Bisous filament catalogue loader (PRIMARY catalog).

Reference: Tempel, Stoica, Martinez, et al., "Detecting filamentary pattern in the
cosmic web: a catalogue of filaments for the SDSS", MNRAS 438, 3465 (2014).
VizieR: J/MNRAS/438/3465. Tables: http://www.aai.ee/~elmo/sdss-filaments
Catalogue cosmology: H0 = 100 h km/s/Mpc, Omega_m = 0.27, Omega_Lambda = 0.73.

The published catalogue gives filament *spine points* (position + direction) plus the
galaxies each filament contains. For this pipeline we need endpoint pairs with mass
proxies. The expected reduced input is a per-filament table whose two ends are the
extreme spine points and whose mass proxies are the summed/representative endpoint
galaxy luminosities or group masses. Reduction from the raw spine files is documented
in ``data/MANIFEST.toml``; once reduced, point this loader at the resulting table.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from ..schema import Endpoint, Filament
from .tabular import ColumnMap, load_pairs_csv, load_pairs_fits

# Default mapping for a reduced Tempel endpoint-pair table. Override if your reduction
# uses different column names.
TEMPEL_COLUMNS = ColumnMap(
    columns={
        "id": "fil_id",
        "ra1": "ra_start", "dec1": "dec_start", "z1": "z_start", "mass1": "mass_start",
        "ra2": "ra_end", "dec2": "dec_end", "z2": "z_end", "mass2": "mass_end",
    },
    provenance="Tempel+2014 SDSS Bisous (J/MNRAS/438/3465)",
)


def load_filaments(path: str | Path, columns: ColumnMap | None = None) -> List[Filament]:
    """Load a reduced Tempel/Bisous endpoint-pair table (CSV or FITS)."""
    path = Path(path)
    cm = columns or TEMPEL_COLUMNS
    if path.suffix.lower() in (".fits", ".fit", ".fits.gz"):
        return load_pairs_fits(path, cm)
    return load_pairs_csv(path, cm)


def load_dr8_fits(
    path: str | Path,
    mass_proxy: str = "lum",
    with_skycoords: bool = True,
) -> List[Filament]:
    """Load the published ``dr8_filaments.fits`` directly (no manual reduction).

    The catalogue row gives, per filament, a comoving bounding box
    (``xmin,ymin,zmin`` + ``xlen,ylen,zlen``, Mpc/h) and endpoint proxies
    (``lum1/lum2`` luminosity, ``ngal1/ngal2`` galaxy counts). Endpoints are taken as
    the two extreme box corners; the mass proxy is ``lum`` (default) or ``ngal``.

    Caveats (documented honestly): (1) box corners approximate the true curved-spine
    endpoints; (2) the catalogue does not state which corner carries ``lum1`` vs
    ``lum2`` — we assign min-corner=end1, max-corner=end2, which only mirrors the
    mass-fraction distribution. Sky coordinates use the catalogue cosmology
    (FlatLambdaCDM H0=100, Om0=0.27).
    """
    try:
        import numpy as np
        from astropy.table import Table
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("astropy required: pip install -e '.[data]'") from exc

    t = Table.read(str(path), hdu=1)
    p1 = mass_proxy + "1"
    p2 = mass_proxy + "2"

    xyz1 = np.stack([t["xmin"], t["ymin"], t["zmin"]], axis=1).astype(float)
    xyz2 = xyz1 + np.stack([t["xlen"], t["ylen"], t["zlen"]], axis=1).astype(float)

    if with_skycoords:
        ra1, dec1, z1 = _xyz_to_radecz(xyz1)
        ra2, dec2, z2 = _xyz_to_radecz(xyz2)
    else:
        zeros = np.zeros(len(t))
        ra1 = dec1 = z1 = ra2 = dec2 = z2 = zeros

    out: List[Filament] = []
    for i in range(len(t)):
        fid = str(int(t["id"][i]))
        ep1 = Endpoint(id=f"{fid}_1", ra=float(ra1[i]), dec=float(dec1[i]),
                       z=float(z1[i]), mass_proxy=float(t[p1][i]))
        ep2 = Endpoint(id=f"{fid}_2", ra=float(ra2[i]), dec=float(dec2[i]),
                       z=float(z2[i]), mass_proxy=float(t[p2][i]))
        out.append(Filament(id=fid, ep1=ep1, ep2=ep2, meta={
            "source": "Tempel+2014 dr8_filaments.fits",
            "len_mpc_h": float(t["len"][i]), "npts": int(t["npts"][i]),
            "ngal1": int(t["ngal1"][i]), "ngal2": int(t["ngal2"][i]),
            "xyz1": xyz1[i].tolist(), "xyz2": xyz2[i].tolist(),
        }))
    return out


def _xyz_to_radecz(xyz):
    """Comoving Cartesian (Mpc/h) -> (ra_deg, dec_deg, redshift) in catalogue cosmology."""
    import numpy as np
    import astropy.units as u
    from astropy.cosmology import FlatLambdaCDM

    cosmo = FlatLambdaCDM(H0=100, Om0=0.27)
    x, y, z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    dist = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    ra = np.degrees(np.arctan2(y, x)) % 360.0
    dec = np.degrees(np.arcsin(np.clip(z / np.where(dist == 0, 1, dist), -1, 1)))
    # Invert comoving distance -> redshift via an interpolation table (fast for 15k rows).
    zgrid = np.linspace(0.0, 1.0, 2001)
    dgrid = cosmo.comoving_distance(zgrid).to(u.Mpc).value
    redshift = np.interp(dist, dgrid, zgrid)
    return ra, dec, redshift
