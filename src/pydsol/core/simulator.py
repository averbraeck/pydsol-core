"""
The simulator module defines different simulators that can be used to
advance time in a simulation and change the state of the model over time. 
"""

from abc import abstractmethod
import enum
import logging
import sys
from threading import Thread
import threading
from time import sleep
import time
import traceback
from typing import TypeVar, Generic

from pydsol.core.eventlist import EventListInterface, EventListHeap
from pydsol.core.interfaces import ModelInterface, SimulatorInterface
from pydsol.core.interfaces import ReplicationInterface
from pydsol.core.pubsub import EventProducer
from pydsol.core.simevent import SimEventInterface, SimEvent
from pydsol.core.units import Duration
from pydsol.core.utils import DSOLError, get_module_logger


__all__ = [
    "Simulator",
    "DEVSSimulator",
    "DEVSSimulatorFloat",
    "DEVSSimulatorInt",
    "DEVSSimulatorDuration",
    "RunState",
    "ReplicationState",
    "SimulatorWorkerThread",
    ]

logger = get_module_logger('simulator')

# The TypeVar for time is used for type hinting for simulator time types
TIME = TypeVar("TIME", float, int)


class RunState(enum.Enum):
    """
    RunState indicates the precise state of the Simulator.
    """
    
    NOT_INITIALIZED = 1
    """"The simulator has been instantiated, but not yet initialized with 
    a Replication"""

    INITIALIZED = 2
    """The replication has started, and the simulator has been initialized, 
    but it has not been started yet"""

    STARTING = 3
    """The Simulator has been started, but the run() thread did not 
    start yet"""

    STARTED = 4
    """The Simulator run() thread has started; the simulation is running"""

    STOPPING = 5
    """The stopping of the simulator has been initiated, but the run() 
    thread is still running"""

    STOPPED = 6
    """The Simulator run() thread has been stopped; the simulator is 
    not running"""

    ENDED = 7
    """The replication has ended, and the simulator cannot be restarted"""


class ReplicationState(enum.Enum):
    """
    ReplicationState indicates the precise state of the replication that is
    being executed by the simulator.
    """
    
    NOT_INITIALIZED = 1
    """"The simulator has been instantiated, but not yet initialized 
    with a Replication"""

    INITIALIZED = 2
    """The simulator has been initialized with the replication, but it has 
    not been started yet, and the the START_REPLICATION_EVENT has not yet 
    been fired."""

    STARTED = 3
    """The execution of the replication has started, and the 
    START_REPLICATION_EVENT has been fired"""

    ENDING = 4
    """The replication has ended, but the run() thread is still running; 
    the END_REPLICATION_EVENT has not yet been fired"""

    ENDED = 5
    """The replication has ended, and the simulator cannot be restarted; 
    the END_REPLICATION_EVENT has been fired."""


class ErrorStrategy():
    """
    ErrorStrategy indicates what to do when there is an error in the 
    execution of the simulation. In order to set the error handling, 
    the Simulator's error_strategy can be set and changed, even during 
    the execution of the simulation run. The log level can be overridden 
    (and even be set to NONE).
    """

    LOG_AND_CONTINUE = 1
    """
    Send the error to the logger as WARNING. Both RunState and 
    ReplicationState remain in the RUNNING state. The Simulator.run() 
    continues as if the error did not occur.
    """
    
    WARN_AND_CONTINUE = 2
    """
    Send the error to logger as ERROR and print the exception on stderr. 
    Both RunState and ReplicationState remain in the RUNNING state. 
    The Simulator.run() continues as if the error did not occur.
    """
    
    WARN_AND_PAUSE = 3
    """
    Send the error to logger as ERROR and print the exception on stderr 
    The RunState goes to STOPPING, leading to the stop of the loop in the 
    Simulator.run() method and a subsequent STOPPED state in the 
    SimulatorWorkerThread.run() method. The SimulatorWorkerThread will go 
    into a Thread.wait(), to wait for start (or cleanup).
    """

    WARN_AND_END = 4
    """
    Send the error to logger as CRITICAL and print the exception on stderr 
    The Simulator.cleanup() method is called to ensure the 
    SimulatorWorkerThread.run() method completely ends and can be garbage 
    collected. If there is a UI thread, it will keep running.
    """
    
    WARN_AND_EXIT = 5
    """
    Send the error to logger as FATAL and print the exception on stderr 
    The Simulator.cleanup() method is called to ensure the stop of the 
    run() in SimulatorWorkerThread; the System.exit() method is called to 
    end the complete program.
    """

    LOG_LEVELS = {LOG_AND_CONTINUE: logging.WARNING,
                  WARN_AND_CONTINUE: logging.ERROR,
                  WARN_AND_PAUSE: logging.ERROR,
                  WARN_AND_END: logging.CRITICAL,
                  WARN_AND_EXIT: logging.FATAL}
    """Dictionary for default log level per error handling strategy."""


class SimulatorWorkerThread(Thread):
    """
    The Simulator uses a worker thread to execute the simulation. The
    reason to use a worker thread is to not block execution of user interface
    activities while the simulation is running. In an interactive setting, a
    user can hereby stop() the simulator and inspect the state of the 
    simulation model, and continue the simulation by calling start().
    """

    def __init__(self, name: str, job: 'Simulator'):
        super().__init__(name=name)
        self._job: 'Simulator' = job
        self.daemon = False
        self._running: bool = False
        self._finalized: bool = False
        self.__wakeup_flag = threading.Event()
        self.start()
    
    def cleanup(self):
        self._running = False
        self._finalized = True
        self.wakeup()  # just to be sure...
        
    def is_running(self) -> bool:
        return self._running
    
    def wakeup(self):
        self.__wakeup_flag.set()
        
    def is_waiting(self):
        return len(self.__wakeup_flag._cond._waiters) > 0

    def is_finalized(self):
        return self._finalized
    
    def run(self):
        while not self._finalized:
            # wait till wakeup, e.g., to start the simulation
            self.__wakeup_flag.wait()
            self._running = True
            if not self._finalized:
                if self._job._replication_state != ReplicationState.ENDING:
                    try:
                        self._job.fire_timed(self._job.simulator_time,
                            Simulator.START_EVENT, None)
                        self._job._run_state = RunState.STARTED
                        self._job._run()
                        self._job.fire_timed(self._job.simulator_time,
                            Simulator.STOP_EVENT, None)
                        self._job._run_state = RunState.STOPPED
                    except Exception as e:
                        print("Simulator run interrupted by exception:")
                        print(str(e))
                        traceback.print_exc()
                if self._job._replication_state == ReplicationState.ENDING:
                    self._job._replication_state = ReplicationState.ENDED
                    self._job._run_state = RunState.ENDED
                    self._job.fire_timed(self._job.simulator_time,
                        ReplicationInterface.END_REPLICATION_EVENT, None)
                    self._finalized = True
            self.__wakeup_flag.clear()
            self._running = False
        # end while
    # end run()


class Simulator(EventProducer, SimulatorInterface, Generic[TIME]):
    """
    The Simulator class 
    """
    
    def __init__(self, name: str, time_type: type, initial_time: TIME):
        EventProducer.__init__(self)
        """
        """
        if not isinstance(name, str):
            raise DSOLError("simulator id should be a str")
        if not (issubclass(time_type, int) or issubclass(time_type, float)):
            raise DSOLError("simulator time_type should be float or int")
        if not isinstance(initial_time, time_type):
            raise DSOLError(f"simulator initial_time not of type {time_type}")
        self._name = name
        self._time_type: type = time_type 
        self._simulator_time: TIME = initial_time
        self._run_until_time: TIME = None
        self._run_until_including: bool = True
        self._replication: ReplicationInterface = None
        self._model: ModelInterface = None
        self._run_state: RunState = RunState.NOT_INITIALIZED
        self._replication_state = ReplicationState.NOT_INITIALIZED
        self.__worker: Thread = None
        self._initial_time = initial_time
        self._initial_methods: list[SimEventInterface] = []
        self._error_strategy = ErrorStrategy.WARN_AND_PAUSE
        self._error_log_level = logging.ERROR
        self._runflag: bool = False
        
    @property
    def name(self) -> str:
        """return the name of the simulator"""
        return self._name
        
    @property
    def time_type(self) -> type:
        """return the time type of the simulator"""
        return self._time_type

    @property
    def simulator_time(self) -> TIME:
        """return the current absolute time of the simulator"""
        return self._simulator_time

    @property
    def initial_time(self) -> TIME:
        """return the first possible time of the used time type"""
        return self._initial_time
        
    @property
    def replication(self) -> ReplicationInterface:
        """return the replication with which the simulator has been 
        initialized, or None when initialize has not yet been called"""
        return self._replication
    
    @property
    def model(self) -> ModelInterface:
        """return the model that is being simulated, or None when 
        initialize for a model has not yet been called"""
        return self._model
        
    def initialize(self, model: ModelInterface, replication: ReplicationInterface):
        """initialize the simulator with a replication for a model"""
        if not isinstance(model, ModelInterface):
            raise DSOLError(f"model {model} not valid")
        if not hasattr(model, '_simulator'):
            raise DSOLError(f"model {model} does not have a simulator. " + 
                "Did you call super.__init__(...) in the model constructor?")
        if not isinstance(replication, ReplicationInterface):
            raise DSOLError(f"replication {replication} not valid")
        if self.is_starting_or_running():
            raise DSOLError("cannot initialize a running simulation")
        if self.__worker is not None:
            self.cleanup()
        self.__worker = SimulatorWorkerThread(self.name, self)
        self._replication = replication
        self._model = model
        self._simulator_time = replication.start_sim_time
        model.construct_model()
        self._run_state = RunState.INITIALIZED
        self._replication_state = ReplicationState.INITIALIZED
        for initial_event in self._initial_methods:
            initial_event.execute()
        # wait till the worker thread is waiting or ready (end replication)
        count: int = 0
        while (not self.__worker.is_waiting() 
               and not self.__worker.is_finalized()
               and count < 1000):
            sleep(0.001)
            count += 1

    def add_initial_method(self, target, method: str, **kwargs):
        """Add a method call that has to be performed at the end if 
        initialize, and before the model starts. This can, for instance,
        be used to schedule the execution of simulation events before 
        initialize has been called, and solved the problem that,
        for discrete event simulators, the scheduleEvent(...) methods 
        cannot be called before initialize()."""
        self._initial_methods.append(SimEvent(self.initial_time,
                target, method, **kwargs))
        
    def cleanup(self):
        """clean up after a replication has finished, and prepare for the
        next replication to run"""
        if self.has_listeners():
            self.remove_all_listeners()
        if self.__worker is not None:
            self._stop_impl()
            self.__worker.cleanup()
            self.__worker = None
        self._run_state = RunState.NOT_INITIALIZED
        self._replication_state = ReplicationState.NOT_INITIALIZED
    
    def _start_impl(self):
        """Implementation of the start method. Checks preconditions for 
        running and fires the right events."""
        if self.is_starting_or_running():
            raise DSOLError("cannot start a running simulator")
        if self._replication == None:
            raise DSOLError("no replication details")
        if not self.is_initialized():
            raise DSOLError("cannot start an uninitialized simulator")
        if not (self._replication_state == ReplicationState.INITIALIZED \
                or self.replication_state == ReplicationState.STARTED):
            raise DSOLError("replication state not INITIALIZED or STARTED")
        if self._simulator_time >= self._replication.end_sim_time:
            raise DSOLError("cannot start: simulator_time > run length")
        self._run_state = RunState.STARTING
        if self._replication_state == ReplicationState.INITIALIZED:
            self.fire_timed(self._simulator_time,
                ReplicationInterface.START_REPLICATION_EVENT, None)
            self._replication_state = ReplicationState.STARTED
        self.fire(Simulator.STARTING_EVENT, None)
        # wake up the run() method of the worker thread to start Simulator.run
        self.__worker.wakeup()
        # wait maximally one second
        msec: int = int(time.time() * 1000)
        while not self._runflag and int(time.time() * 1000) - msec < 1000:
            sleep(0.001)
        self._runflag = False
            
    def start(self):
        """Starts the simulator, and fire a START_EVENT that the simulator 
        was started. Note that when the simulator was already started an 
        exception will be thrown, and no event will be fired. The start 
        uses the RunUntil property with a value of the end time of the 
        replication when starting the simulator."""
        if self._replication == None:
            raise DSOLError("no replication details")
        self._run_until_time = self._replication.end_sim_time
        self._run_until_including = True
        self._start_impl()
     
    @abstractmethod
    def _step_impl(self):
        """The implementation body of the step() method. The stepImpl() 
        method should fire the TIME_CHANGED_EVENT before the execution of 
        the simulation event, or before executing the integration of the 
        differential equation for the next timestep. So the time is changed 
        first to match the logic carried out for that time, and then the 
        action for that time is carried out. This is INDEPENDENT of the 
        fact whether the time changes or not. The TIME_CHANGED_EVENT is
        always fired."""
     
    def step(self):
        """Steps the simulator, and fire a STEP_EVENT to indicate the 
        simulator made a step. Note that when the simulator is running
        an exception will be thrown, and no event will be fired."""
        if self.is_starting_or_running():
            raise DSOLError("cannot start a running simulator")
        if not self.is_initialized():
            raise DSOLError("cannot start an uninitialized simulator")
        if (self._replication_state != ReplicationState.INITIALIZED \
                and self.replication_state != ReplicationState.STARTED):
            raise DSOLError("replication state not INITIALIZED or STARTED")
        if self._simulator_time >= self._replication.end_sim_time:
            raise DSOLError("cannot start: simulator_time > run length")
        try:
            if self._replication_state == ReplicationState.INITIALIZED:
                self.fire_timed(self._simulator_time,
                    ReplicationInterface.START_REPLICATION_EVENT, None)
                self._replication_state = ReplicationState.STARTED
            self._run_state = RunState.STARTED
            self.fire_timed(self._simulator_time,
                            Simulator.START_EVENT, None)
            self._step_impl()
        except Exception as e:
            print("Simulator step got exception: " + e)
        finally:
            self.fire_timed(self._simulator_time,
                            Simulator.STOP_EVENT, None)
            self._run_state = RunState.STOPPED

    def _stop_impl(self):
        """Implementation of the stop behavior."""
        self._run_state = RunState.STOPPING
        # wait till the worker thread is waiting or ready (end replication)
        msec: int = int(time.time() * 1000)
        while (not self.__worker.is_waiting() 
               and not self.__worker.is_finalized()
               and int(time.time() * 1000) - msec < 1000):
            sleep(0.001)

    def stop(self):
        """Stops the simulator, and fire a STOP_EVENT that the simulator 
        was stopped. Note that when the simulator was already stopped an 
        exception will be thrown, and no event will be fired."""
        if self.is_stopping_or_stopped():
            raise DSOLError("cannot stop an already stopped simulator")
        self.fire(Simulator.STOPPING_EVENT, None)
        self._stop_impl()
     
    def run_up_to(self, stop_time: TIME):
        """Runs the simulator up to a certain time; any events at that time, 
        or the solving of the differential equation at that timestep, 
        will not yet be executed."""
        self._run_until_time = stop_time
        self._run_until_including = False
        self._start_impl()
        
    def run_up_to_including(self, stop_time: TIME):
        """Runs the simulator up to a certain time; all events at that time, 
        or the solving of the differential equation at that timestep, 
        will be executed."""
        self._run_until_time = stop_time
        self._run_until_including = True
        self._start_impl()
    
    def warmup(self):
        self.fire_timed(self.simulator_time,
                        ReplicationInterface.WARMUP_EVENT, None)

    @property
    def run_state(self) -> RunState:
        """return the run state of the simulator"""
        return self._run_state

    def is_initialized(self) -> bool:
        """Return whether the simulator has been initialized with a 
        replication for a model."""
        return self.run_state != RunState.NOT_INITIALIZED
    
    def is_starting_or_running(self) -> bool:
        """Return whether the simulator is starting or has started.""" 
        return (self.run_state == RunState.STARTING or \
               self.run_state == RunState.STARTED)
    
    def is_stopping_or_stopped(self) -> bool:
        """Return whether the simulator is stopping or has been stopped. 
        This method also returns True when the simulator has not yet been
        initialized, or when the model has not yet started, or when the
        model run has ended.""" 
        return not self.is_starting_or_running()
    
    @property
    def replication_state(self) -> ReplicationState:
        """return the replication state"""
        return self._replication_state

    def end_replication(self):
        self._replication_state = ReplicationState.ENDING
        self.__worker.wakeup()  # just to be sure
        if self._simulator_time < self._replication.end_sim_time:
            print("warning: end_replication called with simtime < runlength")
            self._simulator_time = self._replication.end_sim_time
    
    def set_error_strategy(self, error_strategy: ErrorStrategy,
                           log_level: int=-1):
        """
        Set a new error handling strategy for the simulator, and possibly
        override the default log level belonging to the error strategy 
        (e.g. with logging.NONE to suppress logging altogether). 
        """
        if not error_strategy in ErrorStrategy.LOG_LEVELS:
            raise ValueError("None-existent error strategy for simulator")
        self._error_strategy = error_strategy
        if log_level >= 0:
            self._error_log_level = log_level
            return
        self._error_log_level = ErrorStrategy.LOG_LEVELS[error_strategy]

    @abstractmethod
    def _run(self):
        """
        The run method defines the actual time step mechanism of the 
        simulator. The implementation of this method depends on the
        formalism. Where discrete event formalisms loop over an event list, 
        continuous simulators take predefined time steps.
        Make sure that:
         - self._runflag is set to True at the start of the run() method.
         - SimulatorInterface.TIME_CHANGED_EVENT is fired when the time 
           of the simulator changes.
         - the warmup() method is called when the warmup period has expired 
           (through an event or based on simulation time).
         - the endReplication() method is called when the replication 
           has ended.
         - the simulator runs until the runUntil time, which is also set 
           by the start() method.
        """


class DEVSSimulator(Simulator[TIME], Generic[TIME]):
    
    def __init__(self, name: str, time_type: type, initial_time: TIME):
        super().__init__(name, time_type, initial_time)
        self._eventlist: EventListInterface = EventListHeap()
    
    def initialize(self, model:ModelInterface, replication:ReplicationInterface):
        # this check HAS to be done before clearing the eventlist
        if self.is_starting_or_running():
            raise DSOLError("cannot initialize a running simulation")
        self._eventlist.clear()
        super().initialize(model, replication)
        # schedule warmup BEFORE events at warmup time
        self.schedule_event_abs(self.replication.warmup_sim_time,
            self, "warmup", priority=SimEventInterface.MAX_PRIORITY)

    def eventlist(self) -> EventListInterface:
        """Return the event list used by this simulator."""
        return self._eventlist
        
    def schedule_event(self, event: SimEventInterface) -> SimEventInterface:
        """schedule the provided event on the event list"""
        if event.time < self._simulator_time:
            raise DSOLError("cannot schedule event in the past")
        self._eventlist.add(event)
        return event

    def schedule_event_now(self, target, method: str,
                 priority: int=SimEventInterface.NORMAL_PRIORITY,
                 **kwargs) -> SimEventInterface:
        """schedule a method call at the current simulator time"""
        return self.schedule_event(SimEvent(self._simulator_time, target,
                 method, priority, **kwargs))

    def schedule_event_rel(self, delay, target, method: str,
                 priority: int=SimEventInterface.NORMAL_PRIORITY,
                 **kwargs) -> SimEventInterface:
        """schedule a methodCall at a relative duration. The execution 
        time is thus simulator.simulator_time + delay."""
        if delay < 0:
            raise DSOLError("cannot schedule event in the past")
        return self.schedule_event(SimEvent(self._simulator_time + delay,
                 target, method, priority, **kwargs))

    def schedule_event_abs(self, time, target, method: str,
                 priority: int=SimEventInterface.NORMAL_PRIORITY,
                 **kwargs) -> SimEventInterface:
        """schedule a methodCall at a relative duration. The execution 
        time is thus simulator.simulator_time + delay."""
        if time < self._simulator_time:
            raise DSOLError("cannot schedule event in the past")
        return self.schedule_event(SimEvent(time,
                 target, method, priority, **kwargs))

    def cancel_event(self, event: SimEventInterface):
        """remove the provided event from the event list"""
        self._eventlist.remove(event)
        
    def _step_impl(self):
        """The implementation body of the step() method. The stepImpl() 
        method fires the TIME_CHANGED_EVENT before the execution of the 
        simulation event. So the time is changed first to match the logic 
        carried out for that time, and then the action for that time is 
        carried out. This is INDEPENDENT of the fact whether the time changes 
        or not. The TIME_CHANGED_EVENT is always fired."""
        if not self._eventlist.is_empty():
            event: SimEventInterface = self._eventlist.pop_first()
            self.fire_timed(event.time, Simulator.TIME_CHANGED_EVENT,
                            event.time)
            self._simulator_time = event.time
            event.execute()

    def end_replication(self):
        super().end_replication()
        self.eventlist().clear()
        
    def _run(self):
        self._runflag = True
        while not self.is_stopping_or_stopped():
            # check if we are done
            if self.eventlist().is_empty():
                t = self._run_until_time
            else:
                t = self.eventlist().peek_first().time
            if (t > self._run_until_time or (t == self._run_until_time \
                    and not self._run_until_including) 
                    or self.eventlist().is_empty()):
                self._simulator_time = self._run_until_time
                self._replication_state = ReplicationState.ENDING
                self._run_state = RunState.STOPPING
                return;
            # get the first event
            event: SimEventInterface = self.eventlist().pop_first()
            if not isinstance(event, SimEventInterface):
                raise DSOLError(f"Invalid SimEvent {event} from eventlist")
            if (event.time != self.simulator_time):
                self.fire_timed(event.time, Simulator.TIME_CHANGED_EVENT,
                                event.time)
            self._simulator_time = event.time
            try:
                event.execute()
            except Exception as e:
                s = "Exception during simulation at t={self.simulator_time}: "
                logger.log(self._error_log_level, s + str(e))
                if self._error_strategy > ErrorStrategy.LOG_AND_CONTINUE:
                    print(s + str(e))
                    traceback.print_exc()
                if self._error_strategy == ErrorStrategy.WARN_AND_PAUSE:
                    self._run_state = RunState.STOPPING
                elif self._error_strategy == ErrorStrategy.WARN_AND_END:
                    self.cleanup()
                elif self._error_strategy == ErrorStrategy.WARN_AND_EXIT:
                    sys.exit()
            # end except
        # end while
    # end run()

                
class DEVSSimulatorFloat(DEVSSimulator[float]):
    
    def __init__(self, name:str):
        super().__init__(name, float, 0.0)


class DEVSSimulatorInt(DEVSSimulator[int]):
    
    def __init__(self, name:str):
        super().__init__(name, int, 0)


class DEVSSimulatorDuration(DEVSSimulator[Duration]):
    
    def __init__(self, name: str, display_unit: str='s'):
        super().__init__(name, Duration, Duration(0.0, display_unit))
        self._display_unit = display_unit
