"""
Test the classes that represent quantities and units in the units module
""" 

import math

import pytest

from pydsol.core.units import Duration, Length


def test_assign():
    ds = Duration(2.0, 's')
    assert ds.si == 2.0
    assert ds.unit == 's'
    assert ds.displayvalue == 2.0
    dm = Duration(3.0, 'min')
    assert dm.si == 3.0 * 60.0
    assert dm.unit == 'min'
    assert dm.displayvalue == 3.0
    dc = dm.as_unit('s')
    # check that as_unit has no rounding errors
    assert Length(3.4, 'mi').si == Length(3.4, 'mi').as_unit('mm').si
    assert dc.si == dm.si
    assert dc.unit == 's'
    assert dc.displayvalue == 180
    dd = Duration(2, 'w').as_unit('day')
    assert dd.si == 14.0 * 86400.0
    assert dd.unit == 'day'
    assert dd.displayvalue == 14.0
    assert str(dd) == '14.0day'
    assert f"{ds}" == '2.0s'
    assert f"{Duration(9, 'mus')}" == '9.0\u03BCs'
    d1 = Duration(3.0)
    assert d1.unit == 's'
    assert d1.si == 3.0
    assert d1.displayvalue == 3.0
    with pytest.raises(ValueError):
        Length('x', 'm')
    with pytest.raises(TypeError):
        Length(1 + 2j, 'm')
    with pytest.raises(ValueError):
        Length(1.0, 'xyz')
        

def test_add_sub():
    ds = Duration(2.0, 's')
    dm = Duration(3.0, 'min')
    dp = ds + dm
    assert dp.si == 182.0
    assert dp.unit == ds.unit
    dr = dm - ds
    assert dr.si == 178.0
    assert dr.unit == dm.unit
    ds += ds
    assert ds.si == 4
    assert ds.unit == 's'
    dm -= Duration(30.0, 's')
    assert dm.si == 150
    assert dm.unit == 'min'
    with pytest.raises(ValueError):
        ds + Length(1.0)
    with pytest.raises(ValueError):
        ds - Length(1.0)
    with pytest.raises(ValueError):
        ds += 'x'
    with pytest.raises(ValueError):
        ds -= 3 + 5j


def test_mul_div():
    l1 = Length(2.0, "hm")
    l2 = Length(45, "cm")
    lm = l1 * 2.0
    assert type(lm) == Length
    assert lm.si == 400.0
    assert lm.unit == 'hm'
    lm = 2.0 * l1
    assert type(lm) == Length
    assert lm.si == 400.0
    assert lm.unit == 'hm'
    ld = lm / 2.0
    assert type(ld) == Length
    assert ld.si == 200.0
    assert ld.unit == 'hm'
    assert ld.displayvalue == 2.0
    l2 *= 2.0
    assert type(l2) == Length
    assert l2.si == 0.9
    assert l2.unit == 'cm'
    assert l2.displayvalue == 90.0 
    ld /= 2.0
    assert type(ld) == Length
    assert ld.si == 100.0
    assert ld.unit == 'hm'
    assert ld.displayvalue == 1.0
    # not a unit
    ln = 1.0 / l2
    assert type(ln) != Length
    assert type(ln) == float
    assert ln == 1.0 / 0.9
    with pytest.raises(ValueError):
        Length(1.0) * 'x'
    with pytest.raises(ValueError):
        Length(1.0) / (1 + 4j)
    with pytest.raises(TypeError):
        ln = (1.0, 'hm')
        ln *= 'x'
    with pytest.raises(ValueError):
        ln = Length(1.0, 'hm')
        ln /= (3 + 5j)

def test_math():
    L = Length
    a = L(-15.4, 'cm')
    x = abs(a)
    assert x == L(15.4, 'cm')
    assert math.fabs(x) == L(15.4, 'cm')
    assert math.ceil(x) == L(16.0, 'cm')
    assert math.floor(x) == L(15.0, 'cm')
    assert round(x) == L(15.0, 'cm')
    assert round(x * 2.0) == L(31.0, 'cm')
    
    
def test_duration():
    assert Duration(1, 's').si == 1.0
    assert Duration(1, 's').unit == 's'
    assert Duration(1, 'min').si == 60.0
    assert Duration(1, 'min').unit == 'min'
    assert Duration(1, 'h').si == 3600.0
    assert Duration(1, 'h').unit == 'h'
    assert Duration(1, 'day').si == 86400.0
    assert Duration(1, 'day').unit == 'day'
    types = {'s': 1, 'min': 60, 'h': 3600, 'hr': 3600, 'd': 86400,
             'day': 86400, 'wk': 7 * 86400, 'week': 7 * 86400,
             'ms': 1E-3, 'mus': 1E-6, 'ns': 1E-9}
    for unit in types:
        assert Duration(1, unit).si == types[unit]
        assert Duration(1, unit).unit == unit


def test_length():
    inch = 39.3700787402
    types = {'m': 1, 'dm': 0.1, 'cm': 0.01, 'mm': 0.001, 'mum': 1E-6,
             'nm': 1E-9, 'dam': 10, 'hm': 100, 'km': 1000, 'Mm': 1E6,
             'Gm': 1E9, 'meter': 1,
             'in': 1.0 / inch, '"': 1.0 / inch, 'inch': 1.0 / inch,
             'ft': 12.0 / inch, 'foot': 12.0 / inch,
             'yd': 36.0 / inch, 'yard': 36.0 / inch,
             'mi': 1760.0 * 36.0 / inch, 'mile': 1760.0 * 36.0 / inch}
    for unit in types:
        assert abs(Length(1, unit).si - types[unit]) < 1E-6
        assert Length(1, unit).unit == unit


if __name__ == '__main__':
    pytest.main()
