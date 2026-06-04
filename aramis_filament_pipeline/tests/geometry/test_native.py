import numpy as np

from aramis.geometry.native import (
    GAUSS_KUZMIN_LE2,
    continued_fraction_of_float,
    fibonacci_indices,
    mediant_fold,
    native_tension,
    phi_coherence,
)
from aramis.geometry.ratio import Ratio


def test_native_tension_is_composition_cf_length():
    a, b = Ratio(3, 2), Ratio(5, 3)
    assert native_tension(a, b) == a.compose(b).cf_length()
    # identity composes to 1:1 -> cf [1] -> length 1 (not normalized; framework-native)
    assert native_tension(a, a) == 1


def test_mediant_fold_is_order_dependent_not_average():
    rs = [Ratio(1, 2), Ratio(2, 3), Ratio(3, 4)]
    folded = mediant_fold(rs)
    # mediant of 1/2 and 2/3 is 3/5, then with 3/4 -> 6/9 = 2/3
    assert folded == Ratio(1, 2).mediant(Ratio(2, 3)).mediant(Ratio(3, 4))
    # not the arithmetic mean
    assert folded != Ratio(1, 1)


def test_continued_fraction_of_float():
    # 0.5 -> [0; 2]; 1/3 -> [0; 3]
    assert continued_fraction_of_float(0.5, 4)[:2] == [0, 2]
    assert continued_fraction_of_float(1 / 3, 4)[:2] == [0, 3]


def test_phi_coherence_counts_small_quotients():
    # quotients after a0: [2, 5, 1] -> two of three are <=2
    assert abs(phi_coherence([0, 2, 5, 1]) - 2 / 3) < 1e-9


def test_uniform_reals_approximate_gauss_kuzmin():
    rng = np.random.default_rng(0)
    qs = []
    for x in rng.random(20000):
        qs.extend(continued_fraction_of_float(float(x), 12)[1:])
    qs = np.array(qs)
    # finite truncation biases slightly high, but should be in the right neighborhood
    assert abs((qs <= 2).mean() - GAUSS_KUZMIN_LE2) < 0.03


def test_fibonacci_indices():
    assert fibonacci_indices(7, start=10) == [10, 11, 12, 13, 15, 18, 23]
