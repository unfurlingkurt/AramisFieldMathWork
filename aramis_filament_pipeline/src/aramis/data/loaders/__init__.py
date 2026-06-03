"""Catalog loaders. All emit the normalized schema in :mod:`aramis.data.schema`."""

from .synthetic import make_synthetic

__all__ = ["make_synthetic"]
