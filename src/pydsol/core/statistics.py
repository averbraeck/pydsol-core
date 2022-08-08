"""
The statistics objects collect observations and produce summarized information
about the observations, such as the mean, standard deviation, minimum value,
and maximum value. The statistics module has four types of statistics objects
in three different families. 

The statistics objects are:

* The *Counter* that collects integer values, such as the occurrences of an 
  event, and produces the count as the statistics result. The counter receives
  its observations through a method ``register(int_value)``
* The *Tally* that collects floating point values such as processing times,
  and produces statistics results such as the mean, standard deviation, and
  variance of the submitted values. The Tally receives its observations
  through a method ``register(float_value)``
* The *WeightedTally* that collects floating point values with an associated
  weight factor, for example the number of entities in a queue as the 
  observations and the duration of the particular queue length as the weights,
  and produces results such as weighted average and weighted variance of the
  observations. The WeightedTally receives its observations through a method 
  ``register(float_weight, float_value)``
* The *TimestampWeightedTally* that is a specialization of the WeightedTally
  where the weights are derived automatically from the intervals between 
  timestamps. Each observation is provided with the time when the value of a 
  property changed. The TimestampWeightedTally receives its observations
  through a method ``register(float_timestamp, float_value)``  
   
The statistics families are:

1. *Ordinary statistics*. These receive the observations by explicitly calling 
   the `register` method for any of the four statistics. The classes are 
   `Counter`, `Tally`, `WeightedTally`, and `TimestampWeightedTally`.
2. *Event-based statistics*. These receive the observations by listening to
   an EventProducer (see the pubsub.py module) that 'fires' events to one or
   more listeners, among which the Event-based statistics. This way, the 
   statistic gathering and processing is decoupled from the process in the 
   simulation that generates the data: there can be zero, one, or many 
   statistics listeners for each data producing object in the simulation. The
   Event-based statistics also fire events with the values of the calculated
   statistics values, so a GUI-element such as a graph or table can be
   automatically updated when values of the statistic change. The classes 
   extend the 'ordinary statistics', and are called `EventBasedCounter`, 
   `EventBasedTally`, `EventBasedWeightedTally`, and 
   `EventBasedTimestampWeightedTally`.
3. *Simulation statistics*. These receive the observations in the same way as
   the Event-based statistics, but are also aware of the Simulator. This
   means they can subscribe to the Simulator's WARMUP_EVENT taking care
   that the statistics are initialized appropriately. Additionally, the 
   `SimPersistent` class that extends `EventBasedTimestampWeightedTally` can
   retrieve the timestamps directly from the Simulator. The classes are:
   
   * `SimCounter` extending `EventBasedCounter`
   * `SimTally` extending `EventBasedTally`
   * `SimWeightedTally`, extending `EventBasedWeightedTally`
   * `SimPersistent`, extending `EventBasedTimestampWeightedTally`
   
Examples
--------
    **SimCounter** is used in discrete-event simulation to count the number of
    occurrences in a model, such as the number of generated entities, or the
    number of processed entities by a server.
    
    **SimTally** is used in discrete-event simulation to calculate statistics 
    for the waiting time in a queue, the time-in-system of an entity, or the 
    processing time at a server.
    
    **SimPersistent** is used in discrete-event simulation to calculate 
    statistics for the length of a queue or the utilization of a server.
    
Notes
-----
    The average of the SimTally can be calculated as:
    
    .. math::
       \\mu = \\sum_{i=1}^{n}{\\frac{x_{i}}{n}}
    
    where :math:`x_{i}` are the observations and :math:`n` is the number of
    observations (only observations after the warmup time are included).
    
    The average of the SimPersistent can be calculated as:
    
    .. math::
       \\mu = \\int_{0}^{T}{\\frac{x_{t}}{T} dt}

    where :math:`x_{t}` is the stepwise changing x-value (it changes at each 
    observation) and :math:`T` is the total time of the simulation (after the
    warmup time). it can be through of as the time-normalized surface 'under'
    the curve of the observed variable.  
"""

import math
from typing import Union
from statistics import NormalDist

from pydsol.core.interfaces import StatEvents, SimulatorInterface, \
    ReplicationInterface, SimStatisticsInterface, StatisticsInterface
from pydsol.core.pubsub import EventProducer, EventListener, Event, \
    TimedEvent, EventType
from pydsol.core.utils import get_module_logger


#from statistics import NormalDist
__all__ = [
    "Counter",
    "Tally",
    "WeightedTally",
    "TimestampWeightedTally",
    "EventBasedCounter",
    "EventBasedTally",
    "EventBasedWeightedTally",
    "EventBasedTimestampWeightedTally",
    "SimCounter",
    "SimTally",
    "SimWeightedTally",
    "SimPersistent",
    ]

logger = get_module_logger('statistics')


class Counter(StatisticsInterface):
    """
    The Counter is a simple statistics object that can count events or
    occurrences. Note that the number of observations is not necessarily
    equal to the value of the counter, since the counter allows any 
    integer as the increment (or decrement) during an observation.
    
    The initialize() method resets the statistics object. The initialize 
    method can, for instance, be called when the warmup period of the 
    simulation experiment has completed. 
    
    Example
    -------
    In simulation, the Counter can be used to count arrivals, the number of
    processed entities in servers, the number of entities in the system, etc.  
    
    Attributes
    ----------
    _name: str
        the name by which the statistics object can be identified
    _n: int
        the number of observations
    _count: int
        the current value of the counter 
    """

    def __init__(self, name: str):
        """
        Construct a new Counter statistics object. The Counter is a simple 
        statistics object that can count events or occurrences. Note that 
        the number of observations is not necessarily equal to the value 
        of the counter, since the counter allows any integer as the 
        increment (or decrement) during an observation.
        
        Parameters
        ----------
        name: str
            The name by which the statistics object can be identified.
            
        Raises
        ------
        TypeError
            when name is not a string
        """
        if not isinstance(name, str):
            raise TypeError("counter name {name} not a str")
        self._name = name
        self.initialize()
        
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        self._count = 0
        self._n = 0

    @property
    def name(self):
        """
        Return the name of this statistics object.
        
        Returns
        -------
        str
            The name of this statistics object.
        """
        return self._name

    def register(self, value: int):
        """
        Process one observation. The value indicates the increment or 
        decrement of the counter (often 1). 
        
        Parameters
        ----------
        value: int
            The increment or decrement of the Counter.
            
        Raises
        ------
        TypeError
            when value is not an int
        """
        if not isinstance(value, int):
            raise TypeError("registered value {value} not an int")
        self._count += value
        self._n += 1

    def count(self):
        """
        Return the current value of the counter statistic.
        
        Returns
        -------
        int
            The current value of the counter statistic.
        """
        return self._count

    def n(self):
        """
        Return the number of observations.
        
        Returns
        -------
        int
            The number of observations.
        """
        return self._n

    def __str__(self):
        return f"Counter[name={self._name}, n={self._n}, count={self._count}]"
    
    def __repr__(self):
        return str(self)
    
    def report_header(self) -> str:
        """
        Return a string representing a header for a textual table with a
        monospaced font that can contain multiple counters.
        """
        return '-' * 72 \
             +f"\n| {'Counter name':<48} | {'n':>6} | {'count':>8} |\n" \
             +'-' * 72
    
    def report_line(self) -> str:
        """
        Return a string representing a line with important statistics values 
        for this counter, for a textual table with a monospaced font that 
        can contain multiple counters.
        """
        return f"| {self.name:<48} | {self.n():>6} | {self.count():>8} |"

    def report_footer(self) -> str:
        """
        Return a string representing a footer for a textual table with a
        monospaced font that can contain multiple counters.
        """
        return '-' * 72
    

class Tally(StatisticsInterface):
    r"""
    The Tally is a statistics object that calculates descriptive statistics
    for a number of observations, such as mean, variance, minimum, maximum, 
    skewness, etc. 
    
    The initialize() method resets the statistics object. The initialize 
    method can, for instance, be called when the warmup period of the 
    simulation experiment has completed. 
    
    The mean of the Tally is calculated with the formula:
    
    .. math:: \mu = \sum_{i=1}^{n} {x_{i}} / n
    
    where n is the number of observations and :math:`x_{i}` are the observations.
    
    Example
    -------
    In discrete-event simulation, the Tally can be used to calculate 
    statistical values for waiting times in queues, time in system of entities, 
    processing times at a server, and throughput times of partial processes. 
    
    Attributes
    ----------
    _name: str
        the name by which the statistics object can be identified
    _n: int
        the number of observations
    _sum: float
        the sum of the observation values 
    _min: float
        the lowest value in the current observations 
    _max: float
        the highest value in the current observations
    _m1, _m2, _m3, _m4: float
        the 1st to 4th moment of the observations
    """

    def __init__(self, name: str):
        """
        Construct a new Tally statistics object. The Tally is a statistics 
        object that calculates descriptive statistics for a number of 
        observations, such as mean, variance, minimum, maximum, skewness, etc. 
        
        Parameters
        ----------
        name: str
            The name by which the statistics object can be identified.
            
        Raises
        ------
        TypeError
            when name is not a string
        """
        if not isinstance(name, str):
            raise TypeError("tally name {name} not a str")
        self._name = name
        self.initialize()
        
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
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
        """
        Return the name of this statistics object.
        
        Returns
        -------
        str
            The name of this statistics object.
        """
        return self._name

    def register(self, value: Union[float, int]):
        """
        Record one or more observation values, and calculate all statistics 
        up to and including the last value (mean, standard deviation, minimum,
        maximum, skewness, etc.).
        
        Parameters
        ----------
        value: float
            The value of the observation.
            
        Raises
        ------
        TypeError
            when value is not a number
        ValueError
            when value is NaN
        """
        if not isinstance(value, (int, float)):
            raise TypeError("tally registered value must be a number")
        if math.isnan(value):
            raise ValueError("tally registered value cannot be nan")
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

    def n(self) -> int:
        """
        Return the number of observations.
        
        Returns
        -------
        int
            The number of observations.
        """
        return self._n

    def min(self) -> float:
        """
        Return the observation with the lowest value. When no observations
        were registered, NaN is returned.
        
        Returns
        -------
        float
            The observation with the lowest value, or NaN when no observations
            were registered.
        """
        return self._min

    def max(self) -> float:
        """
        Return the observation with the highest value. When no observations
        were registered, NaN is returned.
        
        Returns
        -------
        float
            The observation with the highest value, or NaN when no observations
            were registered.
        """
        return self._max
        
    def sum(self) -> float:
        """
        Return the sum of all observations since the statistic initialization.
        
        Returns
        -------
        float
            The sum of the observations.
        """
        return self._sum

    def mean(self) -> float:
        r"""
        Return the mean. When no observations were registered, NaN is returned.
        
        The mean of the Tally is calculated with the formula:
    
        .. math:: \mu = \sum_{i=1}^{n} {x_{i}} / n
    
        where n is the number of observations and :math:`x_{i}` are the 
        observations.

        Returns
        -------
        float
            The mean, or NaN when no observations were registered.
        """
        if self._n > 0:
            return self._m1
        return math.nan

    def confidence_interval(self, alpha: float) -> tuple[float]:
        r"""
        Return the confidence interval around the mean with the provided 
        alpha. When fewer than two observations were registered, (NaN, NaN) 
        is returned.
        
        Parameters
        ----------
        alpha: float
             Alpha is the significance level used to compute the confidence 
             level. The confidence level equals :math:`100 * (1 - alpha)\%`, 
             or in other words, an alpha of 0.05 indicates a 95 percent 
             confidence level.
        
        Returns
        -------
        (float, float)
            The confidence interval around the mean, or (NaN, NaN) when 
            fewer than two observations were registered.
            
        Raises
        ------
        TypeError
            when alpha is not a float
        ValueError
            when alpha is not between 0 and 1, inclusive
        """
        if not isinstance(alpha, float):
            raise TypeError(f"alpha {alpha} not a float")
        if not 0 <= alpha <= 1:
            raise ValueError(f"alpha {alpha} not between 0 and 1")
        mean = self.mean()
        if math.isnan(mean) or math.isnan(self.stdev(False)):
            return (math.nan, math.nan)
        level = 1.0 - alpha / 2.0
        z = NormalDist(0.0, 1.0).inv_cdf(level)
        confidence = z * math.sqrt(self.variance(False) / self._n)
        return (max(self._min, mean - confidence),
                min(self._max, mean + confidence))
    
    def variance(self, biased: bool = True) -> float:
        r"""
        Return the variance of all observations since the statistic 
        initialization. By default, the biased (population) variance
        is returned. The biased variance needs at least 1 observation,
        the unbiased variance needs at least 2.
        
        The formula for the biased (or population) variance is:
        
         .. math::
            \sigma^2 = { {\frac{1}{n}} \left( \sum{x_{i}^2} - 
            \left( \sum{x_{i}} \right)^2 / n \right) }

        The formula for the unbiased (or sample) variance is:
        
         .. math::
            S^2 = { {\frac{1}{n-1}} \left( \sum{x_{i}^2} - 
            \left( \sum{x_{i}} \right)^2 / n \right) }

        Parameters
        ----------
        biased: bool
            Whether to return the biased (population) variance or the 
            unbiased (sample) variance. By default, biased is True and the
            population variance is returned.
        
        Returns
        -------
        float
            The biassed or unbiased variance of all observations since the 
            initialization, or NaN when too few observations were registered.
        """
        if biased:
            if self._n > 0:
                return self._m2 / (self._n)
        elif self._n > 1:
            return self._m2 / (self._n - 1)
        return math.nan
    
    def stdev(self, biased: bool = True) -> float:
        r"""
        Return the standard deviation of all observations since the 
        initialization. The sample standard deviation is defined as the 
        square root of the variance. The biased standard deviation needs at 
        least 1 observation, the unbiased version needs at least 2.
        
        The formula for the biased (population) standard deviation is:
        
         .. math::
            \sigma = \sqrt{ {\frac{1}{n}} \left( \sum{x_{i}^2} - 
            \left( \sum{x_{i}} \right)^2 / n \right) }

        The formula for the unbiased (sample) standard deviation is:
        
         .. math::
            S = \sqrt{ {\frac{1}{n - 1}} \left( \sum{x_{i}^2} - 
            \left( \sum{x_{i}} \right)^2 / n \right) }
        
        Parameters
        ----------
        biased: bool
            Whether to return the biased (population) standard deviation or the 
            unbiased (sample) standard deviation. By default, biased is True 
            and the population standard deviation is returned.

        Returns
        -------
        float
            The (unbiased) sample standard deviation of all observations 
            since the initialization, or NaN when not enough observations 
            were registered.
        """
        return math.sqrt(self.variance(biased))
    
    def skewness(self, biased: bool = True) -> float:
        r"""
        Return the skewness of all observations since the statistic 
        initialization. For the biased (population) skewness, at least two 
        observations are needed; for the unbiased (sample) skewness, at least
        three observations are needed. If there are too few observations,
        NaN is returned. The method returns the biased (population) skewness
        as the default.
        
        The formula for the biased (population) skewness is:
        
         .. math::
            Skew_{biased} = \frac{ \sum{(x_{i} - \mu)^3} }{n . \sigma^3} 
        
        where :math:`\sigma^2` is the biased (population) variance. So 
        the denominator is equal to :math:`n . population\_var^{3/2}`.

        There are different formulas to calculate the unbiased (sample) 
        skewness from the biased (population) skewness. Minitab, for 
        instance calculates unbiased skewness as:
        
         .. math::
            Skew_{unbiased} = Skew_{biased} {\left(  
            \frac{n - 1}{n} \right)} ^{3/2}
            
        whereas SAS, SPSS and Excel calculate it as:
        
         .. math::
            Skew_{unbiased} = Skew_{biased} \sqrt{\frac{n (n - 1)}{n - 2} }
        
        Here we follow the last mentioned formula. All formulas converge 
        to the same value with larger n.
        
        Parameters
        ----------
        biased: bool
            Whether to return the biased (population) skewness or the 
            unbiased (sample) skewness. By default, biased is True and the 
            population skewness is returned.
        
        Returns
        -------
        float
            The skewness of all observations since the initialization, 
            or NaN  when too few observations were registered.
        """
        n = float(self._n)
        if n > 1:
            skew_biased = (self._m3 / n) / self.variance() ** 1.5 
            if biased:
                return skew_biased
            elif n > 2:
                return (skew_biased * math.sqrt(n * (n - 1)) / (n - 2))
        return math.nan
    
    def kurtosis(self, biased: bool = True) -> float:
        r"""
        Return the kurtosis of all observations since the statistic 
        initialization. The biased (sample) kurtosis calculation needs three 
        observations, and the unbiased (population) calculation needs four 
        observations. When too few observations were registered, NaN is 
        returned.
        
        The formula for the biased (population) kurtosis is:
        
         .. math::
            kurt_{biased} = \frac{\sum{(x_{i} - \mu)^4}}{n.\sigma^4}
        
        where :math:`\sigma^2` is the population variance. So the denominator 
        is equal to :math:`n . pop\_var^2`.
        
        The formula for the unbiased (sample) kurtosis is:
        
         .. math::
            kurt_{unbiased} = \frac{\sum{(x_{i} - \mu)^4}}{(n-1).S^4}
        
        where :math:`S^2` is the sample variance. So the denominator is equal 
        to :math:`(n - 1) . sample\_var^2`.
        
        Parameters
        ----------
        biased: bool
            Whether to return the biased (population) kurtosis or the 
            unbiased (sample) kurtosis. By default, biased is True and the 
            population kurtosis is returned.
        
        Returns
        -------
        float
            The kurtosis of all observations since the initialization, or 
            NaN  when too few observations were registered.
        """
        n = self._n
        if biased:
            if n > 2:
                d2 = (self._m2 / n)
                return (self._m4 / n) / d2 / d2
        elif n > 3:
            svar = self.variance(False)
            return self._m4 / (n - 1) / svar / svar
        return math.nan
    
    def excess_kurtosis(self, biased: bool = True) -> float:
        r"""
        Return the excess kurtosis of the registered data. The kurtosis value 
        of the normal distribution is 3. The (biased) excess kurtosis is the 
        kurtosis value shifted by -3 to be 0 for the normal distribution. The  
        biased excess kurtosis needs three observations; if fewer observations
        were registered, NaN is returned.
 
        The formula for the biased (population) excess kurtosis is:
        
         .. math::
            ExcessKurt_{biased} = Kurt_{biased} - 3
        
        The unbiased (sample) excess kurtosis is the sample-corrected value 
        of the biased excess kurtosis. When fewer than four observations were 
        registered, NaN is returned for the unbiased excess kurtosis. Several 
        formulas exist to calculate the sample excess kurtosis from the 
        biased excess kurtosis. Here we use:
        
         .. math::
            ExcessKurt_{unbiased} = \frac{n - 1}{(n - 2) (n - 3)}
            \left( (n + 1) ExcessKurt_{biased} + 6 \right)
             
        This is the excess kurtosis that is calculated by, for instance, 
        SAS, SPSS and Excel.
        
        Parameters
        ----------
        biased: bool
            Whether to return the biased (population) excess kurtosis or the 
            unbiased (sample) excess kurtosis. By default, biased is True and 
            the population excess kurtosis is returned.
        
        Returns
        -------
        float
            The excess kurtosis of all observations since the initialization, 
            or NaN  when too few observations were registered.
        """
        n = float(self._n)
        if biased:
            if n > 2:
                # convert kurtosis to excess kurtosis, shift by -3
                return self.kurtosis() - 3.0
        elif n > 3:
            g2 = self.excess_kurtosis()
            return ((n - 1) / (n - 2) / (n - 3)) * ((n + 1) * g2 + 6)
        return math.nan

    def __str__(self):
        return f"Tally[name={self._name}, n={self._n}, mean={self.mean()}]"
    
    def __repr__(self):
        return str(self)

    def report_header(self) -> str:
        """
        Return a string representing a header for a textual table with a
        monospaced font that can contain multiple tallies.
        """
        return '-' * 72 \
             +f"\n| {'Tally name':<48} | {'n':>6} | {'p_mean':>8} |\n" \
             +'-' * 72
    
    def report_line(self) -> str:
        """
        Return a string representing a line with important statistics values 
        for this tally, for a textual table with a monospaced font that can 
        contain multiple tallies.
        """
        return f"| {self.name:<48} | {self.n():>6} | {self.mean():8.2f} |"

    def report_footer(self) -> str:
        """
        Return a string representing a footer for a textual table with a
        monospaced font that can contain multiple tallies.
        """
        return '-' * 72


class WeightedTally(StatisticsInterface):
    """
    The WeightedTally is a statistics object that calculates descriptive 
    statistics for weighted observations, such as weighted mean, weighted 
    variance, minimum observation, maximum observation, etc. 
    
    The initialize() method resets the statistics object. The initialize 
    method can, for instance, be called when the warmup period of the 
    simulation experiment has completed. 

    In a sense, the weighted tally can be seen as a normal Tally where 
    the observations are multiplied by their weights. But instead of dividing
    by the number of observations to calculate the mean, the sum of weights
    times observations is divided by the sum of the weights. Note that when
    the weights are all set to 1, the WeghtedTally reduces to the ordinary
    Tally.
      
    Example
    -------
    In discrete-event simulation, the WeightedTally is often used with elapsed
    time as the weights (See the `EventBasedTimestampWeightedTally` class and
    the 'SimPersistent' class later in this module). This creates a 
    time-weighted statistic that can for instance be used to calculate 
    statistics for (average) queue length, or (average) utilization of a server.
    
    Attributes
    ----------
    _name: str
        the name by which the statistics object can be identified
    _n: int
        the number of observations
    _n_nonzero: int
        the number of non-zero weights
    _sum_of_weights: float
        the sum of the weights
    _weighted_sum: float
        the sum of the observation values times their weights
    _weight_times_variance: float
        the weighted variant of the second moment of the statistic 
    _min: float
        the lowest value in the current observations 
    _max: float
        the highest value in the current observations
    """

    def __init__(self, name: str):
        """
        Construct a new WeightedTally statistics object. The WeightedTally 
        is a statistics object that calculates descriptive statistics for 
        weighted observations, such as weighted mean, weighted variance, 
        minimum, and maximum. 
        
        Parameters
        ----------
        name: str
            The name by which the statistics object can be identified.
            
        Raises
        ------
        TypeError
            when name is not a string
        """
        if not isinstance(name, str):
            raise TypeError("weighted tally name {name} not a str")
        self._name = name
        self.initialize()
        
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        self._n = 0
        self._n_nonzero = 0
        self._sum_of_weights = 0.0
        self._weighted_mean = 0.0
        self._weight_times_variance = 0.0
        self._weighted_sum = 0.0
        self._min = math.nan
        self._max = math.nan

    @property
    def name(self) -> str:
        """
        Return the name of this statistics object.
        
        Returns
        -------
        str
            The name of this statistics object.
        """
        return self._name

    def register(self, weight: float, value: float):
        """
        Process one observation value and a corresponding weight, and 
        calculate all statistics up to and including the last weight-value 
        pair (mean, standard deviation, minimum, maximum, sum, etc.).
        Weight has to be >= 0.
        
        Note
        ----
        When weight equals zero, the value **is** counted towards the number
        of observations, and for the minimum and maximum observation value,
        but it does not contribute to the other statistics. 
        
        Parameters
        ----------
        weight: float
            The weight of this observation (has to be >= 0).
        value: float
            The value of the observation.
            
        Raises
        ------
        TypeError
            when weight or value is not a number
        ValueError
            when weight or value is NaN
        ValueError
            when weight < 0
        """
        if not isinstance(weight, (int, float)):
            raise TypeError("weight should be a number")
        if not isinstance(value, (int, float)):
            raise TypeError("value should be a number")
        if math.isnan(value):
            raise ValueError("tally registered value cannot be nan")
        if math.isnan(weight):
            raise ValueError("tally weight cannot be nan")
        if weight < 0:
            raise ValueError("tally weight cannot be < 0")
        if self._n == 0:
            self._min = +math.inf
            self._max = -math.inf
        if value < self._min:
            self._min = value
        if value > self._max:
            self._max = value
        self._n += 1
        if weight == 0.0:
            return
        self._n_nonzero += 1
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

    def n(self) -> int:
        """
        Return the number of observations.
        
        Returns
        -------
        int
            The number of observations.
        """
        return self._n

    def min(self) -> float:
        """
        Return the (unweighted) observation with the lowest value. When 
        no observations were registered, NaN is returned.
        
        Returns
        -------
        float
            The observation with the lowest value, or NaN when no observations
            were registered.
        """
        return self._min

    def max(self) -> float:
        """
        Return the (unweighted) observation with the highest value. When 
        no observations were registered, NaN is returned.
        
        Returns
        -------
        float
            The observation with the highest value, or NaN when no observations
            were registered.
        """
        return self._max

    def weighted_sum(self) -> float:
        """
        Return the sum of all observations times their weights since the 
        statistic initialization.
        
        Returns
        -------
        float
            The sum of the observations times their weights.
        """
        return self._weighted_sum

    def weighted_mean(self) -> float:
        r"""
        Return the weighted mean. When no observations were registered, 
        NaN is returned.
        
        The weighted mean of the WeightedTally is calculated with the formula:
    
        .. math:: \mu_{W} = \frac{\sum_{i=1}^{n} w_{i}.x_{i}}{\sum_{i=1}^{n} w_{i}}
    
        where n is the number of observations, :math:`w_{i}` are the weights,
        and :math:`x_{i}` are the observations.

        Returns
        -------
        float
            The weighted mean, or NaN when no observations were registered.
        """
        if self._n > 0:
            return self._weighted_mean
        return math.nan

    def weighted_variance(self, biased: bool = True) -> float:
        r"""
        Return the weighted population variance of all observations since 
        the statistic initialization. The biased version needs at least one
        observation. For the unbiased version, two observations with non-zero 
        weights are needed. When too few observations were registered, NaN 
        is returned. 
        
        The formula for the biased (population) weighted variance is:
        
         .. math::
            \sigma^{2}_{W} = \frac{\sum_{i=1}^{n}{w_i (x_i - \mu_{W})^2}}
                                  {\sum_{i=1}^{n}{w_i}}
        
        where :math:`w_i` are the weights, :math:`x_i` are the observations,
        :math:`n` is the number of observations, and :math:`\mu_W` is the
        weighted mean of the observations.
        
        For the unbiased (sample) weighted variance, different algorithms are 
        suggested by the literature. As an example, R and MATLAB calculate 
        weighted sample variance differently.  SPSS rounds the sum of weights 
        to the nearest integer and counts that as the 'sample size' in the 
        unbiased formula. When weights are used as so-called reliability 
        weights (non-integer) rather than as frequency weights (integer), 
        rounding to the nearest integer and using that to calculate a 
        'sample size' is obviously incorrect. See the discussion at
        https://en.wikipedia.org/wiki/Weighted_arithmetic_mean#Weighted_sample_variance
        and at
        https://stats.stackexchange.com/questions/51442/weighted-variance-one-more-time.
        Here we have chosen to implement the version that uses reliability
        weights. The reason is that the weights in simulation study are most 
        usually time intervals that can be on any (non-integer) scale.
        
        The formula used for the unbiased (sample) weighted variance is:

         .. math::
            S^{2}_{W} = \frac{M}{M - 1} . \sigma^2_{W}
            
        or as a complete formula:
        
         .. math::
            S^{2}_{W} = \frac{M}{M - 1} . 
                        \frac{\sum_{i=1}^{n}{w_i (x_i-\mu_{W})^2}}
                             {\sum_{i=1}^{n}{w_i}}
        
        where :math:`w_i` are the weights, :math:`x_i` are the observations,
        :math:`n` is the number of observations, :math:`M` is the number of
        non-zero observations, and :math:`\mu_W` is the weighted mean of 
        the observations.

        Parameters
        ----------
        biased: bool
            Whether to return the biased (population) variance or the 
            unbiased (sample) variance. By default, biased is True and the
            population variance is returned.
        
        Returns
        -------
        float
            The weighted variance of all observations since the initialization, 
            or NaN when too few (non-zero) observations were registered.
        """
        if self._n > 0:
            w_pop_var = self._weight_times_variance / self._sum_of_weights
            if biased:
                return w_pop_var
            elif self._n_nonzero > 1:
                return w_pop_var * self._n_nonzero / (self._n_nonzero - 1)
        return math.nan
    
    def weighted_stdev(self, biased: bool = True) -> float:
        r"""
        Return the (biased) weighted population standard deviation of all 
        observations since the statistic initialization. The biased version 
        needs at least one observation. For the unbiased version, two 
        observations are needed. When too few observations were registered, 
        NaN is returned.
        
        The formula for the biased (population) weighted standard deviation is:
        
         .. math::
            \sigma_{W} = \sqrt{ \frac{\sum_{i=1}^{n}{w_i (x_i - \mu_{W})^2}}
                                     {\sum_{i=1}^{n}{w_i}} }
        
        where :math:`w_i` are the weights, :math:`x_i` are the observations,
        :math:`n` is the number of observations, and :math:`\mu_W` is the
        weighted mean of the observations.
            
        For the unbiased (sample) weighted variance (and, hence, for the 
        standard deviation), different algorithms are suggested by the 
        literature. As an example, R and MATLAB calculate weighted sample 
        variance differently.  SPSS rounds the sum of weights to the nearest 
        integer and counts that as the 'sample size' in the unbiased formula. 
        When weights are used as so-called reliability weights (non-integer) 
        rather than as frequency weights (integer), rounding to the nearest 
        integer and using that to calculate a 'sample size' is obviously 
        incorrect. See the discussion at
        https://en.wikipedia.org/wiki/Weighted_arithmetic_mean#Weighted_sample_variance
        and at
        https://stats.stackexchange.com/questions/51442/weighted-variance-one-more-time.
        Here we have chosen to implement the version that uses reliability
        weights. The reason is that the weights in simulation study are most 
        usually time intervals that can be on any (non-integer) scale.
        
        The formula used for the unbiased (sample) weighted standard deviation is:

         .. math::
            S_{W} = \sqrt{ \frac{M}{M - 1} . \sigma^2_{W} }
            
        or as a complete formula:
        
         .. math::
            S_{W} = \sqrt{ \frac{M}{M - 1} .
                           \frac{\sum_{i=1}^{n}{w_i (x_i - \mu_{W})^2}}
                                {\sum_{i=1}^{n}{w_i}} }
        
        where :math:`w_i` are the weights, :math:`x_i` are the observations,
        :math:`n` is the number of observations, :math:`M` is the number of
        non-zero observations, and :math:`\mu_W` is the weighted mean of 
        the observations.

        Parameters
        ----------
        biased: bool
            Whether to return the biased (population) standard deviation or the 
            unbiased (sample) standard deviation. By default, biased is True 
            and the population standard deviation is returned.
        
        Returns
        -------
        float
            The weighted standard deviation of all observations since the 
            initialization, or NaN when too few (non-zero) observations 
            were registered.
        """
        return math.sqrt(self.weighted_variance(biased))
    
    def __str__(self):
        return f"WeightedTally[name={self._name}, n={self._n}, "\
            +f"weighted mean={self.weighted_mean()}]"
            
    def __repr__(self):
        return str(self)

    def report_header(self) -> str:
        """
        Return a string representing a header for a textual table with a
        monospaced font that can contain multiple weighted tallies.
        """
        return '-' * 72 \
             +f"\n| {'Weighted Tally name':<48} | {'n':>6} | "\
             +f"{'p_mean':>8} |\n" \
             +'-' * 72
    
    def report_line(self) -> str:
        """
        Return a string representing a line with important statistics values 
        for this tally, for a textual table with a monospaced font that can 
        contain multiple tallies.
        """
        return f"| {self.name:<48} | {self.n():>6} | "\
            +f"{self.weighted_mean():8.2f} |"

    def report_footer(self) -> str:
        """
        Return a string representing a footer for a textual table with a
        monospaced font that can contain multiple tallies.
        """
        return '-' * 72


class TimestampWeightedTally(WeightedTally):
    """
    The TimestampWeightedTally is a statistics object that calculates 
    descriptive statistics for piecewise constant observations, such as 
    weighted mean, weighted variance, minimum observation, maximum 
    observation, etc. Contrary to the WeightedTally, the weights are 
    implicitly calculated based on **timestamps** that are provided with 
    each observation.
    
    The initialize() method resets the statistics object. The initialize 
    method can, for instance, be called when the warmup period of the 
    simulation experiment has completed. 
    
    In order to properly 'close' the series of observations, a virtual 
    observation has to be provided at the end of the observation period, to 
    count the value and duration of the last interval into the statistics. The 
    `end_observations` method takes care of ending the observation period. 
    After calling `end_observations(timestamp)`, further calls to the 
    `register` method will be silently ignored.

    In a sense, the TimestampWeightedTally can be seen as a normal Tally 
    where the observations are multiplied by the duration (interval between two
    successive timestamps) when the observation had that particular value. 
    But instead of dividing by the number of observations to calculate the 
    mean of the ordinary Tally, the sum of durations times observation values 
    is divided by the total duration of the observation period till the last 
    registered timestamp.
      
    Example
    -------
    In discrete-event simulation, the TimestampWeightedTally is often used 
    to calculate statistics for (average) queue length, or (average) 
    utilization of a server. Every time the actual queue length or utilization 
    changes, the new value is registered with the timestamp, and the 
    **previous** observation value is counted towards the statistic with the 
    time interval between the previous timestamp and the new timestamp as the
    weight. 
    
    Attributes
    ----------
    _name: str
        the name by which the statistics object can be identified
    _n: int
        the number of observations
    _n_nonzero: int
        the number of non-zero weights
    _sum_of_weights: float
        the sum of the weights
    _weighted_sum: float
        the sum of the observation values times their weights
    _weight_times_variance: float
        the weighted variant of the second moment of the statistic 
    _min: float
        the lowest value in the current observations 
    _max: float
        the highest value in the current observations
    _start_time: float
        timestamp of the first registered observation
    _last_timestamp: float
        timestamp when the currently valid observation value was set
    _last_value
        currently valid observation value
    _active
        true after initializations until end_observations has been called
    """
        
    def __init__(self, name: str):
        """
        Construct a new TimestampWeightedTally statistics object. The 
        TimestampWeightedTally is a statistics object that calculates 
        descriptive statistics for weighted observations, such as 
        weighted mean, weighted variance, minimum, and maximum, where the 
        weights are implicitly calculated based on successive timestamps. The
        intervals between the timestamp are used as the weights.
        
        Parameters
        ----------
        name: str
            The name by which the statistics object can be identified.
            
        Raises
        ------
        TypeError
            when name is not a string
        """
        super().__init__(name)
        self.initialize()
        
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        super().initialize()
        self._start_time = math.nan
        self._last_timestamp = math.nan
        self._last_value = 0.0
        self._active = True

    def isactive(self) -> bool:
        """
        Indicate whether the statistic is active and can register observations.
        After calling `end_observations(timestamp)` _active will be set to 
        False and further calls to the `register` method will be silently 
        ignored.
        
        Returns
        -------
        bool
            Whether the statistic is active and can register observations.
        """
        return self._active

    def end_observations(self, timestamp: float):
        """
        In order to properly 'close' the series of observations, a virtual 
        observation has to be provided at the end of the observation period, 
        to count the value and duration of the last interval into the 
        statistics. The `end_observations` method takes care of ending the 
        observation period. After calling `end_observations(timestamp)`, 
        further calls to the `register` method will be silently ignored.
        
        Parameters
        ----------
        timestamp: float
            The timestamp of the final interval before the observations end.
            The last registered value will be counted into the statistics 
            for the duration of `(timestamp - last_timestamp)`.
            
        Raises
        ------
        ValueError
            when the provided timestamp is nan
        ValueError
            when the provided timestamp is before the last registered timestamp
        """
        self.register(timestamp, self._last_value)
        self._active = False
        
    def last_value(self) -> float:
        """
        Return the last registered value (this value has not yet been counted 
        into the statistics, unless end_observations() has been called).
        
        Returns
        -------
        float
            The last registered value.
        """
        return self._last_value
        
    def register(self, timestamp: float, value:float):
        """
        Process one observation value and a timestamp that indicates from
        which time the observation is valid, and calculate all statistics 
        up to and including the previous registered value for the duration 
        between the last timestamp and the timestamp provided in this method.
        Successive timestamps can be the same, but a later timestamp cannot
        be before an earlier one.
        
        Note
        ----
        When two successive timestamps are the same, the observation value 
        **is** counted towards the number of observations, and for the 
        minimum and maximum observation value, but it does not contribute 
        to the other statistics. 
        
        Parameters
        ----------
        timestamp: float
            The timestamp from which the observation value is valid.
        value: float
            The observation value.
            
        Raises
        ------
        TypeError
            when timestamp or value is not a number
        ValueError
            when weight or value is NaN
        ValueError
            when the provided timestamp is before the last registered timestamp
        """
        if not isinstance(timestamp, (float, int)):
            raise TypeError("timestamp is not a number")
        if not isinstance(value, (float, int)):
            raise TypeError("observation value is not a number")
        if math.isnan(value):
            raise ValueError("tally registered value cannot be nan")
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
                super().register(deltatime, self._last_value)
            self._last_timestamp = timestamp
        self._last_value = value

#----------------------------------------------------------------------------
# EVENT-BASED STATISTICS
#----------------------------------------------------------------------------


class EventBasedCounter(EventProducer, EventListener, Counter):
    """
    The EventBasedCounter can receive its observations by subscribing 
    (listening) to one or more EventProducers that provides the values for 
    the statistic using the EventProducer's `fire(...)` method. This way, the 
    statistic gathering and processing is decoupled from the process in the 
    simulation that generates the data: there can be zero, one, or many 
    statistics listeners for each data producing object in the simulation.
    
    This event-based statistic object also fire events with the values of 
    the calculated statistics values, so a GUI-element such as a graph or 
    table can subscribe to this event-based statistics object and be 
    automatically updated when values of the statistic change. Again, this
    provides decoupling and flexibility where on beforehand it is not known
    whether zero, one, or many (graphics or simulation) objects are interested
    in the values that this statistics object calculates.  
    
    The EventBasedCounter is a simple statistics object that can count events 
    or occurrences. Note that the number of observations is not necessarily
    equal to the value of the counter, since the counter allows any 
    integer as the increment (or decrement) during an observation.
    
    The initialize() method resets the statistics object. The initialize 
    method can, for instance, be called when the warmup period of the 
    simulation experiment has completed. 
    
    Example
    -------
    In simulation, a counter can be used to count arrivals, the number of
    processed entities in servers, the number of entities in the system, etc.  
    
    Attributes
    ----------
    _name: str
        the name by which the statistics object can be identified
    _n: int
        the number of observations
    _count: int
        the current value of the counter 
    """
    
    def __init__(self, name: str):
        """
        Construct a new EventBasedCounter statistics object. The 
        EventBasedCounter can receive its observations by subscribing 
        (listening) to one or more EventProducers that provides the values 
        for the statistic using the EventProducer's `fire(...)` method. 
        This way, the statistic gathering and processing is decoupled from 
        the process in the simulation that generates the data: there can be 
        zero, one, or many statistics listeners for each data producing 
        object in the simulation.
    
        This event-based statistic object also fire events with the values of 
        the calculated statistics values, so a GUI-element such as a graph or 
        table can subscribe to this event-based statistics object and be 
        automatically updated when values of the statistic change. Again, this
        provides decoupling and flexibility where on beforehand it is not known
        whether zero, one, or many (graphics or simulation) objects are 
        interested in the values that this statistics object calculates.  
    
        The EventBasedCounter is a simple statistics object that can count 
        events or occurrences. Note that the number of observations is not 
        necessarily equal to the value of the counter, since the counter 
        allows any integer as the increment (or decrement) during an 
        observation.
        
        Parameters
        ----------
        name: str
            The name by which the statistics object can be identified.
            
        Raises
        ------
        TypeError
            when name is not a string
        """
        EventProducer.__init__(self)
        Counter.__init__(self, name)
 
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        Counter.initialize(self)
        self.fire_initialized()
    
    def fire_initialized(self):
        """
        Separate method to allow easy overriding of firing the 
        `INITIALIZED_EVENT`, for instance as a TimedEvent in the simulation 
        statistics.
        """
        self.fire(StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        """
        The `notify` method is the method that is called by the `EventProducer`
        to register an observation. The `EventType` for the observation 
        should be the `StatEvents.DATA_EVENT` and the payload should be a 
        single integer. This value will be registered by the counter.
        
        Parameters
        ----------
        event: Event
            The event fired by the `EventProducer` to provide data to the 
            statistic. The event's content should be a single int with the
            value.
        
        Raises
        ------
        TypeError
            when event is not of the type Event
        ValueError
            when the event's event_type is not a DATA_EVENT
        ValueError
            when the event's payload is not an int
        """
        if not isinstance(event, Event):
            raise TypeError("event is not of type Event")
        if not event.event_type == StatEvents.DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for counter " + \
                             "is not a DATA_EVENT")
        if not isinstance(event.content, int):
            raise TypeError(f"notification {event.content} for counter " + \
                            "is not an int")
        self.register(event.content)
            
    def register(self, value: int):
        """
        The event-based classes still have a `register` method. This method 
        is called by the `notify` method, but can also be called separately. 
        The method processes one observation. The value indicates the increment 
        or decrement of the counter (often 1). After processing, the method
        will fire updates to all listeners with the new values of the 
        statistics. 
        
        Parameters
        ----------
        value: int
            The increment or decrement of the Counter.
            
        Raises
        ------
        TypeError
            when value is not an int
        """
        super().register(value)
        if self.has_listeners():
            self.fire_events(value)

    def fire_events(self, value: int):
        """
        Separate method to allow easy overriding of firing the statistics
        events. This is, for instance, necessary in later classes when 
        TimedEvents are fired rather than ordinary events.
        
        Parameters
        ----------
        value: int
            The registered value. It is provided in the method since it is
            not separately stored.
        """
        self.fire(StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire(StatEvents.N_EVENT, self.n())
        self.fire(StatEvents.COUNT_EVENT, self.count())


class EventBasedTally(EventProducer, EventListener, Tally):
    """
    The EventBasedTally can receive its observations by subscribing 
    (listening) to one or more EventProducers that provides the values for 
    the statistic using the EventProducer's `fire(...)` method. This way, the 
    statistic gathering and processing is decoupled from the process in the 
    simulation that generates the data: there can be zero, one, or many 
    statistics listeners for each data producing object in the simulation.
    
    This event-based statistic object also fire events with the values of 
    the calculated statistics values, so a GUI-element such as a graph or 
    table can subscribe to this event-based statistics object and be 
    automatically updated when values of the statistic change. Again, this
    provides decoupling and flexibility where on beforehand it is not known
    whether zero, one, or many (graphics or simulation) objects are interested
    in the values that this statistics object calculates.  
    
    The EventBasedTally is a statistics object that calculates descriptive 
    statistics for a number of observations, such as mean, variance, minimum, 
    maximum, skewness, etc. 
    
    The initialize() method resets the statistics object. The initialize 
    method can, for instance, be called when the warmup period of the 
    simulation experiment has completed. 
    
    The mean of the EventBasedTally is calculated with the formula:
    
    .. math:: \mu = \sum_{i=1}^{n} {x_{i}} / n
    
    where n is the number of observations and :math:`x_{i}` are the 
    observations.
    
    Example
    -------
    In discrete-event simulation, the EventBasedTally can be used to calculate 
    statistical values for waiting times in queues, time in system of entities, 
    processing times at a server, and throughput times of partial processes.
    When objects such as Servers or Entities are EventProducers, they can
    easily feed the EventBasedTally when their internal state changes. 
    
    Attributes
    ----------
    _name: str
        the name by which the statistics object can be identified
    _n: int
        the number of observations
    _sum: float
        the sum of the observation values 
    _min: float
        the lowest value in the current observations 
    _max: float
        the highest value in the current observations
    _m1, _m2, _m3, _m4: float
        the 1st to 4th moment of the observations
    """
    
    def __init__(self, name: str):
        """
        Construct a new EventBasedTally statistics object. The 
        EventBasedTally can receive its observations by subscribing 
        (listening) to one or more EventProducers that provides the values 
        for the statistic using the EventProducer's `fire(...)` method. 
        This way, the statistic gathering and processing is decoupled from 
        the process in the simulation that generates the data: there can be 
        zero, one, or many statistics listeners for each data producing 
        object in the simulation.
    
        This event-based statistic object also fire events with the values of 
        the calculated statistics values, so a GUI-element such as a graph or 
        table can subscribe to this event-based statistics object and be 
        automatically updated when values of the statistic change. Again, this
        provides decoupling and flexibility where on beforehand it is not known
        whether zero, one, or many (graphics or simulation) objects are 
        interested in the values that this statistics object calculates.  
    
        The EventBasedTally is a a statistics object that calculates 
        descriptive statistics for a number of observations, such as mean, 
        variance, minimum, maximum, skewness, etc. 
        
        Parameters
        ----------
        name: str
            The name by which the statistics object can be identified.
            
        Raises
        ------
        TypeError
            when name is not a string
        """
        EventProducer.__init__(self)
        Tally.__init__(self, name)
 
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        Tally.initialize(self)
        self.fire_initialized()
    
    def fire_initialized(self):
        """
        Separate method to allow easy overriding of firing the 
        `INITIALIZED_EVENT`, for instance as a TimedEvent in the simulation 
        statistics.
        """
        self.fire(StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        """
        The `notify` method is the method that is called by the `EventProducer`
        to register an observation. The `EventType` for the observation 
        should be the `StatEvents.DATA_EVENT` and the payload should be a 
        single float value. This value will be registered by the tally.
        
        Parameters
        ----------
        event: Event
            The event fired by the `EventProducer` to provide data to the 
            statistic. The event's content should be a single float with the
            value.
        
        Raises
        ------
        TypeError
            when event is not of the type Event
        ValueError
            when the event's event_type is not a DATA_EVENT
        TypeError
            when the event's payload is not a float
        """
        if not isinstance(event, Event):
            raise TypeError("event is not of type Event")
        if not event.event_type == StatEvents.DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for tally " + \
                             "is not a DATA_EVENT")
        if not isinstance(event.content, (float, int)): 
            raise TypeError(f"notification {event.content} for tally " + \
                            "is not a float or int")
        self.register(float(event.content))

    def register(self, value: float):
        """
        The event-based classes still have a `register` method. This method 
        is called by the `notify` method, but can also be called separately. 
        The method processes one observation. 

        The method records a single observation value, and calculate all 
        statistics up to and including the last value (mean, standard 
        deviation, minimum, maximum, skewness, etc.).
        
        Parameters
        ----------
        value: float
            The value of the observation.
            
        Raises
        ------
        TypeError
            when value is not a number
        ValueError
            when value is NaN
        """
        super().register(value)
        if self.has_listeners():
            self.fire_events(value)

    def fire_events(self, value: float):
        """
        Separate method to allow easy overriding of firing the statistics
        events. This is, for instance, necessary in later classes when 
        TimedEvents are fired rather than ordinary events.
        
        Parameters
        ----------
        value: float
            The registered value. It is provided in the method since it is
            not separately stored.
        """
        self.fire(StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire(StatEvents.N_EVENT, self.n())
        self.fire(StatEvents.MIN_EVENT, self.min())
        self.fire(StatEvents.MAX_EVENT, self.max())
        self.fire(StatEvents.SUM_EVENT, self.sum())
        self.fire(StatEvents.MEAN_EVENT, self.mean())
        self.fire(StatEvents.POPULATION_STDEV_EVENT, self.stdev())
        self.fire(StatEvents.POPULATION_VARIANCE_EVENT, self.variance())
        self.fire(StatEvents.POPULATION_SKEWNESS_EVENT, self.skewness())
        self.fire(StatEvents.POPULATION_KURTOSIS_EVENT, self.kurtosis())
        self.fire(StatEvents.POPULATION_EXCESS_K_EVENT, self.excess_kurtosis())
        self.fire(StatEvents.SAMPLE_STDEV_EVENT, self.stdev(False))
        self.fire(StatEvents.SAMPLE_VARIANCE_EVENT, self.variance(False))
        self.fire(StatEvents.SAMPLE_SKEWNESS_EVENT, self.skewness(False))
        self.fire(StatEvents.SAMPLE_KURTOSIS_EVENT, self.kurtosis(False))
        self.fire(StatEvents.SAMPLE_EXCESS_K_EVENT, self.excess_kurtosis(False))


class EventBasedWeightedTally(EventProducer, EventListener, WeightedTally):
    """
    The EventBasedWeightedTally can receive its observations by subscribing 
    (listening) to one or more EventProducers that provides the values for 
    the statistic using the EventProducer's `fire(...)` method. This way, the 
    statistic gathering and processing is decoupled from the process in the 
    simulation that generates the data: there can be zero, one, or many 
    statistics listeners for each data producing object in the simulation.
    
    This event-based statistic object also fire events with the values of 
    the calculated statistics values, so a GUI-element such as a graph or 
    table can subscribe to this event-based statistics object and be 
    automatically updated when values of the statistic change. Again, this
    provides decoupling and flexibility where on beforehand it is not known
    whether zero, one, or many (graphics or simulation) objects are interested
    in the values that this statistics object calculates.  

    The EventBasedWeightedTally is a statistics object that calculates 
    descriptive statistics for weighted observations, such as weighted mean, 
    weighted variance, minimum observation, maximum observation, etc. 
    
    The initialize() method resets the statistics object. The initialize 
    method can, for instance, be called when the warmup period of the 
    simulation experiment has completed. 

    In a sense, the weighted tally can be seen as a normal Tally where 
    the observations are multiplied by their weights. But instead of dividing
    by the number of observations to calculate the mean, the sum of weights
    times observations is divided by the sum of the weights. Note that when
    the weights are all set to 1, the WeghtedTally reduces to the ordinary
    Tally.
      
    Example
    -------
    In discrete-event simulation, the (event based) WeightedTally is often 
    used with elapsed time as the weights (See the 
    `EventBasedTimestampWeightedTally` class and the 'SimPersistent' class 
    later in this module). This creates a time-weighted statistic that can 
    for instance be used to calculate statistics for (average) queue length, 
    or (average) utilization of a server.
    
    Attributes
    ----------
    _name: str
        the name by which the statistics object can be identified
    _n: int
        the number of observations
    _n_nonzero: int
        the number of non-zero weights
    _sum_of_weights: float
        the sum of the weights
    _weighted_sum: float
        the sum of the observation values times their weights
    _weight_times_variance: float
        the weighted variant of the second moment of the statistic 
    _min: float
        the lowest value in the current observations 
    _max: float
        the highest value in the current observations
    """
    
    def __init__(self, name: str):
        """
        Construct a new EventBasedWeightedTally statistics object. The 
        EventBasedWeightedTally can receive its observations by subscribing 
        (listening) to one or more EventProducers that provides the values 
        for the statistic using the EventProducer's `fire(...)` method. 
        This way, the statistic gathering and processing is decoupled from 
        the process in the simulation that generates the data: there can be 
        zero, one, or many statistics listeners for each data producing 
        object in the simulation.
    
        This event-based statistic object also fire events with the values of 
        the calculated statistics values, so a GUI-element such as a graph or 
        table can subscribe to this event-based statistics object and be 
        automatically updated when values of the statistic change. Again, this
        provides decoupling and flexibility where on beforehand it is not known
        whether zero, one, or many (graphics or simulation) objects are 
        interested in the values that this statistics object calculates.  
    
        The EventBasedWeightedTally is a statistics object that calculates 
        descriptive statistics for weighted observations, such as weighted 
        mean, weighted variance, minimum observation, maximum observation, etc. 
        
        Parameters
        ----------
        name: str
            The name by which the statistics object can be identified.
            
        Raises
        ------
        TypeError
            when name is not a string
        """
        EventProducer.__init__(self)
        WeightedTally.__init__(self, name)
 
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        WeightedTally.initialize(self)
        self.fire_initialized()
    
    def fire_initialized(self):
        """
        Separate method to allow easy overriding of firing the 
        `INITIALIZED_EVENT`, for instance as a TimedEvent in the simulation 
        statistics.
        """
        self.fire(StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        """
        The `notify` method is the method that is called by the `EventProducer`
        to register an observation. The `EventType` for the observation 
        should be the `StatEvents.WEIGHT_DATA_EVENT` and the payload should 
        a tuple with two values (weight, value), both floats. This value will 
        be registered by the weighted tally.
        
        Parameters
        ----------
        event: Event
            The event fired by the `EventProducer` to provide data to the 
            statistic. The content of the event has to be a tuple with two
            values (weight, value), both floats. 
        
        Raises
        ------
        TypeError
            when event is not of the type Event
        ValueError
            when the event's event_type is not a WEIGHT_DATA_EVENT
        TypeError
            when the event's payload is not a tuple
        ValueError
            when the tuple in the content does not have a length of 2
        TypeError
            when one of the tuple's elements is not a number
        """
        if not event.event_type == StatEvents.WEIGHT_DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for " + \
                             "weighted tally is not a WEIGHT_DATA_EVENT")
        if not (isinstance(event.content, tuple)):
            raise TypeError(f"notification {event.content} for weighted " + \
                            "tally is not a tuple")
        if not len(event.content) == 2:
            raise ValueError(f"notification {event.content} for weighted " + \
                            "tally is not a tuple of length 2")
        if not isinstance(event.content[0], (float, int)):
            raise TypeError(f"notification {event.content} for weighted " + \
                            "tally: weight is not a float or int")
        if not isinstance(event.content[1], (float, int)):
            raise TypeError(f"notification {event.content} for weighted " + \
                            "tally: value is not a float or int")
        self.register(float(event.content[0]), float(event.content[1]))

    def register(self, weight: float, value: float):
        """
        The event-based classes still have a `register` method. This method 
        is called by the `notify` method, but can also be called separately. 
        The method processes one observation. 

        The method processes one observation value and a corresponding weight, 
        and calculate all statistics up to and including the last weight-value 
        pair (mean, standard deviation, minimum, maximum, sum, etc.).
        Weight has to be >= 0.
        
        Note
        ----
        When weight equals zero, the value **is** counted towards the number
        of observations, and for the minimum and maximum observation value,
        but it does not contribute to the other statistics. 
        
        Parameters
        ----------
        weight: float
            The weight of this observation (has to be >= 0).
        value: float
            The value of the observation.
            
        Raises
        ------
        TypeError
            when weight or value is not a number
        ValueError
            when weight or value is NaN
        ValueError
            when weight < 0
        """
        super().register(weight, value)
        if self.has_listeners():
            self.fire_events(value)  

    def fire_events(self, value: float):
        """
        Separate method to allow easy overriding of firing the statistics
        events. This is, for instance, necessary in later classes when 
        TimedEvents are fired rather than ordinary events.
        
        Parameters
        ----------
        value: float
            The registered value. It is provided in the method to be symmetric 
            with the.other event-based classes.
        """
        self.fire(StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire(StatEvents.N_EVENT, self.n())
        self.fire(StatEvents.MIN_EVENT, self.min())
        self.fire(StatEvents.MAX_EVENT, self.max())
        self.fire(StatEvents.WEIGHTED_SUM_EVENT, self.weighted_sum())
        self.fire(StatEvents.WEIGHTED_MEAN_EVENT,
                  self.weighted_mean())
        self.fire(StatEvents.WEIGHTED_POPULATION_STDEV_EVENT,
                  self.weighted_stdev())
        self.fire(StatEvents.WEIGHTED_POPULATION_VARIANCE_EVENT,
                  self.weighted_variance())
        self.fire(StatEvents.WEIGHTED_SAMPLE_STDEV_EVENT,
                  self.weighted_stdev(False))
        self.fire(StatEvents.WEIGHTED_SAMPLE_VARIANCE_EVENT,
                  self.weighted_variance(False))


class EventBasedTimestampWeightedTally(EventProducer, EventListener,
                                       TimestampWeightedTally):
    """
    The EventBasedTimestampWeightedTally can receive its observations by 
    subscribing (listening) to one or more EventProducers that provides the 
    values for the statistic using the EventProducer's `fire(...)` method. 
    This way, the statistic gathering and processing is decoupled from the 
    process in the simulation that generates the data: there can be zero, one, 
    or many statistics listeners for each data producing object in the 
    simulation.
    
    This event-based statistic object also fire events with the values of 
    the calculated statistics values, so a GUI-element such as a graph or 
    table can subscribe to this event-based statistics object and be 
    automatically updated when values of the statistic change. Again, this
    provides decoupling and flexibility where on beforehand it is not known
    whether zero, one, or many (graphics or simulation) objects are interested
    in the values that this statistics object calculates.  

    The EventBasedTimestampWeightedTally is a statistics object that calculates 
    descriptive statistics for piecewise constant observations, such as 
    weighted mean, weighted variance, minimum observation, maximum 
    observation, etc. Contrary to the WeightedTally, the weights are 
    implicitly calculated based on **timestamps** that are provided with 
    each observation.
    
    The initialize() method resets the statistics object. The initialize 
    method can, for instance, be called when the warmup period of the 
    simulation experiment has completed. 
    
    In order to properly 'close' the series of observations, a virtual 
    observation has to be provided at the end of the observation period, to 
    count the value and duration of the last interval into the statistics. The 
    `end_observations` method takes care of ending the observation period. 
    After calling `end_observations(timestamp)`, further calls to the 
    `register` method will be silently ignored.

    In a sense, the EventBasedTimestampWeightedTally can be seen as a normal 
    Tally where the observations are multiplied by the duration (interval 
    between two successive timestamps) when the observation had that particular 
    value. But instead of dividing by the number of observations to calculate 
    the mean of the ordinary Tally, the sum of durations times observation 
    values is divided by the total duration of the observation period till 
    the last registered timestamp.
      
    Example
    -------
    In discrete-event simulation, the EventBasedTimestampWeightedTally is often 
    used to calculate statistics for (average) queue length, or (average) 
    utilization of a server. Every time the actual queue length or utilization 
    changes, the new value is registered with the timestamp, and the 
    **previous** observation value is counted towards the statistic with the 
    time interval between the previous timestamp and the new timestamp as the
    weight. 
    
    Attributes
    ----------
    _name: str
        the name by which the statistics object can be identified
    _n: int
        the number of observations
    _n_nonzero: int
        the number of non-zero weights
    _sum_of_weights: float
        the sum of the weights
    _weighted_sum: float
        the sum of the observation values times their weights
    _weight_times_variance: float
        the weighted variant of the second moment of the statistic 
    _min: float
        the lowest value in the current observations 
    _max: float
        the highest value in the current observations
    _start_time: float
        timestamp of the first registered observation
    _last_timestamp: float
        timestamp when the currently valid observation value was set
    _last_value
        currently valid observation value
    _active
        true after initializations until end_observations has been called
    """
    
    def __init__(self, name: str):
        """
        Construct a new EventBasedTimestampWeightedTally statistics object. The 
        EventBasedTimestampWeightedTally can receive its observations by subscribing 
        (listening) to one or more EventProducers that provides the values 
        for the statistic using the EventProducer's `fire(...)` method. 
        This way, the statistic gathering and processing is decoupled from 
        the process in the simulation that generates the data: there can be 
        zero, one, or many statistics listeners for each data producing 
        object in the simulation.
    
        This event-based statistic object also fire events with the values of 
        the calculated statistics values, so a GUI-element such as a graph or 
        table can subscribe to this event-based statistics object and be 
        automatically updated when values of the statistic change. Again, this
        provides decoupling and flexibility where on beforehand it is not known
        whether zero, one, or many (graphics or simulation) objects are 
        interested in the values that this statistics object calculates.  
    
        The EventBasedTimestampWeightedTally is a statistics object that 
        calculates descriptive statistics for weighted observations, such as 
        weighted mean, weighted variance, minimum, and maximum, where the 
        weights are implicitly calculated based on successive timestamps. The
        intervals between the timestamp are used as the weights.
        
        Parameters
        ----------
        name: str
            The name by which the statistics object can be identified.
            
        Raises
        ------
        TypeError
            when name is not a string
        """
        EventProducer.__init__(self)
        TimestampWeightedTally.__init__(self, name)
 
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        TimestampWeightedTally.initialize(self)
        self.fire_initialized()
    
    def fire_initialized(self):
        """
        Separate method to allow easy overriding of firing the 
        `INITIALIZED_EVENT`, for instance as a TimedEvent in the simulation 
        statistics.
        """
        self.fire(StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: TimedEvent):
        """
        The `notify` method is the method that is called by the `EventProducer`
        to register an observation. The event should be a TimedEvent that has
        a timestamp as one of its attributes. The `EventType` for the 
        observation should be the `StatEvents.TIMESTAMP_DATA_EVENT` and 
        the payload should be a float with the observation value.
        
        Parameters
        ----------
        event: TimedEvent
            The timed event fired by the `EventProducer` to provide data to the 
            statistic. The content of the event has to be a float with the
            observation value.
        
        Raises
        ------
        TypeError
            when event is not of the type TimedEvent
        ValueError
            when the event's event_type is not a TIMESTAMP_DATA_EVENT
        TypeError
            when the event's payload is not a float
        ValueError
            when timestamp or value is NaN
        ValueError
            when the provided timestamp is before the last registered timestamp
        """
        if not isinstance(event, TimedEvent):
            raise TypeError(f"event notification {event} for " + \
                            "timestamped tally is not timestamped")
        if not event.event_type == StatEvents.TIMESTAMP_DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for " + \
                             "timestamped tally is not a TIMESTAMP_DATA_EVENT")
        if not isinstance(event.content, (float, int)):
            raise TypeError(f"notification {event.content} for " + \
                            "timestamped tally: value is not a float or int")
        # float(...) will turn a Duration timestamp into its si-value
        self.register(float(event.timestamp), float(event.content))

    def register(self, timestamp: float, value: float):
        """
        The event-based classes still have a `register` method. This method 
        is called by the `notify` method, but can also be called separately. 
        The method processes one timestamped observation. 
        
        The method processes one observation value and a timestamp that 
        indicates from which time the observation is valid, and calculate 
        all statistics up to and including the previous registered value for 
        the duration between the last timestamp and the timestamp provided in 
        this method. Successive timestamps can be the same, but a later 
        timestamp cannot be before an earlier one.
        
        Note
        ----
        When two successive timestamps are the same, the observation value 
        **is** counted towards the number of observations, and for the 
        minimum and maximum observation value, but it does not contribute 
        to the other statistics. 
        
        Parameters
        ----------
        timestamp: float
            The timestamp from which the observation value is valid.
        value: float
            The observation value.
            
        Raises
        ------
        TypeError
            when timestamp or value is not a number
        ValueError
            when weight or value is NaN
        ValueError
            when the provided timestamp is before the last registered timestamp
        """
        super().register(timestamp, value)
        if self.has_listeners():
            self.fire_events(timestamp, value)  

    def fire_events(self, timestamp: float, value: float):
        """
        Separate method to allow easy overriding of firing the (timestamped)
        statistics events. 
        
        Parameters
        ----------
        value: float
            The registered value.
        """
        self.fire_timed(timestamp, StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire_timed(timestamp, StatEvents.N_EVENT, self.n())
        self.fire_timed(timestamp, StatEvents.MIN_EVENT, self.min())
        self.fire_timed(timestamp, StatEvents.MAX_EVENT, self.max())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_SUM_EVENT,
                  self.weighted_sum())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_MEAN_EVENT,
                  self.weighted_mean())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_POPULATION_STDEV_EVENT,
                  self.weighted_stdev())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_POPULATION_VARIANCE_EVENT,
                  self.weighted_variance())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_SAMPLE_STDEV_EVENT,
                  self.weighted_stdev(False))
        self.fire_timed(timestamp, StatEvents.WEIGHTED_SAMPLE_VARIANCE_EVENT,
                  self.weighted_variance(False))

#----------------------------------------------------------------------------
# SIMULATION SPECIFIC STATISTICS
#----------------------------------------------------------------------------


class SimCounter(EventBasedCounter, SimStatisticsInterface):
    
    def __init__(self, key: str, name: str, simulator: SimulatorInterface, *,
                 producer: EventProducer=None, event_type: EventType=None):
        if not isinstance(key, str):
            raise TypeError(f"key {key} is not a str")
        if not isinstance(simulator, SimulatorInterface):
            raise TypeError(f"simulator {simulator} is not a simulator")
        self._simulator = simulator
        EventBasedCounter.__init__(self, name)
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
        if not isinstance(key, str):
            raise TypeError(f"key {key} is not a str")
        if not isinstance(simulator, SimulatorInterface):
            raise TypeError(f"simulator {simulator} is not a simulator")
        self._simulator = simulator
        EventBasedTally.__init__(self, name)
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
        self.fire_timed(t, StatEvents.MEAN_EVENT,
                        self.mean())
        self.fire_timed(t, StatEvents.POPULATION_STDEV_EVENT,
                        self.stdev())
        self.fire_timed(t, StatEvents.POPULATION_VARIANCE_EVENT,
                        self.variance())
        self.fire_timed(t, StatEvents.POPULATION_SKEWNESS_EVENT,
                        self.skewness())
        self.fire_timed(t, StatEvents.POPULATION_KURTOSIS_EVENT,
                        self.kurtosis())
        self.fire_timed(t, StatEvents.POPULATION_EXCESS_K_EVENT,
                        self.excess_kurtosis())
        self.fire_timed(t, StatEvents.SAMPLE_STDEV_EVENT,
                        self.stdev(False))
        self.fire_timed(t, StatEvents.SAMPLE_VARIANCE_EVENT,
                        self.variance(False))
        self.fire_timed(t, StatEvents.SAMPLE_SKEWNESS_EVENT,
                        self.skewness(False))
        self.fire_timed(t, StatEvents.SAMPLE_KURTOSIS_EVENT,
                        self.kurtosis(False))
        self.fire_timed(t, StatEvents.SAMPLE_EXCESS_K_EVENT,
                        self.excess_kurtosis(False))


class SimWeightedTally(EventBasedWeightedTally, SimStatisticsInterface):
    
    def __init__(self, key: str, name: str, simulator: SimulatorInterface, *,
                 producer: EventProducer=None, event_type: EventType=None):
        if not isinstance(key, str):
            raise TypeError(f"key {key} is not a str")
        if not isinstance(simulator, SimulatorInterface):
            raise TypeError(f"simulator {simulator} is not a simulator")
        self._simulator = simulator
        EventBasedWeightedTally.__init__(self, name)
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
        if event.event_type == StatEvents.WEIGHT_DATA_EVENT:
            super().notify(event)
        elif event.event_type == self._event_type:
            super().notify(Event(StatEvents.WEIGHT_DATA_EVENT, event.content))
        elif event.event_type == ReplicationInterface.WARMUP_EVENT:
            self.initialize()
            
    def fire_events(self, value: float):
        t = self.simulator.simulator_time
        self.fire_timed(t, StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire_timed(t, StatEvents.N_EVENT, self.n())
        self.fire_timed(t, StatEvents.MIN_EVENT, self.min())
        self.fire_timed(t, StatEvents.MAX_EVENT, self.max())
        self.fire_timed(t, StatEvents.WEIGHTED_SUM_EVENT, self.weighted_sum())
        self.fire_timed(t, StatEvents.WEIGHTED_MEAN_EVENT,
                  self.weighted_mean())
        self.fire_timed(t, StatEvents.WEIGHTED_POPULATION_STDEV_EVENT,
                  self.weighted_stdev())
        self.fire_timed(t, StatEvents.WEIGHTED_POPULATION_VARIANCE_EVENT,
                  self.weighted_variance())
        self.fire_timed(t, StatEvents.WEIGHTED_SAMPLE_STDEV_EVENT,
                  self.weighted_stdev(False))
        self.fire_timed(t, StatEvents.WEIGHTED_SAMPLE_VARIANCE_EVENT,
                  self.weighted_variance(False))


class SimPersistent(EventBasedTimestampWeightedTally, SimStatisticsInterface):
    
    def __init__(self, key: str, name: str, simulator: SimulatorInterface, *,
                 producer: EventProducer=None, event_type: EventType=None):
        if not isinstance(key, str):
            raise TypeError(f"key {key} is not a str")
        if not isinstance(simulator, SimulatorInterface):
            raise TypeError(f"simulator {simulator} is not a simulator")
        self._simulator = simulator
        EventBasedTimestampWeightedTally.__init__(self, name)
        simulator.add_listener(ReplicationInterface.WARMUP_EVENT, self)
        simulator.add_listener(ReplicationInterface.END_REPLICATION_EVENT, self)
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
        elif event.event_type == ReplicationInterface.END_REPLICATION_EVENT:
            self.end_observations(self.simulator.simulator_time)
