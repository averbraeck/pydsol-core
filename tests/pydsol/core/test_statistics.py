import logging
import math
import sys
import time

import pytest

from pydsol.core.experiment import SingleReplication, Replication
from pydsol.core.interfaces import StatEvents, ReplicationInterface
from pydsol.core.model import DSOLModel
from pydsol.core.pubsub import EventListener, Event, TimedEvent, EventError, \
    EventProducer, EventType
from pydsol.core.simulator import DEVSSimulator, DEVSSimulatorFloat, \
    ErrorStrategy
from pydsol.core.statistics import Counter, Tally, WeightedTally, \
    TimestampWeightedTally, EventBasedCounter, EventBasedTally, \
    EventBasedWeightedTally, EventBasedTimestampWeightedTally, SimCounter
from pydsol.core.units import Duration


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

#----------------------------------------------------------------------------
# Tests for EventBased statistics
#----------------------------------------------------------------------------


class LoggingEventListener(EventListener):

    def __init__(self):
        self.last_event: Event = None
        self.nr_events: int = 0
    
    def notify(self, event: Event):
        self.last_event = event
        self.nr_events += 1
    

class CounterEventListener(EventListener):

    def __init__(self):
        self.count_events: int = 0
    
    def notify(self, event: Event):
        assert event.event_type == StatEvents.OBSERVATION_ADDED_EVENT
        assert isinstance(event.content, int)
        self.count_events += 1

        
def test_e_counter():
    name = "event-based counter description"
    c: EventBasedCounter = EventBasedCounter(name)
    assert c.name == name
    assert name in str(c)
    assert name in repr(c)
    assert c.n() == 0
    assert c.count() == 0
    c.notify(Event(StatEvents.DATA_EVENT, 2))
    assert c.n() == 1
    assert c.count() == 2
    
    c.initialize()
    assert c.name == name
    assert c.n() == 0
    assert c.count() == 0
    cel: CounterEventListener = CounterEventListener()
    c.add_listener(StatEvents.OBSERVATION_ADDED_EVENT, cel)
    assert cel.count_events == 0
    nl: LoggingEventListener = LoggingEventListener()
    c.add_listener(StatEvents.N_EVENT, nl)
    cl: LoggingEventListener = LoggingEventListener()
    c.add_listener(StatEvents.COUNT_EVENT, cl)
    v = 0
    for i in range(100):
        c.notify(Event(StatEvents.DATA_EVENT, 2 * i))
        v += 2 * i
    assert c.n() == 100
    assert c.count() == v
    assert cel.count_events == 100
    assert nl.nr_events == 100
    assert cl.nr_events == 100
    assert nl.last_event.content == 100
    assert cl.last_event.content == v
    
    with pytest.raises(TypeError):
        EventBasedCounter(4)
    with pytest.raises(TypeError):
        c.notify(Event(StatEvents.DATA_EVENT, 'abc'))
    with pytest.raises(ValueError):
        c.notify(Event(StatEvents.N_EVENT, 1))


class TallyEventListener(EventListener):

    def __init__(self):
        self.nr_events: int = 0
        self.last_observation = math.nan
    
    def notify(self, event: Event):
        assert event.event_type == StatEvents.OBSERVATION_ADDED_EVENT
        assert isinstance(event.content, float)
        self.nr_events += 1
        self.last_observation = event.content


def test_e_tally_11():
    name = "event-based tally description"
    t: EventBasedTally = EventBasedTally(name)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 0
    assert math.isnan(t.min())
    assert math.isnan(t.max())

    tel: TallyEventListener = TallyEventListener()
    t.add_listener(StatEvents.OBSERVATION_ADDED_EVENT, tel)
    assert tel.nr_events == 0
    log_n: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.N_EVENT, log_n)
    log_pm: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.POPULATION_MEAN_EVENT, log_pm)
    log_sm: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.SAMPLE_MEAN_EVENT, log_sm)
    log_min: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.MIN_EVENT, log_min)
    log_max: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.MAX_EVENT, log_max)
    log_sum: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.SUM_EVENT, log_sum)
    
    for i in range(11):
        t.notify(Event(StatEvents.DATA_EVENT, 1.0 + 0.1 * i))
    assert t.n() == 11
    assert tel.nr_events == 11
    assert tel.last_observation == 2.0
    assert log_n.nr_events == 11
    assert log_n.last_event.content == 11
    assert math.isclose(t.min(), 1.0)
    assert log_min.nr_events == 11
    assert log_min.last_event.content == 1.0
    assert math.isclose(t.max(), 2.0)
    assert log_max.nr_events == 11
    assert log_max.last_event.content == 2.0
    assert math.isclose(t.sum(), 16.5)
    assert log_sum.nr_events == 11
    assert log_sum.last_event.content == 16.5
    assert math.isclose(t.sample_mean(), 1.5)
    assert math.isclose(log_sm.last_event.content, 1.5)
    assert math.isclose(t.population_mean(), 1.5)
    assert math.isclose(log_pm.last_event.content, 1.5)

    with pytest.raises(TypeError):
        EventBasedTally(4)
    with pytest.raises(TypeError):
        t.notify(Event(StatEvents.DATA_EVENT, 'abc'))
    with pytest.raises(ValueError):
        t.notify(Event(StatEvents.N_EVENT, 1))


def test_e_w_tally_11():
    name = "event-based weighted tally description"
    t: EventBasedWeightedTally = EventBasedWeightedTally(name)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 0
    assert math.isnan(t.min())
    assert math.isnan(t.max())

    tel: TallyEventListener = TallyEventListener()
    t.add_listener(StatEvents.OBSERVATION_ADDED_EVENT, tel)
    assert tel.nr_events == 0
    log_n: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.N_EVENT, log_n)
    log_pm: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_POPULATION_MEAN_EVENT, log_pm)
    log_sm: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_SAMPLE_MEAN_EVENT, log_sm)
    log_min: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.MIN_EVENT, log_min)
    log_max: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.MAX_EVENT, log_max)
    log_sum: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_SUM_EVENT, log_sum)
    log_pstd: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_POPULATION_STDEV_EVENT, log_pstd)
    log_sstd: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_SAMPLE_STDEV_EVENT, log_sstd)
    log_pvar: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_POPULATION_VARIANCE_EVENT, log_pvar)
    log_svar: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_SAMPLE_VARIANCE_EVENT, log_svar)
    
    for i in range(11):
        t.notify(Event(StatEvents.WEIGHT_DATA_EVENT, (0.1, 1.0 + 0.1 * i)))
    assert t.n() == 11
    assert tel.nr_events == 11
    assert tel.last_observation == 2.0
    assert log_n.nr_events == 11
    assert log_n.last_event.content == 11
    assert math.isclose(t.min(), 1.0)
    assert log_min.nr_events == 11
    assert log_min.last_event.content == 1.0
    assert math.isclose(t.max(), 2.0)
    assert log_max.nr_events == 11
    assert log_max.last_event.content == 2.0
    assert math.isclose(t.weighted_sum(), 1.5 * 0.1 * 11)
    assert log_sum.nr_events == 11
    assert math.isclose(log_sum.last_event.content, 1.5 * 0.1 * 11)
    assert math.isclose(t.weighted_sample_mean(), 1.5)
    assert math.isclose(log_sm.last_event.content, 1.5)
    assert math.isclose(t.weighted_population_mean(), 1.5)
    assert math.isclose(log_pm.last_event.content, 1.5)
    assert math.isclose(t.weighted_population_stdev(), 0.316228, abs_tol=1E-6)
    assert math.isclose(log_pstd.last_event.content, 0.316228, abs_tol=1E-6)
    assert math.isclose(t.weighted_sample_stdev(), 0.331662, abs_tol=1E-6)
    assert math.isclose(log_sstd.last_event.content, 0.331662, abs_tol=1E-6)
    assert math.isclose(t.weighted_population_variance(), 0.1, abs_tol=1E-6)
    assert math.isclose(log_pvar.last_event.content, 0.1, abs_tol=1E-6)
    assert math.isclose(t.weighted_sample_variance(), 0.11, abs_tol=1E-6)
    assert math.isclose(log_svar.last_event.content, 0.11, abs_tol=1E-6)

    with pytest.raises(TypeError):
        EventBasedWeightedTally(4)
    with pytest.raises(ValueError):
        t.notify(Event(StatEvents.DATA_EVENT, 1))
    with pytest.raises(TypeError):
        t.notify(Event(StatEvents.WEIGHT_DATA_EVENT, 'abc'))
    with pytest.raises(TypeError):
        t.notify(Event(StatEvents.WEIGHT_DATA_EVENT, (1.0,)))
    with pytest.raises(TypeError):
        t.notify(Event(StatEvents.WEIGHT_DATA_EVENT, (1.0, 'abc')))
    with pytest.raises(TypeError):
        t.notify(Event(StatEvents.WEIGHT_DATA_EVENT, ('abc', 1.0)))
    with pytest.raises(TypeError):
        t.notify(Event(StatEvents.WEIGHT_DATA_EVENT, (1.0, 2.0, 3.0)))


def test_e_t_tally_11():
    name = "event-based weighted tally description"
    t: EventBasedTimestampWeightedTally = EventBasedTimestampWeightedTally(name)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 0
    assert math.isnan(t.min())
    assert math.isnan(t.max())

    tel: TallyEventListener = TallyEventListener()
    t.add_listener(StatEvents.OBSERVATION_ADDED_EVENT, tel)
    assert tel.nr_events == 0
    log_n: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.N_EVENT, log_n)
    log_pm: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_POPULATION_MEAN_EVENT, log_pm)
    log_sm: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_SAMPLE_MEAN_EVENT, log_sm)
    log_min: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.MIN_EVENT, log_min)
    log_max: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.MAX_EVENT, log_max)
    log_sum: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_SUM_EVENT, log_sum)
    log_pstd: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_POPULATION_STDEV_EVENT, log_pstd)
    log_sstd: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_SAMPLE_STDEV_EVENT, log_sstd)
    log_pvar: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_POPULATION_VARIANCE_EVENT, log_pvar)
    log_svar: LoggingEventListener = LoggingEventListener()
    t.add_listener(StatEvents.WEIGHTED_SAMPLE_VARIANCE_EVENT, log_svar)
    
    for i in range(11):
        t.notify(TimedEvent(0.1 * i, StatEvents.TIMESTAMP_DATA_EVENT,
                            1.0 + 0.1 * i))
    assert t.n() == 10
    assert math.isclose(t.min(), 1.0)
    assert math.isclose(t.max(), 1.9)
    t.end_observations(1.1)
    assert not t.isactive()

    assert t.n() == 11
    assert tel.nr_events == 12  # the event-listeners all got 1 extra event
    assert tel.last_observation == 2.0
    assert log_n.nr_events == 12
    assert log_n.last_event.content == 11
    assert math.isclose(t.min(), 1.0)
    assert log_min.nr_events == 12
    assert log_min.last_event.content == 1.0
    assert math.isclose(t.max(), 2.0)
    assert log_max.nr_events == 12
    assert log_max.last_event.content == 2.0
    assert math.isclose(t.weighted_sum(), 1.5 * 0.1 * 11)
    assert math.isclose(log_sum.last_event.content, 1.5 * 0.1 * 11)
    assert log_sum.nr_events == 12
        
    # Let's compute the standard deviation
    variance = 0;
    for i  in range(11):
        variance += math.pow(1.5 - (1.0 + i / 10.0), 2)
    variance = variance / 10.0;
    stdev = math.sqrt(variance)

    assert math.isclose(log_sum.last_event.content, 1.5 * 0.1 * 11)
    assert math.isclose(t.weighted_sample_mean(), 1.5)
    assert math.isclose(log_sm.last_event.content, 1.5)
    assert math.isclose(t.weighted_population_mean(), 1.5)
    assert math.isclose(log_pm.last_event.content, 1.5)
    assert math.isclose(t.weighted_population_stdev(), math.sqrt(0.1), abs_tol=1E-6)
    assert math.isclose(log_pstd.last_event.content, math.sqrt(0.1), abs_tol=1E-6)
    assert math.isclose(t.weighted_sample_stdev(), stdev, abs_tol=1E-6)
    assert math.isclose(log_sstd.last_event.content, stdev, abs_tol=1E-6)
    assert math.isclose(t.weighted_population_variance(), 0.1, abs_tol=1E-6)
    assert math.isclose(log_pvar.last_event.content, 0.1, abs_tol=1E-6)
    assert math.isclose(t.weighted_sample_variance(), variance, abs_tol=1E-6)
    assert math.isclose(log_svar.last_event.content, variance, abs_tol=1E-6)
    
    t.notify(TimedEvent(Duration(3.0, 's'), StatEvents.TIMESTAMP_DATA_EVENT, 2))

    with pytest.raises(TypeError):
        EventBasedTimestampWeightedTally(4)
    with pytest.raises(ValueError):
        t.notify(TimedEvent(1.0, StatEvents.WEIGHT_DATA_EVENT, 2))
    with pytest.raises(TypeError):
        t.notify(Event(StatEvents.TIMESTAMP_DATA_EVENT, 2))
    with pytest.raises(TypeError):
        t.notify(TimedEvent(1.0, StatEvents.TIMESTAMP_DATA_EVENT, 'abc'))
    with pytest.raises(EventError):
        t.notify(TimedEvent('abc', StatEvents.TIMESTAMP_DATA_EVENT, 1.0))

#----------------------------------------------------------------------------
# Tests for Simulation statistics
#----------------------------------------------------------------------------


class QueuingModel(DSOLModel, EventProducer):
    
    GEN_EVENT: EventType = EventType("GEN_EVENT")
    
    def __init__(self, simulator: DEVSSimulator):
        DSOLModel.__init__(self, simulator)
        EventProducer.__init__(self)
    
    def construct_model(self):
        self.simulator.schedule_event_now(self, "generate", i=1.0)
        self.gen_counter: SimCounter = SimCounter("generator.nr",
            "number of generated entities", self.simulator)
        self.gen_counter.listen_to(self, self.GEN_EVENT)

    def generate(self, i:float):
        t = self.simulator.simulator_time
        # count the generated items
        self.simulator.schedule_event_rel(i, self, "generate", i=i + 1.0)
        self.fire_timed_event(TimedEvent(t, self.GEN_EVENT, 1))
        # sys.stdout.write(f"gen at {t}\n")- combine with --capture=tee-sys

        
class Simulation(EventListener):

    def __init__(self):
        self.simulator: DEVSSimulatorFloat = DEVSSimulatorFloat("sim")
        self.simulator.set_error_strategy(ErrorStrategy.WARN_AND_END,
                                          logging.FATAL)
        self.simulator.add_listener(ReplicationInterface.END_REPLICATION_EVENT, self)
        self.model: DSOLModel = QueuingModel(self.simulator)
        replication: Replication = SingleReplication("rep", 0.0, 0.0, 20.0)
        self.simulator.initialize(self.model, replication)
        self.simulator.start()

    def notify(self, event: Event):
        if event.event_type == ReplicationInterface.END_REPLICATION_EVENT:
            m: QueuingModel = self.model
            gc: SimCounter = m.gen_counter
            assert gc.key == "generator.nr"
            # times are 0, 1, 3, 6, 10, 15, (not 21)
            assert gc.n() == 6
            assert gc.count() == 6
            assert len(gc.report_footer()) == 72 
            assert "count" in gc.report_header()
            assert " 6 " in gc.report_line()
            assert gc.name in gc.report_line()


def test_sim_stats():
    s = Simulation()
    t = time.time()
    while s.simulator.is_starting_or_running() and time.time() - t < 1.0:
        time.sleep(0.001)
    t_after = time.time()
    s.simulator.cleanup()
    assert t_after - t < 1.0


if __name__ == "__main__":
    pytest.main()
