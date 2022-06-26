"""
Test the classes that define simulation events
""" 

from pydsol.core.utils import DSOLError
from pydsol.core.simevent import SimEvent, SimEventInterface
import pytest


class Target:

    def __init__(self):
        self.val = 0
    
    def empty(self):
        self.val = None
        
    def m_arg1(self, arg1):
        self.val = arg1
        
    def m_arg10(self, arg1="null"):
        self.val = arg1
    
    # class (static) variable
    sv = 10
    
    @staticmethod
    def m_static():
        Target.sv += 1
        
    @classmethod
    def m_class(cls):
        cls.sv = 0


def test_create_event():
    test = Target()
    
    # test base properties of SimEvent
    e1 = SimEvent(2.0, test, "empty")
    assert e1.time == 2.0
    assert e1.target == test
    assert e1.method == "empty"
    assert e1.priority == SimEventInterface.NORMAL_PRIORITY
    assert e1.id >= 0
    assert e1.kwargs == {}
    
    # float time, kwargs, look at increment if id
    e2 = SimEvent(3.0, test, "m_arg1", 1, arg1="abc")
    assert e2.method == "m_arg1"
    assert e2.id > e1.id
    assert e2.priority == 1
    assert e2.kwargs == {"arg1": "abc"}
    
    # int time
    e3 = SimEvent(1, test, "empty")
    assert e3.time == 1
    

def test_create_event_errors():
    test = Target()
    with pytest.raises(DSOLError):
        SimEvent("x", test, "empty")
    with pytest.raises(DSOLError):
        SimEvent(2.0, test, "empty", "x")
    with pytest.raises(DSOLError):
        SimEvent(2.0, None, "empty")
    with pytest.raises(DSOLError):
        SimEvent(2.0, test, 1)
    with pytest.raises(DSOLError):
        SimEvent(2.0, test, "xyz")
    # this is an attr, but not a method
    with pytest.raises(DSOLError):
        SimEvent(7.0, test, "sv") 

        
def test_compare():
    test = Target()
    e15a = SimEvent(1, test, "empty")
    e15b = SimEvent(1, test, "m_arg10")
    e25 = SimEvent(2, test, "empty")
    e26 = SimEvent(2, test, "empty", 6)
    e24 = SimEvent(2, test, "empty", 4)
    assert e15a == e15a
    assert e15a != e15b
    assert e15b > e15a
    assert e15a < e15b
    assert e15a >= e15a        
    assert e15a <= e15a
    assert e25 > e15a
    assert e15a < e25
    assert e24 < e25
    assert e26 > e25
    assert e26 == e26

    
def test_str():
    test = Target()
    e1 = SimEvent(2.5, test, "m_arg10", arg1=12345)
    s = str(e1)
    assert s.count("time=2.5") > 0
    assert s.count("target=Target") > 0
    assert s.count("method=m_arg10") > 0
    assert s.count("prio=5") > 0
    s = repr(e1)
    assert s.count("t=2.5") > 0
    assert s.count("ta=Target") > 0
    assert s.count("m=m_arg10") > 0
    assert s.count("p=5") > 0
    assert s.count("args={'arg1': 12345}") > 0

    
def test_execute_event():
    t1 = Target()
    
    # non-existing method of t
    with pytest.raises(DSOLError):
        e0 = SimEvent(2.0, t1, "doesnotexist")
        e0.execute()
    
    # method without arguments
    t1.val = 0
    e1 = SimEvent(2.0, t1, "empty")
    e1.execute()
    assert t1.val == None
    
    # extra argument
    with pytest.raises(DSOLError):
        e11 = SimEvent(2.0, t1, "empty", k1=1)
        e11.execute()
    
    # method with an argument
    e2 = SimEvent(3.0, t1, "m_arg1", arg1="abc")
    e2.execute()
    assert t1.val == "abc"
    
    # method with missing argument
    with pytest.raises(DSOLError):
        e21 = SimEvent(2.0, t1, "m_arg1")
        e21.execute()
    
    # method expecting an argument -- but wrong one
    with pytest.raises(DSOLError):
        e22 = SimEvent(2.0, t1, "m_arg1", k1=1)
        e22.execute()
    
    # method expecting an argument -- but extra one
    with pytest.raises(DSOLError):
        e23 = SimEvent(2.0, t1, "m_arg1", arg1=21, k1=1)
        e23.execute()
    
    # method with optional argument, provided
    e3 = SimEvent(4.0, t1, "m_arg10", arg1=10.0)
    e3.execute()
    assert t1.val == 10.0

    # method with optional argument, not provided
    e4 = SimEvent(4.0, t1, "m_arg10")
    e4.execute()
    assert t1.val == "null"
    
    
def test_event_special():
    t1 = Target()
    assert Target.sv == 10
    
    # call static method on the instance
    es1 = SimEvent(5.0, t1, "m_static")
    es1.execute()
    assert Target.sv == 11
    
    # call static method on the class
    es2 = SimEvent(5.0, Target, "m_static")
    es2.execute()
    assert Target.sv == 12
    
    # call class method on the instance
    ec1 = SimEvent(5.0, t1, "m_class")
    ec1.execute()
    assert Target.sv == 0
    Target.sv = 20

    # call class method on the class
    ec2 = SimEvent(5.0, Target, "m_class")
    ec2.execute()
    assert Target.sv == 0


def test_interface():
    """Check that the needed methods exist"""
    SimEventInterface.time
    SimEventInterface.priority
    SimEventInterface.id
    SimEventInterface.execute(None)
    

if __name__ == '__main__':
    pytest.main()
