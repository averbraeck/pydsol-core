"""
The eventlist module contains a reference implementation of an event list that
can store SimEvents ordered by simulation time. Typically, event lists become
inefficient after a while, because events are only taken away from the "front"
whereas new events are added in the entire event list. When trees are used 
as an event list, frequent rebalancing is necessary. In the reference
implementation in this module, a heap queue (priority queue) is used. This
data structure handles removal of first iems very well, and is faster than
red-black tree implementations in Python.

The EventListInterface in this module allows other implementations of the 
event list, which will be recognized by the simulators and other classes.
"""

from abc import ABC, abstractmethod
import heapq

from pydsol.core.simevent import SimEventInterface
from pydsol.core.utils import get_module_logger


__all__ = [
    "EventListInterface",
    "EventListHeap",
    ]

logger = get_module_logger('eventlist')


class EventListInterface(ABC):
    """
    EventListInterface defines the properties that all implementations of an 
    EveltList class need to have. The most important property of an EventList 
    is that you can add an event, and that you can both peek and remove the 
    first event from the list. For the implementation it is important to
    realize that elements (events) disappear only disappear from the "left"
    of the event list in simulation, so tree implementations become
    unbalanced quite quickly. Typical implementations use red-black trees 
    or heap queue (priority queue) data structures.
    
    Events in an event list are sorted on absolute execution time, with
    priority as a tie breaker, and an unique id for an event as the second
    tie breaker.
    """
    
    @abstractmethod
    def add(self, event: SimEventInterface):
        """add an event to the event list"""
        pass

    @abstractmethod
    def peek_first(self) -> SimEventInterface:
        """return the first event from the list without removing it"""
        pass

    @abstractmethod
    def pop_first(self) -> SimEventInterface:
        """remove and return the first event from the event list"""
        pass

    @abstractmethod
    def size(self) -> int:
        """return the number of events on the event list"""
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        """return whether the event list is empty"""
        pass

    @abstractmethod
    def contains(self, event: SimEventInterface) -> bool:
        """return whether the event is stored in the event list"""
        pass

    @abstractmethod
    def remove(self, event: SimEventInterface) -> bool:
        """remove the provided event from the event list, and return 
        whether the event was present in the list"""
        pass

    @abstractmethod
    def clear(self):
        """remove all events from the event list"""
        pass


class EventListHeap(EventListInterface):
    """
    EventListHeap provides a basic implementation of an event list for 
    simulation, using an internal heap queue structure for the events. 
    The most important property of the EventList is to add events, and 
    peek and remove the first event from the list. 

    The internal Python heapq structure deals very well with the fact that
    elements (events) disappear only from the "left" of the event list in 
    simulation.
    
    Events in an event list are sorted on absolute execution time, with
    priority as a tie breaker, and an unique id for an event as the second
    tie breaker. The key for the events is a a tuple (time, priority, id)
    that is always unique, because every simulation event has a unique id.
    
    Attributes
    ----------
    _event_list
        the internal heapq structure to store the events
    _number_events
        an internal counter for the number of events
        
    Methods
    -------
    add(event: SimEventInterface)
        store an event on the event list
    peek_first(): SimEventInterface
        return the first event from the event list without removing it
    pop_first(): SimEventInterface
        remove and return the first event from the event list
    size(): int
        return the number of events on the event list
    is_empty(): bool
        return whether the evenr list is empty or not
    contains(event: SimEventInterface) : bool
        return whether the event is stored in the event list
    remove(event: SimEventInterface): bool
        remove the event from the event list; return whether it was present
    clear()
        remove all events from the event list
    """

    def __init__(self):
        """Create a new, empty event list"""
        self._event_list: list[SimEventInterface] = []
        heapq.heapify(self._event_list)
        self._number_events: int = 0
    
    def add(self, event: SimEventInterface):
        """
        Store an event on the event list.
        
        Parameters
        ----------
        event : SimEventInterface
            the event to store on the event list
        """
        heapq.heappush(self._event_list, (event.time, event.priority,
                                          event._id, event))
        self._number_events += 1
    
    def peek_first(self) -> SimEventInterface:
        """
        Return the first event from the event list without removing it.
        
        Returns
        -------
        The first event with the lowest time (and in case of a tie, lowest 
        priority and lowest id in case priorities also tie) from the event 
        list. In case the event list is empty, None is returned.
        """
        if self.is_empty():
            return None
        return self._event_list[0][3]

    def pop_first(self) -> SimEventInterface:
        """
        Remove and return the first event from the event list.
        
        Returns
        -------
        The first event with the lowest time (and in case of a tie, lowest 
        priority and lowest id in case priorities also tie) from the event 
        list. In case the event list is empty, None is returned.
        """
        if self.is_empty():
            return None
        self._number_events -= 1
        return heapq.heappop(self._event_list)[3]

    def size(self) -> int:
        """
        Return the number of events on the event list.
        
        Returns
        -------
        The number of events on the event list as an int.
        """
        return self._number_events

    def contains(self, event: SimEventInterface) -> bool:
        """
        Return whether the event list contains the event.
        
        Parameters
        ----------
        event : SimEventInterface
            the event to look up in the event list
            
        Returns
        -------
        True or False, depending on whether the event is in the event list.
        """
        if self.is_empty():
            return False
        return self._event_list.count((event.time, event.priority,
                                       event._id, event)) > 0
        
    def remove(self, event: SimEventInterface) -> bool:
        """
        Remove the event from the event list and return success.
        
        Parameters
        ----------
        event : SimEventInterface
            the event to remove from the event list
            
        Returns
        -------
        True or False, depending on whether the event was present in 
        the event list.
        """
        if (self.contains(event)):
            self._event_list.remove((event.time, event.priority,
                                     event._id, event))
            self._number_events -= 1
            return True
        return False

    def is_empty(self) -> bool:
        """
        Return whether the event list is empty
            
        Returns
        -------
        True or False, depending on whether the event list is empty.
        """
        return self.size() == 0

    def clear(self):
        """Remove all events from the event list."""
        self._event_list.clear()
        self._number_events: int = 0
        
    def __str__(self) -> str:
        s = "["
        for e in self._event_list:
            s += "(" + str(e[0]) + ", " + str(e[1]) + ") "
        s += "]"
        return s
    
    def __repr__(self) -> str:
        return str(self)
