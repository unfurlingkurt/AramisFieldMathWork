#!/usr/bin/env python3
"""Download and verify datasets recorded in ``data/MANIFEST.toml``.

Usage:
    python scripts/download_data.py --list
    python scripts/download_data.py --source tempel_bisous --url <direct-file-url>

Raw data is never committed. This script fetches into ``data/<name>/`` and records /
verifies a sha256 so the dataset is reproducible. Direct file URLs differ per product
(VizieR/CADE/PLA give landing pages), so the resolved file URL is passed explicitly
or read from the manifest once known.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "MANIFEST.toml"


def load_manifest() -> dict:
    with MANIFEST.open("rb") as fh:
        return tomllib.load(fh)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="List manifest sources.")
    ap.add_argument("--source", help="Source name from the manifest.")
    ap.add_argument("--url", help="Direct file URL (overrides manifest landing page).")
    args = ap.parse_args(argv)

    manifest = load_manifest()
    sources = {s["name"]: s for s in manifest.get("source", [])}

    if args.list or not args.source:
        for name, s in sources.items():
            print(f"{name:16s} stage {s.get('stage','?')}  {s.get('description','')}")
            print(f"{'':16s} url: {s.get('url','')}")
        return 0

    if args.source not in sources:
        print(f"Unknown source '{args.source}'. Known: {', '.join(sources)}", file=sys.stderr)
        return 2

    s = sources[args.source]
    url = args.url or s.get("url", "")
    if not url or url.endswith("/"):
        print(
            f"'{args.source}' resolves to a landing page, not a direct file:\n  {url}\n"
            "Open it, pick the data product, and re-run with --url <direct-file-url>.\n"
            f"Reduction notes:\n{s.get('reduction','(none)')}",
            file=sys.stderr,
        )
        return 3

    dest_dir = ROOT / "data" / args.source
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / Path(url).name
    print(f"Downloading {url} -> {dest}")
    urllib.request.urlretrieve(url, dest)  # noqa: S310 - explicit user-provided URL
    digest = sha256_of(dest)
    recorded = s.get("sha256", "")
    if recorded and recorded != digest:
        print(f"CHECKSUM MISMATCH: expected {recorded}, got {digest}", file=sys.stderr)
        return 4
    print(f"sha256: {digest}")
    if not recorded:
        print("Record this sha256 in data/MANIFEST.toml to lock the dataset.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
