from abc import abstractmethod

from pydsol.core.interfaces import SimulatorInterface, ModelInterface
from pydsol.core.parameters import InputParameterMap, InputParameter
from pydsol.core.utils import DSOLError, get_module_logger

logger = get_module_logger('model')


class DSOLModel(ModelInterface):
    
    def __init__(self, simulator: SimulatorInterface):  # TODO: streams
        if not isinstance(simulator, SimulatorInterface):
            raise DSOLError(f"simulator {simulator} not valid")
        self._simulator = simulator
        self._input_parameters = InputParameterMap("root", "parameters", 1)

    @abstractmethod
    def construct_model(self):
        """code to construct the model for each replication"""

    @property
    def simulator(self):
        return self._simulator

    @property
    def input_parameters(self):
        return self._input_parameters
    
    @input_parameters.setter
    def input_parameters(self, input_parameters: InputParameterMap):
        if not isinstance(input_parameters, InputParameterMap):
            raise TypeError(f"input_parameters {input_parameters}" + \
                            "not an InputparameterMap")
        self._input_parameters = input_parameters 
    
    def add_parameter(self, input_parameter: InputParameter):
        self._input_parameters.add(input_parameter)

    def set_parameter(self, key: str, value: object):
        self._input_parameters.get(key).value = value
        
    def get_parameter(self, key: str) -> object:
        return self._input_parameters.get(key).value
        
