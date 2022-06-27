"""
Test the classes that represent quantities and units in the units module
""" 

import math

import pytest

from pydsol.core.units import Duration, Length, Area, Speed, Quantity, \
    Frequency, Dimensionless, Volume


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
    dd = Duration(2, 'wk').as_unit('day')
    assert dd.si == 14.0 * 86400.0
    assert dd.unit == 'day'
    assert dd.displayvalue == 14.0
    assert str(dd) == '14.0day'
    assert repr(dd) == '14.0day'
    assert f"{ds}" == '2.0s'
    assert f"{Duration(9, 'mus')}" == '9.0\u03BCs'
    d1 = Duration(3.0)
    assert d1.unit == 's'
    assert d1.si == 3.0
    assert d1.displayvalue == 3.0
    with pytest.raises(ValueError):
        Length('x', 'm')
    with pytest.raises(ValueError):
        Length(1 + 2j, 'm')
    with pytest.raises(ValueError):
        Length(1.0, 'xyz')
    with pytest.raises(ValueError):
        Length(1.0, 'mi').as_unit("x")
        
def test_cmp():
    assert Length(10, 'm') == Length(10, 'm')
    assert Length(10, 'm') != Length(10, 'cm')
    assert Length(10, 'm') != Duration(10.0, 's')
    assert not Length(10, 'm') == Duration(10.0, 's')
    assert Length(10.0, 'm') != Volume(5.0, 'm^3')
    assert Area(10.0, 'km^2') > Area(5.0, 'km^2')
    assert Area(10.0, 'km^2') >= Area(5.0, 'km^2')
    assert Area(10.0, 'km^2') >= Area(10.0, 'km^2')
    assert Area(10.0, 'm^2') < Area(5.0, 'km^2')
    assert Area(10.0, 'm^2') <= Area(5.0, 'km^2')
    assert Area(10.0, 'm^2') <= Area(10.0, 'm^2')


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
    with pytest.raises(ValueError):
        ds = 2.0 + Length(1.0)
    with pytest.raises(ValueError):
        ds = 2.0 - Length(1.0)


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
    # check errors
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
    assert abs(x) == L(15.4, 'cm')
    assert math.ceil(x) == L(16.0, 'cm')
    assert math.floor(x) == L(15.0, 'cm')
    assert round(x) == L(15.0, 'cm')
    assert round(x * 2.0) == L(31.0, 'cm')
    assert math.ceil(a) == L(-15.0, 'cm')
    assert math.floor(a) == L(-16.0, 'cm')
    assert math.trunc(a) == L(-15.0, 'cm')
    assert math.trunc(-a) == L(15.0, 'cm')
    assert L(10, 'cm') // 3 == L(3.0, 'cm')
    assert L(10, 'cm') % 3 == L(1.0, 'cm')
    with pytest.raises(ValueError):
        L(10, 'cm') // L(3, 'cm')
    with pytest.raises(ValueError):
        L(10, 'cm') % L(3, 'cm')
    assert L(10, 'cm') // 3.5 == L(2.0, 'cm')
    assert L(10, 'cm') % 3.5 == L(3.0, 'cm')
    assert -L(10, 'cm') == L(-10, 'cm')
    assert +L(10, 'cm') == L(10, 'cm')
    assert -L(-10, 'cm') == L(10, 'cm')
    assert +L(-10, 'cm') == L(-10, 'cm')
    assert Area(5.0, 'km^2') ** 2 == Area(25.0, 'km^2')
    assert Speed(2.0, 'mi/h') ** 3 == Speed(8.0, 'mi/h')
    with pytest.raises(ValueError):
        L(10, 'cm') ** L(3, 'cm')


def test_siunits():
    assert Length.siunits() == 'm'
    assert Duration.siunits() == 's'
    assert Speed.siunits() == 'm/s'
    assert Area.siunits() == 'm2'
    
    assert Speed.siunits(div=False) == 'ms-1'
    assert Speed.siunits(div=False, dot='.') == 'm.s-1'
    assert Speed.siunits(div=False, hat='^') == 'ms^-1'
    assert Speed.siunits(div=False, hat='^', dot='.') == 'm.s^-1'
    assert Area.siunits(hat='^') == 'm^2'
    
    assert Quantity._siunits({'kg': 1, 'm': 1, 's':-2},
            div=True, hat='^', dot='.') == "kg.m/s^2"
    assert Quantity._siunits({'kg': 1, 'm': 1, 's':-2},
            div=False, hat='^', dot='.') == "kg.m.s^-2"
    assert Quantity._siunits({'kg': 1, 'm': 1, 's':-2, 'A':-1},
            div=True, hat='^', dot='.') == "kg.m/s^2.A"
    assert Quantity._siunits({'kg': 1, 'm': 1, 's':-2, 'A':-1},
            div=False, hat='^', dot='.') == "kg.m.s^-2.A^-1"
    assert Quantity._siunits({'kg': 1, 'm': 1, 's':-2, 'A':-1},
            div=True, hat='^', dot='') == "kgm/s^2A"
    assert Quantity._siunits({'kg': 1, 'm': 1, 's':-2, 'A':-1},
            div=False, hat='', dot=' ') == "kg m s-2 A-1"
    assert Quantity._siunits({'s':-2},
            div=True, hat='^', dot='.') == "1/s^2"
    assert Quantity._siunits({},
            div=True, hat='^', dot='.') == "1"
    
    
def test_duration():
    assert Duration(5) == Duration(5.0, 's')
    assert Duration(1, 's').si == 1.0
    assert Duration(1, 's').unit == 's'
    assert Duration(1, 'min').si == 60.0
    assert Duration(1, 'min').unit == 'min'
    assert Duration(1, 'h').si == 3600.0
    assert Duration(1, 'h').unit == 'h'
    assert Duration(1, 'day').si == 86400.0
    assert Duration(1, 'day').unit == 'day'
    types = {'s': 1, 'min': 60, 'h': 3600, 'hr': 3600, 
             'day': 86400, 'wk': 7 * 86400, 'week': 7 * 86400,
             'ms': 1E-3, 'mus': 1E-6, 'ns': 1E-9}
    for unit in types:
        assert Duration(1, unit).si == types[unit]
        assert Duration(1, unit).unit == unit
    assert Duration.siunits() == 's'
    assert Duration(1, 'day').siunits() == 's'
    assert f"{Duration(2, 'mus')}" == '2.0\u03BCs'


def test_length():
    assert Length(5) == Length(5.0, 'm')
    inch = 39.3700787402
    types = {'m': 1, 'dm': 0.1, 'cm': 0.01, 'mm': 0.001, 'mum': 1E-6,
             'nm': 1E-9, 'dam': 10, 'hm': 100, 'km': 1000, 'Mm': 1E6,
             'Gm': 1E9, 'in': 1.0 / inch, 'ft': 12.0 / inch, 
             'yd': 36.0 / inch, 'mi': 1760.0 * 36.0 / inch}
    for unit in types:
        assert abs(Length(1, unit).si - types[unit]) < 1E-6
        assert Length(1, unit).unit == unit
    assert Length.siunits() == 'm'
    assert Length(10, 'mi').siunits() == 'm'
    assert f"{Length(2, 'mum')}" == '2.0\u03BCm'


def test_speed():
    assert Speed(5) == Speed(5.0, 'm/s')
    inch = 39.3700787402
    types = {'m/s': 1, 'km/s': 1000, 'km/h': 1.0 / 3.6,
             'in/s': 1.0 / inch, 'ft/s': 12.0 / inch, 
             'mi/s': 1760.0 * 36.0 / inch,
             'mi/h': 17.60 / inch}
    for unit in types:
        assert abs(Speed(1, unit).si - types[unit]) < 1E-6
        assert Speed(1, unit).unit == unit
    assert Speed.siunits() == 'm/s'
    assert Speed(10, 'mi/h').siunits() == 'm/s'


def test_area():
    assert Area(5) == Area(5.0, 'm^2')
    inch = 39.3700787402
    types = {'m^2': 1, 'dm^2': 1E-2, 'cm^2': 1E-4, 'mm^2': 1E-6,
             'mum^2': 1E-12, 'nm^2': 1E-18, 'dam^2': 100, 'hm^2': 1E4,
             'km^2': 1E6,
             'in^2': 1.0 / inch / inch, 'ft^2': 12.0 * 12.0 / inch / inch,
             'yd^2': 36.0 * 36.0 / inch / inch,
             'mi^2': (1760.0 * 36.0 / inch) ** 2}
    for unit in types:
        if unit == 'mi^2':
            assert abs(Area(1, unit).si - types[unit]) < 1E-3
        else:
            assert abs(Area(1, unit).si - types[unit]) < 1E-6
        assert Area(1, unit).unit == unit
    assert Area.siunits() == 'm2'
    assert Area(10, 'ft^2').siunits() == 'm2'
    assert f"{Area(2, 'mum^2')}" == '2.0\u03BCm^2'


def test_combine():
    l = Length(2.0, 'm')
    assert l / l == Dimensionless(1.0)
    assert Length(2.0, 'm') * Length(300, 'cm') == Area(6.0, 'm^2')
    
    t = Duration(4.0, 's')
    assert t / t == Dimensionless(1.0)
    assert l / t == Speed(0.5, 'm/s')
    
    s = Speed(3.0, 'm/s')
    assert s / s == Dimensionless(1.0)
    
    a = Area(10.0, 'm^2')
    assert a / a == Dimensionless(1.0)

    assert Dimensionless(1) / Duration(2, 's') == Frequency(0.5, 'Hz')
    assert 1 / Duration(0.1, 's') == Frequency(10, 'Hz')
    assert 1 / Frequency(10, 'Hz') == Duration(0.1, 's')
    
    with pytest.raises(ValueError):
        'x' / Length(10.0, 'm')


if __name__ == '__main__':
    pytest.main()
