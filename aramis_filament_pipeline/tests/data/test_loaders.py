from pathlib import Path

import pytest

from aramis.data.loaders.tabular import ColumnMap, load_pairs_csv
from aramis.pipeline.stages import stage1_catalog
from aramis.systems import EuclideanMidpoint, FareyMedoid, ForceBalancePoint

FIXTURE = Path(__file__).parent / "fixtures" / "mini_pairs.csv"


def test_load_pairs_csv_default_columns():
    fils = load_pairs_csv(FIXTURE)
    assert len(fils) == 3
    assert fils[0].id == "p1"
    assert fils[2].mass1 == 8.0 and fils[2].mass2 == 1.0


def test_loaded_filaments_drive_systems():
    fils = load_pairs_csv(FIXTURE)
    skew = fils[2]  # 8:1 mass ratio
    # Euclidean ignores mass; force-balance and Farey medoid pull toward the heavy end.
    assert EuclideanMidpoint().locate(skew).t == 0.5
    assert ForceBalancePoint().locate(skew).t < 0.5  # m2/(m1+m2) = 1/9
    medoid = FareyMedoid().locate(skew)
    assert medoid.extra.get("fallback") == "mass_snap"
    assert medoid.t < 0.5


def test_stage1_runs_on_fixture(tmp_path):
    result = stage1_catalog(FIXTURE, out_dir=tmp_path, loader="csv")
    assert result["summary"]["n_filaments"] == 3
    assert Path(result["csv"]).exists()


def test_custom_column_map():
    cm = ColumnMap(columns={
        "id": "id",
        "ra1": "ra1", "dec1": "dec1", "z1": "z1", "mass1": "mass1_proxy",
        "ra2": "ra2", "dec2": "dec2", "z2": "z2", "mass2": "mass2_proxy",
    }, provenance="test")
    fils = load_pairs_csv(FIXTURE, cm)
    assert fils[0].meta["source"] == "test"
