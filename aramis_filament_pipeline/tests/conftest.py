import pytest

from aramis.data.loaders.synthetic import make_synthetic
from aramis.geometry.metric import tension_additive
from aramis.quantize.scale import DEFAULT_MASS_SCALE


@pytest.fixture
def default_spec():
    return DEFAULT_MASS_SCALE


@pytest.fixture
def default_metric():
    return tension_additive


@pytest.fixture
def synthetic_filaments():
    return make_synthetic(n=40, seed=7)


@pytest.fixture
def symmetric_filaments():
    return make_synthetic(n=20, seed=3, symmetric=True)
