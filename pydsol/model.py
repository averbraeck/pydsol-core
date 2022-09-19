from abc import abstractmethod

from pydsol.interfaces import SimulatorInterface, ModelInterface, \
    StatisticsInterface
from pydsol.parameters import InputParameterMap, InputParameter
from pydsol.utils import DSOLError, get_module_logger

__all__ = [
    "DSOLModel",
    ]

logger = get_module_logger('model')


class DSOLModel(ModelInterface):
    
    def __init__(self, simulator: SimulatorInterface):  # TODO: streams
        if not isinstance(simulator, SimulatorInterface):
            raise DSOLError(f"simulator {simulator} not valid")
        self._simulator = simulator
        self._input_parameters = InputParameterMap("root", "parameters", 1)
        self._output_statistics: dict[str, StatisticsInterface] = {}

    @abstractmethod
    def construct_model(self):
        """code to construct the model for each replication"""

    @property
    def simulator(self):
        """return the simulator for this model"""
        return self._simulator

    @property
    def input_parameters(self):
        """return the input parameter map."""
        return self._input_parameters
    
    @input_parameters.setter
    def input_parameters(self, input_parameters: InputParameterMap):
        """set a new input parameter map."""
        if not isinstance(input_parameters, InputParameterMap):
            raise TypeError(f"input_parameters {input_parameters}" + \
                            "not an InputparameterMap")
        self._input_parameters = input_parameters 
    
    def add_parameter(self, input_parameter: InputParameter):
        """add an input parameter to the input parameter map."""
        self._input_parameters.add(input_parameter)

    def set_parameter(self, key: str, value: object):
        """set the parameter value of an input parameter."""
        self._input_parameters.get(key).value = value
        
    def get_parameter(self, key: str) -> object:
        """return the value of an input parameter."""
        return self._input_parameters.get(key).value
    
    def output_statistics(self) -> dict[str, StatisticsInterface]:
        """return the output statistics map."""
        return self._output_statistics
    
    def add_output_statistic(self, key: str, statistic: StatisticsInterface):
        """add an output statistic to the output statistics map."""
        if key in self._output_statistics:
            raise DSOLError(f"output statistic key {key} already registered")
        if not isinstance(statistic, StatisticsInterface):
            raise TypeError(f"output statistic {statistic}" + \
                            "not an output statistic type")
        self._output_statistics[key] = statistic

    def get_output_statistic(self, key: str) -> StatisticsInterface:
        """retrieve an output statistic from the output statistics map."""
        return self._output_statistics[key]

