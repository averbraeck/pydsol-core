"""
The simevent module provides the basic implementation for simulation events,
or SimEvent in short. SimEvents are instances that store information about
a method that can be called later by the simulator, as used in the event
scheduling paradigm for discrete-event simulation. This later, or deferred,
calling of a method is known as "deferred method invocation". 

The SimEventInterface in this module allows other implementations of the 
SimEvent, which will be recognized by the event lists and other classes.
"""

from abc import ABC, abstractmethod
from inspect import isfunction, ismethod
from typing import Union

from pydsol.utils import DSOLError, get_module_logger


__all__ = [
    "SimEventInterface",
    "SimEvent",
    ]

logger = get_module_logger('simevent')


class SimEventInterface(ABC):
    """
    SimEventInterface defines the properties that all SimEvent classes 
    need to have. The most important property of a SimEvent is that it is 
    executable, so it defines the execute() method.
    """
    
    # static priorities that can be used, based on Java thread priorities
    MIN_PRIORITY: int = 1
    NORMAL_PRIORITY: int = 5
    MAX_PRIORITY: int = 10
    
    @abstractmethod
    def execute(self):
        """execute the event, usually as a method call on an object."""

    @property 
    @abstractmethod
    def time(self) -> Union[int, float]:
        """Return the absolute execution time, float or int."""

    @property 
    @abstractmethod
    def priority(self) -> int:
        """Return the priority; higher value is higher priority."""

    @property 
    @abstractmethod
    def id(self) -> int:
        """Return the unique id of of the SimEvent."""


class SimEvent(SimEventInterface):
    """
    SimEvent stores the information on a deferred method call that will
    be scheduled on the event list. Deferred method invocation is the 
    execution of a method with arguments at a chosen time, rather than 
    immediately. 
    
    The methods to implement are specified in the SimEventInterface.
    
    Attributes
    ----------
    _absolute_time : float or int
        the absolute execution time of the SimEvent
    _priority : int
        the priority of the event when two events are scheduled at the
        same time; higher numbers indicate higher priority; typically,
        priorities are numbered 1 through 10 with a default priority of 5
    _id : int
        unique number of the event to act as a tie breaker when both the
        absolute time and the priority of the event are the same
    _target : object
        the object on which the method has to be called
    _method : method
        the method to call, stored as the attr of the target
    _kwargs : dict
        a dict with arguments to use for the method
    """
    
    # Internal static event counter to allocate the unique id to a SimEvent
    __event_counter: int = 0
    
    # Increment and return the static event counter
    @classmethod
    def __new_event_counter(cls) -> int:
        cls.__event_counter += 1
        return cls.__event_counter
    
    def __init__(self, time: Union[int, float], target, method: str,
                 priority: int=SimEventInterface.NORMAL_PRIORITY, **kwargs):
        """
        Parameters
        ----------
        time : float or int
            the absolute execution time of the SimEvent
        target : object
            the object instance on which the method has to be called
        method : str
            the name of the method to call, as a string
        priority : int (optional)
            the priority of the event when two events are scheduled at the
            same time. Higher numbers indicate higher priority. Typically,
            priorities are numbered 1 through 10 with a default priority of 5.
            When not provided, the default priority of 5 will be used.
        **kwargs: dict (optional)
            the arguments of the method call provided as comma-separated
            arg=value pairs
            
        Raises
        ------
        DSOLError: when one of the arguments is not of the correct type, when 
            the method does not exist for the target, or when the method is 
            not callable on the target.
        """
        self._absolute_time: Union[int, float] = time
        self._priority: int = priority
        self._id: int = SimEvent.__new_event_counter()
        self._target = target
        self._kwargs = kwargs
        
        if not isinstance(method, str):
            raise DSOLError("method should be a string")
        if getattr(target, method, None) is not None:
            self._method = getattr(target, method)
        else:
            raise DSOLError(\
                f"target does not have executable method {method}")

        if not isfunction(self._method) and not ismethod(self._method):
            raise DSOLError("method should be a valid method name")
        if not isinstance(time, float) and not isinstance(time, int):
            raise DSOLError("time should be float or int")
        if not isinstance(priority, int):
            raise DSOLError("priority should be int")
    
    def execute(self):
        """
        Execute the stored method on the target object with the provided
        arguments for the method.
        
        Returns
        -------
        None
            This is quite important. Since the method will be called 
            asynchronously, no object can do anything with a return value.
        
        Raises
        ------
        DSOLError: when the method call fails or returns an exception
        """
        try:
            self._method(**self._kwargs)
        except:
            raise(DSOLError(f"method {self._method}(..) is not callable " \
                +f"on {self._target} with arguments {self._kwargs}"))

    def __cmp__(self, other: SimEventInterface) -> int:
        """
        Comparison is done on absolute execution time. When there is a tie,
        the priority is used as a tie breaker. When there is still a tie,
        the unique id of the event is used as a final tie breaker.
        """
        if (self._absolute_time < other._absolute_time):
            return -1
        if (self._absolute_time > other._absolute_time):
            return 1
        # lower priority means LATER event
        if (self._priority < other._priority):
            return 1
        # higher priority means EARIER event
        if (self._priority > other._priority):
            return -1
        if (self._id < other._id):
            return -1
        if (self._id > other._id):
            return 1
        return 0
    
    def __eq__(self, other: SimEventInterface) -> bool:
        return self.__cmp__(other) == 0
        
    def __ne__(self, other: SimEventInterface) -> bool:
        return self.__cmp__(other) != 0
        
    def __lt__(self, other: SimEventInterface) -> bool:
        return self.__cmp__(other) < 0
        
    def __le__(self, other: SimEventInterface) -> bool:
        return self.__cmp__(other) <= 0

    def __gt__(self, other: SimEventInterface) -> bool:
        return self.__cmp__(other) > 0
        
    def __ge__(self, other: SimEventInterface) -> bool:
        return self.__cmp__(other) >= 0
    
    def __str__(self):
        return "[time=" + str(self._absolute_time) \
            +", prio=" + str(self._priority) \
            +", uniq=" + str(self._id) \
            +", target=" + type(self._target).__name__ \
            +", method=" + self._method.__name__ + "]"
    
    def __repr__(self):
        return "[t=" + str(self._absolute_time) \
            +", p=" + str(self._priority) \
            +", n=" + str(self._id) \
            +", ta=" + type(self._target).__name__ \
            +" - m=" + self._method.__name__ \
            +", args=" + str(self._kwargs) + "]"
    
    @property 
    def time(self) -> Union[float, int]: 
        """Return the absolute execution time, float or int."""
        return self._absolute_time
    
    @property 
    def priority(self) -> int: 
        """Return the priority; higher value is higher priority."""
        return self._priority
    
    @property 
    def id(self) -> int: 
        """Return the unique id of of the SimEvent."""
        return self._id
    
    @property
    def target(self) -> object:
        """Return the target object instance to execute the method call on.""" 
        return self._target
    
    @property
    def method(self) -> str: 
        """Return the name of the method to be called on the target."""
        return self._method.__name__
    
    @property
    def kwargs(self) -> dict: 
        """Return the dict of arguments to be passed to the method."""
        return self._kwargs
    
