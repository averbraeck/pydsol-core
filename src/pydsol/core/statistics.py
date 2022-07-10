import math
from statistics import NormalDist

from pydsol.core.interfaces import StatEvents, SimulatorInterface, \
    ReplicationInterface, SimStatisticsInterface, StatisticsInterface
from pydsol.core.pubsub import EventProducer, EventListener, Event, \
    TimedEvent, EventType


class Counter(StatisticsInterface):

    def __init__(self, name: str):
        if not isinstance(name, str):
            raise TypeError("counter name {name} not a str")
        self._name = name
        self.initialize()
        
    def initialize(self):
        self._count = 0
        self._n = 0

    @property
    def name(self):
        return self._name

    def ingest(self, value:int) -> int:
        if not isinstance(value, int):
            raise TypeError("ingested value {value} not an int")
        self._count += value
        self._n += 1
        return value

    def count(self):
        return self._count

    def n(self):
        return self._n

    def __str__(self):
        return f"Counter[name={self._name}, n={self._n}, count={self._count}]"
    
    def __repr__(self):
        return str(self)
    
    def report_header(self) -> str:
        return '-' * 72 \
             + f"\n| {'Counter name':<48} | {'n':>6} | {'count':>8} |\n" \
             + '-' * 72
    
    def report_line(self) -> str:
        return f"| {self.name:<48} | {self.n():>6} | {self.count():>8} |"

    def report_footer(self) -> str:
        return '-' * 72
    

class Tally(StatisticsInterface):

    def __init__(self, name: str):
        if not isinstance(name, str):
            raise TypeError("tally name {name} not a str")
        self._name = name
        self.initialize()
        
    def initialize(self):
        self._n = 0
        self._sum = 0.0
        self._m1 = 0.0
        self._m2 = 0.0
        self._m3 = 0.0
        self._m4 = 0.0
        self._min = math.nan
        self._max = math.nan

    @property
    def name(self):
        return self._name

    def ingest(self, value:float) -> float:
        if math.isnan(value):
            raise ValueError("tally ingested value cannot be nan")
        if self._n == 0:
            self._min = +math.inf
            self._max = -math.inf
        self._n += 1
        delta = value - self._m1
        oldm2 = self._m2
        oldm3 = self._m3
        n = float(self._n)
        # Eq 4 in https://fanf2.user.srcf.net/hermes/doc/antiforgery/stats.pdf
        # Eq 1.1 in https://prod-ng.sandia.gov/techlib-noauth/access-control.cgi
        #    /2008/086212.pdf
        self._m1 += delta / n
        # Eq 44 in https://fanf2.user.srcf.net/hermes/doc/antiforgery/stats.pdf
        # Eq 1.2 in https://prod-ng.sandia.gov/techlib-noauth/access-control.cgi
        #    /2008/086212.pdf
        self._m2 += delta * (value - self._m1)
        # Eq 2.13 in https://prod-ng.sandia.gov/techlib-noauth/access-control.cgi
        #    /2008/086212.pdf
        self._m3 += (-3 * oldm2 * delta / n + (n - 1) * 
                     (n - 2) * delta * delta * delta / n / n)
        # Eq 2.16 in https://prod-ng.sandia.gov/techlib-noauth/access-control.cgi
        #    /2008/086212.pdf
        self._m4 += (-4 * oldm3 * delta / n + 
            6 * oldm2 * delta * delta / n / n + (n - 1)
            * (n * n - 3 * n + 3) * delta * delta * delta 
            * delta / n / n / n)
        self._sum += value
        if value < self._min:
            self._min = value
        if value > self._max:
            self._max = value
        return value

    def n(self):
        return self._n

    def min(self):
        return self._min

    def max(self):
        return self._max

    def sample_mean(self) -> float:
        if self._n > 0:
            return self._m1
        return math.nan

    def population_mean(self) -> float:
        return self.sample_mean()

    def confidence_interval(self, alpha: float):
        if not isinstance(alpha, float):
            raise TypeError(f"alpha {alpha} not a float")
        if not 0 <= alpha <= 1:
            raise ValueError(f"alpha {alpha} not between 0 and 1")
        sample_mean = self.sample_mean()
        if math.isnan(sample_mean) or math.isnan(self.sample_stdev()):
            return (math.nan, math.nan)
        level = 1.0 - alpha / 2.0
        z = NormalDist(0.0, 1.0).inv_cdf(level)
        confidence = z * math.sqrt(self.sample_variance() / self._n)
        return (max(self._min, sample_mean - confidence),
                min(self._max, sample_mean + confidence))
    
    def sample_stdev(self):
        if self._n > 1:
            return math.sqrt(self.sample_variance())
        return math.nan
    
    def population_stdev(self):
        if self._n > 0:
            return math.sqrt(self.population_variance())
        return math.nan
    
    def sum(self):
        return self._sum
    
    def sample_variance(self):
        if self._n > 1:
            return self._m2 / (self._n - 1)
        return math.nan
    
    def population_variance(self):
        if self._n > 0:
            return self._m2 / (self._n)
        return math.nan
    
    def sample_skewness(self):
        n = float(self._n)
        if n > 2:
            return (self.population_skewness() 
                    * math.sqrt(n * (n - 1)) / (n - 2))
        return math.nan
    
    def population_skewness(self):
        if self._n > 1:
            return (self._m3 / self._n) / self.population_variance() ** 1.5
        return math.nan
    
    def sample_kurtosis(self):
        if self._n > 3:
            svar = self.sample_variance()
            return self._m4 / (self._n - 1) / svar / svar
        return math.nan
    
    def population_kurtosis(self):
        if self._n > 2:
            d2 = (self._m2 / self._n)
            return (self._m4 / self._n) / d2 / d2
        return math.nan
    
    def sample_excess_kurtosis(self):
        n = float(self._n)
        if n > 3:
            g2 = self.population_excess_kurtosis()
            return ((n - 1) / (n - 2) / (n - 3)) * ((n + 1) * g2 + 6)
        return math.nan

    def population_excess_kurtosis(self):
        if self._n > 2:
            # convert kurtosis to excess kurtosis, shift by -3
            return self.population_kurtosis() - 3.0
        return math.nan
     
    def __str__(self):
        return f"Tally[name={self._name}, n={self._n}, mean={self.sample_mean()}]"
    
    def __repr__(self):
        return str(self)

    def report_header(self) -> str:
        return '-' * 72 \
             + f"\n| {'Tally name':<48} | {'n':>6} | {'p_mean':>8} |\n" \
             + '-' * 72
    
    def report_line(self) -> str:
        return f"| {self.name:<48} | {self.n():>6} | {self.population_mean():8.2f} |"

    def report_footer(self) -> str:
        return '-' * 72


class WeightedTally(StatisticsInterface):
    
    def __init__(self, name: str):
        if not isinstance(name, str):
            raise TypeError("weighted tally name {name} not a str")
        self._name = name
        self.initialize()
        
    def initialize(self):
        self._n = 0
        self._sum_of_weights = 0.0
        self._weighted_mean = 0.0
        self._weight_times_variance = 0.0
        self._weighted_sum = 0.0
        self._min = math.nan
        self._max = math.nan

    @property
    def name(self):
        return self._name

    def ingest(self, weight: float, value:float) -> float:
        if math.isnan(value):
            raise ValueError("tally ingested value cannot be nan")
        if math.isnan(weight):
            raise ValueError("tally weight cannot be nan")
        if weight < 0:
            raise ValueError("tally weight cannot be < 0")
        if weight == 0.0:
            return value
        if self._n == 0:
            self._min = +math.inf
            self._max = -math.inf
        self._n += 1
        # Eq 47 in https://fanf2.user.srcf.net/hermes/doc/antiforgery/stats.pdf
        self._sum_of_weights += weight;
        prev_weighted_mean = self._weighted_mean;
        # Eq 53 in https://fanf2.user.srcf.net/hermes/doc/antiforgery/stats.pdf
        self._weighted_mean += (weight / self._sum_of_weights 
                * (value - prev_weighted_mean))
        # Eq 68 in https://fanf2.user.srcf.net/hermes/doc/antiforgery/stats.pdf
        self._weight_times_variance += (weight * (value - prev_weighted_mean) 
                * (value - self._weighted_mean))
        self._weighted_sum += weight * value;
        if value < self._min:
            self._min = value
        if value > self._max:
            self._max = value
        return value

    def n(self):
        return self._n

    def min(self):
        return self._min

    def max(self):
        return self._max

    def weighted_sample_mean(self):
        if self._n > 0:
            return self._weighted_mean
        return math.nan

    def weighted_population_mean(self):
        return self.weighted_sample_mean()
    
    def weighted_sample_stdev(self):
        if self._n > 1:
            return math.sqrt(self.weighted_sample_variance())
        return math.nan
    
    def weighted_population_stdev(self):
        return math.sqrt(self.weighted_population_variance())
    
    def weighted_sample_variance(self):
        if self._n > 1:
            return self.weighted_population_variance() * self._n / (self._n - 1)
        return math.nan

    def weighted_population_variance(self):
        if self._n > 0:
            return self._weight_times_variance / self._sum_of_weights
        return math.nan

    def weighted_sum(self):
        return self._weighted_sum

    def __str__(self):
        return f"WeightedTally[name={self._name}, n={self._n}, "\
            +f"weighted mean={self.weighted_population_mean()}]"
            
    def __repr__(self):
        return str(self)

    def report_header(self) -> str:
        return '-' * 72 \
             + f"\n| {'Weighted Tally name':<48} | {'n':>6} | "\
             + f"{'p_mean':>8} |\n" \
             + '-' * 72
    
    def report_line(self) -> str:
        return f"| {self.name:<48} | {self.n():>6} | "\
            + f"{self.weighted_population_mean():8.2f} |"

    def report_footer(self) -> str:
        return '-' * 72


class TimestampWeightedTally(WeightedTally):
        
    def __init__(self, name: str):
        super().__init__(name)
        self.initialize()
        
    def initialize(self):
        super().initialize()
        self._start_time = math.nan
        self._last_timestamp = math.nan
        self._last_value = 0.0
        self._active = True

    def isactive(self) -> bool:
        return self._active

    def end_observations(self, timestamp: float):
        self.ingest(timestamp, self._last_value)
        self._active = False
        
    def last_value(self) -> float:
        return self._last_value
        
    def ingest(self, timestamp: float, value:float) -> float:
        if math.isnan(value):
            raise ValueError("tally ingested value cannot be nan")
        if math.isnan(timestamp):
            raise ValueError("tally timestamp cannot be nan")
        if timestamp < self._last_timestamp:
            raise ValueError("tally timestamp before last timestamp")
        # only calculate when the time interval is larger than 0, 
        # and when the TimestampWeightedTally is active
        if (math.isnan(self._last_timestamp) 
                or timestamp > self._last_timestamp) and self._active:
            if math.isnan(self._start_time):
                self._start_time = timestamp
            else:
                deltatime = max(0.0, timestamp - self._last_timestamp)
                super().ingest(deltatime, self._last_value)
            self._last_timestamp = timestamp
        self._last_value = value
        return value

#----------------------------------------------------------------------------
# EVENT-BASED STATISTICS
#----------------------------------------------------------------------------


class EventBasedCounter(EventProducer, EventListener, Counter):
    
    def __init__(self, name: str):
        EventProducer.__init__(self)
        Counter.__init__(self, name)
 
    def initialize(self):
        Counter.initialize(self)
        self.fire_initialized()
    
    def fire_initialized(self):
        """Separate method to allow easy overriding of firing the 
        INITIALIZED_EVENT as a TimedEvent."""
        self.fire(StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        if not event.event_type == StatEvents.DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for counter " + \
                             "is not a DATA_EVENT")
        if not isinstance(event.content, int):
            raise TypeError(f"notification {event.content} for counter " + \
                            "is not an int")
        self.ingest(event.content)
            
    def ingest(self, value: int):
        super().ingest(value)
        if self.has_listeners():
            self.fire_events(value)

    def fire_events(self, value: float):
        """Separate method to allow easy overriding of firing the statistics
        events as TimedEvent."""
        self.fire(StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire(StatEvents.N_EVENT, self.n())
        self.fire(StatEvents.COUNT_EVENT, self.count())


class EventBasedTally(EventProducer, EventListener, Tally):
    
    def __init__(self, name: str):
        EventProducer.__init__(self)
        Tally.__init__(self, name)
 
    def initialize(self):
        Tally.initialize(self)
        self.fire(StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        if not event.event_type == StatEvents.DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for tally " + \
                             "is not a DATA_EVENT")
        if not (isinstance(event.content, float) or 
                isinstance(event.content, int)):
            raise TypeError(f"notification {event.content} for tally " + \
                            "is not a float or int")
        self.ingest(float(event.content))

    def ingest(self, value: float):
        super().ingest(value)
        if self.has_listeners():
            self.fire(StatEvents.OBSERVATION_ADDED_EVENT, value)
            self.fire_events()  

    def fire_events(self):
        self.fire(StatEvents.N_EVENT, self.n())
        self.fire(StatEvents.MIN_EVENT, self.min())
        self.fire(StatEvents.MAX_EVENT, self.max())
        self.fire(StatEvents.SUM_EVENT, self.sum())
        self.fire(StatEvents.POPULATION_MEAN_EVENT, self.population_mean())
        self.fire(StatEvents.POPULATION_STDEV_EVENT, self.population_stdev())
        self.fire(StatEvents.POPULATION_VARIANCE_EVENT, self.population_variance())
        self.fire(StatEvents.POPULATION_SKEWNESS_EVENT, self.population_skewness())
        self.fire(StatEvents.POPULATION_KURTOSIS_EVENT, self.population_kurtosis())
        self.fire(StatEvents.POPULATION_EXCESS_K_EVENT, self.population_excess_kurtosis())
        self.fire(StatEvents.SAMPLE_MEAN_EVENT, self.sample_mean())
        self.fire(StatEvents.SAMPLE_STDEV_EVENT, self.sample_stdev())
        self.fire(StatEvents.SAMPLE_VARIANCE_EVENT, self.sample_variance())
        self.fire(StatEvents.SAMPLE_SKEWNESS_EVENT, self.sample_skewness())
        self.fire(StatEvents.SAMPLE_KURTOSIS_EVENT, self.sample_kurtosis())
        self.fire(StatEvents.SAMPLE_EXCESS_K_EVENT, self.sample_excess_kurtosis())


class EventBasedWeightedTally(EventProducer, EventListener, WeightedTally):
    
    def __init__(self, name: str):
        EventProducer.__init__(self)
        WeightedTally.__init__(self, name)
 
    def initialize(self):
        WeightedTally.initialize(self)
        self.fire(StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        if not event.event_type == StatEvents.WEIGHT_DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for " + \
                             "weighted tally is not a WEIGHT_DATA_EVENT")
        if not (isinstance(event.content, tuple)):
            raise TypeError(f"notification {event.content} for weighted " + \
                            "tally is not a tuple")
        if not len(event.content) == 2:
            raise TypeError(f"notification {event.content} for weighted " + \
                            "tally is not a tuple of length 2")
        if not (isinstance(event.content[0], float) or 
                isinstance(event.content[0], int)):
            raise TypeError(f"notification {event.content} for weighted " + \
                            "tally: weight is not a float or int")
        if not (isinstance(event.content[1], float) or 
                isinstance(event.content[1], int)):
            raise TypeError(f"notification {event.content} for weighted " + \
                            "tally: value is not a float or int")
        self.ingest(float(event.content[0]), float(event.content[1]))

    def ingest(self, weight: float, value: float):
        super().ingest(weight, value)
        if self.has_listeners():
            self.fire_events(value)  

    def fire_events(self, value: float):
        self.fire(StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire(StatEvents.N_EVENT, self.n())
        self.fire(StatEvents.MIN_EVENT, self.min())
        self.fire(StatEvents.MAX_EVENT, self.max())
        self.fire(StatEvents.WEIGHTED_SUM_EVENT, self.weighted_sum())
        self.fire(StatEvents.WEIGHTED_POPULATION_MEAN_EVENT,
                  self.weighted_population_mean())
        self.fire(StatEvents.WEIGHTED_POPULATION_STDEV_EVENT,
                  self.weighted_population_stdev())
        self.fire(StatEvents.WEIGHTED_POPULATION_VARIANCE_EVENT,
                  self.weighted_population_variance())
        self.fire(StatEvents.WEIGHTED_SAMPLE_MEAN_EVENT,
                  self.weighted_sample_mean())
        self.fire(StatEvents.WEIGHTED_SAMPLE_STDEV_EVENT,
                  self.weighted_sample_stdev())
        self.fire(StatEvents.WEIGHTED_SAMPLE_VARIANCE_EVENT,
                  self.weighted_sample_variance())


class EventBasedTimestampWeightedTally(EventProducer, EventListener,
                                       TimestampWeightedTally):
    
    def __init__(self, name: str):
        EventProducer.__init__(self)
        TimestampWeightedTally.__init__(self, name)
 
    def initialize(self):
        TimestampWeightedTally.initialize(self)
        self.fire(StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: TimedEvent):
        if not isinstance(event, TimedEvent):
            raise TypeError(f"event notification {event} for " + \
                            "timestamped tally is not timestamped")
        if not event.event_type == StatEvents.TIMESTAMP_DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for " + \
                             "timestamped tally is not a TIMESTAMP_DATA_EVENT")
        if not (isinstance(event.content, float) or 
                isinstance(event.content, int)):
            raise TypeError(f"notification {event.content} for " + \
                            "timestamped tally: value is not a float or int")
        # float(...) will turn a Duration timestamp into its si-value
        self.ingest(float(event.timestamp), float(event.content))

    def ingest(self, timestamp: float, value: float):
        super().ingest(timestamp, value)
        if self.has_listeners():
            self.fire_events(timestamp, value)  

    def fire_events(self, timestamp: float, value: float):
        self.fire_timed(timestamp, StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire_timed(timestamp, StatEvents.N_EVENT, self.n())
        self.fire_timed(timestamp, StatEvents.MIN_EVENT, self.min())
        self.fire_timed(timestamp, StatEvents.MAX_EVENT, self.max())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_SUM_EVENT,
                  self.weighted_sum())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_POPULATION_MEAN_EVENT,
                  self.weighted_population_mean())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_POPULATION_STDEV_EVENT,
                  self.weighted_population_stdev())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_POPULATION_VARIANCE_EVENT,
                  self.weighted_population_variance())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_SAMPLE_MEAN_EVENT,
                  self.weighted_sample_mean())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_SAMPLE_STDEV_EVENT,
                  self.weighted_sample_stdev())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_SAMPLE_VARIANCE_EVENT,
                  self.weighted_sample_variance())

#----------------------------------------------------------------------------
# SIMULATION SPECIFIC STATISTICS
#----------------------------------------------------------------------------


class SimCounter(EventBasedCounter, SimStatisticsInterface):
    
    def __init__(self, key: str, name: str, simulator: SimulatorInterface, *,
                 producer: EventProducer=None, event_type: EventType=None):
        self._simulator = simulator
        EventBasedCounter.__init__(self, name)
        if simulator.simulator_time > simulator.replication.warmup_sim_time:
            self.initialize()
        else:
            simulator.add_listener(ReplicationInterface.WARMUP_EVENT, self)
        self._key = key
        simulator.model.add_output_statistic(key, self)
        if producer != None or event_type != None:
            self.listen_to(producer, event_type)
        else:
            self._event_type = None

    def listen_to(self, producer: EventProducer, event_type: EventType):
        """
        Avoid chicken-and-egg problem and allow for later registration of
        events to listen to.
        """
        if not isinstance(producer, EventProducer):
            raise TypeError(f"producer {producer} not an EventProducer")
        if not isinstance(event_type, EventType):
            raise TypeError(f"event_type {event_type} not an EventType")
        self._event_type = event_type
        producer.add_listener(event_type, self)

    @property
    def key(self) -> str:
        return self._key
    
    @property
    def simulator(self) -> SimulatorInterface:
        return self._simulator

    def fire_initialized(self):
        self.fire_timed(self.simulator.simulator_time,
                        StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        if event.event_type == StatEvents.DATA_EVENT:
            super().notify(event)
        elif event.event_type == self._event_type:
            super().notify(Event(StatEvents.DATA_EVENT, event.content))
        elif event.event_type == ReplicationInterface.WARMUP_EVENT:
            self.initialize()
            
    def fire_events(self, value: float):
        self.fire_timed(self.simulator.simulator_time,
                        StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire_timed(self.simulator.simulator_time,
                        StatEvents.N_EVENT, self.n())
        self.fire_timed(self.simulator.simulator_time,
                        StatEvents.COUNT_EVENT, self.count())

class SimTally(EventBasedTally, SimStatisticsInterface):
    
    def __init__(self, key: str, name: str, simulator: SimulatorInterface, *,
                 producer: EventProducer=None, event_type: EventType=None):
        self._simulator = simulator
        EventBasedTally.__init__(self, name)
        if simulator.simulator_time > simulator.replication.warmup_sim_time:
            self.initialize()
        else:
            simulator.add_listener(ReplicationInterface.WARMUP_EVENT, self)
        self._key = key
        simulator.model.add_output_statistic(key, self)
        if producer != None or event_type != None:
            self.listen_to(producer, event_type)
        else:
            self._event_type = None

    def listen_to(self, producer: EventProducer, event_type: EventType):
        """
        Avoid chicken-and-egg problem and allow for later registration of
        events to listen to.
        """
        if not isinstance(producer, EventProducer):
            raise TypeError(f"producer {producer} not an EventProducer")
        if not isinstance(event_type, EventType):
            raise TypeError(f"event_type {event_type} not an EventType")
        self._event_type = event_type
        producer.add_listener(event_type, self)

    @property
    def key(self) -> str:
        return self._key
    
    @property
    def simulator(self) -> SimulatorInterface:
        return self._simulator

    def fire_initialized(self):
        self.fire_timed(self.simulator.simulator_time,
                        StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        if event.event_type == StatEvents.DATA_EVENT:
            super().notify(event)
        elif event.event_type == self._event_type:
            super().notify(Event(StatEvents.DATA_EVENT, event.content))
        elif event.event_type == ReplicationInterface.WARMUP_EVENT:
            self.initialize()
            
    def fire_events(self, value: float):
        t = self.simulator.simulator_time
        self.fire_timed(t, StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire_timed(t, StatEvents.N_EVENT, self.n())
        self.fire_timed(t, StatEvents.MIN_EVENT, self.min())
        self.fire_timed(t, StatEvents.MAX_EVENT, self.max())
        self.fire_timed(t, StatEvents.SUM_EVENT, self.sum())
        self.fire_timed(t, StatEvents.POPULATION_MEAN_EVENT, 
                        self.population_mean())
        self.fire_timed(t, StatEvents.POPULATION_STDEV_EVENT, 
                        self.population_stdev())
        self.fire_timed(t, StatEvents.POPULATION_VARIANCE_EVENT, 
                        self.population_variance())
        self.fire_timed(t, StatEvents.POPULATION_SKEWNESS_EVENT, 
                        self.population_skewness())
        self.fire_timed(t, StatEvents.POPULATION_KURTOSIS_EVENT, 
                        self.population_kurtosis())
        self.fire_timed(t, StatEvents.POPULATION_EXCESS_K_EVENT, 
                        self.population_excess_kurtosis())
        self.fire_timed(t, StatEvents.SAMPLE_MEAN_EVENT, 
                        self.sample_mean())
        self.fire_timed(t, StatEvents.SAMPLE_STDEV_EVENT, 
                        self.sample_stdev())
        self.fire_timed(t, StatEvents.SAMPLE_VARIANCE_EVENT, 
                        self.sample_variance())
        self.fire_timed(t, StatEvents.SAMPLE_SKEWNESS_EVENT, 
                        self.sample_skewness())
        self.fire_timed(t, StatEvents.SAMPLE_KURTOSIS_EVENT, 
                        self.sample_kurtosis())
        self.fire_timed(t, StatEvents.SAMPLE_EXCESS_K_EVENT, 
                        self.sample_excess_kurtosis())

class SimPersistent(EventBasedTimestampWeightedTally, SimStatisticsInterface):
    
    def __init__(self, key: str, name: str, simulator: SimulatorInterface, *,
                 producer: EventProducer=None, event_type: EventType=None):
        self._simulator = simulator
        EventBasedTimestampWeightedTally.__init__(self, name)
        if simulator.simulator_time > simulator.replication.warmup_sim_time:
            self.initialize()
        else:
            simulator.add_listener(ReplicationInterface.WARMUP_EVENT, self)
        self._key = key
        simulator.model.add_output_statistic(key, self)
        if producer != None or event_type != None:
            self.listen_to(producer, event_type)
        else:
            self._event_type = None

    def listen_to(self, producer: EventProducer, event_type: EventType):
        """
        Avoid chicken-and-egg problem and allow for later registration of
        events to listen to.
        """
        if not isinstance(producer, EventProducer):
            raise TypeError(f"producer {producer} not an EventProducer")
        if not isinstance(event_type, EventType):
            raise TypeError(f"event_type {event_type} not an EventType")
        self._event_type = event_type
        producer.add_listener(event_type, self)

    @property
    def key(self) -> str:
        return self._key
    
    @property
    def simulator(self) -> SimulatorInterface:
        return self._simulator

    def fire_initialized(self):
        self.fire_timed(self.simulator.simulator_time,
                        StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        if event.event_type == StatEvents.TIMESTAMP_DATA_EVENT:
            super().notify(event)
        elif event.event_type == self._event_type:
            super().notify(TimedEvent(self.simulator.simulator_time,
                    StatEvents.TIMESTAMP_DATA_EVENT, event.content))
        elif event.event_type == ReplicationInterface.WARMUP_EVENT:
            self.initialize()
