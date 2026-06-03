from pathlib import Path

from aramis.geometry.metric import tension_additive, tension_multiplicative
from aramis.pipeline.stages import stage0_puremath


def test_stage0_recovers_planted_signal(tmp_path):
    result = stage0_puremath(out_dir=tmp_path, n=80, seed=0)
    summary = result["summary"]
    # The native medoid recovers the planted center better than the Euclidean midpoint.
    assert summary["medoid_beats_euclidean"] is True
    assert summary["farey_medoid_mean_err"] < summary["euclidean_midpoint_mean_err"]


def test_stage0_writes_csv_with_metadata(tmp_path):
    result = stage0_puremath(out_dir=tmp_path, n=20, seed=1)
    csv_path = Path(result["csv"])
    assert csv_path.exists()
    head = csv_path.read_text().splitlines()
    meta = [ln for ln in head if ln.startswith("#")]
    assert any("scale_name" in ln for ln in meta)
    assert any("metric" in ln for ln in meta)


def test_stage0_runs_under_both_metrics(tmp_path):
    for metric in (tension_additive, tension_multiplicative):
        result = stage0_puremath(out_dir=tmp_path, n=30, seed=2, metric=metric)
        assert result["summary"]["farey_medoid_mean_err"] is not None
