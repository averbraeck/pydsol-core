import math

import pytest

from pydsol.core.statistics import Counter, Tally, WeightedTally, \
    TimestampWeightedTally


def test_counter():
    name = "counter description"
    c: Counter = Counter(name)
    assert c.name == name
    assert name in str(c)
    assert name in repr(c)
    assert c.n() == 0
    assert c.count() == 0
    c.ingest(2)
    assert c.n() == 1
    assert c.count() == 2
    c.initialize()
    assert c.name == name
    assert c.n() == 0
    assert c.count() == 0
    v = 0
    for i in range(100):
        c.ingest(2 * i)
        v += 2 * i
    assert c.n() == 100
    assert c.count() == v
    with pytest.raises(TypeError):
        Counter(4)
    with pytest.raises(TypeError):
        c.ingest('x')
    with pytest.raises(TypeError):
        c.ingest('2.0')


def test_tally_0():
    name = "tally description"
    t: Tally = Tally(name)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 0
    assert math.isnan(t.min())
    assert math.isnan(t.max())
    assert math.isnan(t.sample_mean())
    assert math.isnan(t.population_mean())
    assert math.isnan(t.sample_variance())
    assert math.isnan(t.population_variance())
    assert math.isnan(t.sample_stdev())
    assert math.isnan(t.population_stdev())
    assert math.isnan(t.sample_skewness())
    assert math.isnan(t.population_skewness())
    assert math.isnan(t.sample_kurtosis())
    assert math.isnan(t.population_kurtosis())
    assert math.isnan(t.sample_excess_kurtosis())
    assert math.isnan(t.population_excess_kurtosis())
    assert t.sum() == 0.0
    assert math.isnan(t.confidence_interval(0.95)[0])
    assert math.isnan(t.confidence_interval(0.95)[1])
    

def test_tally_1():
    name = "tally description"
    t: Tally = Tally(name)
    t.ingest(1.1)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 1
    assert t.min() == 1.1
    assert t.max() == 1.1
    assert t.sample_mean() == 1.1
    assert t.population_mean() == 1.1
    assert math.isnan(t.sample_variance())
    assert t.population_variance() == 0.0
    assert math.isnan(t.sample_stdev())
    assert t.population_stdev() == 0.0
    assert math.isnan(t.sample_skewness())
    assert math.isnan(t.population_skewness())
    assert math.isnan(t.sample_kurtosis())
    assert math.isnan(t.population_kurtosis())
    assert math.isnan(t.sample_excess_kurtosis())
    assert math.isnan(t.population_excess_kurtosis())
    assert t.sum() == 1.1
    assert math.isnan(t.confidence_interval(0.95)[0])
    assert math.isnan(t.confidence_interval(0.95)[1])


def test_tally_11():
    name = "tally description"
    t: Tally = Tally(name)
    for i in range(11):
        t.ingest(1.0 + 0.1 * i)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 11
    assert math.isclose(t.min(), 1.0)
    assert math.isclose(t.max(), 2.0)
    assert math.isclose(t.sum(), 16.5)
    
    # some test values from: https://atozmath.com/StatsUG.aspx
    assert math.isclose(t.sample_mean(), 1.5)
    assert math.isclose(t.population_mean(), 1.5)
    assert math.isclose(t.sample_variance(), 0.11, abs_tol=1E-6)
    assert math.isclose(t.population_variance(), 0.1, abs_tol=1E-6)
    assert math.isclose(t.sample_stdev(), 0.331662, abs_tol=1E-6)
    assert math.isclose(t.population_stdev(), math.sqrt(0.1), abs_tol=1E-6)
    assert math.isclose(t.sample_skewness(), 0.0, abs_tol=1E-6)
    assert math.isclose(t.population_skewness(), 0.0, abs_tol=1E-6)
    assert math.isclose(t.sample_kurtosis(), 1.618182, abs_tol=1E-6)
    assert math.isclose(t.population_kurtosis(), 1.78, abs_tol=1E-6)
    assert math.isclose(t.sample_excess_kurtosis(), -1.2, abs_tol=1E-6)
    assert math.isclose(t.population_excess_kurtosis(), -1.22, abs_tol=1E-6)

    assert math.isclose(t.confidence_interval(0.05)[0], 1.304003602, abs_tol=1E-5)
    assert math.isclose(t.confidence_interval(0.05)[1], 1.695996398, abs_tol=1E-5)
    assert math.isclose(t.confidence_interval(0.10)[0], 1.335514637, abs_tol=1E-5)
    assert math.isclose(t.confidence_interval(0.10)[1], 1.664485363, abs_tol=1E-5)
    assert math.isclose(t.confidence_interval(0.15)[0], 1.356046853, abs_tol=1E-5)
    assert math.isclose(t.confidence_interval(0.15)[1], 1.643953147, abs_tol=1E-5)
    assert math.isclose(t.confidence_interval(0.50)[0], 1.432551025, abs_tol=1E-5)
    assert math.isclose(t.confidence_interval(0.50)[1], 1.567448975, abs_tol=1E-5)
    assert math.isclose(t.confidence_interval(0.80)[0], 1.474665290, abs_tol=1E-5)
    assert math.isclose(t.confidence_interval(0.80)[1], 1.525334710, abs_tol=1E-5)
    assert math.isclose(t.confidence_interval(0.95)[0], 1.493729322, abs_tol=1E-5)
    assert math.isclose(t.confidence_interval(0.95)[1], 1.506270678, abs_tol=1E-5)


def test_tally_errors():
    t: Tally = Tally("tally")
    with pytest.raises(TypeError):
        Tally(4)
    with pytest.raises(TypeError):
        t.ingest('x')
    with pytest.raises(TypeError):
        t.ingest('2.0')
    with pytest.raises(ValueError):
        t.ingest(math.nan)
    for i in range(10):
        t.ingest(i)
    with pytest.raises(TypeError):
        t.confidence_interval('x')
    with pytest.raises(ValueError):
        t.confidence_interval(-0.05)
    with pytest.raises(ValueError):
        t.confidence_interval(1.05)


def test_w_tally_0():
    name = "weighted tally description"
    t: WeightedTally = WeightedTally(name)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 0
    assert math.isnan(t.min())
    assert math.isnan(t.max())
    assert math.isnan(t.weighted_sample_mean())
    assert math.isnan(t.weighted_population_mean())
    assert math.isnan(t.weighted_sample_variance())
    assert math.isnan(t.weighted_population_variance())
    assert math.isnan(t.weighted_sample_stdev())
    assert math.isnan(t.weighted_population_stdev())
    assert t.weighted_sum() == 0.0
    

def test_w_tally_1():
    name = "weighted tally description"
    t: WeightedTally = WeightedTally(name)
    t.ingest(0.1, 1.1)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 1
    assert t.min() == 1.1
    assert t.max() == 1.1
    assert math.isclose(t.weighted_sample_mean(), 1.1)
    assert math.isclose(t.weighted_population_mean(), 1.1)
    assert math.isnan(t.weighted_sample_variance())
    assert t.weighted_population_variance() == 0.0
    assert math.isnan(t.weighted_sample_stdev())
    assert t.weighted_population_stdev() == 0.0
    assert math.isclose(t.weighted_sum(), 0.11)


def test_w_tally_11():
    name = "weighted tally description"
    t: WeightedTally = WeightedTally(name)
    for i in range(11):
        t.ingest(0.1, 1.0 + 0.1 * i)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 11
    assert math.isclose(t.min(), 1.0)
    assert math.isclose(t.max(), 2.0)
    assert math.isclose(t.weighted_sum(), 1.5 * 0.1 * 11)
    
    assert math.isclose(t.weighted_sample_mean(), 1.5)
    assert math.isclose(t.weighted_population_mean(), 1.5)
    
    # Let's compute the standard deviation
    variance = 0;
    for i  in range(11):
        variance += math.pow(1.5 - (1.0 + i / 10.0), 2)
    variance = variance / 10.0;
    stdev = math.sqrt(variance)

    assert math.isclose(t.weighted_sample_variance(), variance, abs_tol=1E-6)
    assert math.isclose(t.weighted_population_variance(), 0.1, abs_tol=1E-6)
    assert math.isclose(t.weighted_sample_stdev(), stdev, abs_tol=1E-6)
    assert math.isclose(t.weighted_population_stdev(), math.sqrt(0.1), abs_tol=1E-6)
    
    t.ingest(0.0, 10.0)
    assert t.n() == 11
    assert math.isclose(t.min(), 1.0)
    assert math.isclose(t.max(), 2.0)
    assert math.isclose(t.weighted_sum(), 1.5 * 0.1 * 11)


def test_w_tally_errors():
    t: WeightedTally = WeightedTally("w-tally")
    with pytest.raises(TypeError):
        WeightedTally(4)
    with pytest.raises(TypeError):
        t.ingest('x', 1.0)
    with pytest.raises(TypeError):
        t.ingest(1.0, 'x')
    with pytest.raises(ValueError):
        t.ingest(-0.5, 2.0)
    with pytest.raises(ValueError):
        t.ingest(math.nan, 1.0)
    with pytest.raises(ValueError):
        t.ingest(1.0, math.nan)


def test_t_tally_0():
    name = "timestamped tally description"
    t: TimestampWeightedTally = TimestampWeightedTally(name)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 0
    assert t.isactive()
    assert t.last_value() == 0.0
    assert math.isnan(t.min())
    assert math.isnan(t.max())
    assert math.isnan(t.weighted_sample_mean())
    assert math.isnan(t.weighted_population_mean())
    assert math.isnan(t.weighted_sample_variance())
    assert math.isnan(t.weighted_population_variance())
    assert math.isnan(t.weighted_sample_stdev())
    assert math.isnan(t.weighted_population_stdev())
    assert t.weighted_sum() == 0.0
    

def test_t_tally_1():
    name = "timestamped tally description"
    t: TimestampWeightedTally = TimestampWeightedTally(name)
    t.ingest(0.1, 1.1)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 0
    assert t.isactive()
    assert t.last_value() == 1.1
    t.ingest(0.2, 1.1)
    assert t.min() == 1.1
    assert t.max() == 1.1
    assert math.isclose(t.weighted_sample_mean(), 1.1)
    assert math.isclose(t.weighted_population_mean(), 1.1)
    assert math.isnan(t.weighted_sample_variance())
    assert t.weighted_population_variance() == 0.0
    assert math.isnan(t.weighted_sample_stdev())
    assert t.weighted_population_stdev() == 0.0
    assert math.isclose(t.weighted_sum(), 0.11)


def test_t_tally_11():
    name = "timestamped tally description"
    t: TimestampWeightedTally = TimestampWeightedTally(name)
    for i in range(11):
        t.ingest(i * 0.1, 1.0 + 0.1 * i)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 10
    assert math.isclose(t.min(), 1.0)
    assert math.isclose(t.max(), 1.9)
    t.end_observations(1.1)
    assert not t.isactive()
    assert t.n() == 11
    assert math.isclose(t.max(), 2.0)
    assert math.isclose(t.weighted_sum(), 1.5 * 0.1 * 11)
    
    assert math.isclose(t.weighted_sample_mean(), 1.5)
    assert math.isclose(t.weighted_population_mean(), 1.5)
    
    # Let's compute the standard deviation
    variance = 0;
    for i  in range(11):
        variance += math.pow(1.5 - (1.0 + i / 10.0), 2)
    variance = variance / 10.0;
    stdev = math.sqrt(variance)

    assert math.isclose(t.weighted_sample_variance(), variance, abs_tol=1E-6)
    assert math.isclose(t.weighted_population_variance(), 0.1, abs_tol=1E-6)
    assert math.isclose(t.weighted_sample_stdev(), stdev, abs_tol=1E-6)
    assert math.isclose(t.weighted_population_stdev(), math.sqrt(0.1), abs_tol=1E-6)
    

def test_t_tally_errors():
    t: TimestampWeightedTally = TimestampWeightedTally("tw-tally")
    with pytest.raises(TypeError):
        TimestampWeightedTally(4)
    with pytest.raises(TypeError):
        t.ingest('x', 1.0)
    with pytest.raises(TypeError):
        t.ingest(1.0, 'x')
    with pytest.raises(ValueError):
        t.ingest(math.nan, 1.0)
    with pytest.raises(ValueError):
        t.ingest(1.0, math.nan)
    t.ingest(2.0, 4)
    with pytest.raises(ValueError):
        t.ingest(1.0, 5)  # back in time


if __name__ == "__main__":
    pytest.main()
