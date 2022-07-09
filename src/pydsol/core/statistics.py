import math
from statistics import NormalDist

from pydsol.core.pubsub import EventProducer, EventListener, Event, EventType


class Counter:

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
    

class Tally:

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


class WeightedTally:
    
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
        return f"WeightedTally[name={self._name}, n={self._n}, weighted mean="\
            +f"{self._weighted_mean}]"
            
    def __repr__(self):
        return str(self)


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


class EventBasedCounter(EventProducer, EventListener, Counter):
    
    INITIALIZED_EVENT: EventType = EventType("INITIALIZED_EVENT")
    DATA_EVENT: EventType = EventType("DATA_EVENT")
    OBSERVATION_ADDED_EVENT: EventType = EventType("OBSERVATION_ADDED_EVENT")
    N_EVENT: EventType = EventType("N_EVENT")
    COUNT_EVENT: EventType = EventType("COUNT_EVENT")

    def __init__(self, name: str):
        EventProducer.__init__(self)
        Counter.__init__(self, name)
 
    def initialize(self):
        Counter.initialize(self)
        self.fire(self.INITIALIZED_EVENT, None)
        
    def notify(self, event: Event):
        if not event.event_type == self.DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for counter " + \
                             "is not a DATA_EVENT")
        if not isinstance(event.content, int):
            raise TypeError(f"notification {event.content} for counter " + \
                            "is not an int")
        self.ingest(event.content)
            
    def ingest(self, value: int):
        super().ingest(value)
        if self.has_listeners():
            self.fire(self.OBSERVATION_ADDED_EVENT, value)
            self.fire_events()  

    def fire_events(self):
        self.fire(self.N_EVENT, self.n())
        self.fire(self.COUNT_EVENT, self.count())



class EventBasedTally(EventProducer, EventListener, Tally):
    
    INITIALIZED_EVENT: EventType = EventType("INITIALIZED_EVENT")
    DATA_EVENT: EventType = EventType("DATA_EVENT")
    OBSERVATION_ADDED_EVENT: EventType = EventType("OBSERVATION_ADDED_EVENT")
    N_EVENT: EventType = EventType("N_EVENT")
    MIN_EVENT: EventType = EventType("MIN_EVENT")
    MAX_EVENT: EventType = EventType("MAX_EVENT")
    SUM_EVENT: EventType = EventType("SUM_EVENT")
    POPULATION_MEAN_EVENT: EventType = EventType("POPULATION_MEAN_EVENT")
    POPULATION_STDEV_EVENT: EventType = EventType("POPULATION_STDEV_EVENT")
    POPULATION_VARIANCE_EVENT: EventType = EventType("POPULATION_VARIANCE_EVENT")
    POPULATION_SKEWNESS_EVENT: EventType = EventType("POPULATION_SKEWNESS_EVENT")
    POPULATION_KURTOSIS_EVENT: EventType = EventType("POPULATION_KURTOSIS_EVENT")
    POPULATION_EXCESS_K_EVENT: EventType = EventType("POPULATION_EXCESS_K_EVENT")
    SAMPLE_MEAN_EVENT: EventType = EventType("SAMPLE_MEAN_EVENT")
    SAMPLE_STDEV_EVENT: EventType = EventType("SAMPLE_STDEV_EVENT")
    SAMPLE_VARIANCE_EVENT: EventType = EventType("SAMPLE_VARIANCE_EVENT")
    SAMPLE_SKEWNESS_EVENT: EventType = EventType("SAMPLE_SKEWNESS_EVENT")
    SAMPLE_KURTOSIS_EVENT: EventType = EventType("SAMPLE_KURTOSIS_EVENT")
    SAMPLE_EXCESS_K_EVENT: EventType = EventType("SAMPLE_EXCESS_K_EVENT")

    def __init__(self, name: str):
        EventProducer.__init__(self)
        Tally.__init__(self, name)
 
    def initialize(self):
        Tally.initialize(self)
        self.fire(self.INITIALIZED_EVENT, None)
        
    def notify(self, event: Event):
        if not event.event_type == self.DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for counter " + \
                             "is not a DATA_EVENT")
        if not (isinstance(event.content, float) or 
                isinstance(event.content, int)):
            raise TypeError(f"notification {event.content} for counter " + \
                            "is not a float or int")
        self.ingest(event.content)

    def ingest(self, value: int):
        super().ingest(value)
        if self.has_listeners():
            self.fire(self.OBSERVATION_ADDED_EVENT, value)
            self.fire_events()  

    def fire_events(self):
        self.fire(self.N_EVENT, self.n())
        self.fire(self.MIN_EVENT, self.min())
        self.fire(self.MAX_EVENT, self.max())
        self.fire(self.SUM_EVENT, self.sum())
        self.fire(self.POPULATION_MEAN_EVENT, self.population_mean())
        self.fire(self.POPULATION_STDEV_EVENT, self.population_stdev())
        self.fire(self.POPULATION_VARIANCE_EVENT, self.population_variance())
        self.fire(self.POPULATION_SKEWNESS_EVENT, self.population_skewness())
        self.fire(self.POPULATION_KURTOSIS_EVENT, self.population_kurtosis())
        self.fire(self.POPULATION_EXCESS_K_EVENT, self.population_excess_kurtosis())
        self.fire(self.SAMPLE_MEAN_EVENT, self.sample_mean())
        self.fire(self.SAMPLE_STDEV_EVENT, self.sample_stdev())
        self.fire(self.SAMPLE_VARIANCE_EVENT, self.sample_variance())
        self.fire(self.SAMPLE_SKEWNESS_EVENT, self.sample_skewness())
        self.fire(self.SAMPLE_KURTOSIS_EVENT, self.sample_kurtosis())
        self.fire(self.SAMPLE_EXCESS_K_EVENT, self.sample_excess_kurtosis())
