
"""
Test the distribution function classes
""" 

import math

import pytest

from pydsol.core.distributions import Distribution, DistBernoulli, DistBinomial, \
    DistDiscreteUniform
from pydsol.core.statistics import Tally
from pydsol.core.streams import MersenneTwister, StreamInterface


def d_dist(name: str, dist: Distribution, expected_mean: float,
            expected_variance: float, expected_min: float, expected_max: float,
            precision: float):
    tally: Tally = Tally("distTally " + str(dist))
    tally.initialize()
    for _ in range(100000):
        d = dist.draw()
        if not math.isnan(expected_min):
            assert d >= expected_min
        if not math.isnan(expected_max):
            assert d <= expected_max
        tally.ingest(d)
    assert math.isclose(expected_mean, tally.population_mean(),
                abs_tol=precision)
    assert math.isclose(math.sqrt(expected_variance), tally.population_stdev(),
                abs_tol=precision)


def test_d_mean_variance():
    stream = MersenneTwister(12)
    nan = math.nan
    d_dist("DistBernoulli", DistBernoulli(stream, 0.25),
           0.25, 0.25 * (1.0 - 0.25), 0.0, 1.0, 0.01)
    d_dist("DistBinomial", DistBinomial(stream, 3, 0.25),
           3 * 0.25, 3 * 0.25 * 0.75, 0.0, 3.0, 0.01)
    d_dist("DistDiscreteUniform", DistDiscreteUniform(stream, 1, 5), 
           3.0, (5.0 - 1.0) * (5.0 + 1.0) / 12.0, 1, 5, 0.05)
    # d_dist("DistGeometric", DistGeometric(stream, 0.25), 
    #        (1 - 0.25) / 0.25, (1 - 0.25) / (0.25 * 0.25), 0.0, nan, 0.05)
    # d_dist("DistGeometric", DistGeometric(stream, 0.9), 
    #        (1 - 0.9) / 0.9, (1 - 0.9) / (0.9 * 0.9), 0.0, nan, 0.05)
    # d_dist("DistNegBinomial", DistNegBinomial(stream, 10, 0.25), 
    #        10 * (1.0 - 0.25) / 0.25, 10 * (1.0 - 0.25) / (0.25 * 0.25), 
    #        0.0, nan, 0.05)
    # d_dist("DistPoisson", DistPoisson(stream, 8.21), 8.21, 8.21, 
    #        0.0, nan, 0.01)


def test_bernoulli():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistBernoulli = DistBernoulli(stream, 0.25)
    assert stream == dist.stream
    assert dist.p == 0.25
    assert "Bernoulli" in str(dist)
    assert "0.25" in str(dist)
    assert "0.25" in repr(dist)
    value: int = dist.draw()
    assert value == 0 or value == 1
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    for _ in range(20):
        value = dist.draw()
        assert value == 0 or value == 1

    with pytest.raises(TypeError):
        DistBernoulli('x', 0.1)
    with pytest.raises(TypeError):
        DistBernoulli(stream, 'x')
    with pytest.raises(TypeError):
        DistBernoulli(stream, 1)
    with pytest.raises(ValueError):
        DistBernoulli(stream, -0.1)
    with pytest.raises(ValueError):
        DistBernoulli(stream, 1.1)


def test_binomial():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistBinomial = DistBinomial(stream, 4, 0.25)
    assert stream == dist.stream
    assert dist.p == 0.25
    assert dist.n == 4
    assert "Binomial" in str(dist)
    assert "0.25" in str(dist)
    assert "4" in repr(dist)
    value: int = dist.draw()
    assert value >= 0 and value <= 4
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    for _ in range(20):
        value = dist.draw()
        assert value >= 0 and value <= 4

    with pytest.raises(TypeError):
        DistBinomial('x', 4, 0.1)
    with pytest.raises(TypeError):
        DistBinomial(stream, 'x', 0.1)
    with pytest.raises(TypeError):
        DistBinomial(stream, 4, 'x')
    with pytest.raises(TypeError):
        DistBinomial(stream, 4, 1)
    with pytest.raises(TypeError):
        DistBinomial(stream, 4.5, 0.25)
    with pytest.raises(ValueError):
        DistBinomial(stream, 0, 0.1)
    with pytest.raises(ValueError):
        DistBinomial(stream, 4, -1.1)
    with pytest.raises(ValueError):
        DistBinomial(stream, 4, 1.1)


def test_discrete_uniform():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistDiscreteUniform = DistDiscreteUniform(stream, 1, 6)
    assert stream == dist.stream
    assert dist.lo == 1
    assert dist.hi == 6
    assert "DiscreteUniform" in str(dist)
    assert "1" in str(dist)
    assert "6" in repr(dist)
    value: int = dist.draw()
    assert value >= 1 and value <= 6
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    for _ in range(20):
        value = dist.draw()
        assert value >= 1 and value <= 6

    with pytest.raises(TypeError):
        DistDiscreteUniform('x', 1, 6)
    with pytest.raises(TypeError):
        DistDiscreteUniform(stream, 'x', 6)
    with pytest.raises(TypeError):
        DistDiscreteUniform(stream, 4, 'x')
    with pytest.raises(TypeError):
        DistDiscreteUniform(stream, 0.4, 6)
    with pytest.raises(TypeError):
        DistDiscreteUniform(stream, 4, 6.25)
    with pytest.raises(ValueError):
        DistDiscreteUniform(stream, 6, 1)
    with pytest.raises(ValueError):
        DistDiscreteUniform(stream, 4, 4)
    
    
if __name__ == "__main__":
    pytest.main()