"""
InputParameters describe different types of input parameters for the model.
All parameters for a model are contained in a hierarchical map where
successive keys can be retrieved using a dot-notation between the key 
elements. 

Example
-------
Suppose a model has two servers: server1 and server2. Each of the
servers has an average service time and a number of resources. This can be
codes using keys 'server1.avg_serice_time', 'server1.nr_resources',
'server2.avg_serice_time', 'server2.nr_resources'. This means that the 
key 'server1' contains an InputParameterMap with an instance of 
InputParameterFloat for the service time, and InputParameterInt for the
number of resources. Readers for the input parameter map can read the model
parameters, e.g., from the screen, a web page, an Excel file, a properties 
file, or a JSON file.        
"""

import math
from typing import Union

from pydsol.core.units import Quantity
from pydsol.core.utils import get_module_logger
from pydsol.core.interfaces import InputParameterInterface

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


class InputParameter(InputParameterInterface):
    """
    The InputParameter is a user readable and settable property for the 
    simulation model. All parameters for a model are contained in a 
    hierarchical map where successive keys can be retrieved using a 
    dot-notation between the key elements.
    
    Attributes
    ----------
    _key: str
        The key of the parameter that can be a part of the dot-notation to 
        uniquely identify the model parameter. The key does not contain the 
        name of the parent, and should not contain any periods. It should 
        also be unique within its node of the input parameter tree. The key 
        is immutable.
    _name: str
        Concise description of the input parameter, which can be used
        in a GUI to identify the parameter to the user.
    _default_value: object
        The default (initial) value of the parameter. The actual type will 
        be defined in subclasses of `InputParameter`. The default value is
        immutable.
    _display_priority: float
        A number indicating the order of display of the parameter in the 
        parent parameter map. Floats are allowed to make it easy to insert 
        an extra parameter between parameters that have already been 
        allocated subsequent integer values.
    _parent: InputParameterMap (optional)
        The parent map in which the parameter can be retrieved using its  key. 
        Typically, only the root InputParameterMap has no parent, and all 
        other parameters have an InputParameterMap as parent.
    _description: str (optional)
        A description or explanation of the InputParameter. For instance,
        an indication of the bounds or the type. This value is purely there 
        for the user interface.
    _read_only: bool (optional)
        Whether a user is prohibited from changing the value of the
        parameter or not (default false, so the parameter *can* be changed).
    _value: object
        The actual value of the parameter. The value is initialized with
        default_value and is updated based on user input or data input.
        The actual type will be defined in subclasses of `InputParameter`.
    """
    
    def __init__(self, key: str, name: str, default_value,
                 display_priority: Union[int, float], *,
                 parent: "InputParameterMap"=None, description: str=None,
                 read_only: bool=False):
        """
        Create a new InputParameter. 
        
        Parameters
        ----------
        key: str
            The key of the parameter that can be a part of the 
            dot-notation to uniquely identify the model parameter. The key 
            does not contain the name of the parent, and should not contain
            any periods. It should also be unique within its node of the 
            input parameter tree. The key is set at time of construction and 
            it is immutable.
        name: str
            Concise description of the input parameter, which can be used
            in a GUI to identify the parameter to the user.
        default_value: object
            The default (initial) value of the parameter. The actual type
            will be defined in subclasses of `InputParameter`.
        display_priority: Union[int, float]
            A number indicating the order of display of the parameter
            in the parent parameter map. Floats are allowed to make it
            easy to insert an extra parameter between parameters that
            have already been allocated subsequent integer values. 
        parent: InputParameterMap (optional)
            The parent map in which the parameter can be retrieved using its
            key. Typically, only the root InputParameterMap has no parent,
            and all other parameters have an InputParameterMap as parent.
        description: str (optional)
            A description or explanation of the InputParameter. For instance,
            an indication of the bounds or the type. This value is purely 
            there for the user interface.
        read_only: bool (optional)
            Whether a user is prohibited from changing the value of the
            parameter or not (default false, so the parameter *can* be 
            changed).
            
        Raises
        ------
        TypeError
            when key is not a string
        ValueError
            when key is an empty string, or key contains a period
        ValueError
            when key is not unique in the parent InputParameterMap
        TypeError
            when name is not a string
        ValueError
            when name is an empty string
        TypeError
            when display priority is not a number
        TypeError
            when parent is not an InputParametermap or None
        TypeError
            when read_only is not a bool
        """
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
            self._description: str = ""
        else:
            self._description: str = description
        self._default_value = default_value
        self._display_priority: float = float(display_priority)
        self._read_only: bool = read_only
        self._value = default_value
        self._parent: "InputParameterMap" = parent
        if parent is not None:
            # will take care of error for duplicate keys
            parent.add(self)
    
    @property    
    def key(self) -> str:
        """
        Return the key of the parameter that can be a part of the 
        dot-notation to uniquely identify the model parameter. The key 
        does not contain the name of the parent. The key is set at time 
        of construction and it is immutable.
        
        Returns
        -------
        str
            The key of the parameter that can be a part of the 
            dot-notation to uniquely identify the model parameter.
        """
        return self._key
    
    def extended_key(self):
        """
        Return the extended key of this InputParameter including parents 
        with a dot-notation. The name of this parameter is the last entry 
        in the dot notation.
        
        Returns
        -------
        str
            The extended key of this InputParameter including parents 
            with a dot-notation.
        """
        if self._parent == None:
            return self._key
        else:
            return self._parent.extended_key() + '.' + self._key

    @property    
    def name(self) -> str:
        """
        Returns the concise description of the input parameter, which can 
        be used in a GUI to identify the parameter to the user.
        
        Returns
        -------
        str
            The concise description of the input parameter, which can 
            be used in a GUI to identify the parameter to the user.
        """
        return self._name

    @property    
    def description(self) -> str:
        """
        Returns a description or explanation of the InputParameter. For 
        instance, an indication of the bounds or the type. This value is 
        purely there for the user interface.
        
        Returns
        -------
        str
            A description or explanation of the InputParameter.
        """
        return self._description

    @property    
    def default_value(self) -> object:
        """
        Returns the default (initial) value of the parameter. The actual 
        return type will be defined in subclasses of `InputParameter`. 
        The default value is immutable.
        
        Returns
        -------
        object
            The default (initial) value of the parameter.
        """
        return self._default_value

    @property    
    def value(self) -> object:
        """
        Returns the actual value of the parameter. The value is initialized
        with default_value and is updated based on user input or data input.
        The actual type will be defined in subclasses of `InputParameter`.
        
        Returns
        -------
        object
            The actual value of the parameter.
        """
        return self._value

    @value.setter
    def value(self, value: object):
        """
        Set (overwrite) the actual value of the parameter.
        
        Parameters
        ----------
        value: object
            The new value of the parameter.
        """
        if self.read_only:
            raise ValueError("parameter {self.key} is read only")
        self._value = value

    @property    
    def display_priority(self) -> float:
        """
        Return the number indicating the order of display of the parameter 
        in the parent parameter map. Floats make it easy to insert an extra 
        parameter between parameters that have already been allocated 
        subsequent integer values.
        
        Returns
        -------
        float
            The number indicating the order of display of the parameter 
            in the parent parameter map.
        """
        return self._display_priority

    @property    
    def read_only(self) -> bool:
        """
        Return whether a user is prohibited from changing the value of the
        parameter or not.
        
        Returns
        -------
        bool
            Whether a user is prohibited from changing the value of the
            parameter or not.
        """
        return self._read_only

    @property
    def parent(self) -> "InputParameterMap":
        """
        Return the parent map in which the parameter can be retrieved using 
        its  key. Typically, only the root InputParameterMap has no parent, 
        and all other parameters have an InputParameterMap as parent.
        
        Returns
        -------
        InputParameterMap
            the parent map in which the parameter can be retrieved using 
            its  key.
        """
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
    """
    The InputParameterMap contains a number of InputParameters, each of 
    which can also be an InputParameterMap again. The InputParameterMap 
    provides functions to add and remove sub-parameters, to retrieve 
    sub-parameters based on their key, and to return a sorted set of 
    InputParameters based on their displayValue.
    
    The `InputParameterMap` has all attributes of the `InputParameter`. 
    The `_value` attribute is of the type `dict[str, InputParameter]`. 
    """
    
    def __init__(self, key: str, name: str, display_priority: float, *,
                 parent: "InputParameterMap"=None, description: str=None):
        """
        Create a new `InputParameterMap`. This can be the root map, or
        a sub-map. The `InputParameterMap` has no default value, and is
        read-only by definition. 
        
        Parameters
        ----------
        key: str
            The key of the parameter that can be a part of the 
            dot-notation to uniquely identify the model parameter. The key 
            does not contain the name of the parent, and should not contain
            any periods. It should also be unique within its node of the 
            input parameter tree. The key is set at time of construction and 
            it is immutable.
        name: str
            Concise description of the input parameter, which can be used
            in a GUI to identify the parameter to the user.
        display_priority: Union[int, float]
            A number indicating the order of display of the parameter
            in the parent parameter map. Floats are allowed to make it
            easy to insert an extra parameter between parameters that
            have already been allocated subsequent integer values. 
        parent: InputParameterMap (optional)
            The parent map in which the parameter can be retrieved using its
            key. Typically, only the root InputParameterMap has no parent,
            and all other parameters have an InputParameterMap as parent.
        description: str (optional)
            A description or explanation of the InputParameter. For instance,
            an indication of the bounds or the type. This value is purely 
            there for the user interface.
            
        Raises
        ------
        TypeError
            when key is not a string
        ValueError
            when key is an empty string, or key contains a period
        ValueError
            when key is not unique in the parent InputParameterMap
        TypeError
            when name is not a string
        ValueError
            when name is an empty string
        TypeError
            when display priority is not a number
        TypeError
            when parent is not an InputParametermap or None
        """
        super().__init__(key, name, None, display_priority,
                         parent=parent, description=description,
                         read_only=True)
        self._value: dict[str, InputParameter] = {}

    @property    
    def value(self) -> dict[str, InputParameter]:
        """
        Returns the dict defined in this `InputParameterMap`, 
        which is the value.
        
        Returns
        -------
        dict[str, InputParameter]
            The dict defined in this `InputParameterMap`.
        """
        return self._value

    @value.setter
    def value(self, value):
        """
        Note
        ----
        `InputParameterMap` does not have a setter for the value.
        
        Raises
        ------
        NotImplementedError
            when called.
        """
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
    """
    InputParameterInt defines an integer input parameter with possible
    lowest and highest values.
    
    The `InputParameterMap` has all attributes of the `InputParameter`. 
    The `_value` attribute is of the type `int`. It also has the following
    extra attributes:
    
    Attributes
    ----------
    _min: int
        The lowest value (inclusive) that can be entered for this parameter.
    _max: int
        The highest value (inclusive) that can be entered for this parameter.
    _format: str
        The formatting string that is used in the user interface and when
        printing the parameter, e.g. to limit the number of decimals,
        to indicate the + or - sign, etc.
    """

    def __init__(self, key: str, name: str, default_value: int,
                 display_priority: float, *,
                 parent: "InputParameterMap"=None, description: str=None,
                 read_only: bool=False,
                 min_value:int=-math.inf, max_value:int=math.inf,
                 format_str:str="%d"):
        """
        Create a new InputParameterInt that can contain an integer input
        value for the simulation model. 
        
        Parameters
        ----------
        key: str
            The key of the parameter that can be a part of the 
            dot-notation to uniquely identify the model parameter. The key 
            does not contain the name of the parent, and should not contain
            any periods. It should also be unique within its node of the 
            input parameter tree. The key is set at time of construction and 
            it is immutable.
        name: str
            Concise description of the input parameter, which can be used
            in a GUI to identify the parameter to the user.
        default_value: int
            The default (initial) value of the parameter.
        display_priority: Union[int, float]
            A number indicating the order of display of the parameter
            in the parent parameter map. Floats are allowed to make it
            easy to insert an extra parameter between parameters that
            have already been allocated subsequent integer values. 
        parent: InputParameterMap (optional)
            The parent map in which the parameter can be retrieved using its
            key. Typically, only the root InputParameterMap has no parent,
            and all other parameters have an InputParameterMap as parent.
        description: str (optional)
            A description or explanation of the InputParameter. For instance,
            an indication of the bounds or the type. This value is purely 
            there for the user interface.
        read_only: bool (optional)
            Whether a user is prohibited from changing the value of the
            parameter or not (default false, so the parameter *can* be 
            changed).
        min_value: int (optional)
            The lowest value (inclusive) that can be entered for this
            parameter.
        max_value: int (optional)
            The highest value (inclusive) that can be entered for this
            parameter.
        format_str: str (optional)
            The formatting string that is used in the user interface and when
            printing the parameter, e.g. to limit the number of decimals,
            to indicate the + or - sign, etc.
            
        Raises
        ------
        TypeError
            when key is not a string
        ValueError
            when key is an empty string, or key contains a period
        ValueError
            when key is not unique in the parent InputParameterMap
        TypeError
            when name is not a string
        ValueError
            when name is an empty string
        TypeError
            when display priority is not a number
        TypeError
            when parent is not an InputParametermap or None
        TypeError
            when read_only is not a bool
        TypeError
            when default_value is not an int
        TypeError
            when min_value or max_value is not an int or float
        TypeError
            when format_str is not a string
        ValueError
            when min_value >= max_value
        ValueError
            when default value not between min_value and max_value (inclusive)
        """
        super().__init__(key, name, default_value, display_priority,
                         parent=parent, description=description,
                         read_only=read_only)
        if not isinstance(default_value, int):
            raise TypeError(f"default value {default_value} is not an int")
        if not isinstance(min_value, (int, float)):
            raise TypeError(f"min value {min_value} is not an int or float")
        if not isinstance(max_value, (int, float)):
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
        """
        Set (overwrite) the actual value of the parameter.
        
        Parameters
        ----------
        value: int
            The new value of the parameter.
            
        Raises
        ------
        ValueError
            if the parameter is read-only
        ValueError
            if the new value is not an int
        ValueError
            if the new value is not between the min_value and max_value
        """
        if self.read_only:
            raise ValueError(f"parameter {self.key} is read only")
        if not isinstance(value, int):
            raise ValueError(f"parameter value {value} not an int")
        if not self._min <= value <= self._max:
            raise ValueError(f"parameter value {value} not between " + \
                             f"{self._min} and {self._max}")
        self._value = value

        
class InputParameterFloat(InputParameter):
    """
    InputParameterFloat defines a floating point input parameter with possible
    lowest and highest values. 
    """

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
        if not isinstance(min_value, (int, float)):
            raise TypeError(f"min value {min_value} is not an int or float")
        if not isinstance(max_value, (int, float)):
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
        if not isinstance(value, (float, int)):
            raise ValueError(f"parameter value {value} not a float")
        if not self._min <= value <= self._max:
            raise ValueError(f"parameter value {value} not between " + \
                             f"{self._min} and {self._max}")
        self._value = value

        
class InputParameterStr(InputParameter):
    """
    InputParameterStr defines a string input parameter. 
    """

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
    """
    InputParameterBool defines a boolean input parameter. 
    """

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
    """
    InputParameterStr defines an input parameter that can contain a 
    quantity. For example, a Length, Speed or Duration can be entered
    with the corresponding unit. Limits for lowest values and highest values
    (in the SI or base unit) can be provided for error checking, e.g.,
    to indicate that a value should be positive. 
    """

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
        if not isinstance(min_si, (int, float)):
            raise TypeError(f"min si value {min_si} is not an int or float")
        if not isinstance(max_si, (int, float)):
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
    """
    InputParameterStr defines a string input parameter that has to be a 
    member of a provided list of strings. In a user interface, this can
    be indicated as a pick list. An example is a list of the state codes 
    of the USA.   
    """

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
    """
    InputParameterStr defines an input parameter that is a unit for a 
    given quantity type. The `InputParameterUnit` class extends the
    `InputParameterSelectionList` class and autogenerates a list of
    units to select from.
    """

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
        self._type: type[Quantity] = quantity 

    @property    
    def unittype(self) -> type[Quantity]:
        return self._type
