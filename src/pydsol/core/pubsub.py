"""
the pubsub module contains a number of base classes for the publish/subscribe 
pattern as used in pydsol. The package is based on the Java 
implementation of DSOL (Distributed Simulation Object Library), 
first documented in 2002. Information about the Java and Python DSOL 
libraries can be found at https://simulation.tudelft.nl. Specific 
information about the publish/subscribe implementation in Java can be 
found in the djutils project (Delft Java Utilities) at https://djutils.org

Typically, implemented listener classes inherit from the abstract base class
EventListener (possibly through mixin), and classes that produce events 
inherit from the abstract base class EventProducer (possibly using multiple 
inheritance). 

The whole idea of publish/subscribe is that you decouple the producer of
information and the possible receiver(s), which otherwise has to be
hardcoded, making information exchange between objects very inflexible. 
With pub/sub, the producer will notify only subscribed objects of the 
content in the event. The receivers can change dynamically over time, by 
subscribing or unsubscribing for the receipt of certain EventTypes. We call 
the process of producing an event by the publisher "firing" of an event 
with the fire() method; receipt by the receiver is done in the notify() 
method. 

Note that Events are completely different from SimEvents. Events are used
in publish/subscribe; SimEvents contain information about code to be 
executed at a later point in time.
"""

from abc import ABC, abstractmethod
import inspect
from typing import Type, Optional, Any, Union
from pydsol.core.utils import get_module_logger

__all__ = [
    "EventError",
    "EventType",
    "Event",
    "TimedEvent",
    "EventListener",
    "EventProducer",
    ]

logger = get_module_logger('pubsub')


class EventError(Exception):
    """General Exception for working with Events and publish/subscribe"""
    pass


class EventType:
    """
    EventType is a strongly typed identifier for an event, which can contain
    additional information about the event itself such as metadata. The
    EventType is typically instantiated as a static variable in a class.
    
    The implementation of the `EventType` takes care that there will not be
    a problem with duplicate names for EventTypes. As part of the `EventType`,
    the defining class is coded as well to make the `EventType` unique. So,
    in the above example, the name "Producer.PRODUCTION" is stored internally
    as the unique name for the `EventType`.
    
    Example
    -------
        .. code-block:: python
        
           class Producer
               PRODUCTION_EVENT = EventType("PRODUCTION")
        
        The event type can then be used anywhere in the code as 
        `Producer.PRODUCTION_EVENT`. Note that an `Event` and a `SimEvent` 
        are two completely different concepts: Events are for the 
        publish/subscribe pattern, SimEvents are to store deferred method 
        information.
    """
    
    # set of the defined types to check for name clashes
    # each item in the set has the form class_name.event_type_name
    __defined_types: set[str] = set()
    
    def __init__(self, name: str, metadata: dict[str, Type]=None):
        """
        Instantiate a new EventType, usually in a static manner. 
        
        Example
        -------
            .. code-block:: python
        
               class Producer
                   PRODUCTION_EVENT = EventType("PRODUCTION")
            
            The event type can then be used anywhere in the code as 
            `Producer.PRODUCTION_EVENT`. 
        
        Parameters
        ----------
        name : str
            the human readable name of the event
        metadata : dict[str, Type], optional
            a dict with the metadata, defining the structure of the payload 
            in the event, as pairs of the name to be used in the dict and
            the expected type of the data field. When metadata is None
            or undefined, the payload of the event can be anything. When
            metadata IS defined, the payload has to be a dict.
            
        Raises
        ------
        EventError
            when name is not a str, or defining_class is not a type
        EventError
            when there was already an event defined with this name 
            in the defining_class
        EventError
            when the metadata does not consist of [str, Type] pairs
            
        """
        if not isinstance(name, str):
            raise EventError("name {name} is not a str")
        self._defining_class: str = inspect.stack()[1][0].f_code.co_name
        self._name = name
        key = self._defining_class + "." + self._name;
        if key in EventType.__defined_types:
            raise EventError(f"EventType {name} already defined")
        EventType.__defined_types.add(key)
        if metadata is not None:
            for key in metadata.keys():
                if not isinstance(key, str):
                    raise EventError("metadata {metadata} key not a str")
                if not isinstance(metadata[key], type):
                    raise EventError("metadata {metadata} value not a type")
        self._metadata = metadata
    
    @property
    def name(self):
        """Return the human readable name of the event type."""
        return self._name
    
    @property
    def defining_class(self):
        """Return the name of the defining class.
        
        The defining class is the class in which the event type has been 
        defined"""
        return self._defining_class
    
    @property
    def metadata(self) -> Optional[dict[str, Type]]:
        """Return the metadata dict or None.
        
        The metadata dict contains the expected structure of the payload 
        dict of the event in case it is defined. metadata can be None, 
        in which case the payload does not have to be a dict, and can have 
        any structure."""
        return self._metadata
    
    def __str__(self):
        return f"EventType[{self._defining_class}.{self._name}]"
    
    def __repr__(self):
        return f"EventType[{self._defining_class}.{self._name} " \
            +"metadata={self._metadata}]"
    

class Event:
    """
    An event is an object with a payload that is to be sent between 
    a producer and zero or more listeners. In a sense, the Event is the
    "envelope" of the content. 
    """

    def __init__(self, event_type: EventType, content, check:bool=True):
        """
        Instantiate an event with content. Events are strongly typed
        using a (usually static) instance of the EventType class, to
        distinguish different types of events from each other.
        
        Parameters
        ----------
        event_type : EventType
            a reference to a (usually static) event type for identification
        content
            the payload of the event, which can be of any type; common types
            are list, dict, or simple types
        check : bool, optional
            whether to check the fields in the content in case the 
            event_type has metadata; the check whether the content is a
            dict is always checked when there is metadata 
            
        Raises
        ------
        EventError
            if event_type is not an EventType
        EventError
            if the specified metadata and the content is not a dict
        EventError
            if the dict content is not consistent with the EventType metadata
        """
        if not isinstance(event_type, EventType):
            raise EventError("event_type is not an instance of EventType")
        self._event_type = event_type
        self._content = content
        if event_type.metadata is not None:
            if not isinstance(content, dict):
                raise EventError("event_type defined metadata but content "
                    +"is not specified as a dict")
            if check:
                if len(event_type.metadata) != len(content):
                    raise EventError("metadata length but consistent with "
                        +"content length")
                for key in event_type.metadata.keys():
                    if dict(content).get(key, None) == None:
                        raise EventError("metadata requited key '{key}' not "
                        +"found in content dict")
                    if not isinstance(dict(content).get(key),
                                      event_type.metadata.get(key)):
                        raise EventError("metadata requited key '{key}' to "
                        +"be of type {event_type.metadata.get(key).__name__}" 
                        +"but instead got {dict(content).get(key)}")
    
    @property
    def event_type(self) -> EventType:
        """Returns the (usually static) event type for identificatio.n"""
        return self._event_type
        
    @property
    def content(self) -> Any:
        """Returns the payload of the event; can be of any type."""
        return self._content
    
    def __str__(self):
        c = ""
        try:
            c = str(self._content)
        except:
            c = f"[cannot print {type(self._content).__name__}"
        return f"Event[{self._event_type.name}: {c}]"
    
    def __repr__(self):
        c = ""
        try:
            c = str(self._content)
        except:
            c = f"[cannot print {type(self._content).__name__}"
        return f"Event[{self._event_type.name}: {c}]"


class TimedEvent(Event):
    """
    A TimedEvent is an event with a time identifier (int, float).
    
    The time identifier is not specified as an extra element in the payload,
    but rather as an extra attribute of the Event. The constructor explicitly 
    demands for the specification of a timestamp, typically the simulator time. 
    Like an event, it is an object with a payload that is to be sent between 
    a producer and zero or more listeners. In a sense, the TimedEvent is the
    timestamped "envelope" of the content. 
    """

    def __init__(self, timestamp: Union[float, int], event_type: EventType,
                 content, check:bool=True):
        """
        Instantiate a timed event with content. 
        
        TimedEvents are strongly typed using a (usually static) instance of 
        the EventType class, to distinguish different types of events from 
        each other. Furthermore, the timestamp indicates when the event was 
        fired. Typically the value of the timestamp is the simulator time.
        
        Parameters
        ----------
        timestamp : int or float
            the timestamp of the event, typically the simulator time
        event_type : EventType
            a reference to a (usually static) event type for identification
        content
            the payload of the event, which can be of any type; common types
            are list, dict, or simple types
        check : bool, optional
            whether to check the fields in the content in case the 
            event_type has metadata; the check whether the content is a
            dict is always checked when there is metadata 
            
        Raises
        ------
        EventError
            if timestamp is not of type int or float
        EventError
            if event_type is not an EventType
        EventError
            if the EventType specified metadata and the content is not a dict
        EventError
            if the dict content is not consistent with the EventType metadata
        """
        if not isinstance(timestamp, (int, float)):
            raise EventError("timestamp is not an int or a float")
        self._timestamp = timestamp
        super().__init__(event_type, content, check)
    
    @property
    def timestamp(self) -> Union[int, float]:
        """Returns the timestamp of the event; typically the simulator time."""
        return self._timestamp
    
    def __str__(self):
        c = ""
        try:
            c = str(self._content)
        except:
            c = f"[cannot print {type(self._content).__name__}"
        return f"TimedEvent[t={self.timestamp}, {self._event_type.name}: {c}]"
    
    def __repr__(self):
        c = ""
        try:
            c = str(self._content)
        except:
            c = f"[cannot print {type(self._content).__name__}"
        return f"TimedEvent[t={self.timestamp}, {self._event_type.name}: {c}]"


class EventListener(ABC):
    """
    The EventListener abstract class defines the behavior of an event subscriber.
    
    The EventListener is an interface for a class that needs to be able to
    receive events from one or more EventProducers. In order to receive
    events, a listener has to implement the notify() method. In the
    notify() method, events can be tested for their EventType with if-elif
    statements, and then the corresponding content can be acted upon.
    
    Its most important method is notify(event) that is called from the 
    EventProducer (using the fier(event) method) to handle the Event.
    """

    @abstractmethod
    def notify(self, event: Event):
        """Handle an event received from an EventProducer"""


class EventProducer:
    """
    EventProducer is an abstract class defining the producer behavior.
    
    The EventProducer class acts as a superclass for classes that need
    to fire events to an unknown and possibly varying number of subscribers
    (also called listeners). The main methods that can be called on the
    EventProducer are: add_listener and remove_listener. In addition, the
    logic of the class that extends the base EventProducer class calls the
    fire(event_type, content) method to notify the listener(s) (if any).
    
    The most important private attribute of the EventProducer is 
    ``_listeners: dict[EventType, list[EventListener]]``. This structure
    Maps the EventType to a list of listeners for that EventType.
    Note that this is a list to make behavior reproducible: we want
    events to subscribers to be fired in the same order when replicating
    the model run. The dictionary is ordered (unsorted) in Python 3.7+, 
    and the list is reproducible. A ``dict[EventType, set[EventListener]]`` 
    would not be reproducible, since the set is unordered.   
    """

    def __init__(self):
        """Instantiate the EventProducer, and initialize the empty 
        listener data structure"""
        self._listeners: dict[EventType, list[EventListener]] = dict()
        
    def add_listener(self, event_type: EventType, listener: EventListener):
        """
        Add an EventListener to this EventProducer for a given EventType.
        If the listener already is registered for this EventType, this will
        be ignored.
        
        Parameters
        ----------
        event_type : EventType
            the EventType for which this listener subscribes
        listener : EventListener
            the subscriber to register for the provided Eventtype
            
        Raises
        ------
        EventError
            if any of the arguments is of the wrong type
        """
        if not isinstance(event_type, EventType):
            raise EventError("event_type should be an EventType")
        if not isinstance(listener, EventListener):
            raise EventError("listener should be an EventListener")
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        if listener not in self._listeners[event_type]:
            self._listeners[event_type].append(listener)
    
    def remove_listener(self, event_type: EventType, listener: EventListener):
        """
        Remove an EventListener of this EventProducer for a given EventType.
        If the listener is not registered for this EventType, this will
        be ignored.
        
        Parameters
        ----------
        event_type : EventType
            the EventType for which this listener unsubscribes
        listener : EventListener
            the subscriber to remove for the provided Eventtype
            
        Raises
        ------
        EventError
            if any of the arguments is of the wrong type
        """
        if not isinstance(event_type, EventType):
            raise EventError("event_type should be an EventType")
        if not isinstance(listener, EventListener):
            raise EventError("listener should be an EventListener")
        if event_type in self._listeners:
            if listener in self._listeners[event_type]:
                self._listeners[event_type].remove(listener)
                if len(list(self._listeners[event_type])) == 0:
                    del self._listeners[event_type]
    
    def remove_all_listeners(self, event_type:EventType=None,
                        listener:EventListener=None):
        """
        Remove an EventListener (if given) for a provided EventType (if given)
        for this EventProducer. It is no problem if there are no matches. 
        There are four situations:
        
        event_type == None and listener == None
            all listeners for all event types are removed
        event_type == None and listener is specified
            the listener is removed for any event for which it was registered
        event_type is specified and listener == None
            all listeners are removed for the given event_type
        event_type and listener are both specified
            the listener for the given event type is removed, if it was
            registered; in essence this is the same as remove_listener 
        
        Parameters
        ----------
        event_type : EventType, optional
            the EventType for which this listener unsubscribes
        listener : EventListener, optional
            the subscriber to remove for the provided EventType
        
        Raises
        ------
        EventError
            if any of the arguments is of the wrong type
        """
        if not (event_type == None or isinstance(event_type, EventType)):
            raise EventError("event_type should be an EventType or None")
        if not (listener == None or isinstance(listener, EventListener)):
            raise EventError("listener should be an EventListener or None")
        if event_type == None:
            if listener == None:
                self._listeners.clear()
            else:
                # a list() is used to avoid concurrent modification error
                for et in list(self._listeners.keys()):
                    self.remove_listener(et, listener)
        else:
            if listener == None:
                if event_type in self._listeners:
                    del self._listeners[event_type]
            else:
                self.remove_listener(event_type, listener)
    
    def has_listeners(self) -> bool:
        """indicate whether this producer has any listeners or not"""
        return len(self._listeners) > 0
    
    def fire_event(self, event: Event):
        """
        fire this event to the subscribed listeners for the EventType of
        the event.
        
        Parameters
        ----------
        event : Event
            the event to fire to the subscribed listeners
        
        Raises
        ------
        EventError
            if the event is not of the right type
        """
        if not isinstance(event, Event):
            raise EventError("event {event} not of type Event")
        logger.debug("fire %s to %s", event,
                     self._listeners.get(event.event_type))
        if event.event_type not in self._listeners:
            return
        # a copy() is used to avoid concurrent modification error in case 
        # the notification would unsubscribe a listener to this event (!)
        for listener in self._listeners.get(event.event_type).copy():
            listener.notify(event)
 
    def fire(self, event_type: EventType, content, check: bool=True):
        """
        construct an event based on the arguments and fire this event 
        to the subscribed listeners for the event_type
        
        Parameters
        ----------
        event_type : EventType
            a reference to a (usually static) event type for identification
        content
            the payload of the event, which can be of any type; common types
            are list, dict, or simple types
        check : bool, optional
            whether to check the fields in the content in case the 
            event_type has metadata; the check whether the content is a
            dict is always checked when there is metadata 
            
        Raises
        ------
        EventError
            if event_type is not an EventType
        EventError
            if the EventType specified metadata and the content is not a dict
        EventError
            if the dict content is not consistent with the EventType metadata
        """
        event = Event(event_type, content, check)
        self.fire_event(event)
    
    def fire_timed_event(self, timed_event: TimedEvent):
        """
        fire this timed_event to the subscribed listeners for the EventType 
        of the event.
        
        Parameters
        ----------
        event : TimedEvent
            the timed_event to fire to the subscribed listeners
        
        Raises
        ------
        EventError
            if the timed_event is not of the right type
        """
        if not isinstance(timed_event, TimedEvent):
            raise EventError("event {event} not of type TimedEvent")
        logger.debug("fire %s to %s", timed_event,
                     self._listeners.get(timed_event.event_type))
        if timed_event.event_type not in self._listeners:
            return
        # a copy() is used to avoid concurrent modification error in case 
        # the notification would unsubscribe a listener to this event (!)
        for listener in self._listeners.get(timed_event.event_type).copy():
            listener.notify(timed_event)

    def fire_timed(self, time: Union[int, float], event_type: EventType,
                   content, check: bool=True):
        """
        construct a timed event based on the arguments and fire this event 
        to the subscribed listeners for the event_type
        
        Parameters
        ----------
        timestamp : int or float
            the timestamp of the event, typically the simulator time
        event_type : EventType
            a reference to a (usually static) event type for identification
        content
            the payload of the event, which can be of any type; common types
            are list, dict, or simple types
        check : bool, optional
            whether to check the fields in the content in case the 
            event_type has metadata; the check whether the content is a
            dict is always checked when there is metadata 
            
        Raises
        ------
        EventError
            if timestamp is not of type int or float
        EventError
            if event_type is not an EventType
        EventError
            if the EventType specified metadata and the content is not a dict
        EventError
            if the dict content is not consistent with the EventType metadata
        """
        timed_event = TimedEvent(time, event_type, content, check)
        self.fire_timed_event(timed_event)
