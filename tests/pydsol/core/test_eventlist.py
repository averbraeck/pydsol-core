"""
Test the classes that implement the event list for discrete-event simulation 
""" 

import pytest

from pydsol.core.eventlist import EventListHeap, EventListInterface
from pydsol.core.simevent import SimEvent


class Target:

    def __init__(self):
        pass
    
    def empty(self):
        pass
        

def test_eventlist():
    elist = EventListHeap()
    assert elist.size() == 0
    
    t1 = Target()
    e0 = SimEvent(9.0, t1, "empty")
    elist.add(e0)
    assert elist.size() == 1
    e1 = SimEvent(2.0, t1, "empty")
    elist.add(e1)
    assert elist.size() == 2
    
    e2 = SimEvent(3.0, t1, "empty")
    elist.add(e2)
    assert elist.size() == 3
    elist.remove(e2)
    assert elist.size() == 2
    elist.add(e2)
    assert elist.size() == 3
    assert elist.peek_first() == e1
    
    elist.add(SimEvent(3.0, t1, "empty", 2))
    elist.add(SimEvent(3.0, t1, "empty", 4))
    elist.add(SimEvent(3.0, t1, "empty", 4))
    elist.add(SimEvent(3.0, t1, "empty", 8))
    elist.add(SimEvent(3.0, t1, "empty", 1))
    elist.add(SimEvent(0.5, t1, "empty"))
    elist.add(SimEvent(8.0, t1, "empty"))
    
    last_time = -1.0
    last_priority = 5
    last_id = -1
    while not elist.is_empty():
        e = elist.pop_first()
        if e.time == last_time:
            if e.priority == last_priority:
                assert e.id > last_id
            else:
                # note that a high priority is an earlier event
                assert e.priority < last_priority
        else:
            assert e.time >= last_time
        last_time = e.time
        last_priority = e.priority
        last_id = e.id

    assert elist.is_empty()
    assert elist.size() == 0
    assert elist.peek_first() == None
    assert elist.pop_first() == None
    assert not elist.contains(e2)
    assert not elist.remove(e2)
    
    elist.add(e1)
    assert elist.size() == 1
    assert len(str(elist)) > 0
    assert len(repr(elist)) > 0
    assert str(elist).count("(") == 1
    elist.add(e2)
    assert str(elist).count("(") == 2
    elist.clear()
    assert elist.size() == 0
    assert str(elist) == "[]"
    assert repr(elist) == "[]"


def test_interface():
    """Check that the needed methods exist"""
    EventListInterface.add(None, None)
    EventListInterface.clear(None)
    EventListInterface.contains(None, None)
    EventListInterface.remove(None, None)
    EventListInterface.is_empty(None)
    EventListInterface.peek_first(None)
    EventListInterface.pop_first(None)
    EventListInterface.size(None)


if __name__ == '__main__':
    pytest.main()
