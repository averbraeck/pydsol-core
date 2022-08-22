import logging
import math
import time

import pytest

from pydsol.core.experiment import SingleReplication, Replication
from pydsol.core.interfaces import StatEvents
from pydsol.core.model import DSOLModel
from pydsol.core.pubsub import EventListener, Event, TimedEvent, EventError, \
    EventProducer, EventType
from pydsol.core.simulator import DEVSSimulator, DEVSSimulatorFloat, \
    ErrorStrategy
from pydsol.core.statistics import Counter, Tally, WeightedTally, \
    TimestampWeightedTally, EventBasedCounter, EventBasedTally, \
    EventBasedWeightedTally, EventBasedTimestampWeightedTally, SimCounter, \
    SimTally, SimPersistent
from pydsol.core.units import Duration


def test_counter():
    name = "counter description"
    c: Counter = Counter(name)
    assert c.name == name
    assert name in str(c)
    assert name in repr(c)
    assert c.n() == 0
    assert c.count() == 0
    c.register(2)
    assert c.n() == 1
    assert c.count() == 2
    c.initialize()
    assert c.name == name
    assert c.n() == 0
    assert c.count() == 0
    v = 0
    for i in range(100):
        c.register(2 * i)
        v += 2 * i
    assert c.n() == 100
    assert c.count() == v
    with pytest.raises(TypeError):
        Counter(4)
    with pytest.raises(TypeError):
        c.register('x')
    with pytest.raises(TypeError):
        c.register('2.0')


def test_tally_0():
    name = "tally description"
    t: Tally = Tally(name)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 0
    assert math.isnan(t.min())
    assert math.isnan(t.max())
    assert math.isnan(t.mean())
    assert math.isnan(t.variance(False))
    assert math.isnan(t.variance())
    assert math.isnan(t.stdev(False))
    assert math.isnan(t.stdev())
    assert math.isnan(t.skewness(False))
    assert math.isnan(t.skewness())
    assert math.isnan(t.kurtosis(False))
    assert math.isnan(t.kurtosis())
    assert math.isnan(t.excess_kurtosis(False))
    assert math.isnan(t.excess_kurtosis())
    assert t.sum() == 0.0
    assert math.isnan(t.confidence_interval(0.95)[0])
    assert math.isnan(t.confidence_interval(0.95)[1])
    

def test_tally_1():
    name = "tally description"
    t: Tally = Tally(name)
    t.register(1.1)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 1
    assert t.min() == 1.1
    assert t.max() == 1.1
    assert t.mean() == 1.1
    assert math.isnan(t.variance(False))
    assert t.variance() == 0.0
    assert math.isnan(t.stdev(False))
    assert t.stdev() == 0.0
    assert math.isnan(t.skewness(False))
    assert math.isnan(t.skewness())
    assert math.isnan(t.kurtosis(False))
    assert math.isnan(t.kurtosis())
    assert math.isnan(t.excess_kurtosis(False))
    assert math.isnan(t.excess_kurtosis())
    assert t.sum() == 1.1
    assert math.isnan(t.confidence_interval(0.95)[0])
    assert math.isnan(t.confidence_interval(0.95)[1])


def test_tally_11():
    name = "tally description"
    t: Tally = Tally(name)
    for i in range(11):
        t.register(1.0 + 0.1 * i)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 11
    assert math.isclose(t.min(), 1.0)
    assert math.isclose(t.max(), 2.0)
    assert math.isclose(t.sum(), 16.5)
    
    # some test values from: https://atozmath.com/StatsUG.aspx
    assert math.isclose(t.mean(), 1.5)
    assert math.isclose(t.variance(False), 0.11, abs_tol=1E-6)
    assert math.isclose(t.variance(), 0.1, abs_tol=1E-6)
    assert math.isclose(t.stdev(False), 0.331662, abs_tol=1E-6)
    assert math.isclose(t.stdev(), math.sqrt(0.1), abs_tol=1E-6)
    assert math.isclose(t.skewness(False), 0.0, abs_tol=1E-6)
    assert math.isclose(t.skewness(), 0.0, abs_tol=1E-6)
    assert math.isclose(t.kurtosis(False), 1.618182, abs_tol=1E-6)
    assert math.isclose(t.kurtosis(), 1.78, abs_tol=1E-6)
    assert math.isclose(t.excess_kurtosis(False), -1.2, abs_tol=1E-6)
    assert math.isclose(t.excess_kurtosis(), -1.22, abs_tol=1E-6)

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
        t.register('x')
    with pytest.raises(TypeError):
        t.register('2.0')
    with pytest.raises(ValueError):
        t.register(math.nan)
    for i in range(10):
        t.register(i)
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
    assert math.isnan(t.weighted_mean())
    assert math.isnan(t.weighted_variance(False))
    assert math.isnan(t.weighted_variance())
    assert math.isnan(t.weighted_stdev(False))
    assert math.isnan(t.weighted_stdev())
    assert t.weighted_sum() == 0.0
    

def test_w_tally_1():
    name = "weighted tally description"
    t: WeightedTally = WeightedTally(name)
    t.register(0.1, 1.1)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 1
    assert t.min() == 1.1
    assert t.max() == 1.1
    assert math.isclose(t.weighted_mean(), 1.1)
    assert math.isnan(t.weighted_variance(False))
    assert t.weighted_variance() == 0.0
    assert math.isnan(t.weighted_stdev(False))
    assert t.weighted_stdev() == 0.0
    assert math.isclose(t.weighted_sum(), 0.11)


def test_w_tally_11():
    name = "weighted tally description"
    t: WeightedTally = WeightedTally(name)
    for i in range(11):
        t.register(0.1, 1.0 + 0.1 * i)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 11
    assert math.isclose(t.min(), 1.0)
    assert math.isclose(t.max(), 2.0)
    assert math.isclose(t.weighted_sum(), 1.5 * 0.1 * 11)
    assert math.isclose(t.weighted_mean(), 1.5)
    
    # Let's compute the standard deviation
    variance = 0;
    for i  in range(11):
        variance += math.pow(1.5 - (1.0 + i / 10.0), 2)
    variance = variance / 10.0;
    stdev = math.sqrt(variance)

    assert math.isclose(t.weighted_variance(False), variance, abs_tol=1E-6)
    assert math.isclose(t.weighted_variance(), 0.1, abs_tol=1E-6)
    assert math.isclose(t.weighted_stdev(False), stdev, abs_tol=1E-6)
    assert math.isclose(t.weighted_stdev(), math.sqrt(0.1), abs_tol=1E-6)
    
    # note that an observation with a zero weight is STILL an observation
    t.register(0.0, 10.0)
    assert t.n() == 12 
    assert math.isclose(t.min(), 1.0)
    assert math.isclose(t.max(), 10.0)
    assert math.isclose(t.weighted_sum(), 1.5 * 0.1 * 11)
    assert math.isclose(t.weighted_mean(), 1.5 * 0.1 * 11 / 1.1)


def test_w_tally_errors():
    t: WeightedTally = WeightedTally("w-tally")
    with pytest.raises(TypeError):
        WeightedTally(4)
    with pytest.raises(TypeError):
        t.register('x', 1.0)
    with pytest.raises(TypeError):
        t.register(1.0, 'x')
    with pytest.raises(ValueError):
        t.register(-0.5, 2.0)
    with pytest.raises(ValueError):
        t.register(math.nan, 1.0)
    with pytest.raises(ValueError):
        t.register(1.0, math.nan)


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
    assert math.isnan(t.weighted_mean())
    assert math.isnan(t.weighted_variance(False))
    assert math.isnan(t.weighted_variance())
    assert math.isnan(t.weighted_stdev(False))
    assert math.isnan(t.weighted_stdev())
    assert t.weighted_sum() == 0.0
    

def test_t_tally_1():
    name = "timestamped tally description"
    t: TimestampWeightedTally = TimestampWeightedTally(name)
    t.register(0.1, 1.1)
    assert t.name == name
    assert name in str(t)
    assert name in repr(t)
    assert t.n() == 0
    assert t.isactive()
    assert t.last_value() == 1.1
    t.register(0.2, 1.1)
    assert t.min() == 1.1
    assert t.max() == 1.1
    assert math.isclose(t.weighted_mean(), 1.1)
    assert math.isnan(t.weighted_variance(False))
    assert t.weighted_variance() == 0.0
    assert math.isnan(t.weighted_stdev(False))
    assert t.weighted_stdev() == 0.0
    assert math.isclose(t.weighted_sum(), 0.11)


def test_t_tally_11():
    name = "timestamped tally description"
    t: TimestampWeightedTally = TimestampWeightedTally(name)
    for i in range(11):
        t.register(i * 0.1, 1.0 + 0.1 * i)
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
    assert math.isclose(t.weighted_mean(), 1.5)
    
    # Let's compute the standard deviation
    variance = 0;
    for i  in range(11):
        variance += math.pow(1.5 - (1.0 + i / 10.0), 2)
    variance = variance / 10.0;
    stdev = math.sqrt(variance)

    assert math.isclose(t.weighted_variance(False), variance, abs_tol=1E-6)
    assert math.isclose(t.weighted_variance(), 0.1, abs_tol=1E-6)
    assert math.isclose(t.weighted_stdev(False), stdev, abs_tol=1E-6)
    assert math.isclose(t.weighted_stdev(), math.sqrt(0.1), abs_tol=1E-6)
    

def test_t_tally_errors():
    t: TimestampWeightedTally = TimestampWeightedTally("tw-tally")
    with pytest.raises(TypeError):
        TimestampWeightedTally(4)
    with pytest.raises(TypeError):
        t.register('x', 1.0)
    with pytest.raises(TypeError):
        t.register(1.0, 'x')
    with pytest.raises(ValueError):
        t.register(math.nan, 1.0)
    with pytest.raises(ValueError):
        t.register(1.0, math.nan)
    t.register(2.0, 4)
    with pytest.raises(ValueError):
        t.register(1.0, 5)  # back in time

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
    t.add_listener(StatEvents.MEAN_EVENT, log_pm)
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
    assert math.isclose(t.mean(), 1.5)
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
    t.add_listener(StatEvents.WEIGHTED_MEAN_EVENT, log_pm)
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
    assert math.isclose(t.weighted_mean(), 1.5)
    assert math.isclose(log_pm.last_event.content, 1.5)
    assert math.isclose(t.weighted_stdev(), 0.316228, abs_tol=1E-6)
    assert math.isclose(log_pstd.last_event.content, 0.316228, abs_tol=1E-6)
    assert math.isclose(t.weighted_stdev(False), 0.331662, abs_tol=1E-6)
    assert math.isclose(log_sstd.last_event.content, 0.331662, abs_tol=1E-6)
    assert math.isclose(t.weighted_variance(), 0.1, abs_tol=1E-6)
    assert math.isclose(log_pvar.last_event.content, 0.1, abs_tol=1E-6)
    assert math.isclose(t.weighted_variance(False), 0.11, abs_tol=1E-6)
    assert math.isclose(log_svar.last_event.content, 0.11, abs_tol=1E-6)

    with pytest.raises(TypeError):
        EventBasedWeightedTally(4)
    with pytest.raises(ValueError):
        t.notify(Event(StatEvents.DATA_EVENT, 1))
    with pytest.raises(TypeError):
        t.notify(Event(StatEvents.WEIGHT_DATA_EVENT, 'abc'))
    with pytest.raises(ValueError):
        t.notify(Event(StatEvents.WEIGHT_DATA_EVENT, (1.0,)))
    with pytest.raises(TypeError):
        t.notify(Event(StatEvents.WEIGHT_DATA_EVENT, (1.0, 'abc')))
    with pytest.raises(TypeError):
        t.notify(Event(StatEvents.WEIGHT_DATA_EVENT, ('abc', 1.0)))
    with pytest.raises(ValueError):
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
    t.add_listener(StatEvents.WEIGHTED_MEAN_EVENT, log_pm)
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
    assert math.isclose(t.weighted_mean(), 1.5)
    assert math.isclose(log_pm.last_event.content, 1.5)
    assert math.isclose(t.weighted_stdev(), math.sqrt(0.1), abs_tol=1E-6)
    assert math.isclose(log_pstd.last_event.content, math.sqrt(0.1), abs_tol=1E-6)
    assert math.isclose(t.weighted_stdev(False), stdev, abs_tol=1E-6)
    assert math.isclose(log_sstd.last_event.content, stdev, abs_tol=1E-6)
    assert math.isclose(t.weighted_variance(), 0.1, abs_tol=1E-6)
    assert math.isclose(log_pvar.last_event.content, 0.1, abs_tol=1E-6)
    assert math.isclose(t.weighted_variance(False), variance, abs_tol=1E-6)
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


class StatisticsModel(DSOLModel, EventProducer):

    GEN_EVENT: EventType = EventType("GEN_EVENT")
    TALLY_EVENT: EventType = EventType("TALLY_EVENT")
    PERS_EVENT: EventType = EventType("PERS_EVENT")

    def __init__(self, simulator: DEVSSimulator):
        DSOLModel.__init__(self, simulator)
        EventProducer.__init__(self)

    def construct_model(self):
        self.simulator.schedule_event_now(self, "generate", i=1.0)
        self.gen_counter: SimCounter = SimCounter("generator.nr",
            "number of generated entities", self.simulator)
        # with listen_to
        self.gen_counter.listen_to(self, self.GEN_EVENT)
        self.gen_tally: SimTally = SimTally("generator.tally",
            "average value of i", self.simulator)
        self.gen_tally.listen_to(self, self.TALLY_EVENT)
        self.gen_pers: SimPersistent = SimPersistent("generator.pers",
            "time-weighed value of i", self.simulator)
        self.gen_pers.listen_to(self, self.PERS_EVENT)
        # without listen_to
        self.gen_counter2: SimCounter = SimCounter("generator.nr2",
            "number of generated entities", self.simulator,
            producer=self, event_type=self.GEN_EVENT)
        self.gen_tally2: SimTally = SimTally("generator.tally2",
            "average value of i", self.simulator,
            producer=self, event_type=self.TALLY_EVENT)
        self.gen_pers2: SimPersistent = SimPersistent("generator.pers2",
            "time-weighed value of i", self.simulator,
            producer=self, event_type=self.PERS_EVENT)
        # listen to events
        self.lelc: LoggingEventListener = LoggingEventListener()
        self.gen_counter.add_listener(StatEvents.N_EVENT, self.lelc)
        self.lelt: LoggingEventListener = LoggingEventListener()
        self.gen_tally.add_listener(StatEvents.N_EVENT, self.lelt)
        self.lelp: LoggingEventListener = LoggingEventListener()
        self.gen_pers.add_listener(StatEvents.N_EVENT, self.lelp)
    
    def generate(self, i:float):
        t = self.simulator.simulator_time
        # count the generated items
        self.simulator.schedule_event_rel(i, self, "generate", i=i + 1.0)
        self.fire_timed_event(TimedEvent(t, self.GEN_EVENT, 1))
        self.fire_timed_event(TimedEvent(t, self.TALLY_EVENT, i))
        self.fire_timed_event(TimedEvent(t, self.PERS_EVENT, i))
        # combine with --capture=tee-sys
        # import sys
        # sys.stdout.write(f"gen at {t}, value = {i}\n")


class Simulation():

    def __init__(self, warmup: float):
        self.simulator: DEVSSimulatorFloat = DEVSSimulatorFloat("sim")
        self.simulator.set_error_strategy(ErrorStrategy.WARN_AND_END,
                                          logging.FATAL)
        self.model: DSOLModel = StatisticsModel(self.simulator)
        replication: Replication = SingleReplication("rep", 0.0, warmup, 20.0)
        self.simulator.initialize(self.model, replication)
        self.simulator.start()


def test_sim_stats():
    s = Simulation(0.0)
    try:
        t = time.time()
        while s.simulator.is_starting_or_running() and time.time() - t < 1.0:
            time.sleep(0.001)
        t_after = time.time()
        assert t_after - t < 1.0
        
        m: StatisticsModel = s.model
        
        # SimCounter
        gc: SimCounter = m.gen_counter
        gc2: SimCounter = m.gen_counter2
        assert gc.key == "generator.nr"
        # times are 0, 1, 3, 6, 10, 15, (not 21)
        assert gc.n() == 6
        assert gc.count() == 6
        assert gc.n() == gc2.n()
        assert gc.count() == gc2.count()
        assert len(gc.report_footer()) == 72 
        assert "count" in gc.report_header()
        assert " 6 " in gc.report_line()
        assert gc.name in gc.report_line()
        
        assert m.lelc.nr_events == 6
        assert m.lelc.last_event.event_type == StatEvents.N_EVENT
        assert m.lelc.last_event.content == 6
        
        # SimTally
        gt: SimTally = m.gen_tally
        assert gt.key == "generator.tally"
        # average of 1, 2, 3, 4, 5, 6 = 3.5
        assert gt.n() == 6
        assert math.isclose(gt.mean(), 3.5) 
        assert len(gt.report_footer()) == 72
        assert "mean" in gt.report_header()
        assert " 3.5" in gt.report_line()
        assert gt.name in gt.report_line()
        
        assert m.lelt.nr_events == 6
        assert m.lelt.last_event.event_type == StatEvents.N_EVENT
        assert m.lelt.last_event.content == 6
    
        # SimTally
        gp: SimPersistent = m.gen_pers
        assert gp.key == "generator.pers"
        # times are   0,  1,  3,  6, 10, 15, 20
        # delta-t is  1,  2,  3,  4,  5,  5
        # average of  0,  1,  2,  3,  4,  5
        # weighed av (1 + 4 + 9 +16 +25 +30) / 20 = 85/20 = 4.25
        assert gp.n() == 6
        assert math.isclose(gp.weighted_mean(), 85.0 / 20.0) 
        assert len(gp.report_footer()) == 72
        assert "mean" in gp.report_header()
        assert "4.25" in gp.report_line()
        assert gp.name in gp.report_line()
        
        assert m.lelp.nr_events == 7 # including end_observation()
        assert m.lelp.last_event.event_type == StatEvents.N_EVENT
        assert m.lelp.last_event.content == 6

    except Exception as e:
        raise e
    finally:
        try:
            s.simulator.cleanup()
        except Exception:
            pass


def test_sim_warmup():
    s = Simulation(10.0)
    try:
        t = time.time()
        while s.simulator.is_starting_or_running() and time.time() - t < 1.0:
            time.sleep(0.001)
        t_after = time.time()
        assert t_after - t < 1.0
        
        m: StatisticsModel = s.model
        
        # SimCounter
        gc: SimCounter = m.gen_counter
        assert gc.key == "generator.nr"
        # times are x0, x1, x3, x6, 10, 15, (not 21)
        assert gc.n() == 2
        assert gc.count() == 2
    
        # SimTally
        gt: SimTally = m.gen_tally
        assert gt.key == "generator.tally"
        # average of x1, x2, x3, x4, 5, 6 = 5.5
        assert gt.n() == 2
        assert math.isclose(gt.mean(), 5.5) 
    
        # SimTally
        gp: SimPersistent = m.gen_pers
        assert gp.key == "generator.pers"
        # times are   x0,  x1,  x3,  x6, 10, 15, 20
        # delta-t is  x1,  x2,  x3,  x4,  5,  5
        # average of  x0,  x1,  x2,  x3,  4,  5
        # weighed av (x1 + x4 + x9 +16 +25 +30) / 10 = 55/10 = 5.5
        assert gp.n() == 2
        assert math.isclose(gp.weighted_mean(), 5.5)
    except Exception as e:
        raise e
    finally:
        try:
            s.simulator.cleanup()
        except Exception:
            pass
    

def test_sim_errors():
    
    class EmptyModel(DSOLModel):

        def construct_model(self):
            pass
        
    try:
        simulator: DEVSSimulatorFloat = DEVSSimulatorFloat("sim")
        model: DSOLModel = EmptyModel(simulator)
        replication: Replication = SingleReplication("rep", 0.0, 0.0, 20.0)
        simulator.initialize(model, replication)
        EVENT: EventType = EventType("EVENT")
        
        with pytest.raises(TypeError):
            SimCounter(0, "name", simulator)
        with pytest.raises(TypeError):
            SimCounter("key", 0, simulator)
        with pytest.raises(TypeError):
            SimCounter("key", "name", 'x')
        counter: SimCounter = SimCounter("counter", "name", simulator)
        with pytest.raises(TypeError):
            counter.listen_to('x', EVENT)
        with pytest.raises(TypeError):
            counter.listen_to(simulator, 'x')

        with pytest.raises(TypeError):
            SimTally(0, "name", simulator)
        with pytest.raises(TypeError):
            SimTally("key", 0, simulator)
        with pytest.raises(TypeError):
            SimTally("key", "name", 'x')
        tally: SimTally = SimTally("tally", "name", simulator)
        with pytest.raises(TypeError):
            tally.listen_to('x', EVENT)
        with pytest.raises(TypeError):
            tally.listen_to(simulator, 'x')

        with pytest.raises(TypeError):
            SimPersistent(0, "name", simulator)
        with pytest.raises(TypeError):
            SimPersistent("key", 0, simulator)
        with pytest.raises(TypeError):
            SimPersistent("key", "name", 'x')
        pers: SimPersistent = SimPersistent("persistent", "name", simulator)
        with pytest.raises(TypeError):
            pers.listen_to('x', EVENT)
        with pytest.raises(TypeError):
            pers.listen_to(simulator, 'x')

    except Exception as e:
        raise e
    finally:
        try:
            simulator.cleanup()
        except Exception:
            pass

def test_data_events():
    
    class EmptyModel(DSOLModel):

        def construct_model(self):
            pass
        
    try:
        simulator: DEVSSimulatorFloat = DEVSSimulatorFloat("sim")
        model: DSOLModel = EmptyModel(simulator)
        replication: Replication = SingleReplication("rep", 0.0, 0.0, 20.0)
        simulator.initialize(model, replication)
        
        counter: SimCounter = SimCounter("counter", "name", simulator)
        counter.notify(TimedEvent(0.0, StatEvents.DATA_EVENT, 2))
        assert counter.n() == 1
        assert counter.count() == 2

        tally: SimTally = SimTally("tally", "name", simulator)
        tally.notify(TimedEvent(0.0, StatEvents.DATA_EVENT, 10))
        assert tally.n() == 1
        assert tally.mean() == 10.0

        pers: SimPersistent = SimPersistent("persistent", "name", simulator)
        pers.notify(TimedEvent(0.0, StatEvents.TIMESTAMP_DATA_EVENT, 2))
        pers.notify(TimedEvent(1.0, StatEvents.TIMESTAMP_DATA_EVENT, 4))
        assert pers.n() == 1
        assert pers.weighted_mean() == 2.0

    except Exception as e:
        raise e
    finally:
        try:
            simulator.cleanup()
        except Exception:
            pass


if __name__ == "__main__":
    pytest.main()
