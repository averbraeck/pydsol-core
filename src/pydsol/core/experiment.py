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


class RunControl(Generic[TIME]):

    def __init__(self, name: str, start_time: TIME, warmup_period: TIME,
                 run_length: TIME):
        if not isinstance(name, str):
            raise DSOLError("name {name} should be a str")
        if not isinstance(start_time, (float, int)):
            raise DSOLError("start_time {start_time} should be numeric")
        if not (isinstance(warmup_period, float) or \
                isinstance(warmup_period, int)):
            raise DSOLError("warmup_period {warmup_period} should be numeric")
        if not isinstance(run_length, (float, int)):
            raise DSOLError("run_length {run_length} should be numeric")
        self._name = name
        self._start_sim_time = start_time
        self._end_sim_time = start_time + run_length
        self._warmup_sim_time = start_time + warmup_period
        
    @property
    def name(self) -> str:
        return self._name

    @property
    def start_sim_time(self) -> TIME:
        return self._start_sim_time

    @property
    def warmup_sim_time(self) -> TIME:
        return self._warmup_sim_time

    @property
    def end_sim_time(self) -> TIME:
        return self._end_sim_time


class Replication(ReplicationInterface, Generic[TIME]):

    def __init__(self, name: str, start_time: TIME, warmup_period: TIME,
                 run_length: TIME):
        self._run_control = RunControl(name, start_time, warmup_period,
                                      run_length)
        
    @property
    def run_control(self):
        return self._run_control

    @property
    def start_sim_time(self) -> TIME:
        return self.run_control._start_sim_time

    @property
    def warmup_sim_time(self) -> TIME:
        return self.run_control._warmup_sim_time

    @property
    def end_sim_time(self) -> TIME:
        return self.run_control._end_sim_time

    
class SingleReplication(Replication, Generic[TIME]):

    def __init__(self, name: str, start_time: TIME, warmup_period: TIME,
                 run_length: TIME):
        super().__init__(name, start_time, warmup_period, run_length)


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

    def __init__(self, name: str, start_time: TIME, warmup_period: TIME,
                 run_length: TIME, experiment: Experiment):
        super.__init__(name, start_time, warmup_period, run_length)
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
    
