import pytest

from pydsol.core.exceptions import EventError
from pydsol.core.pubsub import EventType, Event, TimedEvent, EventProducer, \
    EventListener


class Defs:
    EVENT: EventType = EventType("EVENT")
    EVENTDICT: EventType = EventType("EVENT2", {"i": int, "s": str})
    EVENTNONE: EventType = EventType("EVENT3", {})


def test_eventtype():
    # normal eventtype
    assert Defs.EVENT.name == "EVENT"
    assert Defs.EVENT.defining_class == "Defs"
    assert Defs.EVENT.metadata == None
    assert str(Defs.EVENT).find("Defs.EVENT") != -1
    assert repr(Defs.EVENT).find("Defs.EVENT") != -1

    # test if EVENT in other class does not lead to name clash
    class OtherWithEvent:
        EVENT: EventType = EventType("EVENT")

    # duplicate error and name error
    with pytest.raises(EventError):
        Defs.EVENTX = EventType("EVENT")
        Defs.EVENTY = EventType("EVENT")
    with pytest.raises(EventError):

        class Wrong:
            EVENT1: EventType = EventType("EVENTW")
            EVENT2: EventType = EventType("EVENTW")

    with pytest.raises(EventError):
        EventType(3.0) 
        
    # eventtype with dict
    assert Defs.EVENTDICT.name == "EVENT2"
    assert Defs.EVENTDICT.defining_class == "Defs"
    assert type(Defs.EVENTDICT.metadata) == dict
    assert Defs.EVENTDICT.metadata == {"i": int, "s": str}
    assert Defs.EVENTNONE.metadata == {}
    
    # eventtypes with dict errors
    with pytest.raises(EventError):
        EventType("EVENT4", {4.0: int, "s": str})
    with pytest.raises(EventError):
        EventType("EVENT5", {"xuz": int, "s": "t"})


def test_event():
    # unchecked event
    e: Event = Event(Defs.EVENT, None)
    assert e.event_type == Defs.EVENT
    assert e.content == None
    e = Event(Defs.EVENT, "abc")
    assert e.content == "abc"
    e = Event(Defs.EVENT, ['a', 'b'])
    assert e.content == ['a', 'b']
    
    # event with error
    with pytest.raises(EventError):
        e = Event('a', 'b')
    
    # event with dict    
    e2: Event = Event(Defs.EVENTDICT, {"i": 3, "s": "abc"})
    assert e2.event_type == Defs.EVENTDICT
    assert e2.content == {"i": 3, "s": "abc"}
    
    # event with dict and error
    with pytest.raises(EventError):
        Event(Defs.EVENTDICT, "abc")
    with pytest.raises(EventError):
        Event(Defs.EVENTDICT, {"i:3"})
    with pytest.raises(EventError):
        Event(Defs.EVENTDICT, {"i":3, "j":5})
    with pytest.raises(EventError):
        Event(Defs.EVENTDICT, {"i": 3, "s": "abc", "j": 5})
    with pytest.raises(EventError):
        Event(Defs.EVENTDICT, {"i": "3", "s": "abc"})
    
    
def test_timed_event():
    # unckecked event
    e: TimedEvent = TimedEvent(1.0, Defs.EVENT, None)
    assert e.event_type == Defs.EVENT
    assert e.content == None
    assert e.timestamp == 1.0
    e = TimedEvent(5.0, Defs.EVENT, "abc")
    assert e.content == "abc"
    assert e.timestamp == 5.0
    e = TimedEvent(0, Defs.EVENT, ['a', 'b'])
    assert e.content == ['a', 'b']
    assert e.timestamp == 0

    # event with error
    with pytest.raises(EventError):
        e = TimedEvent(5.0, 'a', 'b')
    with pytest.raises(EventError):
        e = TimedEvent(None, 'a', 'b')
    
    # event with dict    
    e2: TimedEvent = TimedEvent(15.3, Defs.EVENTDICT, {"i": 3, "s": "abc"})
    assert e2.event_type == Defs.EVENTDICT
    assert e2.content == {"i": 3, "s": "abc"}
    assert e2.timestamp == 15.3
    
    # event with dict and error
    with pytest.raises(EventError):
        TimedEvent(1, Defs.EVENTDICT, "abc")
    with pytest.raises(EventError):
        TimedEvent(2, Defs.EVENTDICT, {"i:3"})
    with pytest.raises(EventError):
        TimedEvent(3, Defs.EVENTDICT, {"i":3, "j":5})
    with pytest.raises(EventError):
        TimedEvent(4, Defs.EVENTDICT, {"i": 3, "s": "abc", "j": 5})
    with pytest.raises(EventError):
        TimedEvent(5, Defs.EVENTDICT, {"i": "3", "s": "abc"})
    
    
def test_event_producer():

    # define producer and listeners
    class P(EventProducer):
        EVENT_PROD1 = EventType("EVENT_PROD1")
        EVENT_PROD2 = EventType("EVENT_PROD2")

    prod = P()

    class L1(EventListener): 

        def notify(self, event:Event):
            pass

    class L2(EventListener): 

        def notify(self, event:Event):
            pass

    listener1 = L1()
    listener2 = L2()

    # check empty situation
    assert len(prod._listeners) == 0
    assert not prod.has_listeners()
    prod.remove_listener(P.EVENT_PROD1, listener1)
    prod.remove_all_listeners()
    prod.remove_all_listeners(event_type=P.EVENT_PROD1)
    prod.remove_all_listeners(listener=listener1)
    prod.remove_all_listeners(event_type=P.EVENT_PROD1, listener=listener1)
    
    # check normal behavior
    prod.add_listener(P.EVENT_PROD1, listener1)
    assert len(prod._listeners) == 1
    assert prod._listeners[P.EVENT_PROD1] == [listener1]
    prod.add_listener(P.EVENT_PROD1, listener2)
    assert len(prod._listeners) == 1
    assert prod._listeners[P.EVENT_PROD1] == [listener1, listener2]
    prod.remove_listener(P.EVENT_PROD1, listener1)
    assert prod._listeners[P.EVENT_PROD1] == [listener2]
    prod.remove_listener(P.EVENT_PROD1, listener1)
    prod.remove_listener(P.EVENT_PROD1, listener2)
    assert not prod.has_listeners()
    
    # check remove_all behavior
    def add4():
        prod._listeners.clear()
        prod.add_listener(P.EVENT_PROD1, listener1)
        prod.add_listener(P.EVENT_PROD1, listener2)
        prod.add_listener(P.EVENT_PROD2, listener1)
        prod.add_listener(P.EVENT_PROD2, listener2)

    add4()
    assert prod._listeners[P.EVENT_PROD1] == [listener1, listener2]
    assert prod._listeners[P.EVENT_PROD2] == [listener1, listener2]
    prod.remove_all_listeners(event_type=P.EVENT_PROD1, listener=listener2)
    assert prod._listeners[P.EVENT_PROD1] == [listener1]
    assert prod._listeners[P.EVENT_PROD2] == [listener1, listener2]
    
    add4()
    assert prod._listeners[P.EVENT_PROD1] == [listener1, listener2]
    assert prod._listeners[P.EVENT_PROD2] == [listener1, listener2]
    prod.remove_all_listeners(event_type=P.EVENT_PROD1)
    assert not P.EVENT_PROD1 in prod._listeners
    assert prod._listeners[P.EVENT_PROD2] == [listener1, listener2]

    add4()
    assert prod._listeners[P.EVENT_PROD1] == [listener1, listener2]
    assert prod._listeners[P.EVENT_PROD2] == [listener1, listener2]
    prod.remove_all_listeners(listener=listener1)
    assert len(prod._listeners) == 2
    assert prod._listeners[P.EVENT_PROD1] == [listener2]
    assert prod._listeners[P.EVENT_PROD2] == [listener2]

    add4()
    print(prod._listeners)
    assert prod._listeners[P.EVENT_PROD1] == [listener1, listener2]
    assert prod._listeners[P.EVENT_PROD2] == [listener1, listener2]
    prod.remove_all_listeners()
    assert not prod.has_listeners()


def test_pub_sub_event():
    
    # define producer and listeners
    class R(EventProducer):
        EVENT_TYPE_INC: EventType = EventType("EVENT_INC")
        EVENT_TYPE_DEC: EventType = EventType("EVENT_DEC")
        EVENT_TYPE_NOT: EventType = EventType("EVENT_NOT")

        def inc(self):
            self.fire(R.EVENT_TYPE_INC, 3)

        def dec(self):
            self.fire(R.EVENT_TYPE_DEC, 2)

        def inc_event(self):
            self.fire_event(Event(R.EVENT_TYPE_INC, 1))

        def dec_event(self):
            self.fire_event(Event(R.EVENT_TYPE_DEC, 1))

    class L1(EventListener): 

        def __init__(self):
            self.value = 0
            
        def notify(self, event:Event):
            if event.event_type == R.EVENT_TYPE_INC:
                self.value += event.content
            elif event.event_type == R.EVENT_TYPE_DEC:
                self.value -= event.content

    producer = R()
    listener1 = L1()
    listener2 = L1()
    
    assert R.EVENT_TYPE_INC.defining_class == "R"
    assert R.EVENT_TYPE_INC.name == "EVENT_INC"
    assert listener1.value == 0
    assert listener2.value == 0
    
    # no listeners
    producer.inc()
    producer.inc_event()
    assert listener1.value == 0
    assert listener2.value == 0

    # two listeners for INC and one for DEC
    producer.add_listener(R.EVENT_TYPE_INC, listener1)
    producer.add_listener(R.EVENT_TYPE_INC, listener2)
    producer.add_listener(R.EVENT_TYPE_DEC, listener1)
    producer.inc()
    assert listener1.value == 3
    assert listener2.value == 3
    producer.dec()
    assert listener1.value == 1
    assert listener2.value == 3
    producer.inc_event()
    assert listener1.value == 2
    assert listener2.value == 4
    producer.dec_event()
    assert listener1.value == 1
    assert listener2.value == 4
    
    # unsubscribed event
    producer.fire(R.EVENT_TYPE_NOT, 7)
    assert listener1.value == 1
    assert listener2.value == 4
    producer.add_listener(R.EVENT_TYPE_NOT, listener2)
    producer.fire(R.EVENT_TYPE_NOT, 7)
    assert listener1.value == 1
    assert listener2.value == 4

def test_pub_sub_timed():
    
    # define producer and listeners
    class T(EventProducer):
        EVENT_TYPE_INC: EventType = EventType("EVENT_INC")
        EVENT_TYPE_DEC: EventType = EventType("EVENT_DEC")
        EVENT_TYPE_NOT: EventType = EventType("EVENT_NOT")

        def inc(self):
            self.fire_timed(5, T.EVENT_TYPE_INC, 3)

        def dec(self):
            self.fire_timed(6, T.EVENT_TYPE_DEC, 2)

        def inc_event(self):
            self.fire_timed_event(TimedEvent(5, T.EVENT_TYPE_INC, 1))

        def dec_event(self):
            self.fire_timed_event(TimedEvent(6, T.EVENT_TYPE_DEC, 1))

    class L1(EventListener): 

        def __init__(self):
            self.value = 0
            
        def notify(self, event:TimedEvent):
            if event.event_type == T.EVENT_TYPE_INC:
                self.value += event.content
                assert isinstance(event, TimedEvent)
                assert event.timestamp == 5
            elif event.event_type == T.EVENT_TYPE_DEC:
                self.value -= event.content
                assert isinstance(event, TimedEvent)
                assert event.timestamp == 6

    producer = T()
    listener1 = L1()
    listener2 = L1()
    
    assert T.EVENT_TYPE_INC.defining_class == "T"
    assert T.EVENT_TYPE_INC.name == "EVENT_INC"
    assert listener1.value == 0
    assert listener2.value == 0
    
    # no listeners
    producer.inc()
    producer.inc_event()
    assert listener1.value == 0
    assert listener2.value == 0

    # two listeners for INC and one for DEC
    producer.add_listener(T.EVENT_TYPE_INC, listener1)
    producer.add_listener(T.EVENT_TYPE_INC, listener2)
    producer.add_listener(T.EVENT_TYPE_DEC, listener1)
    producer.inc()
    assert listener1.value == 3
    assert listener2.value == 3
    producer.dec()
    assert listener1.value == 1
    assert listener2.value == 3
    producer.inc_event()
    assert listener1.value == 2
    assert listener2.value == 4
    producer.dec_event()
    assert listener1.value == 1
    assert listener2.value == 4
    
    # unsubscribed event
    producer.fire_timed(9, T.EVENT_TYPE_NOT, 7)
    assert listener1.value == 1
    assert listener2.value == 4
    producer.add_listener(T.EVENT_TYPE_NOT, listener2)
    producer.fire_timed(9, T.EVENT_TYPE_NOT, 7)
    assert listener1.value == 1
    assert listener2.value == 4


def test_producer_errors():

    class Q(EventProducer):
        EVENT_PROD1 = EventType("EVENT_PROD1")
        EVENT_PROD2 = EventType("EVENT_PROD2", {"i": int, "s": str})

    prod = Q()

    class L1(EventListener): 

        def notify(self, event:Event):
            pass

    listener1 = L1()
    with pytest.raises(EventError):
        prod.add_listener("x", listener1)
    with pytest.raises(EventError):
        prod.add_listener(Q.EVENT_PROD1, "xyz")
    with pytest.raises(EventError):
        prod.remove_listener("x", listener1)
    with pytest.raises(EventError):
        prod.remove_listener(Q.EVENT_PROD1, "xyz")
    with pytest.raises(EventError):
        prod.remove_all_listeners(event_type="x", listener=listener1)
    with pytest.raises(EventError):
        prod.remove_all_listeners(event_type=Q.EVENT_PROD1, listener="xyz")
    with pytest.raises(EventError):
        prod.fire_event("xyz")
    with pytest.raises(EventError):
        prod.fire_timed_event("xyz")

    with pytest.raises(EventError):
        prod.fire(Q.EVENT_PROD2, "abc")
    with pytest.raises(EventError):
        prod.fire(Q.EVENT_PROD2, {"i:3"})
    with pytest.raises(EventError):
        prod.fire(Q.EVENT_PROD2, {"i":3, "j":5})
    with pytest.raises(EventError):
        prod.fire(Q.EVENT_PROD2, {"i": 3, "s": "abc", "j": 5})
    with pytest.raises(EventError):
        prod.fire(Q.EVENT_PROD2, {"i": "3", "s": "abc"})
    
    with pytest.raises(EventError):
        prod.fire_timed(1, Q.EVENT_PROD2, "abc")
    with pytest.raises(EventError):
        prod.fire_timed(2, Q.EVENT_PROD2, {"i:3"})
    with pytest.raises(EventError):
        prod.fire_timed(3, Q.EVENT_PROD2, {"i":3, "j":5})
    with pytest.raises(EventError):
        prod.fire_timed(4, Q.EVENT_PROD2, {"i": 3, "s": "abc", "j": 5})
    with pytest.raises(EventError):
        prod.fire_timed(5, Q.EVENT_PROD2, {"i": "3", "s": "abc"})
    
        
if __name__ == '__main__':
    pytest.main()
    
