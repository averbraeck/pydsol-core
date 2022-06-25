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
    WARMUP_EVENT: EventType = EventType("WARMUL_EVENT")
    
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
