"""Output helpers: CSV emission with reproducibility metadata in the header."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Sequence


def write_csv(
    path: str | Path,
    rows: Sequence[Dict[str, object]],
    metadata: Dict[str, object] | None = None,
) -> Path:
    """Write ``rows`` to ``path`` as CSV, prefixing ``# key: value`` metadata lines.

    Metadata records the ScaleSpec / metric / seed so a run is reproducible from the
    output file alone.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: List[str] = []
    for r in rows:
        for k in r:
            if k not in fieldnames:
                fieldnames.append(k)
    with path.open("w", newline="") as fh:
        if metadata:
            for k, v in metadata.items():
                fh.write(f"# {k}: {v}\n")
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return path
