import numpy as np

from aramis.data.loaders.synthetic import make_synthetic
from aramis.data.schema import Endpoint, Filament, Sample
from aramis.systems import EuclideanMidpoint, FareyMedoid, ForceBalancePoint, default_systems


def _filament(m1, m2, center, n=25, sigma=0.05, seed=0):
    rng = np.random.default_rng(seed)
    pos = np.clip(rng.normal(center, sigma, n), 0.01, 0.99)
    samples = [Sample(s=float(p), intensity=1.0) for p in pos]
    return Filament(
        id="t",
        ep1=Endpoint("a", 0, 0, 0.1, m1),
        ep2=Endpoint("b", 1, 0, 0.1, m2),
        samples=samples,
        meta={"planted_center": center},
    )


def test_euclidean_is_always_half():
    fil = _filament(8.0, 1.0, center=0.7)
    assert EuclideanMidpoint().locate(fil).t == 0.5


def test_force_balance_tracks_mass():
    fil = _filament(1.0, 3.0, center=0.7)
    # center of mass fraction from ep1 = m2/(m1+m2) = 3/4
    assert abs(ForceBalancePoint().locate(fil).t - 0.75) < 1e-9


def test_identical_input_contract():
    # Every system consumes the same Filament and returns a t in [0, 1].
    fil = _filament(2.0, 1.0, center=0.4)
    for sysm in default_systems():
        located = sysm.locate(fil)
        assert located.system_name == sysm.name
        assert 0.0 <= located.t <= 1.0


def test_farey_medoid_recovers_offcenter_peak():
    fil = _filament(5.0, 1.0, center=2 / 3, seed=1)
    medoid_t = FareyMedoid().locate(fil).t
    euclid_t = EuclideanMidpoint().locate(fil).t
    assert abs(medoid_t - 2 / 3) < abs(euclid_t - 2 / 3)


def test_systems_agree_on_symmetric_control():
    # Equal masses, symmetric emission at 0.5: all systems should land near 0.5.
    fil = _filament(1.0, 1.0, center=0.5, seed=2)
    for sysm in default_systems():
        assert abs(sysm.locate(fil).t - 0.5) < 0.06


def test_farey_medoid_fallback_without_samples():
    fil = Filament(
        id="t",
        ep1=Endpoint("a", 0, 0, 0.1, 1.0),
        ep2=Endpoint("b", 1, 0, 0.1, 3.0),
    )
    located = FareyMedoid().locate(fil)
    assert located.extra.get("fallback") == "no_samples"
