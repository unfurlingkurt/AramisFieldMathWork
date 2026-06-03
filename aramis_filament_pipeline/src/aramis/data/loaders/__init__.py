"""Catalog loaders. All emit the normalized schema in :mod:`aramis.data.schema`."""

from .synthetic import make_synthetic
from .tabular import ColumnMap, load_pairs_csv, load_pairs_fits

__all__ = ["make_synthetic", "ColumnMap", "load_pairs_csv", "load_pairs_fits"]
