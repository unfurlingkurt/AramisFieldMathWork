"""Generic tabular loader: a pair/endpoint table -> normalized Filaments.

Every real catalog (Tempel/Bisous, SDSS LRG, future surveys) reduces to a table of
endpoint pairs. This loader reads CSV (always) or FITS (with the ``[data]`` extra)
and maps columns to the normalized schema via an explicit column map, so adapting a
new catalog is a one-line mapping change, not new code.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from ..schema import Endpoint, Filament

# Minimal required logical fields -> their default column names.
DEFAULT_COLUMNS: Dict[str, str] = {
    "id": "id",
    "ra1": "ra1", "dec1": "dec1", "z1": "z1", "mass1": "mass1_proxy",
    "ra2": "ra2", "dec2": "dec2", "z2": "z2", "mass2": "mass2_proxy",
}


@dataclass(frozen=True)
class ColumnMap:
    """Maps logical fields to catalog-specific column names + provenance."""

    columns: Dict[str, str] = field(default_factory=lambda: dict(DEFAULT_COLUMNS))
    provenance: str = ""

    def get(self, key: str) -> str:
        return self.columns.get(key, DEFAULT_COLUMNS[key])


def _row_to_filament(row: Dict[str, str], cm: ColumnMap, idx: int) -> Filament:
    def f(key: str) -> float:
        return float(row[cm.get(key)])

    fid = str(row.get(cm.get("id"), idx))
    ep1 = Endpoint(id=f"{fid}_1", ra=f("ra1"), dec=f("dec1"), z=f("z1"),
                   mass_proxy=f("mass1"))
    ep2 = Endpoint(id=f"{fid}_2", ra=f("ra2"), dec=f("dec2"), z=f("z2"),
                   mass_proxy=f("mass2"))
    return Filament(id=fid, ep1=ep1, ep2=ep2, meta={"source": cm.provenance})


def load_pairs_csv(path: str | Path, cm: ColumnMap | None = None) -> List[Filament]:
    """Load an endpoint-pair table from CSV into normalized Filaments."""
    cm = cm or ColumnMap()
    path = Path(path)
    out: List[Filament] = []
    with path.open(newline="") as fh:
        reader = csv.DictReader(r for r in fh if not r.lstrip().startswith("#"))
        for idx, row in enumerate(reader):
            out.append(_row_to_filament(row, cm, idx))
    return out


def load_pairs_fits(path: str | Path, cm: ColumnMap | None = None) -> List[Filament]:
    """Load an endpoint-pair table from a FITS binary table (requires astropy)."""
    try:
        from astropy.table import Table
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "astropy required for FITS loading. Install with: pip install -e '.[data]'"
        ) from exc
    cm = cm or ColumnMap()
    table = Table.read(str(path))
    out: List[Filament] = []
    for idx, trow in enumerate(table):
        row = {name: trow[name] for name in table.colnames}
        out.append(_row_to_filament(row, cm, idx))
    return out
