"""
The interfaces package defines common interfaces for the major classes 
in the pydsol framework. The use of interfaces (aka abstract base classes
in Python) avoids circular references in the import of modules. 

As an example, the Simulator class refers to a Replication and a Model in 
its initialize method. Both the Replication classes and the Model class
have references to, and use methods from the Simulator class.

Instead of combining all classes in one huge pydsol module with 
thousands of lines of code, the interfaces nicely decouple the definition
of the classes and their implementation, and they avoid circular referencing 
of modules to each other. Think of the interface module as the .h files 
in C++.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from pydsol.core.pubsub import EventType
from pydsol.core.utils import get_module_logger

logger = get_module_logger('interfaces')

# The TypeVar for time is used for type hinting for simulator time types
TIME = TypeVar("TIME", float, int)


class SimulatorInterface(ABC, Generic[TIME]):
    
    STARTING_EVENT: EventType = EventType("STARTING_EVENT") 
    START_EVENT: EventType = EventType("START_EVENT") 
    STOPPING_EVENT: EventType = EventType("STOPPING_EVENT") 
    STOP_EVENT: EventType = EventType("STOP_EVENT")
    TIME_CHANGED_EVENT: EventType = EventType("TIME_CHANGED_EVENT")

    @property
    @abstractmethod
    def name(self) -> str:
        """return the name of the simulator"""
        
    @property
    @abstractmethod
    def time_type(self) -> type:
        """return the time type of the simulator"""

    @property
    @abstractmethod
    def simulator_time(self) -> TIME:
        """return the current absolute time of the simulator"""

    @property
    @abstractmethod
    def replication(self) -> 'ReplicationInterface':
        """return the replication with which the simulator has been 
        initialized, or None when initialize has not yet been called"""
    
    @property
    @abstractmethod
    def model(self) -> 'ModelInterface':
        """return the model that is being simulated, or None when 
        initialize for a model has not yet been called"""
        
    @abstractmethod
    def initialize(self, model: 'ModelInterface',
                   replication: 'ReplicationInterface'):
        """initialize the simulator with a replication for a model"""

    @abstractmethod
    def add_initial_method(self, target, method: str, **kwargs):
        """Add a method call that has to be performed at the end if 
        initialize, and before the model starts. This can, for instance,
        be used to schedule the execution of simulation events before 
        initialize has been called, and solved the problem that,
        for discrete event simulators, the scheduleEvent(...) methods 
        cannot be called before initialize()."""
        
    @abstractmethod
    def cleanup(self):
        """clean up after a replication has finished, and prepare for the
        next replication to run"""

    @abstractmethod
    def start(self):
        """Starts the simulator, and fire a START_EVENT that the simulator 
        was started. Note that when the simulator was already started an 
        exception will be thrown, and no event will be fired. The start 
        uses the RunUntil property with a value of the end time of the 
        replication when starting the simulator."""

    @abstractmethod
    def step(self):
        """Steps the simulator, and fire a STEP_EVENT to indicate the 
        simulator made a step. Note that when the simulator is running
        an exception will be thrown, and no event will be fired."""

    @abstractmethod
    def stop(self):
        """Stops the simulator, and fire a STOP_EVENT that the simulator 
        was stopped. Note that when the simulator was already stopped an 
        exception will be thrown, and no event will be fired."""

    @abstractmethod
    def run_up_to(self, stop_time: TIME):
        """Runs the simulator up to a certain time; any events at that time, 
        or the solving of the differential equation at that timestep, 
        will not yet be executed."""

    @abstractmethod
    def run_up_to_including(self, stop_time: TIME):
        """Runs the simulator up to a certain time; all events at that time, 
        or the solving of the differential equation at that timestep, 
        will be executed."""

    @abstractmethod
    def is_initialized(self) -> bool:
        """Return whether the simulator has been initialized with a 
        replication for a model."""
    
    @abstractmethod
    def is_starting_or_running(self) -> bool:
        """Return whether the simulator is starting or has started.""" 
    
    @abstractmethod
    def is_stopping_or_stopped(self) -> bool:
        """Return whether the simulator is stopping or has been stopped. 
        This method also returns True when the simulator has not yet been
        initialized, or when the model has not yet started.""" 
    

class ReplicationInterface(ABC, Generic[TIME]):
    
    START_REPLICATION_EVENT: EventType = EventType("START_REPLICATION_EVENT")
    END_REPLICATION_EVENT: EventType = EventType("END_REPLICATION_EVENT")
    WARMUP_EVENT: EventType = EventType("WARMUP_EVENT")
    
    @property
    @abstractmethod
    def start_sim_time(self) -> TIME:
        """return the absolute start time of the replication"""

    @property
    @abstractmethod
    def warmup_sim_time(self) -> TIME:
        """return the absolute warmup time of the replication"""

    @property
    @abstractmethod
    def end_sim_time(self) -> TIME:
        """return the absolute end time of the replication"""
    
    
class ExperimentInterface(ABC, Generic[TIME]):
    
    START_EXPERIMENT_EVENT: EventType = EventType("START_EXPERIMENT_EVENT")
    END_EXPERIMENT_EVENT: EventType = EventType("END_EXPERIMENT_EVENT")


class ModelInterface(ABC):
    
    @abstractmethod
    def construct_model(self):
        """code to construct the model for each replication"""

    @property
    @abstractmethod
    def simulator(self):
        """return the simulator for this model"""


class StatEvents:

    DATA_EVENT: EventType = EventType("DATA_EVENT")
    """The DATA_EVENT is the incoming event for EventBased statistics that
    contains a new value for the statistics. The payload is a single float.
    This event can be used by the EventBasedCounter and EventBasedTally 
    and its subclasses. The event is fired from outside to these statistics."""
    
    WEIGHT_DATA_EVENT: EventType = EventType("WEIGHT_DATA_EVENT")
    """The WEIGHT_DATA_EVENT is the incoming event for weighted EventBased 
    statistics that contains a new weight-value pair for the statistics. 
    The payload is a tuple (weight, value). This event can be used by the 
    EventBasedWeightedTally and its subclasses.The event is fired from outside 
    to the statistics."""

    TIMESTAMP_DATA_EVENT: EventType = EventType("TIMESTAMP_DATA_EVENT")
    """The TIMESTAMP_DATA_EVENT is the incoming event for weighted EventBased 
    statistics that contains a new timestamp-value pair for the statistics. 
    The payload is a tuple (timestamp, value). This event can be used by the 
    EventBasedTimestampWeightedTally and its subclasses.The event is fired 
    from outside to the statistics."""
    
    INITIALIZED_EVENT: EventType = EventType("INITIALIZED_EVENT")
    """INITIALIZED_EVENT indicates that the statistic has been
    (re)initialized, and all counters have been reset to the original values.
    The event is fired by the statistic to its listeners."""
     
    OBSERVATION_ADDED_EVENT: EventType = EventType("OBSERVATION_ADDED_EVENT")
    """OBSERVATION_ADDED_EVENT indicates that an observation has been 
    received, and contains the value of the observation as the payload.
    For weight-bsaed and timestamp-based observations, the payload is a tuple.
    For value-based statistics, the payload is just the (float) value. 
    The event is fired by the statistic to its listeners."""

    N_EVENT: EventType = EventType("N_EVENT")
    """N_EVENT indicates that the number of observations has been increased,
    and contains the new number of observation as the payload. 
    The event is fired by the statistic to its listeners."""

    COUNT_EVENT: EventType = EventType("COUNT_EVENT")
    """COUNT_EVENT is an event of the Counter statistic and is subclasses.
    The event indicates that the count has changed, and contains the new 
    count as the payload. The event is fired by the statistic to its 
    listeners."""

    MIN_EVENT: EventType = EventType("MIN_EVENT")
    """MIN_EVENT indicates that the minimum of the observations has changed,
    and contains the new minimum as the payload. This event is fired by the 
    EventBasedTally, its Weighted and Timestamped variant, and its subclasses 
    to the listeners."""

    MAX_EVENT: EventType = EventType("MAX_EVENT")
    """MAX_EVENT indicates that the maximum of the observations has changed,
    and contains the new maximum as the payload. This event is fired by the 
    EventBasedTally, its Weighted and Timestamped variants, and their 
    subclasses to the listeners."""

    SUM_EVENT: EventType = EventType("SUM_EVENT")
    """SUM_EVENT indicates that the sum of the observations has changed,
    and contains the new sum as the payload. This event is fired by the 
    EventBasedTally and its subclasses to the listeners."""

    POPULATION_MEAN_EVENT: EventType = EventType("POPULATION_MEAN_EVENT")
    """POPULATION_MEAN_EVENT indicates that the population mean of the 
    observations has changed, and contains the new mean as the payload. 
    This event is fired by the EventBasedTally and its subclasses to the 
    listeners."""

    POPULATION_STDEV_EVENT: EventType = EventType("POPULATION_STDEV_EVENT")
    """POPULATION_STDEV_EVENT indicates that the population standard
    deviation of the observations has changed, and contains the new standard
    deviation as the payload. This event is fired by the EventBasedTally and 
    its subclasses to the listeners."""

    POPULATION_VARIANCE_EVENT: EventType = EventType("POPULATION_VARIANCE_EVENT")
    """POPULATION_VARIANCE_EVENT indicates that the population variance
    of the observations has changed, and contains the new variance as the 
    payload. This event is fired by the EventBasedTally and its subclasses 
    to the listeners."""

    POPULATION_SKEWNESS_EVENT: EventType = EventType("POPULATION_SKEWNESS_EVENT")
    """POPULATION_SKEWNESS_EVENT indicates that the population skewness
    of the observations has changed, and contains the new skewness as the 
    payload. This event is fired by the EventBasedTally and its subclasses 
    to the listeners."""

    POPULATION_KURTOSIS_EVENT: EventType = EventType("POPULATION_KURTOSIS_EVENT")
    """POPULATION_KURTOSIS_EVENT indicates that the population kurtosis
    of the observations has changed, and contains the new kurtosis as the 
    payload. This event is fired by the EventBasedTally and its subclasses 
    to the listeners."""

    POPULATION_EXCESS_K_EVENT: EventType = EventType("POPULATION_EXCESS_K_EVENT")
    """POPULATION_EXCESS_K_EVENT indicates that the population exces kurtosis
    of the observations has changed, and contains the new excess kurtosis as 
    the payload. This event is fired by the EventBasedTally and its subclasses 
    to the listeners."""

    SAMPLE_MEAN_EVENT: EventType = EventType("SAMPLE_MEAN_EVENT")
    """SAMPLE_MEAN_EVENT indicates that the sample mean of the 
    observations has changed, and contains the new mean as the payload. 
    This event is fired by the EventBasedTally and its subclasses to the 
    listeners."""

    SAMPLE_STDEV_EVENT: EventType = EventType("SAMPLE_STDEV_EVENT")
    """SAMPLE_STDEV_EVENT indicates that the sample standard deviation of 
    the observations has changed, and contains the new standard deviation 
    as the payload. This event is fired by the EventBasedTally and its 
    subclasses to the listeners."""

    SAMPLE_VARIANCE_EVENT: EventType = EventType("SAMPLE_VARIANCE_EVENT")
    """SAMPLE_VARIANCE_EVENT indicates that the sample variance of the 
    observations has changed, and contains the new variance as the payload. 
    This event is fired by the EventBasedTally and its subclasses to the 
    listeners."""

    SAMPLE_SKEWNESS_EVENT: EventType = EventType("SAMPLE_SKEWNESS_EVENT")
    """SAMPLE_SKEWNESS_EVENT indicates that the sample skewness of the 
    observations has changed, and contains the new skewness as the payload. 
    This event is fired by the EventBasedTally and its subclasses to the 
    listeners."""

    SAMPLE_KURTOSIS_EVENT: EventType = EventType("SAMPLE_KURTOSIS_EVENT")
    """SAMPLE_KURTOSIS_EVENT indicates that the sample kurtosis of the 
    observations has changed, and contains the new kurtosis as the payload. 
    This event is fired by the EventBasedTally and its subclasses to the 
    listeners."""

    SAMPLE_EXCESS_K_EVENT: EventType = EventType("SAMPLE_EXCESS_K_EVENT")
    """SAMPLE_EXCESS_K_EVENT indicates that the sample excess kurtosis of the 
    observations has changed, and contains the new excess kurtosis as the 
    payload. This event is fired by the EventBasedTally and its subclasses 
    to the listeners."""

    WEIGHTED_SUM_EVENT: EventType = EventType("WEIGHTED_SUM_EVENT")
    """WEIGHTED_SUM_EVENT indicates that the weighted sum of the observations 
    has changed, and contains the new weighted sum as the payload. This event 
    is fired by the EventBasedWeightedTally and its subclasses to the 
    listeners."""

    WEIGHTED_POPULATION_MEAN_EVENT: EventType = \
            EventType("WEIGHTED_POPULATION_MEAN_EVENT")
    """WEIGHTED_POPULATION_MEAN_EVENT indicates that the weighted population 
    mean of the observations has changed, and contains the new weighted mean 
    as the payload. This event is fired by the EventBasedWeightedTally and 
    its subclasses to the listeners."""

    WEIGHTED_POPULATION_STDEV_EVENT: EventType = \
            EventType("WEIGHTED_POPULATION_STDEV_EVENT")
    """WEIGHTED_POPULATION_STDEV_EVENT indicates that the weighted population 
    standard deviation of the observations has changed, and contains the 
    new weighted standard deviation as the payload. This event is fired by 
    the EventBasedWeightedTally and its subclasses to the listeners."""

    WEIGHTED_POPULATION_VARIANCE_EVENT: EventType = \
            EventType("WEIGHTED_POPULATION_VARIANCE_EVENT")
    """WEIGHTED_POPULATION_VARIANCE_EVENT indicates that the weighted 
    population variance of the observations has changed, and contains the 
    new weighted variance as the payload. This event is fired by the 
    EventBasedWeightedTally and its subclasses to the listeners."""

    WEIGHTED_SAMPLE_MEAN_EVENT: EventType = \
            EventType("WEIGHTED_SAMPLE_MEAN_EVENT")
    """WEIGHTED_SAMPLE_MEAN_EVENT indicates that the weighted sample mean 
    of the observations has changed, and contains the new weighted mean 
    as the payload. This event is fired by the EventBasedWeightedTally and 
    its subclasses to the listeners."""

    WEIGHTED_SAMPLE_STDEV_EVENT: EventType = \
            EventType("WEIGHTED_SAMPLE_STDEV_EVENT")
    """WEIGHTED_SAMPLE_STDEV_EVENT indicates that the weighted sample 
    standard deviation of the observations has changed, and contains the 
    new weighted standard deviation as the payload. This event is fired by 
    the EventBasedWeightedTally and its subclasses to the listeners."""

    WEIGHTED_SAMPLE_VARIANCE_EVENT: EventType = \
            EventType("WEIGHTED_SAMPLE_VARIANCE_EVENT")
    """WEIGHTED_SAMPLE_VARIANCE_EVENT indicates that the weighted sample 
    variance of the observations has changed, and contains the new weighted 
    variance as the payload. This event is fired by the EventBasedWeightedTally 
    and its subclasses to the listeners."""
