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

from ..schema import Filament
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
