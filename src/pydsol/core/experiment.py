"""
The experiment module contains the classes to set-up and carry out simulation
experiments. The structure of a simulation experiment is as follows:

* An `Experiment` contains multiple `Replication` instances. The `Experiment`
  is responsible for executing the replications and for collecting 
  summarizing statistical data from the replications. The `Experiment` 
  runs a model according to a `RunControl` object with fixed values for
  the `InputParameters` of the model. When the `InputParameters` change, 
  one runs a new `Experiment`. Because the `Experiment` involves multiple
  runs (multiple replications), seed management for the stochastic 
  distributions in the model is important. The streams module contains
  several classes for ensuring proper seed management.    
* The `Replication` is a single run of a model. It initializes the model with 
  the values of the InputParameters, and runs the model to calculate the 
  values of the output statistics. Different replications of a model that
  are part of the same experiment only differ in their seeds for the random
  number generator(s) used by the model. Input parameters, model structure,
  run length, and warmup period should all be the same for multiple 
  replications of an experiment.
* The `RunControl` object contains the start time, end time, and warmup 
  period for a model run. Multiple replications of the same experiment use the
  same RunControl.  
* The `Simulator` executes a `Model` on the basis of an `Replication`. The 
  `simulator.initialize(...)` method ensures that the model is built, and
  that the execution of the model using the replication information starts.

The experiment module also contains a `SingleReplication` class, which is 
an easy class to carry out an experiment with a single replication (for 
demonstrations, testing, or for models where stochasticity does not play a 
major role).  
"""

from typing import TypeVar, Generic

from pydsol.core.interfaces import SimulatorInterface, ModelInterface, \
    ReplicationInterface, ExperimentInterface
from pydsol.core.utils import DSOLError, get_module_logger

__all__ = [
    "RunControl",
    "ExperimentRunControl",
    "Replication",
    "SingleReplication",
    "ExperimentReplication",
    "Experiment",
    ]

logger = get_module_logger('pubsub')

# The TypeVar for time is used for type hinting for simulator time types
TIME = TypeVar("TIME", float, int)


class RunControl():
    """
    The RunControl object contains the start time, end time, and warmup 
    period for a model run. Multiple replications of the same experiment 
    use the same RunControl. 

    Note
    ----
    The TIME type mentioned below is float or int, or a class extending 
    float or int. An example of such a class is the Duration unit from the
    units module, which can be used to work with meaningful clock times 
    (e.g., a process duration of 10.5 minutes; a run time of 5 days, etc.).
    
    Attributes
    ----------
    _name: str
        A brief identifying name of the RunControl.
    _start_sim_time: TIME
        The start simulation time (float or int), often zero
    _end_sim_time: TIME
        The end simulation time (float or int). Note that when the start 
        simulation time is not zero, _end_sim_time does **not** indicate the
        run length, but rather the absolute time when the simulation run stops.
    _warmup_sim_time: TIME
        The absolute time when the warmup period of the model has passed,
        resulting in the reset of all simulation statistics objects such as
        the SimCounter, SimTally and SimPersistent used in the model. 
        Ordinary statistics objects (e.g., the Tally) will not be reset.  
    """
    
    def __init__(self, name: str, start_time: TIME, warmup_period: TIME,
                 run_length: TIME):
        """
        Create an instance of the RunControl object that contains the 
        start time, end time, and warmup period for a model run. Multiple 
        replications of the same experiment use the same RunControl.

        **Note**

        The TIME type mentioned below is float or int, or a class extending 
        float or int. An example of such a class is the Duration unit from the
        units module, which can be used to work with meaningful clock times 
        (e.g., a process duration of 10.5 minutes; a run time of 5 days, etc.).
        
        Parameters
        ----------
        name: str
            A brief identifying name of the RunControl.
        start_time: TIME
            The start simulation time (float or int), often zero
        warmup_period: TIME
            The time (float or int) relative to start_time when the warmup 
            period of the model has passed, resulting in the reset of all 
            simulation statistics objects such as the SimCounter, SimTally 
            and SimPersistent used in the model. Ordinary statistics objects 
            (e.g., the Tally) will not be reset.
        run_length: TIME
            The run length (float or int), relative to the start_time. Note
            that the end simulation time is therefore start_time + run_length.
        
        Raises
        ------
        TypeError
            when name is not a str
        TypeError
            when start_time is not a number
        TypeError
            when warmup_period is not a number
        TypeError
            when run_length is not a number
        """
        if not isinstance(name, str):
            raise TypeError("name {name} should be a str")
        if not isinstance(start_time, (float, int)):
            raise TypeError("start_time {start_time} should be numeric")
        if not isinstance(warmup_period, (float, int)):
            raise TypeError("warmup_period {warmup_period} should be numeric")
        if not isinstance(run_length, (float, int)):
            raise TypeError("run_length {run_length} should be numeric")
        self._name: str = name
        self._start_sim_time: TIME = start_time
        self._end_sim_time: TIME = start_time + run_length
        self._warmup_sim_time: TIME = start_time + warmup_period
    
    @property
    def name(self) -> str:
        """
        Return the brief identifying name of the RunControl.
        
        Returns
        -------
        str
            The brief identifying name of the RunControl.
        """
        return self._name

    @property
    def start_sim_time(self) -> TIME:
        """
        Return (absolute) start simulation time.
        
        Returns
        -------
        TIME (float, int, Duration)
            The (absolute) start simulation time.
        """ 
        return self._start_sim_time

    @property
    def warmup_sim_time(self) -> TIME:
        """
        Return absolute time when the warmup period of the model has passed,
        resulting in the reset of all simulation statistics objects such as
        the SimCounter, SimTally and SimPersistent used in the model. 
        Ordinary statistics objects (e.g., the Tally) will not be reset.
        
        Returns
        -------
        TIME (float, int, Duration)
            The (absolute) time when the warmup period of the model has passed.
        """
        return self._warmup_sim_time

    @property
    def end_sim_time(self) -> TIME:
        """
        Return the end simulation time (float or int). Note that when the start 
        simulation time is not zero, _end_sim_time does **not** indicate the
        run length, but rather the absolute time when the simulation run stops.
        
        Returns
        -------
        TIME (float, int, Duration)
            The (absolute) end simulation time.
        """
        return self._end_sim_time

    @property
    def warmup_period(self) -> TIME:
        """
        Return the time, relative to start_time, when the warmup period of the 
        model has passed, resulting in the reset of all simulation statistics 
        objects such as the SimCounter, SimTally and SimPersistent used in 
        the model. Ordinary statistics objects (e.g., the Tally) will not 
        be reset..
        
        Returns
        -------
        TIME (float, int, Duration)
            The time, relative to start_time, when the warmup period of the 
            model has passed.
        """
        return self._warmup_sim_time - self._start_sim_time

    @property
    def run_length(self) -> TIME:
        """
        Return the run length, relative to the start_time.
        
        Returns
        -------
        TIME (float, int, Duration)
            The run length (float or int), relative to the start_time.
        """
        return self._end_sim_time - self._start_sim_time


class Replication(ReplicationInterface):
    """
    The Replication is a single run of a model. It initializes the model with 
    the values of the InputParameters, and runs the model to calculate the 
    values of the output statistics. Different replications of a model that
    are part of the same experiment only differ in their seeds for the random
    number generator(s) used by the model. Input parameters, model structure,
    run length, and warmup period should all be the same for multiple 
    replications of an experiment.
    
    **Note**

    The TIME type mentioned below is float or int, or a class extending 
    float or int. An example of such a class is the Duration unit from the
    units module, which can be used to work with meaningful clock times 
    (e.g., a process duration of 10.5 minutes; a run time of 5 days, etc.).
        
    Attributes
    ----------
    _nr: int
        The number that identifies the Replication within an Experiment. 
    _run_control: RunControl
        The RunContro object that stores the start simulation time, the end 
        simulation time, and the absolute time when the warmup period of 
        the model has passed.  
    """
    
    def __init__(self, name: str, nr: int, start_time: TIME, 
                 warmup_period: TIME, run_length: TIME):
        """
        Create a replication with a replication number. Details about the
        start time, end time, and warmup period will be stored in a
        RunControl object.
        
        Attributes
        ----------
        name: str
            A brief identifying name, that will be used as the name of the 
            RunControl.
        nr: int
            The number that identifies the Replication within an Experiment. 
        start_time: TIME
            The (absolute) start simulation time (float or int), often zero. 
            It will be stored in the RunControl.
        warmup_period: TIME
            The (relative) period when the warmup period of the model has 
            passed, resulting in the reset of all simulation statistics objects 
            such as the SimCounter, SimTally and SimPersistent used in the 
            model. Ordinary statistics objects (e.g., the Tally) will not be 
            reset. It will be stored in the RunControl. The absolute time
            when the warump takes place is (start_time + warmup_period).
        run_length: TIME
            The (relative) duration of the run (float or int). The absolute
            time when the simulation ends is equal to (start_time + run_length).
            run_length and end_sim_time are the same when the start_time is zero.
            The information about run length will be stored in the RunControl.
        """
        self._run_control = RunControl(name, start_time, warmup_period,
                                      run_length)
        self._nr = nr
    
    @property
    def run_control(self) -> RunControl:
        """
        Return the RunControl object that stores the start simulation time, 
        the end simulation time, and warmup time, which is the absolute time 
        when the warmup period of the model has passed.  
        """
        return self._run_control

    @property
    def start_sim_time(self) -> TIME:
        """
        Return the absolute start simulation time (float or int). The value 
        is stored in the RunControl. 
        """
        return self.run_control._start_sim_time

    @property
    def warmup_sim_time(self) -> TIME:
        """
        Return the absolute time when the warmup period of the model has 
        passed, resulting in the reset of all simulation statistics objects 
        such as the SimCounter, SimTally and SimPersistent used in the model. 
        Ordinary statistics objects (e.g., the Tally) will not be reset.
        The value is stored in the RunControl.The (relative) warmup **period**
        is (warmup_sim_time - start_sim_time).
        """
        return self.run_control._warmup_sim_time

    @property
    def end_sim_time(self) -> TIME:
        """
        Return the absolute time when the simulation replication ends, and the 
        statistics for the simulation replication are finalized, Note that 
        when the start simulation time is not zero, _end_sim_time does **not** 
        indicate the run length, but rather the absolute time when the 
        simulation run stops. It is stored in the RunControl. The (relative) 
        **duration** uf the replication is (end_sim_time - start_sim_time).
        """
        return self.run_control._end_sim_time
    
    @property
    def warmup_period(self) -> TIME:
        """
        Return the (relative) duration of the warmup period (float or int). 
        The values ofwarmup_period and end_sim_time are the same when the 
        start_time is zero.
        """
        return self.run_control._warmup_sim_time - self.run_control._start_sim_time

    @property
    def run_length(self) -> TIME:
        """
        Return the (relative) duration of the run (float or int). The values of
        run_length and end_sim_time are the same when the start_time is zero.
        """
        return self.run_control._end_sim_time - self.run_control._start_sim_time

    
class SingleReplication(Replication, Generic[TIME]):

    def __init__(self, name: str, start_time: TIME, warmup_period: TIME,
                 run_length: TIME):
        """
        Create a single replication that will have the replication number 0.
        
        Attributes
        ----------
        name: str
            A brief identifying name, that will be used as the name of the 
            RunControl.
        start_time: TIME
            The (absolute) start simulation time (float or int), often zero. 
            It will be stored in the RunControl.
        warmup_period: TIME
            The (relative) period when the warmup period of the model has 
            passed, resulting in the reset of all simulation statistics objects 
            such as the SimCounter, SimTally and SimPersistent used in the 
            model. Ordinary statistics objects (e.g., the Tally) will not be 
            reset. It will be stored in the RunControl. The absolute time
            when the warump takes place is (start_time + warmup_period).
        run_length: TIME
            The (relative) duration of the run (float or int). The absolute
            time when the simulation ends is equal to (start_time + run_length).
            run_length and end_sim_time are the same when the start_time is zero.
            The information about run length will be stored in the RunControl.
        """
        super().__init__(name, 0, start_time, warmup_period, run_length)


class Experiment(ExperimentInterface):

    def __init__(self, name: str, simulator: SimulatorInterface,
                 model: ModelInterface,
                 start_time: TIME, warmup_period: TIME,
                 run_length: TIME, nr_replications: int):
        if not isinstance(simulator, SimulatorInterface):
            raise DSOLError(f"simulator {simulator} not valid")
        if not isinstance(model, ModelInterface):
            raise DSOLError(f"model {model} not valid")
        if not isinstance(nr_replications, int) or nr_replications < 0:
            raise DSOLError(f"nr_replications {nr_replications} invalid")
        self._simulator = simulator
        self._model = model
        self._run_control = RunControl(name, start_time, warmup_period,
                                       run_length)
        self._nr_replications = nr_replications    

    # TODO: implement start and end experiment, replication, etc.
     
    @property
    def run_control(self):
        return self._run_control
    
    @property
    def simulator(self) -> SimulatorInterface:
        return self._simulator

    @property
    def model(self):
        return self._model

    @property
    def nr_replications(self):
        return self._nr_replications

    
class ExperimentReplication(Replication, Generic[TIME]):

    def __init__(self, name: str, nr: int, start_time: TIME, 
                 warmup_period: TIME, run_length: TIME, 
                 experiment: Experiment):
        super.__init__(name, nr, start_time, warmup_period, run_length)
        if not isinstance(experiment, Experiment):
            raise DSOLError(f"experiment {experiment} not valid")
        self._experiment = experiment
    
    @property
    def experiment(self) -> Experiment:
        return self._experiment


class ExperimentRunControl(RunControl, Generic[TIME]):

    def __init__(self, name: str, start_time: TIME, warmup_period: TIME,
                 run_length: TIME, nr_replications: int):
        super.__init__(name, start_time, warmup_period, run_length)
        if not isinstance(nr_replications, int) or nr_replications < 0:
            raise DSOLError(f"nr_replications {nr_replications} invalid")
        self._nr_replications = nr_replications
        
    @property
    def nr_replications(self) -> int:
        return self._nr_replications
    
