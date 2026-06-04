import re
from pathlib import Path

import numpy as np

from aramis.web.graph import ordered_filaments
from aramis.web.nulls_native import shuffle_within
from aramis.web.relations import (
    consecutive_difference_ratios,
    encode_ratio,
    pairwise_ratios,
    phi_coherence_of_floats,
)

WEB_DIR = Path(__file__).resolve().parents[2] / "src" / "aramis" / "web"


def test_ordered_filaments_orders_by_spine_index():
    fid = np.array([1, 1, 1, 2, 2])
    idpts = np.array([30, 10, 20, 5, 1])
    z = np.array([0.3, 0.1, 0.2, 0.9, 0.8])
    fils = ordered_filaments(fid, idpts, {"z": z}, min_len=3)
    assert len(fils) == 1  # only filament 1 has >=3 members
    assert list(fils[0]["z"]) == [0.1, 0.2, 0.3]  # ordered by idpts


def test_consecutive_difference_ratios():
    # diffs of [0,1,3,6] = [1,2,3]; ratios |1|/|2|, |2|/|3|
    r = consecutive_difference_ratios([0.0, 1.0, 3.0, 6.0])
    assert np.allclose(r, [0.5, 2 / 3])


def test_pairwise_ratios_oriented_ge_one():
    r = pairwise_ratios([1.0, 4.0], [2.0, 1.0])
    assert all(x >= 1.0 for x in r)  # oriented as relation magnitude


def test_encode_ratio_is_exact_convergent():
    assert encode_ratio(0.5).as_float() == 0.5
    r = encode_ratio(2 / 3)
    assert (r.p, r.q) == (2, 3)


def test_phi_coherence_runs():
    phi, n = phi_coherence_of_floats([0.5, 2.0, 1.5, 0.333], n_terms=6)
    assert 0.0 <= phi <= 1.0 and n > 0


def test_shuffle_preserves_multiset():
    rng = np.random.default_rng(0)
    vals = np.array([1.0, 2.0, 3.0, 4.0])
    out = shuffle_within(vals, rng)
    assert sorted(out) == sorted(vals)


def test_web_layer_contains_no_linear_operations():
    """Guard: the web/ layer must never call Euclidean/Gaussian/mean machinery.

    Bans linear *code* (imports and calls), not the prose in docstrings that
    explains the discipline.
    """
    banned = [r"np\.linalg", r"\.euclidean\(", r"gaussian_kde", r"\bscipy\b",
              r"\bsklearn\b", r"np\.mean\(", r"cdist\(", r"np\.std\("]
    for path in WEB_DIR.glob("*.py"):
        # strip the module docstring / comment prose, keep code lines
        src = "\n".join(ln for ln in path.read_text().splitlines()
                        if not ln.lstrip().startswith("#"))
        for pat in banned:
            assert not re.search(pat, src), f"{path.name} uses banned linear op: {pat}"
