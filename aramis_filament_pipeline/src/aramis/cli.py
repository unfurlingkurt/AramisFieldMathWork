"""Command-line entry point: ``aramis <stage> [options]``."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .geometry.metric import tension_additive, tension_multiplicative
from .pipeline.stages import stage0_puremath, stage1_catalog, stage3_battery

_METRICS = {
    "additive": tension_additive,
    "multiplicative": tension_multiplicative,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aramis",
        description="Aramis filament medoid pipeline (RatioSpace geometry).",
    )
    sub = parser.add_subparsers(dest="stage", required=True)

    p0 = sub.add_parser("stage0", help="Zero-data planted-signal recovery demo.")
    p0.add_argument("--out", default="outputs/stage0", help="Output directory.")
    p0.add_argument("--n", type=int, default=60, help="Number of synthetic filaments.")
    p0.add_argument("--seed", type=int, default=0, help="RNG seed.")
    p0.add_argument(
        "--metric", choices=list(_METRICS), default="additive",
        help="Native tension metric.",
    )

    p1 = sub.add_parser("stage1", help="Real catalog geometry (endpoint pairs).")
    p1.add_argument("catalog", help="Path to an endpoint-pair table (CSV or FITS).")
    p1.add_argument("--out", default="outputs/stage1", help="Output directory.")
    p1.add_argument(
        "--loader", choices=["tempel", "lrg", "csv"], default="tempel",
        help="Catalog loader / column mapping.",
    )
    p1.add_argument(
        "--metric", choices=list(_METRICS), default="additive",
        help="Native tension metric.",
    )

    p3 = sub.add_parser("stage3", help="Null/control battery with significance.")
    p3.add_argument("--out", default="outputs/stage3", help="Output directory.")
    p3.add_argument("--n", type=int, default=80, help="Number of synthetic filaments.")
    p3.add_argument("--seed", type=int, default=0, help="RNG seed.")
    p3.add_argument("--n-null", type=int, default=50, help="Null resamples per test.")
    p3.add_argument(
        "--metric", choices=list(_METRICS), default="additive",
        help="Native tension metric.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.stage == "stage0":
        result = stage0_puremath(
            out_dir=args.out, n=args.n, seed=args.seed, metric=_METRICS[args.metric]
        )
        print(json.dumps(result["summary"], indent=2))
        print(f"\nWrote {result['csv']}")
        return 0
    if args.stage == "stage1":
        result = stage1_catalog(
            catalog_path=args.catalog, out_dir=args.out,
            loader=args.loader, metric=_METRICS[args.metric],
        )
        print(json.dumps(result["summary"], indent=2))
        print(f"\nWrote {result['csv']}")
        return 0
    if args.stage == "stage3":
        result = stage3_battery(
            out_dir=args.out, n=args.n, seed=args.seed,
            n_null=args.n_null, metric=_METRICS[args.metric],
        )
        print(json.dumps(result["result"], indent=2))
        print(f"\nWrote {result['json']}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
