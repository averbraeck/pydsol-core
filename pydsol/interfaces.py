"""
The interfaces module defines common interfaces for the major classes 
in the pydsol framework. The use of interfaces (aka abstract base classes
in Python) avoids circular references in the import of modules. 

As an example, the Simulator class refers to a Replication and a Model in 
its initialize method. Both the Replication classes and the Model class
have references to, and use methods from the Simulator class. The interfaces
module that defines the core 'contract' for the Simulator, Model, Experiment,
Replication and Statistics helps to avoid circular references, but also 
defines the core functionalities of these central classes in the pydscol
framework.

Instead of combining all classes in one huge pydsol module with 
thousands of lines of code, the interfaces nicely decouple the definition
of the classes and their implementation, and they avoid circular referencing 
of modules to each other. Think of the use of this particular interface 
module as the .h files in C++.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from pydsol.pubsub import EventType
from pydsol.utils import get_module_logger

__all__ = [
    "SimulatorInterface",
    "ReplicationInterface",
    "ExperimentInterface",
    "InputParameterInterface",
    "ModelInterface",
    "StatisticsInterface",
    "SimStatisticsInterface",
    "StatEvents",
    ]

logger = get_module_logger('interfaces')

#----------------------------------------------------------------------------
# SIMULATOR INTERFACES
#----------------------------------------------------------------------------

# The TypeVar for time is used for type hinting for simulator time types
TIME = TypeVar("TIME", float, int)


class SimulatorInterface(ABC, Generic[TIME]):
    """
    The SimulatorInterface defines the key methods for any Simulator
    to be used in the pydsol-framework. Different types of Simulators can
    be used, e.g., fixed time increment simulators (time ticks) for ABM
    and for solving differential equations, and variable time increments
    for discrete-event models. Simulators can run as-fast-as-possible or
    be synchronized with the wall clock time, etc. 
    
    Event Types
    -----------
    STARTING_EVENT: EventType
        Will be fired when the simulator has been instructed to start. The 
        actual start might not have happened yet.
    START_EVENT: EventType
        Will be fired when the simulator has actually started.
    STOPPING_EVENT: EventType
        Will be fired when the simulator has been instructed to stop or
        pause. The actual stop might not have happened yet.
    START_EVENT: EventType
        Will be fired when the simulator has actually paused or stopped.
    TIME_CHANGED_EVENT: EventType
        Will be fired when the time of the simulation has changed. This 
        event can be very useful, for instance, to draw time-dependent 
        graphs. 
    """
    
    STARTING_EVENT: EventType = EventType("STARTING_EVENT") 
    START_EVENT: EventType = EventType("START_EVENT") 
    STOPPING_EVENT: EventType = EventType("STOPPING_EVENT") 
    STOP_EVENT: EventType = EventType("STOP_EVENT")
    TIME_CHANGED_EVENT: EventType = EventType("TIME_CHANGED_EVENT")

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the simulator."""
        
    @property
    @abstractmethod
    def time_type(self) -> type:
        """Return the time type of the simulator."""

    @property
    @abstractmethod
    def simulator_time(self) -> TIME:
        """Return the current absolute time of the simulator."""

    @property
    @abstractmethod
    def replication(self) -> 'ReplicationInterface':
        """Return the replication with which the simulator has been 
        initialized, or None when initialize has not yet been called."""
    
    @property
    @abstractmethod
    def model(self) -> 'ModelInterface':
        """Return the model that is being simulated, or None when 
        initialize for a model has not yet been called."""
        
    @abstractmethod
    def initialize(self, model: 'ModelInterface',
                   replication: 'ReplicationInterface'):
        """Initialize the simulator with a replication for a model."""

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
        """Clean up after a replication has finished, and prepare for the
        next replication to run."""

    @abstractmethod
    def start(self):
        """Starts the simulator, and fire a START_EVENT when the simulator 
        is started. The start method uses the RunUntil property with a 
        value of the end time of the replication when starting the simulator.
        
        Note
        ----
        Note that when the simulator was already started, an 
        exception will be raised, and no event will be fired."""

    @abstractmethod
    def step(self):
        """Steps the simulator, and fire a START_EVENT before the execution
        of the event, and a STOP_EVENT after the execution of the event to 
        indicate the simulator made a step. 
        
        Note
        ----
        Note that when the simulator is already  running, an exception 
        will be raised, and no event will be fired."""

    @abstractmethod
    def stop(self):
        """Stops or pauses the simulator, and fire a STOP_EVENT when the 
        simulator is stopped. 
        
        Note
        ----
        Note that when the simulator was already stopped, an exception 
        will be raised, and no event will be fired."""

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
    """
    The ReplicationInterface defines the method that an Replication needs
    to implement. It also defines the events that will be fired to 
    indicate that the execution of a replication on the simulator has
    started, and that a replication on the simulator has ended. A 
    replication provides a start time, warmup time, and duration to the
    simulator and model, and it is related to a unique set of seed values
    for the random streams used in the stochastic simulation. 
    
    Event Types
    -----------
    START_REPLICATION_EVENT: EventType
        Will be fired when the execution of the replication has started.
    END_REPLICATION_EVENT: EventType
        Will be fired when the execution of the replication has completed.
    WARMUP_EVENT: EventType
        Will be fired when the warmup period has been reached, and the
        defined statistics in the model will be cleared.
    """   
    START_REPLICATION_EVENT: EventType = EventType("START_REPLICATION_EVENT")
    END_REPLICATION_EVENT: EventType = EventType("END_REPLICATION_EVENT")
    WARMUP_EVENT: EventType = EventType("WARMUP_EVENT")
    
    @property
    @abstractmethod
    def start_sim_time(self) -> TIME:
        """Return the absolute start time of the replication"""

    @property
    @abstractmethod
    def warmup_sim_time(self) -> TIME:
        """Return the absolute warmup time of the replication"""

    @property
    @abstractmethod
    def end_sim_time(self) -> TIME:
        """Return the absolute end time of the replication"""
    
    
class ExperimentInterface(ABC, Generic[TIME]):
    """
    The ExperimentInterface defines the method that an Experiment needs
    to implement. It also defines the events that will be fired to 
    indicate that the execution of an experiment on the simulator has
    started, and that an experiment on the simulator has ended. An 
    experiment consists of a number of replications for the model that 
    will be executed with the same start time, warmup time, and duration. 
    
    Event Types
    -----------
    START_EXPERIMENT_EVENT: EventType
        Will be fired when the execution of the experiment has started.
    END_EXPERIMENT_EVENT: EventType
        Will be fired when the execution of the experiment has completed.
    """
    START_EXPERIMENT_EVENT: EventType = EventType("START_EXPERIMENT_EVENT")
    END_EXPERIMENT_EVENT: EventType = EventType("END_EXPERIMENT_EVENT")


class InputParameterInterface(ABC):
    """
    Input parameters describe different types of input parameters for the 
    model. All parameters for a model are contained in a hierarchical map 
    where successive keys can be retrieved using a dot-notation between 
    the key elements. Suppose a model has two servers: server1 and server2. 
    Each of the servers has an average service time and a number of resources. 
    This can be coded using keys ‘server1.avg_serice_time’, 
    ‘server1.nr_resources’, ‘server2.avg_serice_time’, ‘server2.nr_resources’. 
    This means that the key ‘server1’ contains an `InputParameterMap` with an 
    instance of InputParameterFloat for the service time, and 
    `InputParameterInt` for the number of resources. Readers for the input 
    parameter map can read the model parameters, e.g., from the screen, 
    a web page, an Excel file, a properties file, or a JSON file.
    
    This generic interface describes the minimum set of methods and
    properties that an InputParameter should have. The definition of the
    interface avoids circular references. 
    """
    
    @property
    @abstractmethod
    def key(self) -> str:
        """
        Return the key of the parameter that can be a part of the 
        dot-notation to uniquely identify the model parameter. The key 
        does not contain the name of the parent. The key is set at time 
        of construction and it is immutable.
        """
    
    @abstractmethod
    def extended_key(self):
        """
        Return the extended key of this InputParameter including parents 
        with a dot-notation. The name of this parameter is the last entry 
        in the dot notation.
        """

    @property    
    @abstractmethod
    def name(self) -> str:
        """
        Returns the concise description of the input parameter, which can 
        be used in a GUI to identify the parameter to the user.
        """

    @property    
    @abstractmethod
    def description(self) -> str:
        """
        Returns description or explanation of the InputParameter. For instance,
        an indication of the bounds or the type. This value is purely there 
        for the user interface.
        """

    @property    
    @abstractmethod
    def default_value(self) -> object:
        """
        Returns the default (initial) value of the parameter. The actual 
        return type will be defined in subclasses of `InputParameter`. 
        The default value is immutable.
        """

    @property    
    @abstractmethod
    def value(self) -> object:
        """
        Returns the actual value of the parameter. The value is initialized
        with default_value and is updated based on user input or data input.
        The actual type will be defined in subclasses of `InputParameter`.
        """

    @abstractmethod
    def set_value(self, value: object):
        """
        Provides a new value for the parameter. The actual type of `value` 
        will be defined in subclasses of `InputParameter`. This is actually
        a method and not a setter property because it can raise errors 
        based on the validity of the value.
        """

    @property    
    @abstractmethod
    def display_priority(self) -> float: 
        """
        Return the number indicating the order of display of the parameter 
        in the parent parameter map. Floats make it easy to insert an extra 
        parameter between parameters that have already been allocated 
        subsequent integer values.
        """

    @property    
    @abstractmethod
    def read_only(self) -> bool:
        """
        Return whether a user is prohibited from changing the value of the
        parameter or not.
        """

    @property
    @abstractmethod
    def parent(self):
        """
        Return the parent map in which the parameter can be retrieved using 
        its  key. Typically, only the root InputParameterMap has no parent, 
        and all other parameters have an InputParameterMap as parent.
        """


class ModelInterface(ABC):
    """
    The ModelInterface defines the minimum set of methods that a simulation
    model in the pydsol-framework should implement. Every model consists of
    the business logic (state transitions initialized in the 
    `construct_model` method), input parameters, output statistics, and a
    reference to the simulator that executes the model. 
    
    The most important method for the Model is the `construct_model` method.
    This method is called for each replication to initialize the model to
    its initial state. The state of the model should be the same every time
    after the `construct_model` method has been called. Constant parts of 
    the model that might be expensive to calculate (e.g., maps, large graphs, 
    information from databases) does not have to be calculated every time 
    in the `construct_model` method, but can be defined once in the `__init__`
    method instead.
    """
    
    @abstractmethod
    def construct_model(self):
        """
        Code to construct the model logic for each replication. This 
        method is called for each replication to initialize the model to
        its initial state. The state of the model should be the same every 
        time after the `construct_model` method has been called. Constant 
        parts of the model that might be expensive to calculate (e.g., maps, 
        large graphs, information from databases) does not have to be 
        calculated every time in the `construct_model` method, but can be 
        defined once in the `__init__` method instead.
        """

    @property
    @abstractmethod
    def simulator(self) -> SimulatorInterface:
        """Return the simulator for this model."""

    @abstractmethod
    def add_parameter(self, input_parameter):
        """Add an input parameter to the input parameter map."""

    @abstractmethod
    def set_parameter(self, key: str, value: object):
        """set the parameter value of an input parameter."""
        
    @abstractmethod
    def get_parameter(self, key: str) -> object:
        """return the value of an input parameter."""
    
    @abstractmethod
    def output_statistics(self) -> dict[str, "StatisticsInterface"]:
        """return the output statistics map."""
    
    @abstractmethod
    def add_output_statistic(self, key: str, statistic: "StatisticsInterface"):
        """add an output statistic to the output statistics map."""

    @abstractmethod
    def get_output_statistic(self, key: str) -> "StatisticsInterface":
        """retrieve an output statistic from the output statistics map."""

#----------------------------------------------------------------------------
# STATISTICS INTERFACES
#----------------------------------------------------------------------------


class StatisticsInterface(ABC):
    """
    The StatisticsInterface is a tagging interface for statistics classes. 
    It defines the minimum set of method that any statistic in the
    pydsol-framework needs to implement.
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the statistic. This can happen at a the start and/or
        at a simulation replication warmup event."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the descriptive name of the statistic."""

    @abstractmethod
    def n(self) -> int:
        """Return the number of observations."""


class SimStatisticsInterface(StatisticsInterface):
    """
    The SimStatisticsInterface is a tagging interface for statistics classes
    that are aware of the Simulator, and that can listen to events such as 
    the WARMUP_EVENT to (re)initialize the statistics. 
    """
    
    @abstractmethod
    def notify(self, event) -> None:
        """EventListener behavior, so the statistic can be subscribed to 
        events like WARMUP_EVENT and END_REPLICATION_EVENT.  
        """

    @property
    @abstractmethod
    def simulator(self) -> SimulatorInterface:
        """Return the simulator."""

#----------------------------------------------------------------------------
# STATISTICS EVENTS
#----------------------------------------------------------------------------


class StatEvents:
    """
    StatEvents contains the set of events that different statistics in
    the statistics module can fire. To avoid circular references between the
    statistics module that fires the events, and modules that listen to 
    events, all events are defines in one place as `StatEvents.XXX_EVENT`.
    
    The events that can be used are listed below.
    """

    DATA_EVENT: EventType = EventType("DATA_EVENT")
    """
    The DATA_EVENT is the incoming event for EventBased statistics that 
    contains a new value for the statistics. The payload is a single float. 
    This event can be used by the EventBasedCounter and EventBasedTally 
    and its subclasses. The event is fired from outside to these statistics.
    """
    
    WEIGHT_DATA_EVENT: EventType = EventType("WEIGHT_DATA_EVENT")
    """The WEIGHT_DATA_EVENT is the incoming event for weighted EventBased 
    statistics that contains a new weight-value pair for the statistics. 
    The payload is a tuple (weight, value). This event can be used by the 
    EventBasedWeightedTally and its subclasses.The event is fired from 
    outside to the statistics."""

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

    MEAN_EVENT: EventType = EventType("MEAN_EVENT")
    """MEAN_EVENT indicates that the mean of the observations has changed, 
    and contains the new mean as the payload. This event is fired by the 
    EventBasedTally and its subclasses to the listeners."""

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

    WEIGHTED_MEAN_EVENT: EventType = EventType("WEIGHTED_MEAN_EVENT")
    """WEIGHTED_MEAN_EVENT indicates that the weighted mean of the 
    observations has changed, and contains the new weighted mean 
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
