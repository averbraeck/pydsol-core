"""
Test the Normal and LogNormal distributions as well as their truncated versions.
""" 

import math

import pytest

from pydsol.core.distributions import Distribution, DistNormal, DistLogNormal
from pydsol.core.statistics import Tally
from pydsol.core.streams import MersenneTwister, StreamInterface

from .z_values import Z_VALUES


def n_dist(name: str, dist: Distribution, expected_mean: float,
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


def test_n_mean_variance():
    stream = MersenneTwister(12)
    nan = math.nan
    n_dist("DistLogNormal", DistLogNormal(stream, 0.0, 0.5), 
           math.exp(0.5 * 0.5 / 2.0),
                (math.exp(0.5 * 0.5) - 1.0) * math.exp(0.5 * 0.5), 
                0.0, nan, 0.01)
    n_dist("DistLogNormal", DistLogNormal(stream, 5.0, 0.5), 
                math.exp(5.0 + 0.5 * 0.5 / 2.0),
                (math.exp(0.5 * 0.5) - 1.0) * math.exp(2 * 5.0 + 0.5 * 0.5), 
                0.0, nan, 0.5)
    n_dist("DistNormal", DistNormal(stream), 0.0, 1.0, nan, nan, 0.01)
    n_dist("DistNormal", DistNormal(stream, 5.0, 2.0), 5.0, 4.0, nan, nan, 0.01)


def normpdf(mu, sigma, x):
    """Calculate probability density of Normal(mu, sigma) for value x. 
    From: https://en.wikipedia.org/wiki/Normal_distribution."""
    return ((1.0 / (sigma * math.sqrt(2.0 * math.pi))) 
            * math.exp(-0.5 * math.pow((x - mu) / sigma, 2)))


def normcdf(mu, sigma, x):
    """Calculate cumulative probability density of Normal(mu, sigma) for 
    value x. From: https://en.wikipedia.org/wiki/Normal_distribution."""
    return 0.5 + 0.5 * math.erf((x - mu) / (math.sqrt(2.0) * sigma))


def lnpdf(mu, sigma, x):
    """Calculate probability density of LogNormal(mu, sigma) for value x. 
    From: https://en.wikipedia.org/wiki/Normal_distribution."""
    return ((1.0 / (x * sigma * math.sqrt(2.0 * math.pi))) 
            * math.exp(-math.pow((math.log(x) - mu), 2) / (2.0 * sigma * sigma)))


def lncdf(mu, sigma, x):
    """Calculate cumulative probability density of LogNormal(mu, sigma) for 
    value x. From: https://en.wikipedia.org/wiki/Normal_distribution."""
    return 0.5 + 0.5 * math.erf((math.log(x) - mu) / (math.sqrt(2.0) * sigma))


def test_std_normal():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistNormal = DistNormal(stream)
    assert stream == dist.stream
    assert dist.mu == 0.0
    assert dist.sigma == 1.0
    assert "Normal" in str(dist)
    assert "0.0" in str(dist)
    assert "1.0" in repr(dist)

    stream: StreamInterface = MersenneTwister(12)
    dist: DistNormal = DistNormal(stream)
    value: dist = dist.draw()
    assert dist.draw() != value
    dist.stream = MersenneTwister(12)
    assert dist.draw() == value
    assert dist.draw() != value
    assert dist.draw() != value  # twice because of next_next_gaussian
    dist.stream = MersenneTwister(12)
    assert dist.draw() == value

    assert math.isclose(dist.probability_density(0.0),
                        1.0 / math.sqrt(2.0 * math.pi), abs_tol=0.0001)
    assert math.isclose(dist.cumulative_probability(0.0),
                        0.5, abs_tol=0.0001)
    for x in (0.5, 1.0, 2.0, 4.0, 8.0, -0.5, -1.0, -2.0, -4.0, -8.0):
        assert math.isclose(dist.probability_density(x),
                        normpdf(0.0, 1.0, x), rel_tol=0.0001)
        assert math.isclose(dist.cumulative_probability(x),
                        normcdf(0.0, 1.0, x), rel_tol=0.0001)
    for x in (0.5, 1.0, 2.0, 4.0, -0.5, -1.0, -2.0, -4.0):
        assert math.isclose(dist.inverse_cumulative_probability(
            dist.cumulative_probability(x)), x, abs_tol=0.0001)
        
    assert math.isclose(dist.inverse_cumulative_probability(0.975),
                        1.96, abs_tol=0.0001)
    assert math.isclose(dist.inverse_cumulative_probability(0.025),
                        -1.96, abs_tol=0.0001)
    assert math.isclose(dist.cumulative_probability(1.96),
                        0.975, abs_tol=0.0001)
    assert math.isclose(dist.cumulative_probability(-1.96),
                        0.025, abs_tol=0.0001)

    with pytest.raises(TypeError):
        DistNormal('x')


def test_z_values():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistNormal = DistNormal(stream)
    for i in range(len(Z_VALUES) // 2):
        p = Z_VALUES[2 * i]
        c = Z_VALUES[2 * i + 1]
        assert math.isclose(c, dist.cumulative_probability(p),
                            abs_tol=0.0001)
        assert math.isclose(p, dist.inverse_cumulative_probability(c),
                            abs_tol=0.0001)


def test_normal():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistNormal = DistNormal(stream, 5.0, 2.0)
    assert stream == dist.stream
    assert dist.mu == 5.0
    assert dist.sigma == 2.0
    assert "Normal" in str(dist)
    assert "5.0" in str(dist)
    assert "2.0" in repr(dist)

    stream: StreamInterface = MersenneTwister(12)
    dist: DistNormal = DistNormal(stream, 5.0, 2.0)
    value: dist = dist.draw()
    assert dist.draw() != value
    dist.stream = MersenneTwister(12)
    assert dist.draw() == value
    assert dist.draw() != value
    assert dist.draw() != value  # twice because of next_next_gaussian
    dist.stream = MersenneTwister(12)
    assert dist.draw() == value

    assert math.isclose(dist.cumulative_probability(5.0), 0.5, abs_tol=0.0001)
    
    for x in (0.5, 1.0, 2.0, 4.0, 8.0, 10, -0.5, -1.0, -2.0, -4.0, -8.0, -10):
        assert math.isclose(dist.probability_density(x),
                        normpdf(5.0, 2.0, x), rel_tol=0.0001)
        assert math.isclose(dist.cumulative_probability(x),
                        normcdf(5.0, 2.0, x), rel_tol=0.0001)
    for x in (0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 10):
        assert math.isclose(dist.inverse_cumulative_probability(
            dist.cumulative_probability(x)), x, abs_tol=0.0001)

    with pytest.raises(TypeError):
        DistNormal('x')
    with pytest.raises(TypeError):
        DistNormal('x', 0.1, 2)
    with pytest.raises(TypeError):
        DistNormal(stream, 'x', 2)
    with pytest.raises(TypeError):
        DistNormal(stream, 0.1, 'x')
    with pytest.raises(ValueError):
        DistNormal(stream, 0.1, -1.2)
    with pytest.raises(ValueError):
        DistNormal(stream, 0.1, 0.0)

def test_lognormal():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistLogNormal = DistLogNormal(stream, 1.5, 0.5)
    assert stream == dist.stream
    assert dist.mu == 1.5
    assert dist.sigma == 0.5
    assert "Normal" in str(dist)
    assert "1.5" in str(dist)
    assert "0.5" in repr(dist)

    stream: StreamInterface = MersenneTwister(12)
    dist: DistLogNormal = DistLogNormal(stream, 1.5, 0.5)
    value: dist = dist.draw()
    assert value > 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(12)
    assert dist.draw() == value
    assert dist.draw() != value
    assert dist.draw() != value  # twice because of next_next_gaussian
    dist.stream = MersenneTwister(12)
    assert dist.draw() == value
    for _ in range(100):
        assert dist.draw() > 0

    assert dist.probability_density(0.0) == 0.0
    assert dist.probability_density(-1.0) == 0.0
    for x in (0.5, 1.0, 2.0, 4.0, 8.0):
        assert math.isclose(dist.probability_density(x),
                        lnpdf(1.5, 0.5, x), rel_tol=0.0001)
        assert math.isclose(dist.cumulative_probability(x),
                        lncdf(1.5, 0.5, x), rel_tol=0.0001)
    for x in (0.0, 0.5, 1.0, 2.0, 4.0, 8.0):
        assert math.isclose(dist.inverse_cumulative_probability(
            dist.cumulative_probability(x)), x, abs_tol=0.0001)

    dist: DistLogNormal = DistLogNormal(stream, 0.0, 2.5)
    assert dist.probability_density(0.0) == 0.0
    assert dist.probability_density(-1.0) == 0.0
    for x in (0.5, 1.0, 2.0, 4.0, 8.0):
        assert math.isclose(dist.probability_density(x),
                        lnpdf(0.0, 2.5, x), rel_tol=0.0001)
        assert math.isclose(dist.cumulative_probability(x),
                        lncdf(0.0, 2.5, x), rel_tol=0.0001)
    for x in (0.0, 0.5, 1.0, 2.0, 4.0, 8.0):
        assert math.isclose(dist.inverse_cumulative_probability(
            dist.cumulative_probability(x)), x, abs_tol=0.0001)
    
    with pytest.raises(TypeError):
        DistLogNormal('x', 0.1, 2)
    with pytest.raises(TypeError):
        DistLogNormal(stream, 'x', 2)
    with pytest.raises(TypeError):
        DistLogNormal(stream, 0.1, 'x')
    with pytest.raises(ValueError):
        DistLogNormal(stream, 0.1, -1.2)
    with pytest.raises(ValueError):
        DistLogNormal(stream, 0.1, 0.0)


if __name__ == "__main__":
    pytest.main()
