"""SDSS LRG endpoint-pair loader (SECONDARY catalog).

Luminous Red Galaxies make clean, massive filament endpoints (the Vernstrom-style
stacking approach pairs LRGs and stacks the bridge between them). The expected input
is a table of LRG pairs with sky positions, redshifts, and luminosity/mass proxies.
Build pairs from an SDSS LRG catalogue with a separation cut (e.g. 6-15 Mpc) and a
redshift-difference cut; that reduction is documented in ``data/MANIFEST.toml``.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from ..schema import Filament
from .tabular import ColumnMap, load_pairs_csv, load_pairs_fits

LRG_COLUMNS = ColumnMap(
    columns={
        "id": "pair_id",
        "ra1": "ra_1", "dec1": "dec_1", "z1": "z_1", "mass1": "lum_1",
        "ra2": "ra_2", "dec2": "dec_2", "z2": "z_2", "mass2": "lum_2",
    },
    provenance="SDSS LRG pairs (endpoint reconstruction)",
)


def load_pairs(path: str | Path, columns: ColumnMap | None = None) -> List[Filament]:
    """Load an SDSS LRG endpoint-pair table (CSV or FITS)."""
    path = Path(path)
    cm = columns or LRG_COLUMNS
    if path.suffix.lower() in (".fits", ".fit", ".fits.gz"):
        return load_pairs_fits(path, cm)
    return load_pairs_csv(path, cm)
