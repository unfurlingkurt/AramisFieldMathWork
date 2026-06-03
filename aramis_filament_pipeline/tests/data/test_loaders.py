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


# --- dr8_filaments.fits direct loader (offline fixture; real file is gitignored) ---
DR8_FIXTURE = Path(__file__).parent / "fixtures" / "mini_dr8.fits"


def test_load_dr8_fits_reconstructs_endpoints():
    pytest.importorskip("astropy")
    from aramis.data.loaders.tempel_bisous import load_dr8_fits
    fils = load_dr8_fits(DR8_FIXTURE)
    assert len(fils) == 3
    f3 = fils[2]
    # lum1=8, lum2=1 -> strong asymmetry; metadata carries comoving endpoints + len.
    assert f3.mass1 == 8.0 and f3.mass2 == 1.0
    assert "xyz1" in f3.meta and "len_mpc_h" in f3.meta
    # sky coords are populated and in range.
    assert 0.0 <= f3.ep1.ra < 360.0 and -90.0 <= f3.ep1.dec <= 90.0
    assert f3.ep1.z > 0.0


def test_dr8_loader_drives_systems():
    pytest.importorskip("astropy")
    from aramis.data.loaders.tempel_bisous import load_dr8_fits
    from aramis.systems import ForceBalancePoint
    fils = load_dr8_fits(DR8_FIXTURE)
    # Equal-luminosity filament (lum1==lum2) sits at the midpoint.
    assert abs(ForceBalancePoint().locate(fils[0]).t - 0.5) < 1e-9
