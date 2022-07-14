
"""
Test the distribution function classes
""" 

import math

import pytest

from pydsol.core.distributions import Distribution, DistBeta, DistGamma, \
    DistConstant, DistBernoulli, DistErlang, DistExponential
from pydsol.core.statistics import Tally
from pydsol.core.streams import MersenneTwister, StreamInterface


def c_dist(name: str, dist: Distribution, expected_mean: float,
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


def test_c_mean_variance():
    stream = MersenneTwister(12)
    nan = math.nan
    c_dist("DistBeta", DistBeta(stream, 1.0, 2.0), 1.0 / (1.0 + 2.0),
           (1.0 * 2.0) / ((1.0 + 2.0) * (1.0 + 2.0) * (1.0 + 2.0 + 1.0)),
           0.0, 1.0, 0.1)
    c_dist("DistConstant", DistConstant(stream, 12.1), 12.1, 0.0, 12.1,
           12.1, 0.001)
    c_dist("DistErlang", DistErlang(stream, 2.0, 1), 2.0, 2.0 * 2.0,
           0.0, nan, 0.05)
    c_dist("DistErlang", DistErlang(stream, 0.5, 4), 4.0 * 0.5,
           4.0 * 0.5 * 0.5, 0.0, nan, 0.05)
    c_dist("DistErlang", DistErlang(stream, 0.5, 40), 40.0 * 0.5,
           40.0 * 0.5 * 0.5, 0.0, nan, 0.05)
    c_dist("DistExponential", DistExponential(stream, 1.2), 1.2, 
           1.2 * 1.2, 0.0, nan, 0.05)
    c_dist("DistGamma", DistGamma(stream, 2.0, 4.0), 2.0 * 4.0,
           2.0 * 4.0 * 4.0, 0.0, nan, 0.5)
    c_dist("DistGamma", DistGamma(stream, 3.0, 4.0), 3.0 * 4.0,
           3.0 * 4.0 * 4.0, 0.0, nan, 0.5)
    c_dist("DistGamma", DistGamma(stream, 0.999, 2.0), 0.999 * 2.0,
           0.999 * 2.0 * 2.0, 0.0, nan, 0.5)
    c_dist("DistGamma", DistGamma(stream, 1.0, 4.0), 1.0 * 4.0,
           1.0 * 4.0 * 4.0, 0.0, nan, 0.5)
    c_dist("DistGamma", DistGamma(stream, 0.5, 0.2), 0.5 * 0.2,
           0.5 * 0.2 * 0.2, 0.0, nan, 0.1)
    # c_dist("DistPearson5", DistPearson5(stream, 3, 1), 0.5, 0.25, 0.0, nan, 0.01)
    # c_dist("DistPearson6", DistPearson6(stream, 2, 3, 4), 4.0 * 2 / (3 - 1),
    #         4.0 * 4 * 2 * (2 + 3 - 1) / ((3 - 1) * (3 - 1) * (3 - 2)), 0.0, nan, 0.05)
    # c_dist("DistTriangular", DistTriangular(stream, 1, 4, 9), (1 + 4 + 9) / 3.0,
    #         (1 * 1 + 4 * 4 + 9 * 9 - 1 * 4 - 1 * 9 - 4 * 9) / 18.0, 1.0, 9.0, 0.01)
    # c_dist("DistUniform", DistUniform(stream, 0, 1), 0.5, 1.0 / 12.0, 0.0, 1.0, 0.01)


def test_beta():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistBeta = DistBeta(stream, 1.5, 2.5)
    assert stream == dist.stream
    assert dist.alpha1 == 1.5
    assert dist.alpha2 == 2.5
    assert "Beta" in str(dist)
    assert "1.5" in str(dist)
    assert "2.5" in repr(dist)
    value: float = dist.draw()
    assert value >= 0 and value <= 1
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value

    with pytest.raises(TypeError):
        DistBeta('x', 0.1, 2.0)
    with pytest.raises(TypeError):
        DistBeta(stream, 'x', 2.0)
    with pytest.raises(TypeError):
        DistBeta(stream, 0.1, 'x')
    with pytest.raises(ValueError):
        DistBeta(stream, -0.1, 2.0)
    with pytest.raises(ValueError):
        DistBeta(stream, 0.1, -2.0)


def test_constant():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistConstant = DistConstant(stream, 1.5)
    assert stream == dist.stream
    assert dist.constant == 1.5
    assert "Constant" in str(dist)
    assert "1.5" in str(dist)
    assert "1.5" in repr(dist)
    value: float = dist.draw()
    assert value == 1.5
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    dist: DistConstant = DistConstant(stream, 4)
    assert dist.draw() == 4

    with pytest.raises(TypeError):
        DistConstant('x', 0.1)
    with pytest.raises(TypeError):
        DistConstant(stream, 'x')


def test_erlang():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistErlang = DistErlang(stream, 2.5, 3)
    assert stream == dist.stream
    assert dist.scale == 2.5
    assert dist.k == 3
    assert "Erlang" in str(dist)
    assert "2.5" in str(dist)
    assert "3" in repr(dist)

    # below 10
    value: float = dist.draw()
    assert value > 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    
    # above 10
    stream: StreamInterface = MersenneTwister(10)
    dist: DistErlang = DistErlang(stream, 2, 15)
    value: float = dist.draw()
    assert value > 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    
    # exactly 10
    stream: StreamInterface = MersenneTwister(10)
    dist: DistErlang = DistErlang(stream, 3.14, 10)
    value: float = dist.draw()
    assert value > 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    
    with pytest.raises(TypeError):
        DistErlang('x', 0.1, 2)
    with pytest.raises(TypeError):
        DistErlang(stream, 'x', 2)
    with pytest.raises(TypeError):
        DistErlang(stream, 0.1, 'x')
    with pytest.raises(ValueError):
        DistErlang(stream, -0.1, 2)
    with pytest.raises(ValueError):
        DistErlang(stream, 0.1, -2)
    with pytest.raises(ValueError):
        DistErlang(stream, 0, 2)
    with pytest.raises(ValueError):
        DistErlang(stream, 0.1, 0)


def test_exponential():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistExponential = DistExponential(stream, 2.5)
    assert stream == dist.stream
    assert dist.mean == 2.5
    assert "Exponential" in str(dist)
    assert "2.5" in repr(dist)
    value: float = dist.draw()
    assert value >= 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    dist: DistExponential = DistExponential(stream, 2)
    value: float = dist.draw()
    assert value >= 0
    
    with pytest.raises(TypeError):
        DistExponential('x', 0.1)
    with pytest.raises(TypeError):
        DistExponential(stream, 'x')
    with pytest.raises(ValueError):
        DistExponential(stream, -0.1)
    with pytest.raises(ValueError):
        DistExponential(stream, 0)


def test_gamma():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistGamma = DistGamma(stream, 1.5, 2.5)
    assert stream == dist.stream
    assert dist.shape == 1.5
    assert dist.scale == 2.5
    assert "Gamma" in str(dist)
    assert "1.5" in str(dist)
    assert "2.5" in repr(dist)
    value: float = dist.draw()
    assert value > 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    assert DistGamma(stream, 100, 0.1).draw() > 0
    assert DistGamma(stream, 1, 0.1).draw() > 0
    assert DistGamma(stream, 0.1, 0.1).draw() > 0
    assert DistGamma(stream, 0.9999, 0.1).draw() > 0
    assert DistGamma(stream, 0.0001, 1000.0).draw() > 0
    assert DistGamma(stream, 1000.0, 0.0001).draw() > 0

    with pytest.raises(TypeError):
        DistGamma('x', 0.1, 2.0)
    with pytest.raises(TypeError):
        DistGamma(stream, 'x', 2.0)
    with pytest.raises(TypeError):
        DistGamma(stream, 0.1, 'x')
    with pytest.raises(ValueError):
        DistGamma(stream, -0.1, 2.0)
    with pytest.raises(ValueError):
        DistGamma(stream, 0.1, -2.0)
    
    
if __name__ == "__main__":
    pytest.main()
