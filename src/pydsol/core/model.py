from abc import abstractmethod

from pydsol.core.interfaces import SimulatorInterface, ModelInterface
from pydsol.core.utils import DSOLError, get_module_logger

logger = get_module_logger('model')


class DSOLModel(ModelInterface):
    
    def __init__(self, simulator: SimulatorInterface):  # TODO: streams
        if not isinstance(simulator, SimulatorInterface):
            raise DSOLError(f"simulator {simulator} not valid")
        self._simulator = simulator

    @abstractmethod
    def construct_model(self):
        """code to construct the model for each replication"""

    @property
    def simulator(self):
        return self._simulator
