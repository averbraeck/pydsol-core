
"""
Test the input parameter classes
""" 

import math

import pytest

from pydsol.core.parameters import InputParameter, InputParameterMap, \
    InputParameterFloat, InputParameterInt, InputParameterStr, \
    InputParameterBool, InputParameterQuantity, InputParameterSelectionList, \
    InputParameterUnit
from pydsol.core.units import Length, Speed


def test_parameter():
    m: InputParameterMap = InputParameterMap("root", "root parameters", 1)
    assert m.key == "root"
    assert m.name == "root parameters"
    assert m.display_priority == 1
    assert m.value == {}
    assert m.extended_key() == "root"
    assert m.parent == None
    
    p: InputParameter = InputParameter("p-key", "p-name", 30.0, 2.0)
    assert p.key == "p-key"
    assert p.name == "p-name"
    assert p.default_value == 30.0
    assert p.display_priority == 2.0
    assert p.value == 30.0
    m.add(p)
    assert p.extended_key() == "root.p-key"
    assert m.get("p-key") == p
    assert p.parent == m
    assert p.description == "p-name"
    assert not p.read_only
    p.value = 20.0
    assert p.value == 20.0
    assert p.default_value == 30.0
    
    o: InputParameter = InputParameter("o-key", "o-name", 30.0, 1.0, parent=m)
    assert o.parent == m
    q: InputParameter = InputParameter("q-key", "q-name", 'xyz', 3.0,
                                       description="ddd", parent=m)
    assert q.description == "ddd"
    r: InputParameter = InputParameter("r-key", "r-name", 8.0, 6,
                                       read_only=True, parent=m)
    assert r.read_only
    with pytest.raises(ValueError):
        r.value = 9.0
        
    assert list(m.value.keys()) == ["o-key", "p-key", "q-key", "r-key"]

    with pytest.raises(TypeError):
        InputParameter(3, "n", 1, 1.0)
    with pytest.raises(TypeError):
        InputParameter("k", 3, 1, 1.0)
    with pytest.raises(ValueError):
        InputParameter("k.l", "n", 1, 1.0)
    with pytest.raises(ValueError):
        InputParameter("", "n", 1, 1.0)
    with pytest.raises(ValueError):
        InputParameter("k", "", 1, 1.0)
    with pytest.raises(TypeError):
        InputParameter("k", "n", 1, 'p')
    with pytest.raises(TypeError):
        InputParameter("k", "n", 1, 1.0, parent=p)
    with pytest.raises(TypeError):
        InputParameter("k", "n", 1, 1.0, read_only=3)
    with pytest.raises(NotImplementedError):
        m.value = {}
    with pytest.raises(TypeError):
        m.add('x')
    with pytest.raises(ValueError):
        m.add(InputParameter("p-key", "p-name", 10.0, 9.0))

    tria: InputParameterMap = InputParameterMap("tria", "tria", 7)
    m.add(tria)
    tria.add(InputParameterFloat("a", "a", 1.0, 1.0))
    tria.add(InputParameterFloat("b", "b", 2.0, 2.0))
    tria.add(InputParameterFloat("c", "c", 3.0, 3.0))
    assert tria.get("a").extended_key() == "root.tria.a"
    assert m.get("tria.a") == tria.get("a") 

    with pytest.raises(KeyError):
        m.get("x")
    with pytest.raises(KeyError):
        m.get("tria.d")
    with pytest.raises(KeyError):
        m.get("x.a")
        
    assert m.remove("r-key") == r
    m.add(r)
    m.remove("tria.a")
    assert len(tria.value) == 2
    with pytest.raises(KeyError):
        m.remove("x")
    with pytest.raises(KeyError):
        m.remove("tria.d")
    with pytest.raises(KeyError):
        m.remove("x.a")

    assert "c = 3.0" in m.print_values()
    assert "p-key" in m.print_values()
    assert "q-key" in str(m)
    assert "r-key" in str(r)
    assert "o-key" in repr(m)
    assert "tria" in repr(tria)
    
    assert p < q
    assert p <= q
    assert p == p
    assert r != p
    assert r >= p
    assert r > p
    assert not p == 'x'
    assert p != 'x'
    
    with pytest.raises(TypeError):
        assert p < 'x'
    with pytest.raises(TypeError):
        assert p <= 'x'
    with pytest.raises(TypeError):
        assert p > 'x'
    with pytest.raises(TypeError):
        assert p >= 'x'


def test_parameter_int():
    p = InputParameterInt("p", "pname", 4, 1)
    assert p.key == "p"
    assert p.name == "pname"
    assert p.default_value == 4
    assert p.value == 4
    assert p.display_priority == 1
    assert p.read_only == False
    p.value = 5
    assert p.value == 5
    assert p.min_value == -math.inf
    assert p.max_value == +math.inf
    assert p.format_str == "%d"
    
    q = InputParameterInt("q", "qname", 5, 2, min_value=0, max_value=100,
                          format_str="%3d")
    assert q.min_value == 0
    assert q.max_value == 100
    assert q.format_str == "%3d"
    
    r = InputParameterInt("r", "rname", 4, 1, read_only=True)
    assert r.read_only == True
    
    with pytest.raises(TypeError):
        InputParameterInt("p", "pname", 4.1, 1)
    with pytest.raises(ValueError):
        InputParameterInt("q", "qname", 5, 2, min_value=200, max_value=100,
                          format_str="%3d")
    with pytest.raises(TypeError):
        InputParameterInt("q", "qname", 5, 2, min_value='x', max_value=100,
                          format_str="%3d")
    with pytest.raises(TypeError):
        InputParameterInt("q", "qname", 5, 2, min_value=0, max_value='x',
                          format_str="%3d")
    with pytest.raises(TypeError):
        InputParameterInt("q", "qname", 5, 2, min_value=0, max_value=100,
                          format_str=8)
    with pytest.raises(ValueError):
        InputParameterInt("q", "qname", -1, 2, min_value=0, max_value=100)
    with pytest.raises(ValueError):
        r.value = 4  # read_only
    with pytest.raises(ValueError):
        q.value = 1000  # > max
    with pytest.raises(ValueError):
        p.value = 'x'  # > type


def test_parameter_float():
    p = InputParameterFloat("p", "pname", 4.0, 1)
    assert p.key == "p"
    assert p.name == "pname"
    assert p.default_value == 4
    assert p.value == 4.0
    assert p.display_priority == 1
    assert p.read_only == False
    p.value = 5.0
    assert p.value == 5.0
    assert p.min_value == -math.inf
    assert p.max_value == +math.inf
    assert p.format_str == "%.2f"
    
    q = InputParameterFloat("q", "qname", 5, 2, min_value=0.0, max_value=100.0,
                          format_str="%.3f")
    assert q.min_value == 0.0
    assert q.max_value == 100.0
    assert q.format_str == "%.3f"
    
    r = InputParameterFloat("r", "rname", 4, 1, read_only=True,
                            min_value=0, max_value=10)
    assert r.read_only == True
    
    with pytest.raises(TypeError):
        InputParameterFloat("p", "pname", 'x', 1)
    with pytest.raises(ValueError):
        InputParameterFloat("q", "qname", 5, 2, min_value=200, max_value=100,
                          format_str="%.3f")
    with pytest.raises(TypeError):
        InputParameterFloat("q", "qname", 5, 2, min_value='x', max_value=100,
                          format_str="%.3f")
    with pytest.raises(TypeError):
        InputParameterFloat("q", "qname", 5, 2, min_value=0, max_value='x',
                          format_str="%.3f")
    with pytest.raises(TypeError):
        InputParameterFloat("q", "qname", 5, 2, min_value=0, max_value=100,
                          format_str=8)
    with pytest.raises(ValueError):
        InputParameterFloat("q", "qname", -1, 2, min_value=0, max_value=100)
    with pytest.raises(ValueError):
        r.value = 4  # read_only
    with pytest.raises(ValueError):
        q.value = 1000  # > max
    with pytest.raises(ValueError):
        p.value = 'x'  # > type


def test_parameter_str():
    p = InputParameterStr("p", "pname", 'xyz', 1)
    assert p.key == "p"
    assert p.name == "pname"
    assert p.default_value == 'xyz'
    assert p.value == 'xyz'
    assert p.display_priority == 1
    assert p.read_only == False
    p.value = 'abc'
    assert p.value == 'abc'

    r = InputParameterStr("r", "rname", 'x', 1, read_only=True)
    assert r.read_only == True
    
    with pytest.raises(TypeError):
        InputParameterStr("p", "pname", 4, 1)
    with pytest.raises(ValueError):
        r.value = 4  # read_only
    with pytest.raises(ValueError):
        p.value = 10  # type


def test_parameter_bool():
    p = InputParameterBool("p", "pname", True, 1)
    assert p.key == "p"
    assert p.name == "pname"
    assert p.default_value
    assert p.value
    assert p.display_priority == 1
    assert p.read_only == False
    p.value = False
    assert not p.value

    r = InputParameterBool("r", "rname", False, 1, read_only=True)
    assert r.read_only == True
    
    with pytest.raises(TypeError):
        InputParameterBool("p", "pname", 4, 1)
    with pytest.raises(ValueError):
        r.value = True  # read_only
    with pytest.raises(ValueError):
        p.value = 10  # type


def test_parameter_quantity():
    p = InputParameterQuantity("p", "pname", Length(4.0, 'km'), 1)
    assert p.key == "p"
    assert p.name == "pname"
    assert p.default_value == Length(4.0, 'km')
    assert p.value == Length(4.0, 'km')
    assert p.display_priority == 1
    assert p.read_only == False
    p.value = Length(5000, 'm')
    assert p.value.si == 5000.0
    assert p.min_si == -math.inf
    assert p.max_si == +math.inf
    assert p.format_str == "%.2f"
    assert p.type == Length
    
    q = InputParameterQuantity("q", "qname", Speed(10, 'm/s'), 2,
        min_si=0.0, max_si=100.0, format_str="%.3f")
    assert q.min_si == 0.0
    assert q.max_si == 100.0
    assert q.format_str == "%.3f"
    assert q.type == Speed
    
    r = InputParameterQuantity("r", "rname", Length(1.0, 'm'), 1,
        read_only=True, min_si=0, max_si=10)
    assert r.read_only == True
    
    with pytest.raises(TypeError):
        InputParameterQuantity("p", "pname", 'x', 1)
    with pytest.raises(ValueError):
        InputParameterQuantity("q", "qname", Length(1, 'm'), 2,
            min_si=200, max_si=100, format_str="%.3f")
    with pytest.raises(TypeError):
        InputParameterQuantity("q", "qname", Length(1, 'm'), 2,
            min_si='x', max_si=100, format_str="%.3f")
    with pytest.raises(TypeError):
        InputParameterQuantity("q", "qname", Length(1, 'm'), 2,
            min_si=0, max_si='x', format_str="%.3f")
    with pytest.raises(TypeError):
        InputParameterQuantity("q", "qname", Length(1, 'm'), 2,
            min_si=0, max_si=100, format_str=8)
    with pytest.raises(ValueError):
        InputParameterQuantity("q", "qname", Length(1, 'km'), 2,
            min_si=0, max_si=100)
    with pytest.raises(ValueError):
        r.value = 4  # read_only
    with pytest.raises(ValueError):
        q.value = Speed(1000, 'm/s')  # > max
    with pytest.raises(ValueError):
        p.value = 'x'  # > type


def test_list():
    states = ["AZ", "DE", "MD", "CA", "AK", "MD", "VA"]
    p = InputParameterSelectionList("p", "states", states, "CA", 1)
    assert p.key == "p"
    assert p.name == "states"
    assert p.default_value == "CA"
    assert p.value == "CA"
    assert p.display_priority == 1
    assert not p.read_only
    p.value = "MD"
    assert p.value == "MD"
    assert p.default_value == "CA"
    assert p.options == states
    
    r = InputParameterSelectionList("r", "states", states, "CA", 1,
                                    read_only=True)
    assert r.read_only
    
    with pytest.raises(TypeError):
        InputParameterSelectionList("p", "p", ("CA", "MD"), "CA", 1)
    with pytest.raises(TypeError):
        InputParameterSelectionList("p", "p", "CA", "CA", 1)
    with pytest.raises(TypeError):
        InputParameterSelectionList("p", "p", states, 4, 1)
    with pytest.raises(ValueError):
        InputParameterSelectionList("p", "p", states, 'XX', 1)
    with pytest.raises(TypeError):
        InputParameterSelectionList("p", "p", ["CA", "MD", 4, "VA"], 'CA', 1)
    with pytest.raises(TypeError):
        p.value = 4
    with pytest.raises(ValueError):
        p.value = 'XX'
    with pytest.raises(ValueError):
        r.value = 'MD'


def test_unit():
    p = InputParameterUnit("p", "length", Length, "km", 1)
    assert p.key == "p"
    assert p.name == "length"
    assert p.default_value == "km"
    assert p.value == "km"
    assert p.display_priority == 1
    assert p.read_only == False
    p.value = "mi"
    assert p.value == "mi"
    assert p.default_value == "km"
    assert p.unittype == Length

    r = InputParameterUnit("r", "length", Length, "km", 1, read_only = True)
    assert r.read_only
    
    with pytest.raises(TypeError):
        InputParameterUnit("p", "p", list, "m", 1)
    with pytest.raises(TypeError):
        InputParameterUnit("p", "p", "m", "m", 1)
    with pytest.raises(ValueError):
        InputParameterUnit("p", "p", Speed, 4, 1)
    with pytest.raises(ValueError):
        InputParameterUnit("p", "p", Speed, 'm', 1)
    with pytest.raises(TypeError):
        p.value = 4
    with pytest.raises(ValueError):
        p.value = 'km/s2'
    with pytest.raises(ValueError):
        r.value = 'm/s'
    

if __name__ == "__main__":
    pytest.main()
