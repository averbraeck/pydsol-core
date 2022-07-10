import math
from typing import Union

from pydsol.core.units import Quantity
from pydsol.core.utils import get_module_logger


__all__ = [
    "InputParameter",
    "InputParameterMap",
    "InputParameterInt",
    "InputParameterFloat",
    "InputParameterStr",
    "InputParameterBool",
    "InputParameterQuantity",
    "InputParameterSelectionList",
    "InputParameterUnit",
    ]

logger = get_module_logger('parameters')


class InputParameter:

    def __init__(self, key: str, name: str, default_value,
                 display_priority: Union[int, float], *,
                 parent: "InputParameterMap"=None, description: str=None,
                 read_only: bool=False):
        if not isinstance(key, str):
            raise TypeError(f"parameter key {key} not a string")
        if len(key) == 0:
            raise ValueError("parameter key length 0")
        if '.' in key:
            raise ValueError(f"parameter key {key} contains a period")
        if not isinstance(name, str):
            raise TypeError(f"parameter name {name} not a string")
        if len(name) == 0:
            raise ValueError("parameter name length 0")
        if not (isinstance(display_priority, float) 
                or isinstance(display_priority, int)):
            raise TypeError(f"priority {display_priority} not a float/int")
        if parent is not None and not isinstance(parent, InputParameterMap):
            raise TypeError("parent not an InputParamterMap")
        if not isinstance(read_only, bool):
            raise TypeError(f"parameter read_only {read_only} not a bool")
        self._key: str = key
        self._name: str = name
        if description == None:
            self._description: str = name
        else:
            self._description: str = description
        self._default_value = default_value
        self._display_priority: float = display_priority
        self._read_only: bool = read_only
        self._value = default_value
        self._parent: "InputParameterMap" = parent
        if parent is not None:
            parent.add(self)
    
    @property    
    def key(self) -> str:
        return self._key
    
    def extended_key(self):
        if self._parent == None:
            return self._key
        else:
            return self._parent.extended_key() + '.' + self._key

    @property    
    def name(self) -> str:
        return self._name

    @property    
    def description(self) -> str:
        return self._description

    @property    
    def default_value(self) -> object:
        return self._default_value

    @property    
    def value(self) -> object:
        return self._value

    @value.setter
    def value(self, value: int):
        if self.read_only:
            raise ValueError("parameter {self.key} is read only")
        self._value = value

    @property    
    def display_priority(self) -> float:
        return self._display_priority

    @property    
    def read_only(self) -> bool:
        return self._read_only

    @property
    def parent(self) -> "InputParameterMap":
        return self._parent

    def __eq__(self, other): 
        if not isinstance(other, InputParameter):
            return False
        return self.display_priority == other.display_priority 

    def __ne__(self, other): 
        if not isinstance(other, InputParameter):
            return True
        return self.display_priority != other.display_priority 

    def __gt__(self, other): 
        if not isinstance(other, InputParameter):
            raise TypeError(f"cannot compare parameter with {other}")
        return self.display_priority > other.display_priority 

    def __ge__(self, other): 
        if not isinstance(other, InputParameter):
            raise TypeError(f"cannot compare parameter with {other}")
        return self.display_priority >= other.display_priority 

    def __lt__(self, other): 
        if not isinstance(other, InputParameter):
            raise TypeError(f"cannot compare parameter with {other}")
        return self.display_priority < other.display_priority 

    def __le__(self, other): 
        if not isinstance(other, InputParameter):
            raise TypeError(f"cannot compare parameter with {other}")
        return self.display_priority <= other.display_priority 

    def __str__(self) -> str:
        return self.extended_key() + " [" + self.name + "] = " \
            +str(self.value)
    
    def __repr__(self) -> str:
        return str(self)
    

class InputParameterMap(InputParameter):

    def __init__(self, key: str, name: str, display_priority: float, *,
                 parent: "InputParameterMap"=None, description: str=None):
        super().__init__(key, name, None, display_priority,
                         parent=parent, description=description,
                         read_only=True)
        self._value: dict[str, InputParameter] = {}

    @property    
    def value(self) -> dict:
        return self._value

    @value.setter
    def value(self, value):
        raise NotImplementedError("InputParameterMap value cannot be set")
    
    def add(self, input_parameter):
        if not isinstance(input_parameter, InputParameter):
            raise TypeError("input parameter not of the correct type")
        if input_parameter.key in self._value.keys():
            raise ValueError(f"duplicate key {input_parameter.key} in map {self}")
        input_parameter._parent = self
        self._value[input_parameter.key] = input_parameter
        # sort on the defined ordering in InputParameter after adding
        self._value = {k: v for k, v in sorted(self._value.items(),
                       key=lambda item: item[1])}
    
    def get(self, key: str) -> InputParameter:
        if '.' in key:
            parts = key.split('.')
            if not parts[0] in self._value:
                raise KeyError(f"could not find parameter {parts[0]} in {self}")
            return self._value[parts[0]].get(key[key.find('.') + 1:])
        else:
            if not key in self._value:
                raise KeyError(f"could not find parameter {key} in {self}")
            return self._value[key]
    
    def remove(self, key) -> InputParameter:
        if '.' in key:
            parts = key.split('.')
            if not parts[0] in self._value:
                raise KeyError(f"could not find parameter {parts[0]} in {self}")
            return self._value[parts[0]].remove(key[key.find('.') + 1:])
        return self._value.pop(key) 
        
    def print_values(self, *, depth:int=0) -> str:
        s = ""
        for key, param in self._value.items():
            if isinstance(param, InputParameterMap):
                s += f"{depth * ' '}MAP: {key}\n"
                s += param.print_values(depth=depth + 2)
            else: 
                s += f"{depth * ' '}{key} = {param.value}\n"
        return s


class InputParameterInt(InputParameter):

    def __init__(self, key: str, name: str, default_value: int,
                 display_priority: float, *,
                 parent: "InputParameterMap"=None, description: str=None,
                 read_only: bool=False,
                 min_value:int=-math.inf, max_value:int=math.inf,
                 format_str:str="%d"):
        super().__init__(key, name, default_value, display_priority,
                         parent=parent, description=description,
                         read_only=read_only)
        if not isinstance(default_value, int):
            raise TypeError(f"default value {default_value} is not an int")
        if not (isinstance(min_value, int) or isinstance(min_value, float)):
            raise TypeError(f"min value {min_value} is not an int or float")
        if not (isinstance(max_value, int) or isinstance(max_value, float)):
            raise TypeError(f"max value {max_value} is not an int or float")
        if not isinstance(format_str, str):
            raise TypeError(f"format string {format_str} is not a str")
        if min_value >= max_value:
            raise ValueError(f"min {min_value} >= max {max_value}")
        if not min_value <= default_value <= max_value:
            raise ValueError(f"default value {default_value} not between " + \
                             f"{min_value} and {max_value}")
        self._min: int = min_value
        self._max: int = max_value
        self._format: str = format_str
        
    @property    
    def value(self) -> int:
        return self._value

    @property
    def min_value(self) -> int:
        return self._min
    
    @property
    def max_value(self) -> int:
        return self._max
    
    @property
    def format_str(self) -> str:
        return self._format
    
    @value.setter
    def value(self, value: int):
        if self.read_only:
            raise ValueError(f"parameter {self.key} is read only")
        if not isinstance(value, int):
            raise ValueError(f"parameter value {value} not an int")
        if not self._min <= value <= self._max:
            raise ValueError(f"parameter value {value} not between " + \
                             f"{self._min} and {self._max}")
        self._value = value

        
class InputParameterFloat(InputParameter):

    def __init__(self, key: str, name: str, default_value: float,
                 display_priority: float, *,
                 parent: "InputParameterMap"=None, description: str=None,
                 read_only: bool=False,
                 min_value:int=-math.inf, max_value:int=math.inf,
                 format_str:str="%.2f"):
        super().__init__(key, name, default_value, display_priority,
                         parent=parent, description=description,
                         read_only=read_only)
        if not (isinstance(default_value, float) or 
                isinstance(default_value, int)):
            raise TypeError(f"default value {default_value} is not float/int")
        if not (isinstance(min_value, int) or isinstance(min_value, float)):
            raise TypeError(f"min value {min_value} is not an int or float")
        if not (isinstance(max_value, int) or isinstance(max_value, float)):
            raise TypeError(f"max value {max_value} is not an int or float")
        if not isinstance(format_str, str):
            raise TypeError(f"format string {format_str} is not a str")
        if min_value >= max_value:
            raise ValueError(f"min {min_value} >= max {max_value}")
        if not min_value <= default_value <= max_value:
            raise ValueError(f"default value {default_value} not between " + \
                             f"{min_value} and {max_value}")
        self._min: float = min_value
        self._max: float = max_value
        self._format: str = format_str
        
    @property    
    def value(self) -> float:
        return self._value

    @property
    def min_value(self) -> int:
        return self._min
    
    @property
    def max_value(self) -> int:
        return self._max
    
    @property
    def format_str(self) -> str:
        return self._format

    @value.setter
    def value(self, value: float):
        if self.read_only:
            raise ValueError(f"parameter {self.key} is read only")
        if not (isinstance(value, float) or isinstance(value, int)):
            raise ValueError(f"parameter value {value} not a float")
        if not self._min <= value <= self._max:
            raise ValueError(f"parameter value {value} not between " + \
                             f"{self._min} and {self._max}")
        self._value = value

        
class InputParameterStr(InputParameter):

    def __init__(self, key: str, name: str, default_value: str,
                 display_priority: float, *,
                 parent: "InputParameterMap"=None, description: str=None,
                 read_only: bool=False):
        super().__init__(key, name, default_value, display_priority,
                         parent=parent, description=description,
                         read_only=read_only)
        if not isinstance(default_value, str):
            raise TypeError(f"default value {default_value} is not a str")

    @property    
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str):
        if not isinstance(value, str):
            raise ValueError(f"parameter value {value} not a str")
        self._value = value

        
class InputParameterBool(InputParameter):

    def __init__(self, key: str, name: str, default_value: bool,
                 display_priority: float, *,
                 parent: "InputParameterMap"=None, description: str=None,
                 read_only: bool=False):
        super().__init__(key, name, default_value, display_priority,
                         parent=parent, description=description,
                         read_only=read_only)
        if not isinstance(default_value, bool):
            raise TypeError(f"default value {default_value} is not a bool")

    @property    
    def value(self) -> bool:
        return self._value

    @value.setter
    def value(self, value: bool):
        if self.read_only:
            raise ValueError(f"parameter {self.key} is read only")
        if not isinstance(value, bool):
            raise ValueError(f"parameter value {value} not a bool")
        self._value = value

        
class InputParameterQuantity(InputParameter):

    def __init__(self, key: str, name: str, default_value: Quantity,
                 display_priority: float, *,
                 parent: "InputParameterMap"=None, description: str=None,
                 read_only: bool=False,
                 min_si:int=-math.inf, max_si:int=math.inf,
                 format_str:str="%.2f"):
        super().__init__(key, name, default_value, display_priority,
                         parent=parent, description=description,
                         read_only=read_only)
        if not isinstance(default_value, Quantity):
            raise TypeError(f"default value {default_value} is not a Quantity")
        if not (isinstance(min_si, int) or isinstance(min_si, float)):
            raise TypeError(f"min si value {min_si} is not an int or float")
        if not (isinstance(max_si, int) or isinstance(max_si, float)):
            raise TypeError(f"max si value {max_si} is not an int or float")
        if not isinstance(format_str, str):
            raise TypeError(f"format string {format_str} is not a str")
        if min_si >= max_si:
            raise ValueError(f"min SI {min_si} >= max SI {max_si}")
        if not min_si <= default_value.si <= max_si:
            raise ValueError(f"default value {default_value.si} not between " + \
                             f"{min_si} and {max_si}")
        self._min: float = min_si
        self._max: float = max_si
        self._format: str = format_str
        self._type: type[Quantity] = type(default_value)

    @property    
    def value(self) -> Quantity:
        return self._value

    @property
    def min_si(self) -> int:
        return self._min
    
    @property
    def max_si(self) -> int:
        return self._max
    
    @property
    def format_str(self) -> str:
        return self._format

    @property
    def type(self) -> int:
        return self._type
    
    @value.setter
    def value(self, value: Quantity):
        if self.read_only:
            raise ValueError("parameter {self.key} is read only")
        if not isinstance(value, self._type):
            raise ValueError(f"parameter value {value} not a {self._type.__name__}")
        if not self._min <= value.si <= self._max:
            raise ValueError(f"parameter SI value {value.si} not between " + \
                             f"{self._min} and {self._max}")
        self._value = value

        
class InputParameterSelectionList(InputParameter):

    def __init__(self, key: str, name: str, options: list[str],
                 default_value: str, display_priority: float, *,
                 parent: "InputParameterMap"=None, description: str=None,
                 read_only: bool=False):
        super().__init__(key, name, default_value, display_priority,
                         parent=parent, description=description,
                         read_only=read_only)
        if not isinstance(options, list):
            raise TypeError(f"options {options} is not a list")
        if not all([isinstance(x, str) for x in options]):
            raise TypeError(f"non-str element(s) in options {options}")
        if not isinstance(default_value, str):
            raise TypeError(f"default value {default_value} not a str")
        if not default_value in options:
            raise ValueError(f"default value {default_value} not in options " \
                             +f"list {options}")
        self._options = options

    @property    
    def value(self) -> str:
        return self._value

    @property    
    def options(self) -> str:
        return self._options

    @value.setter
    def value(self, value: str):
        if self.read_only:
            raise ValueError("parameter {self.key} is read only")
        if not isinstance(value, str):
            raise TypeError(f"parameter value {value} not a string")
        if not value in self._options:
            raise ValueError(f"value {value} is not a valid option " \
                             +f"from {self._options}")
        self._value = value


class InputParameterUnit(InputParameterSelectionList):

    def __init__(self, key: str, name: str, quantity: type[Quantity],
                 default_value: str, display_priority: float, *,
                 parent: "InputParameterMap"=None, description: str=None,
                 read_only: bool=False):
        if not issubclass(quantity, Quantity):
            raise TypeError(f"quantity type {quantity} is not a Quantity")
        if not default_value in quantity._units:
            raise ValueError(f"default value {default_value} is not a unit " \
                             +f"for quantity {quantity}")
        super().__init__(key, name, list(quantity._units.keys()),
                         default_value, display_priority, parent=parent,
                         description=description, read_only=read_only)
        self._type = quantity 

    @property    
    def unittype(self) -> str:
        return self._type
