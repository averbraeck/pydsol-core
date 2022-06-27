"""
The units module provides classes that represent quantities and units, 
with quantities like Duration, Length and Speed, and units for the quantities,
e.g.,'s', 'h' and 'min' for the Duration quantity. For simulation models, 
it is convenient to enter durations and delays using a quantity with a unit,
and to display the simulator time in a value with a unit, to know, e.g., 
that 3 hours have passed in the simulation.

For now, units assume linear scales with respect to a base unit, usually
an SI unit. Most of the calculation and transformation work is done in the
Quantity class. The Quantity class subclasses the builtin float class. 
Internally, the value of the quantity is stored in the base unit in the
float class, and the actual unit is stored in the Quantity class as a str. 

This module has been based on the Java DJUNITS project (Delft Java units), as
documented at https://djunits.org. 
"""

from abc import ABC
from typing import TypeVar, Generic

from pydsol.core.utils import get_module_logger, Assert

logger = get_module_logger('units')

Q = TypeVar('Q')


class Quantity(Generic[Q], ABC, float):
    """
    Abstract class properties
    -------------------------
    _baseunit : dict
        Defines the baseunit for this quantity, preferably an SI unit.
        The baseunit is coded as a string, and should be present in the 
        units dictionary with a conversion factor of 1.
    _units: dict[str, float]:
        Defines the available units for this quantity with a conversion 
        factor to the baseunit. The units are specified in a dictionary,
        mapping each string descriptor for the unit onto the conversion
        factor to the baseunit.
    _displayunits: dict[str, str]:
        Defines a dictionary with a translation of the unit as it is
        entered in the code and the way the unit will be displayed in the
        str(..) and repr(..) methods. An example is the 'micro' sugn, 
        which is entered as 'mu' in the units, but should be displayed as 
        a real mu sign (\u03BC). To make this translation for, for instance, 
        a micrometer, the displayunits method should return a dict
        {'mum', '\03BCm'}. Another examples is the Angstrom sign for length. 
        In case no transformations are necessary for the units in the 
        quantity, an empty dict {} can be returned.
    _sisig: dict[str, int]:
        Defines  dictionary with the SI signature of the quantity. The 
        symbols that can be used are '1', 'kg', 'm', 's', 'A', 'K', 'mol',
        and 'cd'. For force (Newton), the SI signature would be given as
        {'kg': 1, 'm': 1, 's': -2} equivalent to kg.m/s^2. In addition to
        the SI-units, we allow 'rad' (m/m) and 'sr' (m^2/m^2) as well for
        reasons of clarity.
    _mul: dict[Quantity, Quantity]
        Defines with which quantities the defined quantity can be multiplied,
        and what the resulting quantity will be.
    _div: dict[Quantity, Quantity]
        Defines by which quantities the defined quantity can be divided,
        and what the resulting quantity will be.
    """
    
    __unitlist = ('rad', 'sr', 'kg', 'm', 's', 'A', 'K', 'mol', 'cd')
    """ SI units in the order they will be displayed, plus rad and sr""" 

    def __new__(cls, value, unit: str=None, **kwargs):
        """
        The __new__ method created a Quantity instance of the right type. 
        It stores the si-value of the quantity in the float that Quantity
        subclasses. The storage of the unit is done in __init__. 
        
        Raises
        ------
        ValueError
            when the provided unit is not defined for this quantity
            when value is not a number
        """
        if unit == None:
            unitmultiplier = cls._units[cls._baseunit]
        else:
            if not unit in cls._units:
                raise ValueError(f"unit {unit} not defined")
            if not (type(value) == float or type(value) == int):
                raise ValueError(f"value {value} not a number")
            unitmultiplier = cls._units[unit]
        basevalue = value * unitmultiplier
        return super().__new__(cls, basevalue, **kwargs)
    
    def __init__(self, value: float, unit: str=None, **kwargs):
        """
        Create a Quantity instance of the right type. The si-value of 
        the quantity is stored in the float that Quantity subclasses, so
        internally all values are stored in their base-unit, which is 
        most often the si-unit.
        
        Raises
        ------
        ValueError
            when the provided unit is not defined for this quantity
        """
        if unit == None:
            self._unit = self._baseunit
        else:
            self._unit = unit
    
    @property
    def displayvalue(self) -> float:
        """
        Return the display value of the quantity. So, for Length(14, 'cm')
        the displayvalue is 14. 
        """
        return float(self) / self._units[self._unit]
    
    @property
    def si(self) -> float:
        """
        Return the internal unit (often, but not always, si) value of the 
        quantity. So, for Length(14, 'cm') si is 0.14, since the base si unit
        is meters. 
        """
        return float(self)

    @property
    def unit(self) -> str:
        """
        Return the unit with which the quantity was defined. So, for 
        Length(14, 'cm') the unit is 14. Note that the unit is different from
        the displayunit. For Length(14, 'mum'), the unit is 'mum'.   
        """
        return self._unit
        
    def as_unit(self, newunit: str) -> Q:
        """
        Return a new quantity that has been transformed to the new unit.
        The instantiation avoids multiplication and division for the
        allocation to the new unit as would be the case in:
        return self.instantiate(float(self) / self.units()[newunit], newunit).
        Instead, the internal si-value is copied into the return value and
        the unit is adapted to the new unit. This means that the two 
        quantities Length(3.4, 'mi').si and Length(3.4, 'mi').as_unit('mm').si
        are exactly the same without rounding errors. 
        
        Raises
        ------
        ValueError
            when newunit is not defined for this quantity
        """
        if not newunit in self._units:
            raise ValueError(f"unit {newunit} not defined")
        ret = type(self)(self.si, self._baseunit)
        ret._unit = newunit
        return ret
    
    def _val(self, si:float) -> Q:
        """
        Create a new quantity with the given si value and the base unit
        of the current quantity. So, if _val(80) is called on Area(10, "ha"),
        the returning value will be 
        """
        q = type(self)(si, self._baseunit)
        q._unit = self._unit
        return q

    def __abs__(self) -> Q:
        """
        Return a new quantity with the absolute value. So, abs(Length(-2, 'm')
        will return Length(2.0, 'm').
        """
        return self._val(abs(float(self)))
    
    def __add__(self, other) -> Q:
        """
        Return a new quantity containing the sum of this quantity and the
        other quantity.
        
        Raises
        ------
        ValueError
            when the two quantities are of different types
        """
        if (type(self) != type(other)):
            raise ValueError("adding incompatible quantities")
        return self._val(float(self) + float(other))
    
    def __ceil__(self) -> Q:
        """
        Return the nearest integer value above the value of this quantity.
        Note that this function works on the display value of the quantity
        and not on the internal si-value. When we want to calculate the
        ceiling of 10.4 cm, we expect 11 cm, and not 100 cm (the nearest 
        integer value above 0.104 m is 1 m = 100 cm). Note that the ceil of 
        -3.5 is -3.
        """
        return type(self)(self.displayvalue.__ceil__(), self._unit)
    
    def __floor__(self) -> Q:
        """
        Return the nearest integer value below the value of this quantity.
        Note that this function works on the display value of the quantity
        and not on the internal si-value. When we want to calculate the
        floor of 10.4 cm, we expect 10 cm, and not 0 cm (the nearest integer
        value below 0.104 m is 0 m). Note that the floor of -3.5 is -4.
        """
        return type(self)(self.displayvalue.__floor__(), self._unit)
    
    def __floordiv__(self, other):
        """
        Return the nearest integer value below the value of the division of 
        this quantity by the provided float or integer value. Note that 
        this function works on the display value of the quantity and
        not on the internal si-value. When we want to calculate 
        (10.0 cm // 3), we expect 3 cm, and not 0 cm (the nearest integer
        value below the result of 0.1 // 3 in the si unit meter is 0 m). 
        """
        if not (type(other) == float or type(other) == int):
            raise ValueError("// operator needs float or int")
        return type(self)(self.displayvalue // other, self._unit)
    
    def __mod__(self, other):
        """
        Return the remainder of the integer division of  this quantity 
        by the provided float or integer value. Note that this function 
        works on the display value of the quantity and not on the internal 
        si-value. When we want to calculate (10.0 cm % 3), we expect 1 cm, 
        and not 0.1 m (the remainder of 0.1 % 3 in the si unit meter). 
        """
        if not (type(other) == float or type(other) == int):
            raise ValueError("% operator needs float or int")
        return type(self)(self.displayvalue % other, self._unit)

    def __mul__(self, other):
        """
        Return a new quantity containing the multiplication of this quantity 
        by the provided factor (where the factor comes last in the 
        multiplication). The factor has to be of type float or int. 
        The result of Area(25.0, 'm^2') * 2 = Area(50.0, 'm^2).
        
        Raises
        ------
        ValueError
            when the multiplication factor is not a float or an int, and the
            multiplication is not between quantities
        """
        if type(other) == float or type(other) == int:
            return self._val(float(self) * other)
        if type(other) in type(self)._mul:
            newclass = type(self)._mul[type(other)]
            return newclass(float(self) * float(other),
                            newclass._baseunit)
        raise ValueError("* operator not defined for {} * {}".format(
                         self, other))
        
    def __neg__(self):
        """
        Return a new quantity containing the negation of the value of the
        quantity. A Duration of 10 seconds becomes a Duration of -10 
        seconds. The __neg__ function implements the behavior of the
        unary "-" behavior in front of a number. 
        """
        return self._val(-float(self))

    def __pos__(self):
        """
        Return the quantity, since the unary "+" operator (placing a "+"
        sign in front of a number or quantity) has no effect.
        """
        return self

    def __radd__(self, other):
        """
        Return a new quantity containing the sum of this quantity and the
        other quantity. radd is called for 2.0 + Length(1.0, 'm'),
        where the left hand side is not a Quantity, and the right hand 
        side is a Quantity. Since (a + b) == (b + a), the add function
        is used for the implementation. Typically, the radd function will 
        lead to a ValueError 
        
        Raises
        ------
        ValueError
            when the other is of a different type than self
        """
        return self.__add__(other)

    def __rmul__(self, other):
        """
        Return a new quantity containing the multiplication of this quantity 
        by the provided factor (where the factor comes first in the
        multiplication). The factor has to be of type float or int. 
        The result of 2.0 * Area(25.0, 'm^2') = Area(50.0, 'm^2).
        
        Raises
        ------
        ValueError
            when the multiplication factor is not a float or an int, and the
            multiplication is not between quantities
        """
        return self.__mul__(other)
    
    def __round__(self) -> Q:
        """
        Return the nearest integer value for the value of this quantity.
        Note that this function works on the display value of the quantity
        and not on the internal si-value. When we want to calculate the
        round(10.4 cm), we expect 10 cm, and not 0 cm (the rounded value of
        0.104 m). 
        """
        return type(self)(self.displayvalue.__round__(), self._unit)

    def __rsub__(self, other):
        """
        Return a new quantity containing the difference of the other value
        and this quantity. rsub is called for 2.0 - Length(1.0, 'm'),
        where the left hand side is not a Quantity, and the right hand 
        side is a Quantity. Typically, the rsub function will lead to a
        ValueError 
        
        Raises
        ------
        ValueError
            when the other is of a different type than self
        """
        return self.__add__(other.__neg__())

    def __sub__(self, other):
        """
        Return a new quantity containing the difference of this quantity 
        and the other quantity.
        
        Raises
        ------
        ValueError
            when the two quantities are of different types
        """
        if (type(self) != type(other)):
            raise ValueError("subtracting incompatible quantities")
        return self._val(float(self) - float(other))

    def __truediv__(self, other):
        """
        Return a new quantity containing the division of this quantity 
        by the provided divisor. The factor has to be of type float or int. 
        The result of Area(50.0, 'm^2') / 2 = Area(25.0, 'm^2).
        
        Raises
        ------
        ValueError
            when the divisor is not a float or an int, and the division
            between two quantities is not defined
        """
        if type(other) == float or type(other) == int:
            return self._val(float(self) / other)
        if type(other) in type(self)._div:
            newclass = type(self)._div[type(other)]
            return newclass(float(self) / float(other),
                            newclass._baseunit)
        raise ValueError("/ operator not defined for {} / {}".format(
                         self, other))

    def __rtruediv__(self, other):
        """
        Return a new quantity containing the division of the other quantity 
        or value by the self object. If other is a Quantity, 
        __truediv__(other, self) can be called. If other is a number, 
        __truediv__(Domensionless, self) will be called instead.
        
        Raises
        ------
        ValueError
            when other is not a float or an int, and the division between 
            the two quantities is not defined
        """
        if type(other) == float or type(other) == int:
            return Dimensionless(other).__truediv__(self)
        raise ValueError("/ operator not defined for {} / {}".format(
                         other, self))

    def __trunc__(self):
        """
        Return the nearest integer value below the value of this quantity,
        where the direction for negative numbers is towards zero. The trunc 
        of -3.5 is therefore -3, symmetric with the trunc of +3.5.
        Note that this function works on the display value of the quantity
        and not on the internal si-value. When we want to calculate the
        floor of 10.4 cm, we expect 10 cm, and not 0 cm (the nearest integer
        value below 0.104 m is 0 m). 
        """
        return type(self)(self.displayvalue.__trunc__(), self._unit)
    
    def __pow__(self, power):
        """
        Return a new quantity containing the value of this quantity to the
        provided power. The power has to be of type float or int. Note that 
        this function works on the display value of the quantity and not
        on the internal si-value.
        The result of Area(5.0, 'km^2') ** 2 = Area(25.0, 'km^2).
        
        Raises
        ------
        ValueError
            when the multiplication factor is not a float or an int
        """
        if not (type(power) == float or type(power) == int):
            raise ValueError("** operator needs float or int")
        return type(self)(self.displayvalue ** power, self._unit)

    def __eq__(self, other) -> bool:
        """
        Return whether this quantity is equal to the other quantity.
        False will be returned when the types are different.
        """
        if type(self) != type(other):
            return False
        return float(self) == float(other)

    def __ne__(self, other) -> bool:
        """
        Return whether this quantity is not equal to the other quantity.
        True will be returned when the types are different.
        """
        if type(self) != type(other):
            return True
        return float(self) != float(other)
         
    def __lt__(self, other) -> bool:
        """
        Return whether this quantity is less than the other quantity.
        
        Raises
        ------
        TypeError
            when the two quantities are of different types
        """
        Assert.that(type(self) == type(other), TypeError,
            "comparing incompatible quantities {0} and {1}",
                    type(self).__name__, type(other).__name__)
        return float(self) < float(other)
         
    def __le__(self, other) -> bool:
        """
        Return whether this quantity is less than or equal to the 
        other quantity.
        
        Raises
        ------
        TypeError
            when the two quantities are of different types
        """
        Assert.that(type(self) == type(other), TypeError,
            "comparing incompatible quantities {0} and {1}",
                    type(self).__name__, type(other).__name__)
        return float(self) <= float(other)
         
    def __gt__(self, other) -> bool:
        """
        Return whether this quantity is greater than the other quantity.
        
        Raises
        ------
        TypeError
            when the two quantities are of different types
        """
        Assert.that(type(self) == type(other), TypeError,
            "comparing incompatible quantities {0} and {1}",
                    type(self).__name__, type(other).__name__)
        return float(self) > float(other)
         
    def __ge__(self, other) -> bool:
        """
        Return whether this quantity is greater than or equal to the 
        other quantity.
        
        Raises
        ------
        TypeError
            when the two quantities are of different types
        """
        Assert.that(type(self) == type(other), TypeError,
            "comparing incompatible quantities {0} and {1}",
                    type(self).__name__, type(other).__name__)
        return float(self) >= float(other)
         
    def __str__(self):
        """
        Return a string representation of the quantity, where the chosen unit 
        follows the value without a space.
        """
        return str(self.displayvalue) + self._displayunits.get(self._unit,
                self._unit)

    def __repr__(self):
        """
        Return a string representation of the quantity, where the chosen unit 
        follows the value without a space.
        """
        return str(self.displayvalue) + self._displayunits.get(self._unit,
                self._unit)

    @classmethod
    def siunits(cls, div:bool=True, hat:str='', dot:str='') -> str:
        return Quantity._siunits(cls._sisig, div, hat, dot)
    
    @staticmethod
    def _siunits(sistr: dict[str, int], div:bool=True, hat:str='',
                 dot:str='') -> str:
        s = ""
        t = ""
        for unit in Quantity.__unitlist:
            if unit in sistr:
                v: int = sistr[unit]
                if v > 0 or (v < 0 and not div):
                    if len(s) > 0:
                        s += dot
                    s += unit
                    if v > 1 or v < 0:
                        s += hat + str(v)
        if div:
            for unit in Quantity.__unitlist:
                if unit in sistr:
                    v: int = sistr[unit]
                    if v < 0:
                        if len(t) > 0:
                            t += dot
                        t += unit
                        if v < -1:
                            t += hat + str(-v)
        if len(s) == 0:
            s = "1"
        if len(t) > 0:
            s += "/" + t
        return s


class Acceleration(Quantity['Acceleration']):
    _baseunit = 'm/s2'
    _units = {'m/s2': 1.0, 'm/sec^2': 1.0, 'km/h2': 7.71604938271605E-5,
              'km/hr^2': 7.71604938271605E-5,
              'km/hour^2': 7.71604938271605E-5, 'ft/s2': 0.3048,
              'ft/sec^2': 0.3048, 'in/s2': 0.0254, 'in/sec^2': 0.0254,
              'mi/h2': 1.241777777777778E-4,
              'mi/hr^2': 1.241777777777778E-4,
              'mi/hour^2': 1.241777777777778E-4, 'mi/s2': 1609.344,
              'mi/sec^2': 1609.344, 'kt/s': 0.5144444444444445,
              'kt/sec': 0.5144444444444445, 'mi/h/s': 0.44704,
              'mi/hr/s': 0.44704, 'mi/hour/s': 0.44704, 'mi/h/sec': 0.44704,
              'mi/hr/sec': 0.44704, 'mi/hour/sec': 0.44704, 'g': 9.80665,
              'Gal': 0.01}
    _displayunits = {'m/sec^2': 'm/s2', 'km/hr^2': 'km/h2',
                     'km/hour^2': 'km/h2', 'ft/sec^2': 'ft/s2',
                     'in/sec^2': 'in/s2', 'mi/hr^2': 'mi/h2',
                     'mi/hour^2': 'mi/h2', 'mi/sec^2': 'mi/s2',
                     'kt/sec': 'kt/s', 'mi/hr/s': 'mi/h/s',
                     'mi/hour/s': 'mi/h/s', 'mi/h/sec': 'mi/h/s',
                     'mi/hr/sec': 'mi/h/s', 'mi/hour/sec': 'mi/h/s'}
    _descriptions = {'m/s2': 'meter per second squared',
                     'm/sec^2': 'meter per second squared',
                     'km/h2': 'kilometer per hour squared',
                     'km/hr^2': 'kilometer per hour squared',
                     'km/hour^2': 'kilometer per hour squared',
                     'ft/s2': 'foot per second squared',
                     'ft/sec^2': 'foot per second squared',
                     'in/s2': 'inch per second squared',
                     'in/sec^2': 'inch per second squared',
                     'mi/h2': 'mile per hour squared',
                     'mi/hr^2': 'mile per hour squared',
                     'mi/hour^2': 'mile per hour squared',
                     'mi/s2': 'mile per second squared',
                     'mi/sec^2': 'mile per second squared',
                     'kt/s': 'knot per second',
                     'kt/sec': 'knot per second',
                     'mi/h/s': 'mile per hour per second',
                     'mi/hr/s': 'mile per hour per second',
                     'mi/hour/s': 'mile per hour per second',
                     'mi/h/sec': 'mile per hour per second',
                     'mi/hr/sec': 'mile per hour per second',
                     'mi/hour/sec': 'mile per hour per second',
                     'g': 'standard gravity', 'Gal': 'gal'}
    _sisig = {'m': 1, 's':-2}
    _mul = {}
    _div = {}


class Angle(Quantity['Angle']):
    _baseunit = 'rad'
    _units = {'rad': 1.0, '%': 0.00999966668666524, '°': 0.0174532925199433,
              'deg': 0.0174532925199433, 'dg': 0.0174532925199433,
              '\'': 2.908882086657216E-4, 'arcmin': 2.908882086657216E-4,
              '"': 4.84813681109536E-6, 'arcsec': 4.84813681109536E-6,
              'grad': 0.01570796326794897, 'c\'': 1.570796326794897E-4,
              'c"': 1.570796326794897E-6}
    _displayunits = {'deg': '°', 'dg': '°', 'arcmin': '\'', 'arcsec': '"'}
    _descriptions = {'rad': 'radians', '%': 'percent', '°': 'degree',
                     'deg': 'degree', 'dg': 'degree', '\'': 'arcminute',
                     'arcmin': 'arcminute', '"': 'arcsecond',
                     'arcsec': 'arcsecond', 'grad': 'gradian',
                     'c\'': 'centesimal arcminute',
                     'c"': 'centesimal arcsecond'}
    _sisig = {'rad': 1}
    _mul = {}
    _div = {}


class AngularAcceleration(Quantity['AngularAcceleration']):
    _baseunit = 'rad/s2'
    _units = {'rad/s2': 1.0, 'rad/sec2': 1.0, '°/s2': 0.0174532925199433,
              'deg/s2': 0.0174532925199433, 'dg/s2': 0.0174532925199433,
              'dg/sec2': 0.0174532925199433,
              'deg/sec2': 0.0174532925199433,
              '\'/s2': 2.908882086657216E-4,
              '\'/sec2': 2.908882086657216E-4,
              'arcmin/sec2': 2.908882086657216E-4,
              '"/s2': 4.84813681109536E-6, '"/sec2': 4.84813681109536E-6,
              'arcsec/sec2': 4.84813681109536E-6,
              'grad/s2': 0.01570796326794897,
              'c\'/s2': 1.570796326794897E-4,
              'c\'/sec2': 1.570796326794897E-4,
              'c"/s2': 1.570796326794897E-6,
              'c"/sec2': 1.570796326794897E-6}
    _displayunits = {'rad/sec2': 'rad/s2', 'deg/s2': '°/s2',
                     'dg/s2': '°/s2', 'dg/sec2': '°/s2', 'deg/sec2': '°/s2',
                     '\'/sec2': '\'/s2', 'arcmin/sec2': '\'/s2',
                     '"/sec2': '"/s2', 'arcsec/sec2': '"/s2',
                     'c\'/sec2': 'c\'/s2', 'c"/sec2': 'c"/s2'}
    _descriptions = {'rad/s2': 'radians per second squared',
                     'rad/sec2': 'radians per second squared',
                     '°/s2': 'degree per second',
                     'deg/s2': 'degree per second',
                     'dg/s2': 'degree per second',
                     'dg/sec2': 'degree per second',
                     'deg/sec2': 'degree per second',
                     '\'/s2': 'arcminute per second squared',
                     '\'/sec2': 'arcminute per second squared',
                     'arcmin/sec2': 'arcminute per second squared',
                     '"/s2': 'arcsecond per second squared',
                     '"/sec2': 'arcsecond per second squared',
                     'arcsec/sec2': 'arcsecond per second squared',
                     'grad/s2': 'gradian per second squared',
                     'c\'/s2': 'centesimal arcminute per second squared',
                     'c\'/sec2': 'centesimal arcminute per second squared',
                     'c"/s2': 'centesimal arcsecond per second squared',
                     'c"/sec2': 'centesimal arcsecond per second squared'}
    _sisig = {'rad': 1, 's':-2}
    _mul = {}
    _div = {}


class AngularVelocity(Quantity['AngularVelocity']):
    _baseunit = 'rad/s'
    _units = {'rad/s': 1.0, 'rad/sec': 1.0, '°/s': 0.0174532925199433,
              'deg/s': 0.0174532925199433, 'dg/s': 0.0174532925199433,
              'dg/sec': 0.0174532925199433, 'deg/sec': 0.0174532925199433,
              '\'/s': 2.908882086657216E-4,
              '\'/sec': 2.908882086657216E-4,
              'arcmin/sec': 2.908882086657216E-4,
              '"/s': 4.84813681109536E-6, '"/sec': 4.84813681109536E-6,
              'arcsec/sec': 4.84813681109536E-6,
              'grad/s': 0.01570796326794897,
              'c\'/s': 1.570796326794897E-4,
              'c\'/sec': 1.570796326794897E-4,
              'c"/s': 1.570796326794897E-6,
              'c"/sec': 1.570796326794897E-6}
    _displayunits = {'rad/sec': 'rad/s', 'deg/s': '°/s', 'dg/s': '°/s',
                     'dg/sec': '°/s', 'deg/sec': '°/s', '\'/sec': '\'/s',
                     'arcmin/sec': '\'/s', '"/sec': '"/s',
                     'arcsec/sec': '"/s', 'c\'/sec': 'c\'/s',
                     'c"/sec': 'c"/s'}
    _descriptions = {'rad/s': 'radians per second',
                     'rad/sec': 'radians per second',
                     '°/s': 'degree per second',
                     'deg/s': 'degree per second',
                     'dg/s': 'degree per second',
                     'dg/sec': 'degree per second',
                     'deg/sec': 'degree per second',
                     '\'/s': 'arcminute per second',
                     '\'/sec': 'arcminute per second',
                     'arcmin/sec': 'arcminute per second',
                     '"/s': 'arcsecond per second',
                     '"/sec': 'arcsecond per second',
                     'arcsec/sec': 'arcsecond per second',
                     'grad/s': 'gradian per second',
                     'c\'/s': 'centesimal arcminute per second',
                     'c\'/sec': 'centesimal arcminute per second',
                     'c"/s': 'centesimal arcsecond per second',
                     'c"/sec': 'centesimal arcsecond per second'}
    _sisig = {'rad': 1, 's':-1}
    _mul = {}
    _div = {}


class Area(Quantity['Area']):
    _baseunit = 'm^2'
    _units = {'pm^2': 1.0E-24, 'nm^2': 1.0E-18, 'μm^2': 1.0E-12,
              'mum^2': 1.0E-12, 'mm^2': 1.0E-6, 'cm^2': 1.0E-4, 'dm^2': 0.01,
              'dam^2': 100.0, 'hm^2': 10000.0, 'km^2': 1000000.0,
              'Mm^2': 1.0E12, 'Gm^2': 1.0E18, 'Tm^2': 1.0E24, 'Pm^2': 1.0E30,
              'm^2': 1.0, 'ca': 1.0, 'a': 100.0, 'ha': 10000.0,
              'mi^2': 2589988.110336, 'NM^2': 3429904.0, 'ft^2': 0.09290304,
              'in^2': 6.4516E-4, 'yd^2': 0.8361273600000002,
              'ac': 4046.8564224}
    _displayunits = {'mum^2': 'μm^2'}
    _descriptions = {'pm^2': 'square pico meter',
                     'nm^2': 'square nano meter',
                     'μm^2': 'square micro meter',
                     'mum^2': 'square micro meter',
                     'mm^2': 'square millimeter',
                     'cm^2': 'square centimeter',
                     'dm^2': 'square decimeter',
                     'dam^2': 'square decameter',
                     'hm^2': 'square hectometer',
                     'km^2': 'square kilometer',
                     'Mm^2': 'square mega meter',
                     'Gm^2': 'square giga meter',
                     'Tm^2': 'square tera meter',
                     'Pm^2': 'square peta meter', 'm^2': 'square meter',
                     'ca': 'centiare', 'a': 'are', 'ha': 'hectare',
                     'mi^2': 'square mile',
                     'NM^2': 'square Nautical Mile',
                     'ft^2': 'square foot', 'in^2': 'square inch',
                     'yd^2': 'square yard', 'ac': 'acre'}
    _sisig = {'m': 2}
    _mul = {}
    _div = {}


class Density(Quantity['Density']):
    _baseunit = 'kg/m^3'
    _units = {'kg/m^3': 1.0, 'g/cm^3': 1000.0}
    _displayunits = {'kg/m^3': 1.0, 'g/cm^3': 1000.0}
    _descriptions = {'kg/m^3': 'kilogram per cubic meter',
                     'g/cm^3': 'gram per cubic centimeter'}
    _sisig = {'kg': 1, 'm':-3}
    _mul = {}
    _div = {}


class Dimensionless(Quantity['Dimensionless']):
    _baseunit = 'unit'
    _units = {'unit': 1.0}
    _displayunits = {'unit': 1.0}
    _descriptions = {'unit': 'unit'}
    _sisig = {}
    _mul = {}
    _div = {}


class Duration(Quantity['Duration']):
    _baseunit = 's'
    _units = {'ps': 1.0E-12, 'psec': 1.0E-12, 'ns': 1.0E-9, 'nsec': 1.0E-9,
              'μs': 1.0E-6, 'mus': 1.0E-6, 'μsec': 1.0E-6, 'musec': 1.0E-6,
              'ms': 0.001, 'msec': 0.001, 'cs': 0.01, 'csec': 0.01, 'ds': 0.1,
              'dsec': 0.1, 'das': 10.0, 'dasec': 10.0, 'hs': 100.0,
              'hsec': 100.0, 'ks': 1000.0, 'ksec': 1000.0, 'Ms': 1000000.0,
              'Msec': 1000000.0, 'Gs': 1.0E9, 'Gsec': 1.0E9, 'Ts': 1.0E12,
              'Tsec': 1.0E12, 'Ps': 1.0E15, 'Psec': 1.0E15, 's': 1.0,
              'sec': 1.0, 'min': 60.0, 'h': 3600.0, 'hr': 3600.0,
              'hour': 3600.0, 'day': 86400.0, 'wk': 604800.0,
              'week': 604800.0}
    _displayunits = {'psec': 'ps', 'nsec': 'ns', 'mus': 'μs', 'μsec': 'μs',
                     'musec': 'μs', 'msec': 'ms', 'csec': 'cs', 'dsec': 'ds',
                     'dasec': 'das', 'hsec': 'hs', 'ksec': 'ks', 'Msec': 'Ms',
                     'Gsec': 'Gs', 'Tsec': 'Ts', 'Psec': 'Ps', 'sec': 's',
                     'hr': 'h', 'hour': 'h', 'week': 'wk'}
    _descriptions = {'ps': 'picosecond', 'psec': 'picosecond',
                     'ns': 'nanosecond', 'nsec': 'nanosecond',
                     'μs': 'microsecond', 'mus': 'microsecond',
                     'μsec': 'microsecond', 'musec': 'microsecond',
                     'ms': 'millisecond', 'msec': 'millisecond',
                     'cs': 'centisecond', 'csec': 'centisecond',
                     'ds': 'decisecond', 'dsec': 'decisecond',
                     'das': 'decasecond', 'dasec': 'decasecond',
                     'hs': 'hectosecond', 'hsec': 'hectosecond',
                     'ks': 'kilosecond', 'ksec': 'kilosecond',
                     'Ms': 'megasecond', 'Msec': 'megasecond',
                     'Gs': 'gigasecond', 'Gsec': 'gigasecond',
                     'Ts': 'terasecond', 'Tsec': 'terasecond',
                     'Ps': 'petasecond', 'Psec': 'petasecond',
                     's': 'second', 'sec': 'second', 'min': 'minute',
                     'h': 'hour', 'hr': 'hour', 'hour': 'hour', 'day': 'day',
                     'wk': 'week', 'week': 'week'}
    _sisig = {'s': 1}
    _mul = {}
    _div = {}


class ElectricalCharge(Quantity['ElectricalCharge']):
    _baseunit = 'C'
    _units = {'pC': 1.0E-12, 'nC': 1.0E-9, 'μC': 1.0E-6, 'muC': 1.0E-6,
              'mC': 0.001, 'cC': 0.01, 'dC': 0.1, 'daC': 10.0, 'hC': 100.0,
              'kC': 1000.0, 'MC': 1000000.0, 'GC': 1.0E9, 'TC': 1.0E12,
              'PC': 1.0E15, 'C': 1.0, 'pAh': 3.6E-9, 'nAh': 3.6E-6,
              'μAh': 0.0036, 'muAh': 0.0036, 'mAh': 3.6, 'cAh': 36.0,
              'dAh': 360.0, 'daAh': 36000.0, 'hAh': 360000.0,
              'kAh': 3600000.0, 'MAh': 3.6E9, 'GAh': 3.6E12, 'TAh': 3.6E15,
              'PAh': 3.6E18, 'Ah': 3600.0, 'mAs': 1.0, 'F': 96485.3383,
              'e': 1.602176634E-19, 'statC': 3.335641E-10,
              'Fr': 3.335641E-10, 'esu': 3.335641E-10, 'abC': 10.0,
              'emu': 10.0}
    _displayunits = {'muC': 'μC', 'muAh': 'μAh'}
    _descriptions = {'pC': 'picocoulomb', 'nC': 'nanocoulomb',
                     'μC': 'microcoulomb', 'muC': 'microcoulomb',
                     'mC': 'millicoulomb', 'cC': 'centicoulomb',
                     'dC': 'decicoulomb', 'daC': 'decacoulomb',
                     'hC': 'hectocoulomb', 'kC': 'kilocoulomb',
                     'MC': 'megacoulomb', 'GC': 'gigacoulomb',
                     'TC': 'teracoulomb', 'PC': 'petacoulomb',
                     'C': 'coulomb', 'pAh': 'picoampere hour',
                     'nAh': 'nanoampere hour', 'μAh': 'microampere hour',
                     'muAh': 'microampere hour',
                     'mAh': 'milliampere hour', 'cAh': 'centiampere hour',
                     'dAh': 'deciampere hour', 'daAh': 'decaampere hour',
                     'hAh': 'hectoampere hour', 'kAh': 'kiloampere hour',
                     'MAh': 'megaampere hour', 'GAh': 'gigaampere hour',
                     'TAh': 'teraampere hour', 'PAh': 'petaampere hour',
                     'Ah': 'ampere hour', 'mAs': 'milliampere second',
                     'F': 'faraday', 'e': 'elementary unit of charge',
                     'statC': 'statcoulomb', 'Fr': 'franklin',
                     'esu': 'electrostatic unit', 'abC': 'abcoulomb',
                     'emu': 'electromagnetic unit'}
    _sisig = {'s': 1, 'A': 1}
    _mul = {}
    _div = {}


class ElectricalCurrent(Quantity['ElectricalCurrent']):
    _baseunit = 'A'
    _units = {'pA': 1.0E-12, 'nA': 1.0E-9, 'μA': 1.0E-6, 'muA': 1.0E-6,
              'mA': 0.001, 'cA': 0.01, 'dA': 0.1, 'daA': 10.0, 'hA': 100.0,
              'kA': 1000.0, 'MA': 1000000.0, 'GA': 1.0E9, 'TA': 1.0E12,
              'PA': 1.0E15, 'A': 1.0, 'statA': 3.335641E-10, 'abA': 10.0}
    _displayunits = {'muA': 'μA'}
    _descriptions = {'pA': 'picoampere', 'nA': 'nanoampere',
                     'μA': 'microampere', 'muA': 'microampere',
                     'mA': 'milliampere', 'cA': 'centiampere',
                     'dA': 'deciampere', 'daA': 'decaampere',
                     'hA': 'hectoampere', 'kA': 'kiloampere',
                     'MA': 'megaampere', 'GA': 'gigaampere',
                     'TA': 'teraampere', 'PA': 'petaampere', 'A': 'ampere',
                     'statA': 'statampere', 'abA': 'abampere'}
    _sisig = {'A': 1}
    _mul = {}
    _div = {}


class ElectricalPotential(Quantity['ElectricalPotential']):
    _baseunit = 'V'
    _units = {'pV': 1.0E-12, 'nV': 1.0E-9, 'μV': 1.0E-6, 'muV': 1.0E-6,
              'mV': 0.001, 'cV': 0.01, 'dV': 0.1, 'daV': 10.0, 'hV': 100.0,
              'kV': 1000.0, 'MV': 1000000.0, 'GV': 1.0E9, 'TV': 1.0E12,
              'PV': 1.0E15, 'V': 1.0, 'stV': 299.792458, 'abV': 1.0E-8}
    _displayunits = {'muV': 'μV'}
    _descriptions = {'pV': 'picovolt', 'nV': 'nanovolt', 'μV': 'microvolt',
                     'muV': 'microvolt', 'mV': 'millivolt',
                     'cV': 'centivolt', 'dV': 'decivolt', 'daV': 'decavolt',
                     'hV': 'hectovolt', 'kV': 'kilovolt', 'MV': 'megavolt',
                     'GV': 'gigavolt', 'TV': 'teravolt', 'PV': 'petavolt',
                     'V': 'volt', 'stV': 'statvolt', 'abV': 'abvolt'}
    _sisig = {'kg': 1, 'm': 2, 's':-3, 'A':-1}
    _mul = {}
    _div = {}


class ElectricalResistance(Quantity['ElectricalResistance']):
    _baseunit = 'ohm'
    _units = {'pΩ': 1.0E-12, 'pohm': 1.0E-12, 'nΩ': 1.0E-9, 'nohm': 1.0E-9,
              'μΩ': 1.0E-6, 'muohm': 1.0E-6, 'muΩ': 1.0E-6, 'mΩ': 0.001,
              'mohm': 0.001, 'cΩ': 0.01, 'cohm': 0.01, 'dΩ': 0.1, 'dohm': 0.1,
              'daΩ': 10.0, 'daohm': 10.0, 'hΩ': 100.0, 'hohm': 100.0,
              'kΩ': 1000.0, 'kohm': 1000.0, 'MΩ': 1000000.0,
              'Mohm': 1000000.0, 'GΩ': 1.0E9, 'Gohm': 1.0E9, 'TΩ': 1.0E12,
              'Tohm': 1.0E12, 'PΩ': 1.0E15, 'Pohm': 1.0E15, 'Ω': 1.0,
              'ohm': 1.0, 'abΩ': 1.0E-9, 'abohm': 1.0E-9,
              'stΩ': 8.987551787E11, 'stohm': 8.987551787E11}
    _displayunits = {'pohm': 'pΩ', 'nohm': 'nΩ', 'muohm': 'μΩ', 'muΩ': 'μΩ',
                     'mohm': 'mΩ', 'cohm': 'cΩ', 'dohm': 'dΩ', 'daohm': 'daΩ',
                     'hohm': 'hΩ', 'kohm': 'kΩ', 'Mohm': 'MΩ', 'Gohm': 'GΩ',
                     'Tohm': 'TΩ', 'Pohm': 'PΩ', 'ohm': 'Ω', 'abohm': 'abΩ',
                     'stohm': 'stΩ'}
    _descriptions = {'pΩ': 'picoohm', 'pohm': 'picoohm', 'nΩ': 'nanoohm',
                     'nohm': 'nanoohm', 'μΩ': 'microohm',
                     'muohm': 'microohm', 'muΩ': 'microohm',
                     'mΩ': 'milliohm', 'mohm': 'milliohm', 'cΩ': 'centiohm',
                     'cohm': 'centiohm', 'dΩ': 'deciohm', 'dohm': 'deciohm',
                     'daΩ': 'decaohm', 'daohm': 'decaohm', 'hΩ': 'hectoohm',
                     'hohm': 'hectoohm', 'kΩ': 'kiloohm', 'kohm': 'kiloohm',
                     'MΩ': 'megaohm', 'Mohm': 'megaohm', 'GΩ': 'gigaohm',
                     'Gohm': 'gigaohm', 'TΩ': 'teraohm', 'Tohm': 'teraohm',
                     'PΩ': 'petaohm', 'Pohm': 'petaohm', 'Ω': 'ohm',
                     'ohm': 'ohm', 'abΩ': 'abohm', 'abohm': 'abohm',
                     'stΩ': 'statohm', 'stohm': 'statohm'}
    _sisig = {'kg': 1, 'm': 2, 's':-3, 'A':-2}
    _mul = {}
    _div = {}


class Energy(Quantity['Energy']):
    _baseunit = 'J'
    _units = {'pJ': 1.0E-12, 'nJ': 1.0E-9, 'μJ': 1.0E-6, 'muJ': 1.0E-6,
              'mJ': 0.001, 'cJ': 0.01, 'dJ': 0.1, 'daJ': 10.0, 'hJ': 100.0,
              'kJ': 1000.0, 'MJ': 1000000.0, 'GJ': 1.0E9, 'TJ': 1.0E12,
              'PJ': 1.0E15, 'J': 1.0, 'ft.lbf': 1.3558179483314003,
              'in.lbf': 0.1129848290276167, 'BTU(ISO)': 1054.5,
              'BTU(IT)': 1055.05585262, 'cal(IT)': 4.1868, 'cal': 4.184,
              'kcal': 4184.0, 'pWh': 3.6E-9, 'nWh': 3.6E-6, 'μWh': 0.0036,
              'muWh': 0.0036, 'mWh': 3.6, 'cWh': 36.0, 'dWh': 360.0,
              'daWh': 36000.0, 'hWh': 360000.0, 'kWh': 3600000.0,
              'MWh': 3.6E9, 'GWh': 3.6E12, 'TWh': 3.6E15, 'PWh': 3.6E18,
              'Wh': 3600.0, 'peV': 1.602176634E-31, 'neV': 1.602176634E-28,
              'μeV': 1.602176634E-25, 'mueV': 1.602176634E-25,
              'meV': 1.602176634E-22, 'ceV': 1.602176634E-21,
              'deV': 1.602176634E-20, 'daeV': 1.602176634E-18,
              'heV': 1.602176634E-17, 'keV': 1.602176634E-16,
              'MeV': 1.602176634E-13, 'GeV': 1.602176634E-10,
              'TeV': 1.602176634E-7, 'PeV': 1.602176634E-4,
              'eV': 1.602176634E-19, 'sn.m': 1000.0, 'erg': 1.0E-7}
    _displayunits = {'muJ': 'μJ', 'muWh': 'μWh', 'mueV': 'μeV'}
    _descriptions = {'pJ': 'picojoule', 'nJ': 'nanojoule',
                     'μJ': 'microjoule', 'muJ': 'microjoule',
                     'mJ': 'millijoule', 'cJ': 'centijoule',
                     'dJ': 'decijoule', 'daJ': 'decajoule',
                     'hJ': 'hectojoule', 'kJ': 'kilojoule',
                     'MJ': 'megajoule', 'GJ': 'gigajoule',
                     'TJ': 'terajoule', 'PJ': 'petajoule', 'J': 'joule',
                     'ft.lbf': 'foot pound-force',
                     'in.lbf': 'inch pound-force',
                     'BTU(ISO)': 'British thermal unit (ISO)',
                     'BTU(IT)': 'British thermal unit (International Table)',
                     'cal(IT)': 'calorie (International Table)',
                     'cal': 'calorie', 'kcal': 'kilocalorie',
                     'pWh': 'picowatt-hour', 'nWh': 'nanowatt-hour',
                     'μWh': 'microwatt-hour', 'muWh': 'microwatt-hour',
                     'mWh': 'milliwatt-hour', 'cWh': 'centiwatt-hour',
                     'dWh': 'deciwatt-hour', 'daWh': 'decawatt-hour',
                     'hWh': 'hectowatt-hour', 'kWh': 'kilowatt-hour',
                     'MWh': 'megawatt-hour', 'GWh': 'gigawatt-hour',
                     'TWh': 'terawatt-hour', 'PWh': 'petawatt-hour',
                     'Wh': 'watt-hour', 'peV': 'picoelectronvolt',
                     'neV': 'nanoelectronvolt',
                     'μeV': 'microelectronvolt',
                     'mueV': 'microelectronvolt',
                     'meV': 'millielectronvolt',
                     'ceV': 'centielectronvolt',
                     'deV': 'decielectronvolt',
                     'daeV': 'decaelectronvolt',
                     'heV': 'hectoelectronvolt',
                     'keV': 'kiloelectronvolt', 'MeV': 'megaelectronvolt',
                     'GeV': 'gigaelectronvolt', 'TeV': 'teraelectronvolt',
                     'PeV': 'petaelectronvolt', 'eV': 'electronvolt',
                     'sn.m': 'sthene meter', 'erg': 'erg'}
    _sisig = {'kg': 1, 'm': 2, 's':-2}
    _mul = {}
    _div = {}


class FlowMass(Quantity['FlowMass']):
    _baseunit = 'kg/s'
    _units = {'kg/s': 1.0, 'kg/sec': 1.0, 'lb/s': 0.45359237,
              'lb/sec': 0.45359237}
    _displayunits = {'kg/sec': 'kg/s', 'lb/sec': 'lb/s'}
    _descriptions = {'kg/s': 'kilogram per second',
                     'kg/sec': 'kilogram per second',
                     'lb/s': 'pound per second',
                     'lb/sec': 'pound per second'}
    _sisig = {'kg': 1, 's':-1}
    _mul = {}
    _div = {}


class FlowVolume(Quantity['FlowVolume']):
    _baseunit = 'm^3/s'
    _units = {'m^3/s': 1.0, 'm^3/sec': 1.0, 'm^3/min': 0.01666666666666667,
              'm^3/h': 2.777777777777778E-4,
              'm^3/hr': 2.777777777777778E-4,
              'm^3/hour': 2.777777777777778E-4,
              'm^3/day': 1.1574074074074073E-5, 'L/s': 0.001,
              'L/sec': 0.001, 'L/min': 1.666666666666667E-5,
              'L/h': 2.777777777777778E-7, 'L/hr': 2.777777777777778E-7,
              'L/hour': 2.777777777777778E-7,
              'L/day': 1.1574074074074074E-8, 'ft^3/s': 0.028316846592,
              'ft^3/sec': 0.028316846592,
              'ft^3/min': 4.719474432000001E-4, 'in^3/s': 1.6387064E-5,
              'in^3/sec': 1.6387064E-5, 'in^3/min': 2.731177333333334E-7,
              'gal(US)/s': 0.003785411784, 'gal(US)/sec': 0.003785411784,
              'gal(US)/min': 6.30901964E-5,
              'gal(US)/h': 1.051503273333333E-6,
              'gal(US)/hr': 1.051503273333333E-6,
              'gal(US)/hour': 1.051503273333333E-6,
              'gal(US)/day': 4.381263638888889E-8}
    _displayunits = {'m^3/sec': 'm^3/s', 'm^3/hr': 'm^3/h',
                     'm^3/hour': 'm^3/h', 'L/sec': 'L/s', 'L/hr': 'L/h',
                     'L/hour': 'L/h', 'ft^3/sec': 'ft^3/s',
                     'in^3/sec': 'in^3/s', 'gal(US)/sec': 'gal(US)/s',
                     'gal(US)/hr': 'gal(US)/h',
                     'gal(US)/hour': 'gal(US)/h'}
    _descriptions = {'m^3/s': 'cubic meter per second',
                     'm^3/sec': 'cubic meter per second',
                     'm^3/min': 'cubic meter per minute',
                     'm^3/h': 'cubic meter per hour',
                     'm^3/hr': 'cubic meter per hour',
                     'm^3/hour': 'cubic meter per hour',
                     'm^3/day': 'cubic meter per day',
                     'L/s': 'liter per second',
                     'L/sec': 'liter per second',
                     'L/min': 'liter per minute', 'L/h': 'liter per hour',
                     'L/hr': 'liter per hour', 'L/hour': 'liter per hour',
                     'L/day': 'liter per day',
                     'ft^3/s': 'cubic foot per second',
                     'ft^3/sec': 'cubic foot per second',
                     'ft^3/min': 'cubic foot per minute',
                     'in^3/s': 'cubic inch per second',
                     'in^3/sec': 'cubic inch per second',
                     'in^3/min': 'cubic inch per minute',
                     'gal(US)/s': 'US gallon per second',
                     'gal(US)/sec': 'US gallon per second',
                     'gal(US)/min': 'US gallon per minute',
                     'gal(US)/h': 'US gallon per hour',
                     'gal(US)/hr': 'US gallon per hour',
                     'gal(US)/hour': 'US gallon per hour',
                     'gal(US)/day': 'US gallon per day'}
    _sisig = {'m': 3, 's':-1}
    _mul = {}
    _div = {}


class Force(Quantity['Force']):
    _baseunit = 'N'
    _units = {'N': 1.0, 'dyn': 1.0E-5, 'kgf': 9.80665,
              'ozf': 0.2780138509537812, 'lbf': 4.4482216152605,
              'tnf': 8896.443230521, 'sn': 1000.0}
    _displayunits = {'N': 1.0, 'dyn': 1.0E-5, 'kgf': 9.80665,
              'ozf': 0.2780138509537812, 'lbf': 4.4482216152605,
              'tnf': 8896.443230521, 'sn': 1000.0}
    _descriptions = {'N': 'newton', 'dyn': 'dyne', 'kgf': 'kilogram-force',
                     'ozf': 'ounce-force', 'lbf': 'pound-force',
                     'tnf': 'ton-force', 'sn': 'sthene'}
    _sisig = {'kg': 1, 'm': 1, 's':-2}
    _mul = {}
    _div = {}


class Frequency(Quantity['Frequency']):
    _baseunit = 'Hz'
    _units = {'pHz': 1.0E-12, 'nHz': 1.0E-9, 'μHz': 1.0E-6, 'muHz': 1.0E-6,
              'mHz': 0.001, 'cHz': 0.01, 'dHz': 0.1, 'daHz': 10.0, 'hHz': 100.0,
              'kHz': 1000.0, 'MHz': 1000000.0, 'GHz': 1.0E9, 'THz': 1.0E12,
              'PHz': 1.0E15, 'Hz': 1.0, 'rpm': 0.01666666666666667,
              '/ys': 1.0E24, '/ysec': 1.0E24, '/zs': 1.0E21, '/zsec': 1.0E21,
              '/as': 1.0E18, '/asec': 1.0E18, '/fs': 1.0E15, '/fsec': 1.0E15,
              '/ps': 1.0E12, '/psec': 1.0E12, '/ns': 1.0E9, '/nsec': 1.0E9,
              '/μs': 1000000.0, '/mus': 1000000.0, '/musec': 1000000.0,
              '/μsec': 1000000.0, '/ms': 1000.0, '/msec': 1000.0,
              '/cs': 100.0, '/csec': 100.0, '/ds': 10.0, '/dsec': 10.0,
              '/das': 0.1, '/dasec': 0.1, '/hs': 0.01, '/hsec': 0.01,
              '/ks': 0.001, '/ksec': 0.001, '/Ms': 1.0E-6, '/Msec': 1.0E-6,
              '/Gs': 1.0E-9, '/Gsec': 1.0E-9, '/Ts': 1.0E-12,
              '/Tsec': 1.0E-12, '/Ps': 1.0E-15, '/Psec': 1.0E-15,
              '/Es': 1.0E-18, '/Esec': 1.0E-18, '/Zs': 1.0E-21,
              '/Zsec': 1.0E-21, '/Ys': 1.0E-24, '/Ysec': 1.0E-24, '/s': 1.0,
              '/sec': 1.0, '/min': 0.01666666666666667,
              '/h': 2.777777777777778E-4, '/hr': 2.777777777777778E-4,
              '/hour': 2.777777777777778E-4,
              '/day': 1.1574074074074073E-5, '/wk': 1.653439153439153E-6,
              '/week': 1.653439153439153E-6}
    _displayunits = {'muHz': 'μHz', '/ysec': '/ys', '/zsec': '/zs',
                     '/asec': '/as', '/fsec': '/fs', '/psec': '/ps',
                     '/nsec': '/ns', '/mus': '/μs', '/musec': '/μs',
                     '/μsec': '/μs', '/msec': '/ms', '/csec': '/cs',
                     '/dsec': '/ds', '/dasec': '/das', '/hsec': '/hs',
                     '/ksec': '/ks', '/Msec': '/Ms', '/Gsec': '/Gs',
                     '/Tsec': '/Ts', '/Psec': '/Ps', '/Esec': '/Es',
                     '/Zsec': '/Zs', '/Ysec': '/Ys', '/sec': '/s',
                     '/hr': '/h', '/hour': '/h', '/week': '/wk'}
    _descriptions = {'pHz': 'picohertz', 'nHz': 'nanohertz',
                     'μHz': 'microhertz', 'muHz': 'microhertz',
                     'mHz': 'millihertz', 'cHz': 'centihertz',
                     'dHz': 'decihertz', 'daHz': 'decahertz',
                     'hHz': 'hectohertz', 'kHz': 'kilohertz',
                     'MHz': 'megahertz', 'GHz': 'gigahertz',
                     'THz': 'terahertz', 'PHz': 'petahertz', 'Hz': 'hertz',
                     'rpm': 'revolutions per minute',
                     '/ys': 'per yoctosecond', '/ysec': 'per yoctosecond',
                     '/zs': 'per zeptosecond', '/zsec': 'per zeptosecond',
                     '/as': 'per attosecond', '/asec': 'per attosecond',
                     '/fs': 'per femtosecond', '/fsec': 'per femtosecond',
                     '/ps': 'per picosecond', '/psec': 'per picosecond',
                     '/ns': 'per nanosecond', '/nsec': 'per nanosecond',
                     '/μs': 'per microsecond', '/mus': 'per microsecond',
                     '/musec': 'per microsecond',
                     '/μsec': 'per microsecond', '/ms': 'per millisecond',
                     '/msec': 'per millisecond', '/cs': 'per centisecond',
                     '/csec': 'per centisecond', '/ds': 'per decisecond',
                     '/dsec': 'per decisecond', '/das': 'per decasecond',
                     '/dasec': 'per decasecond', '/hs': 'per hectosecond',
                     '/hsec': 'per hectosecond', '/ks': 'per kilosecond',
                     '/ksec': 'per kilosecond', '/Ms': 'per megasecond',
                     '/Msec': 'per megasecond', '/Gs': 'per gigasecond',
                     '/Gsec': 'per gigasecond', '/Ts': 'per terasecond',
                     '/Tsec': 'per terasecond', '/Ps': 'per petasecond',
                     '/Psec': 'per petasecond', '/Es': 'per exasecond',
                     '/Esec': 'per exasecond', '/Zs': 'per zettasecond',
                     '/Zsec': 'per zettasecond', '/Ys': 'per yottasecond',
                     '/Ysec': 'per yottasecond', '/s': 'per second',
                     '/sec': 'per second', '/min': 'per minute',
                     '/h': 'per hour', '/hr': 'per hour',
                     '/hour': 'per hour', '/day': 'per day',
                     '/wk': 'per week', '/week': 'per week'}
    _sisig = {'s':-1}
    _mul = {}
    _div = {}


class Length(Quantity['Length']):
    _baseunit = 'm'
    _units = {'pm': 1.0E-12, 'nm': 1.0E-9, 'μm': 1.0E-6, 'mum': 1.0E-6,
              'mm': 0.001, 'cm': 0.01, 'dm': 0.1, 'dam': 10.0, 'hm': 100.0,
              'km': 1000.0, 'Mm': 1000000.0, 'Gm': 1.0E9, 'Tm': 1.0E12,
              'Pm': 1.0E15, 'm': 1.0, 'ft': 0.3048, 'in': 0.0254, 'yd': 0.9144,
              'mi': 1609.344, 'NM': 1852.0, 'AU': 1.495978707E11,
              'ly': 9.4607304725808E15, 'Pc': 1.951415737882879E21,
              'Å': 1.0E-10, 'A': 1.0E-10}
    _displayunits = {'mum': 'μm', 'A': 'Å'}
    _descriptions = {'pm': 'picometer', 'nm': 'nanometer',
                     'μm': 'micrometer', 'mum': 'micrometer',
                     'mm': 'millimeter', 'cm': 'centimeter',
                     'dm': 'decimeter', 'dam': 'decameter',
                     'hm': 'hectometer', 'km': 'kilometer',
                     'Mm': 'megameter', 'Gm': 'gigameter',
                     'Tm': 'terameter', 'Pm': 'petameter', 'm': 'meter',
                     'ft': 'foot', 'in': 'inch', 'yd': 'yard', 'mi': 'mile',
                     'NM': 'nautical mile', 'AU': 'Astronomical Unit',
                     'ly': 'lightyear', 'Pc': 'Parsec', 'Å': 'Angstrom',
                     'A': 'Angstrom'}
    _sisig = {'m': 1}
    _mul = {}
    _div = {}


class LinearDensity(Quantity['LinearDensity']):
    _baseunit = '/m'
    _units = {'/ym': 1.0E24, '/zm': 1.0E21, '/am': 1.0E18, '/fm': 1.0E15,
              '/pm': 1.0E12, '/nm': 1.0E9, '/μm': 1000000.0,
              '/mum': 1000000.0, '/mm': 1000.0, '/cm': 100.0, '/dm': 10.0,
              '/dam': 0.1, '/hm': 0.01, '/km': 0.001, '/Mm': 1.0E-6,
              '/Gm': 1.0E-9, '/Tm': 1.0E-12, '/Pm': 1.0E-15, '/Em': 1.0E-18,
              '/Zm': 1.0E-21, '/Ym': 1.0E-24, '/m': 1.0,
              '/ft': 3.280839895013123, '/in': 39.37007874015748,
              '/yd': 1.0936132983377076, '/mi': 6.21371192237334E-4,
              '/NM': 5.399568034557236E-4, '/AU': 6.684587122268445E-12,
              '/ly': 1.0570008340246154E-16, '/pc': 5.124484652793234E-22,
              '/Å': 1.0E-10, '/A': 1.0E-10}
    _displayunits = {'/mum': '/μm', '/A': '/Å'}
    _descriptions = {'/ym': 'per yoctometer', '/zm': 'per zeptometer',
                     '/am': 'per attometer', '/fm': 'per femtometer',
                     '/pm': 'per picometer', '/nm': 'per nanometer',
                     '/μm': 'per micrometer', '/mum': 'per micrometer',
                     '/mm': 'per millimeter', '/cm': 'per centimeter',
                     '/dm': 'per decimeter', '/dam': 'per decameter',
                     '/hm': 'per hectometer', '/km': 'per kilometer',
                     '/Mm': 'per megameter', '/Gm': 'per gigameter',
                     '/Tm': 'per terameter', '/Pm': 'per petameter',
                     '/Em': 'per exameter', '/Zm': 'per zettameter',
                     '/Ym': 'per yottameter', '/m': 'per meter',
                     '/ft': 'per foot', '/in': 'per inch',
                     '/yd': 'per yard', '/mi': 'per mile',
                     '/NM': 'per Nautical Mile',
                     '/AU': 'per Astronomical Unit',
                     '/ly': 'per lightyear', '/pc': 'per parsec',
                     '/Å': 'per Angstrom', '/A': 'per Angstrom'}
    _sisig = {'m':-1}
    _mul = {}
    _div = {}


class Mass(Quantity['Mass']):
    _baseunit = 'kg'
    _units = {'pg': 1.0E-15, 'ng': 1.0E-12, 'μg': 1.0E-9, 'mug': 1.0E-9,
              'mg': 1.0E-6, 'cg': 1.0E-5, 'dg': 1.0E-4, 'g': 0.001, 'dag': 0.01,
              'hg': 0.1, 'Mg': 1000.0, 'Gg': 1000000.0, 'Tg': 1.0E9,
              'Pg': 1.0E12, 'kg': 1.0, 'lb': 0.45359237, 'oz': 0.028349523125,
              'long tn': 1016.0469088, 'sh tn': 907.18474, 't': 1000.0,
              't(mts)': 1000.0, 'Da': 1.6605388628E-27,
              'daeV': 1.782661907E-35, 'heV': 1.782661907E-34,
              'keV': 1.782661907E-33, 'MeV': 1.782661907E-30,
              'GeV': 1.782661907E-27, 'TeV': 1.782661907E-24,
              'PeV': 1.782661907E-21, 'eV': 1.782661907E-36,
              'μeV': 1.782661907E-42, 'mueV': 1.782661907E-42,
              'meV': 1.782661907E-39}
    _displayunits = {'mug': 'μg', 'mueV': 'μeV'}
    _descriptions = {'pg': 'picogram', 'ng': 'nanogram', 'μg': 'microgram',
                     'mug': 'microgram', 'mg': 'milligram',
                     'cg': 'centigram', 'dg': 'decigram', 'g': 'gram',
                     'dag': 'decagram', 'hg': 'hectogram', 'Mg': 'megagram',
                     'Gg': 'gigagram', 'Tg': 'teragram', 'Pg': 'petagram',
                     'kg': 'kilogram', 'lb': 'pound', 'oz': 'ounce',
                     'long tn': 'long ton', 'sh tn': 'short ton',
                     't': 'metric tonne', 't(mts)': 'tonne', 'Da': 'Dalton',
                     'daeV': 'decaelectronvolt',
                     'heV': 'hectoelectronvolt',
                     'keV': 'kiloelectronvolt', 'MeV': 'megaelectronvolt',
                     'GeV': 'gigaelectronvolt', 'TeV': 'teraelectronvolt',
                     'PeV': 'petaelectronvolt', 'eV': 'electronvolt',
                     'μeV': 'microelectronvolt',
                     'mueV': 'microelectronvolt',
                     'meV': 'millielectronvolt'}
    _sisig = {'kg': 1}
    _mul = {}
    _div = {}


class Momentum(Quantity['Momentum']):
    _baseunit = 'kgm/s'
    _units = {'kgm/s': 1.0, 'kgm/sec': 1.0}
    _displayunits = {'kgm/sec': 'kgm/s'}
    _descriptions = {'kgm/s': 'kilogram meter per second',
                     'kgm/sec': 'kilogram meter per second'}
    _sisig = {'kg': 1, 'm': 1, 's':-1}
    _mul = {}
    _div = {}


class Power(Quantity['Power']):
    _baseunit = 'W'
    _units = {'pW': 1.0E-12, 'nW': 1.0E-9, 'μW': 1.0E-6, 'muW': 1.0E-6,
              'mW': 0.001, 'cW': 0.01, 'dW': 0.1, 'daW': 10.0, 'hW': 100.0,
              'kW': 1000.0, 'MW': 1000000.0, 'GW': 1.0E9, 'TW': 1.0E12,
              'PW': 1.0E15, 'W': 1.0, 'ft.lbf/h': 3.766160967587223E-4,
              'ft.lbf/min': 0.02259696580552334,
              'ft.lbf/s': 1.3558179483314003, 'hp(M)': 735.49875,
              'sn.m/s': 1000.0, 'erg/s': 1.0E-7}
    _displayunits = {'muW': 'μW'}
    _descriptions = {'pW': 'picowatt', 'nW': 'nanowatt', 'μW': 'microwatt',
                     'muW': 'microwatt', 'mW': 'milliwatt',
                     'cW': 'centiwatt', 'dW': 'deciwatt', 'daW': 'decawatt',
                     'hW': 'hectowatt', 'kW': 'kilowatt', 'MW': 'megawatt',
                     'GW': 'gigawatt', 'TW': 'terawatt', 'PW': 'petawatt',
                     'W': 'watt', 'ft.lbf/h': 'foot pound-force per hour',
                     'ft.lbf/min': 'foot pound-force per minute',
                     'ft.lbf/s': 'foot pound-force per second',
                     'hp(M)': 'horsepower (metric)',
                     'sn.m/s': 'sthene-meter per second',
                     'erg/s': 'erg per second'}
    _sisig = {'kg': 1, 'm': 2, 's':-3}
    _mul = {}
    _div = {}


class Pressure(Quantity['Pressure']):
    _baseunit = 'Pa'
    _units = {'pPa': 1.0E-12, 'nPa': 1.0E-9, 'μPa': 1.0E-6, 'muPa': 1.0E-6,
              'mPa': 0.001, 'cPa': 0.01, 'dPa': 0.1, 'daPa': 10.0, 'hPa': 100.0,
              'kPa': 1000.0, 'MPa': 1000000.0, 'GPa': 1.0E9, 'TPa': 1.0E12,
              'PPa': 1.0E15, 'Pa': 1.0, 'atm': 101325.0,
              'torr': 133.3223684210526, 'at': 98066.5, 'Ba': 0.1,
              'bar': 100000.0, 'mbar': 100.0, 'cmHg': 1333.224,
              'mmHg': 133.3224, 'ftHg': 40636.66, 'inHg': 3386.389,
              'kgf/mm^2': 9806650.0, 'lbf/ft^2': 47.88025898033584,
              'lbf/in^2': 6894.75729316836, 'pz': 1000.0}
    _displayunits = {'muPa': 'μPa'}
    _descriptions = {'pPa': 'picopascal', 'nPa': 'nanopascal',
                     'μPa': 'micropascal', 'muPa': 'micropascal',
                     'mPa': 'millipascal', 'cPa': 'centipascal',
                     'dPa': 'decipascal', 'daPa': 'decapascal',
                     'hPa': 'hectopascal', 'kPa': 'kilopascal',
                     'MPa': 'megapascal', 'GPa': 'gigapascal',
                     'TPa': 'terapascal', 'PPa': 'petapascal',
                     'Pa': 'pascal', 'atm': 'atmosphere (standard)',
                     'torr': 'Torr', 'at': 'atmosphere (technical)',
                     'Ba': 'barye', 'bar': 'bar', 'mbar': 'millibar',
                     'cmHg': 'centimeter mercury',
                     'mmHg': 'millimeter mercury', 'ftHg': 'foot mercury',
                     'inHg': 'inch mercury',
                     'kgf/mm^2': 'kilogram-force per square millimeter',
                     'lbf/ft^2': 'pound-force per square foot',
                     'lbf/in^2': 'pound-force per square inch',
                     'pz': 'pièze'}
    _sisig = {'kg': 1, 'm':-1, 's':-2}
    _mul = {}
    _div = {}


class SolidAngle(Quantity['SolidAngle']):
    _baseunit = 'sr'
    _units = {'sr': 1.0, 'sq.deg': 3.046174197867086E-4}
    _displayunits = {'sr': 1.0, 'sq.deg': 3.046174197867086E-4}
    _descriptions = {'sr': 'steradian', 'sq.deg': 'square degree'}
    _sisig = {'sr': 1}
    _mul = {}
    _div = {}


class Speed(Quantity['Speed']):
    _baseunit = 'm/s'
    _units = {'m/s': 1.0, 'm/sec': 1.0, 'm/h': 2.777777777777778E-4,
              'm/hr': 2.777777777777778E-4,
              'm/hour': 2.777777777777778E-4, 'km/s': 1000.0,
              'km/sec': 1000.0, 'km/h': 0.2777777777777778,
              'km/hr': 0.2777777777777778, 'km/hour': 0.2777777777777778,
              'in/s': 0.0254, 'in/sec': 0.0254,
              'in/min': 4.233333333333334E-4,
              'in/h': 7.055555555555555E-6, 'in/hr': 7.055555555555555E-6,
              'in/hour': 7.055555555555555E-6, 'ft/s': 0.3048,
              'ft/sec': 0.3048, 'ft/min': 0.00508,
              'ft/h': 8.466666666666667E-5, 'ft/hr': 8.466666666666667E-5,
              'ft/hour': 8.466666666666667E-5, 'mi/s': 1609.344,
              'mi/sec': 1609.344, 'mi/min': 26.8224, 'mi/h': 0.44704,
              'mi/hr': 0.44704, 'mi/hour': 0.44704,
              'kt': 0.5144444444444445}
    _displayunits = {'m/sec': 'm/s', 'm/hr': 'm/h', 'm/hour': 'm/h',
                     'km/sec': 'km/s', 'km/hr': 'km/h', 'km/hour': 'km/h',
                     'in/sec': 'in/s', 'in/hr': 'in/h', 'in/hour': 'in/h',
                     'ft/sec': 'ft/s', 'ft/hr': 'ft/h', 'ft/hour': 'ft/h',
                     'mi/sec': 'mi/s', 'mi/hr': 'mi/h', 'mi/hour': 'mi/h'}
    _descriptions = {'m/s': 'meter per second',
                     'm/sec': 'meter per second', 'm/h': 'meter per hour',
                     'm/hr': 'meter per hour', 'm/hour': 'meter per hour',
                     'km/s': 'kilometer per second',
                     'km/sec': 'kilometer per second',
                     'km/h': 'kilometer per hour',
                     'km/hr': 'kilometer per hour',
                     'km/hour': 'kilometer per hour',
                     'in/s': 'inch per second',
                     'in/sec': 'inch per second',
                     'in/min': 'inch per minute', 'in/h': 'inch per hour',
                     'in/hr': 'inch per hour', 'in/hour': 'inch per hour',
                     'ft/s': 'foot per second',
                     'ft/sec': 'foot per second',
                     'ft/min': 'inch per minute', 'ft/h': 'foot per hour',
                     'ft/hr': 'foot per hour', 'ft/hour': 'foot per hour',
                     'mi/s': 'mile per second',
                     'mi/sec': 'mile per second',
                     'mi/min': 'mile per minute', 'mi/h': 'mile per hour',
                     'mi/hr': 'mile per hour', 'mi/hour': 'mile per hour',
                     'kt': 'knot'}
    _sisig = {'m': 1, 's':-1}
    _mul = {}
    _div = {}


class Temperature(Quantity['Temperature']):
    _baseunit = 'K'
    _units = {'pK': 1.0E-12, 'nK': 1.0E-9, 'μK': 1.0E-6, 'muK': 1.0E-6,
              'mK': 0.001, 'cK': 0.01, 'dK': 0.1, 'daK': 10.0, 'hK': 100.0,
              'kK': 1000.0, 'MK': 1000000.0, 'GK': 1.0E9, 'TK': 1.0E12,
              'PK': 1.0E15, 'K': 1.0, '°C': 1.0, 'degC': 1.0, 'C': 1.0,
              '°F': 0.5555555555555556, 'degF': 0.5555555555555556,
              'F': 0.5555555555555556, '°R': 0.5555555555555556,
              'degR': 0.5555555555555556, 'R': 0.5555555555555556,
              '°Ré': 0.8, 'degRe': 0.8, 'Re': 0.8, 'Ré': 0.8}
    _displayunits = {'muK': 'μK', 'degC': '°C', 'C': '°C', 'degF': '°F',
                     'F': '°F', 'degR': '°R', 'R': '°R', 'degRe': '°Ré',
                     'Re': '°Ré', 'Ré': '°Ré'}
    _descriptions = {'pK': 'picoKelvin', 'nK': 'nanoKelvin',
                     'μK': 'microKelvin', 'muK': 'microKelvin',
                     'mK': 'milliKelvin', 'cK': 'centiKelvin',
                     'dK': 'deciKelvin', 'daK': 'decaKelvin',
                     'hK': 'hectoKelvin', 'kK': 'kiloKelvin',
                     'MK': 'megaKelvin', 'GK': 'gigaKelvin',
                     'TK': 'teraKelvin', 'PK': 'petaKelvin', 'K': 'Kelvin',
                     '°C': 'degree Celcius', 'degC': 'degree Celcius',
                     'C': 'degree Celcius', '°F': 'degree Fahrenheit',
                     'degF': 'degree Fahrenheit',
                     'F': 'degree Fahrenheit', '°R': 'degree Rankine',
                     'degR': 'degree Rankine', 'R': 'degree Rankine',
                     '°Ré': 'degree Reaumur', 'degRe': 'degree Reaumur',
                     'Re': 'degree Reaumur', 'Ré': 'degree Reaumur'}
    _sisig = {'K': 1}
    _mul = {}
    _div = {}


class Torque(Quantity['Torque']):
    _baseunit = 'N.m'
    _units = {'N.m': 1.0, 'm.kgf': 9.80665, 'lbf.ft': 1.3558179483314003,
              'lbf.in': 0.1129848290276167}
    _displayunits = {'N.m': 1.0, 'm.kgf': 9.80665, 'lbf.ft': 1.3558179483314003,
              'lbf.in': 0.1129848290276167}
    _descriptions = {'N.m': 'Newton meter',
                     'm.kgf': 'meter kilogram-force',
                     'lbf.ft': 'pound-foot', 'lbf.in': 'pound-inch'}
    _sisig = {'kg': 1, 'm': 2, 's':-2}
    _mul = {}
    _div = {}


class Volume(Quantity['Volume']):
    _baseunit = 'm^3'
    _units = {'pm^3': 1.0E-36, 'nm^3': 1.0E-27, 'μm^3': 1.0E-18,
              'mum^3': 1.0E-18, 'mm^3': 1.0E-9, 'cm^3': 1.0E-6, 'dm^3': 0.001,
              'dam^3': 1000.0, 'hm^3': 1000000.0, 'km^3': 1.0E9,
              'Mm^3': 1.0E18, 'Gm^3': 1.0E27, 'Tm^3': 1.0E36, 'Pm^3': 1.0E45,
              'm^3': 1.0, 'mi^3': 4.16818182544058E9, 'NM^3': 6.352182208E9,
              'ft^3': 0.028316846592, 'in^3': 1.6387064E-5,
              'yd^3': 0.7645548579840002, 'L': 0.001,
              'gal(US)': 0.003785411784, 'gal(imp)': 0.00454609,
              'qt(US)': 9.46352946E-4, 'qt(imp)': 0.0011365225,
              'pt(US)': 4.73176473E-4, 'pt(imp)': 5.6826125E-4,
              'fl.oz(US)': 2.95735295625E-5,
              'fl.oz(imp)': 2.841306250000001E-5,
              'ly^3': 8.46786664623715E47, 'pc^3': 7.43103675797198E63}
    _displayunits = {'mum^3': 'μm^3'}
    _descriptions = {'pm^3': 'cubic pico meter',
                     'nm^3': 'cubic nano meter',
                     'μm^3': 'cubic micro meter',
                     'mum^3': 'cubic micro meter',
                     'mm^3': 'cubic millimeter',
                     'cm^3': 'cubic centimeter',
                     'dm^3': 'cubic decimeter',
                     'dam^3': 'cubic decameter',
                     'hm^3': 'cubic hectometer',
                     'km^3': 'cubic kilometer',
                     'Mm^3': 'cubic mega meter',
                     'Gm^3': 'cubic giga meter',
                     'Tm^3': 'cubic tera meter',
                     'Pm^3': 'cubic peta meter', 'm^3': 'cubic meter',
                     'mi^3': 'cubic mile', 'NM^3': 'cubic Nautical Mile',
                     'ft^3': 'cubic foot', 'in^3': 'cubic inch',
                     'yd^3': 'cubic yard', 'L': 'liter',
                     'gal(US)': 'gallon (US)', 'gal(imp)': 'gallon (imp)',
                     'qt(US)': 'quart (US)', 'qt(imp)': 'quart (imp)',
                     'pt(US)': 'pint (US)', 'pt(imp)': 'pint (imp)',
                     'fl.oz(US)': 'fluid ounce (US)',
                     'fl.oz(imp)': 'fluid ounce (imp)',
                     'ly^3': 'cubic lightyear', 'pc^3': 'cubic Parsec'}
    _sisig = {'m': 3}
    _mul = {}
    _div = {}


class AbsorbedDose(Quantity['AbsorbedDose']):
    _baseunit = 'Gy'
    _units = {'pGy': 1.0E-12, 'nGy': 1.0E-9, 'μGy': 1.0E-6, 'muGy': 1.0E-6,
              'mGy': 0.001, 'cGy': 0.01, 'dGy': 0.1, 'daGy': 10.0, 'hGy': 100.0,
              'kGy': 1000.0, 'MGy': 1000000.0, 'GGy': 1.0E9, 'TGy': 1.0E12,
              'PGy': 1.0E15, 'Gy': 1.0, 'erg/g': 1.0E-4, 'rad': 0.01}
    _displayunits = {'muGy': 'μGy'}
    _descriptions = {'pGy': 'picogray', 'nGy': 'nanogray',
                     'μGy': 'microgray', 'muGy': 'microgray',
                     'mGy': 'milligray', 'cGy': 'centigray',
                     'dGy': 'decigray', 'daGy': 'decagray',
                     'hGy': 'hectogray', 'kGy': 'kilogray',
                     'MGy': 'megagray', 'GGy': 'gigagray',
                     'TGy': 'teragray', 'PGy': 'petagray', 'Gy': 'gray',
                     'erg/g': 'erg per gram', 'rad': 'rad'}
    _sisig = {'m': 2, 's':-2}
    _mul = {}
    _div = {}


class AmountOfSubstance(Quantity['AmountOfSubstance']):
    _baseunit = 'mol'
    _units = {'pmol': 1.0E-12, 'nmol': 1.0E-9, 'μmol': 1.0E-6,
              'mumol': 1.0E-6, 'mmol': 0.001, 'cmol': 0.01, 'dmol': 0.1,
              'damol': 10.0, 'hmol': 100.0, 'kmol': 1000.0, 'Mmol': 1000000.0,
              'Gmol': 1.0E9, 'Tmol': 1.0E12, 'Pmol': 1.0E15, 'mol': 1.0}
    _displayunits = {'mumol': 'μmol'}
    _descriptions = {'pmol': 'picomole', 'nmol': 'nanomole',
                     'μmol': 'micromole', 'mumol': 'micromole',
                     'mmol': 'millimole', 'cmol': 'centimole',
                     'dmol': 'decimole', 'damol': 'decamole',
                     'hmol': 'hectomole', 'kmol': 'kilomole',
                     'Mmol': 'megamole', 'Gmol': 'gigamole',
                     'Tmol': 'teramole', 'Pmol': 'petamole', 'mol': 'mole'}
    _sisig = {'mol': 1}
    _mul = {}
    _div = {}


class CatalyticActivity(Quantity['CatalyticActivity']):
    _baseunit = 'kat'
    _units = {'pkat': 1.0E-12, 'nkat': 1.0E-9, 'μkat': 1.0E-6,
              'mukat': 1.0E-6, 'mkat': 0.001, 'ckat': 0.01, 'dkat': 0.1,
              'dakat': 10.0, 'hkat': 100.0, 'kkat': 1000.0, 'Mkat': 1000000.0,
              'Gkat': 1.0E9, 'Tkat': 1.0E12, 'Pkat': 1.0E15, 'kat': 1.0}
    _displayunits = {'mukat': 'μkat'}
    _descriptions = {'pkat': 'picokatal', 'nkat': 'nanokatal',
                     'μkat': 'microkatal', 'mukat': 'microkatal',
                     'mkat': 'millikatal', 'ckat': 'centikatal',
                     'dkat': 'decikatal', 'dakat': 'decakatal',
                     'hkat': 'hectokatal', 'kkat': 'kilokatal',
                     'Mkat': 'megakatal', 'Gkat': 'gigakatal',
                     'Tkat': 'terakatal', 'Pkat': 'petakatal',
                     'kat': 'katal'}
    _sisig = {'s':-1, 'mol': 1}
    _mul = {}
    _div = {}


class ElectricalCapacitance(Quantity['ElectricalCapacitance']):
    _baseunit = 'F'
    _units = {'pF': 1.0E-12, 'nF': 1.0E-9, 'uF': 1.0E-6, 'μF': 1.0E-6,
              'muF': 1.0E-6, 'mF': 0.001, 'cF': 0.01, 'dF': 0.1, 'daF': 10.0,
              'hF': 100.0, 'kF': 1000.0, 'MF': 1000000.0, 'GF': 1.0E9,
              'TF': 1.0E12, 'PF': 1.0E15, 'F': 1.0}
    _displayunits = {'μF': 'uF', 'muF': 'uF'}
    _descriptions = {'pF': 'picofarad', 'nF': 'nanofarad',
                     'uF': 'microfarad', 'μF': 'microfarad',
                     'muF': 'microfarad', 'mF': 'millifarad',
                     'cF': 'centifarad', 'dF': 'decifarad',
                     'daF': 'decafarad', 'hF': 'hectofarad',
                     'kF': 'kilofarad', 'MF': 'megafarad',
                     'GF': 'gigafarad', 'TF': 'terafarad',
                     'PF': 'petafarad', 'F': 'farad'}
    _sisig = {'kg':-1, 'm':-2, 's': 4, 'A': 2}
    _mul = {}
    _div = {}


class ElectricalConductance(Quantity['ElectricalConductance']):
    _baseunit = 'S'
    _units = {'pS': 1.0E-12, 'nS': 1.0E-9, 'muS': 1.0E-6, 'μS': 1.0E-6,
              'mS': 0.001, 'cS': 0.01, 'dS': 0.1, 'daS': 10.0, 'hS': 100.0,
              'kS': 1000.0, 'MS': 1000000.0, 'GS': 1.0E9, 'TS': 1.0E12,
              'PS': 1.0E15, 'S': 1.0}
    _displayunits = {'μS': 'muS'}
    _descriptions = {'pS': 'picosiemens', 'nS': 'nanosiemens',
                     'muS': 'microsiemens', 'μS': 'microsiemens',
                     'mS': 'millisiemens', 'cS': 'centisiemens',
                     'dS': 'decisiemens', 'daS': 'decasiemens',
                     'hS': 'hectosiemens', 'kS': 'kilosiemens',
                     'MS': 'megasiemens', 'GS': 'gigasiemens',
                     'TS': 'terasiemens', 'PS': 'petasiemens',
                     'S': 'siemens'}
    _sisig = {'kg':-1, 'm':-2, 's': 3, 'A': 2}
    _mul = {}
    _div = {}


class ElectricalInductance(Quantity['ElectricalInductance']):
    _baseunit = 'H'
    _units = {'pH': 1.0E-12, 'nH': 1.0E-9, 'muH': 1.0E-6, 'μH': 1.0E-6,
              'mH': 0.001, 'cH': 0.01, 'dH': 0.1, 'daH': 10.0, 'hH': 100.0,
              'kH': 1000.0, 'MH': 1000000.0, 'GH': 1.0E9, 'TH': 1.0E12,
              'PH': 1.0E15, 'H': 1.0}
    _displayunits = {'μH': 'muH'}
    _descriptions = {'pH': 'picohenry', 'nH': 'nanohenry',
                     'muH': 'microhenry', 'μH': 'microhenry',
                     'mH': 'millihenry', 'cH': 'centihenry',
                     'dH': 'decihenry', 'daH': 'decahenry',
                     'hH': 'hectohenry', 'kH': 'kilohenry',
                     'MH': 'megahenry', 'GH': 'gigahenry',
                     'TH': 'terahenry', 'PH': 'petahenry', 'H': 'henry'}
    _sisig = {'kg': 1, 'm': 2, 's':-2, 'A':-2}
    _mul = {}
    _div = {}


class EquivalentDose(Quantity['EquivalentDose']):
    _baseunit = 'Sv'
    _units = {'pSv': 1.0E-12, 'nSv': 1.0E-9, 'μSv': 1.0E-6, 'muSv': 1.0E-6,
              'mSv': 0.001, 'cSv': 0.01, 'dSv': 0.1, 'daSv': 10.0, 'hSv': 100.0,
              'kSv': 1000.0, 'MSv': 1000000.0, 'GSv': 1.0E9, 'TSv': 1.0E12,
              'PSv': 1.0E15, 'Sv': 1.0, 'rem': 0.01}
    _displayunits = {'muSv': 'μSv'}
    _descriptions = {'pSv': 'picosievert', 'nSv': 'nanosievert',
                     'μSv': 'microsievert', 'muSv': 'microsievert',
                     'mSv': 'millisievert', 'cSv': 'centisievert',
                     'dSv': 'decisievert', 'daSv': 'decasievert',
                     'hSv': 'hectosievert', 'kSv': 'kilosievert',
                     'MSv': 'megasievert', 'GSv': 'gigasievert',
                     'TSv': 'terasievert', 'PSv': 'petasievert',
                     'Sv': 'sievert', 'rem': 'rem'}
    _sisig = {'m': 2, 's':-2}
    _mul = {}
    _div = {}


class Illuminance(Quantity['Illuminance']):
    _baseunit = 'lx'
    _units = {'plx': 1.0E-12, 'nlx': 1.0E-9, 'mulx': 1.0E-6, 'μlx': 1.0E-6,
              'mlx': 0.001, 'clx': 0.01, 'dlx': 0.1, 'dalx': 10.0, 'hlx': 100.0,
              'klx': 1000.0, 'Mlx': 1000000.0, 'Glx': 1.0E9, 'Tlx': 1.0E12,
              'Plx': 1.0E15, 'lx': 1.0, 'ph': 10000.0, 'nx': 0.001}
    _displayunits = {'μlx': 'mulx'}
    _descriptions = {'plx': 'picolux', 'nlx': 'nanolux', 'mulx': 'microlux',
                     'μlx': 'microlux', 'mlx': 'millilux',
                     'clx': 'centilux', 'dlx': 'decilux', 'dalx': 'decalux',
                     'hlx': 'hectolux', 'klx': 'kilolux', 'Mlx': 'megalux',
                     'Glx': 'gigalux', 'Tlx': 'teralux', 'Plx': 'petalux',
                     'lx': 'lux', 'ph': 'phot', 'nx': 'nox'}
    _sisig = {'sr': 1, 'm':-2, 'cd': 1}
    _mul = {}
    _div = {}


class LuminousFlux(Quantity['LuminousFlux']):
    _baseunit = 'lm'
    _units = {'plm': 1.0E-12, 'nlm': 1.0E-9, 'μlm': 1.0E-6, 'mulm': 1.0E-6,
              'mlm': 0.001, 'clm': 0.01, 'dlm': 0.1, 'dalm': 10.0, 'hlm': 100.0,
              'klm': 1000.0, 'Mlm': 1000000.0, 'Glm': 1.0E9, 'Tlm': 1.0E12,
              'Plm': 1.0E15, 'lm': 1.0}
    _displayunits = {'mulm': 'μlm'}
    _descriptions = {'plm': 'picolumen', 'nlm': 'nanolumen',
                     'μlm': 'microlumen', 'mulm': 'microlumen',
                     'mlm': 'millilumen', 'clm': 'centilumen',
                     'dlm': 'decilumen', 'dalm': 'decalumen',
                     'hlm': 'hectolumen', 'klm': 'kilolumen',
                     'Mlm': 'megalumen', 'Glm': 'gigalumen',
                     'Tlm': 'teralumen', 'Plm': 'petalumen', 'lm': 'lumen'}
    _sisig = {'sr': 1, 'cd': 1}
    _mul = {}
    _div = {}


class LuminousIntensity(Quantity['LuminousIntensity']):
    _baseunit = 'cd'
    _units = {'pcd': 1.0E-12, 'ncd': 1.0E-9, 'μcd': 1.0E-6, 'mucd': 1.0E-6,
              'mcd': 0.001, 'ccd': 0.01, 'dcd': 0.1, 'dacd': 10.0, 'hcd': 100.0,
              'kcd': 1000.0, 'Mcd': 1000000.0, 'Gcd': 1.0E9, 'Tcd': 1.0E12,
              'Pcd': 1.0E15, 'cd': 1.0}
    _displayunits = {'mucd': 'μcd'}
    _descriptions = {'pcd': 'picocandela', 'ncd': 'nanocandela',
                     'μcd': 'microcandela', 'mucd': 'microcandela',
                     'mcd': 'millicandela', 'ccd': 'centicandela',
                     'dcd': 'decicandela', 'dacd': 'decacandela',
                     'hcd': 'hectocandela', 'kcd': 'kilocandela',
                     'Mcd': 'megacandela', 'Gcd': 'gigacandela',
                     'Tcd': 'teracandela', 'Pcd': 'petacandela',
                     'cd': 'candela'}
    _sisig = {'cd': 1}
    _mul = {}
    _div = {}


class MagneticFluxDensity(Quantity['MagneticFluxDensity']):
    _baseunit = 'T'
    _units = {'pT': 1.0E-12, 'nT': 1.0E-9, 'muT': 1.0E-6, 'μT': 1.0E-6,
              'mT': 0.001, 'cT': 0.01, 'dT': 0.1, 'daT': 10.0, 'hT': 100.0,
              'kT': 1000.0, 'MT': 1000000.0, 'GT': 1.0E9, 'TT': 1.0E12,
              'PT': 1.0E15, 'T': 1.0, 'G': 1.0E-4}
    _displayunits = {'μT': 'muT'}
    _descriptions = {'pT': 'picotesla', 'nT': 'nanotesla',
                     'muT': 'microtesla', 'μT': 'microtesla',
                     'mT': 'millitesla', 'cT': 'centitesla',
                     'dT': 'decitesla', 'daT': 'decatesla',
                     'hT': 'hectotesla', 'kT': 'kilotesla',
                     'MT': 'megatesla', 'GT': 'gigatesla',
                     'TT': 'teratesla', 'PT': 'petatesla', 'T': 'tesla',
                     'G': 'Gauss'}
    _sisig = {'kg': 1, 's':-2, 'A':-1}
    _mul = {}
    _div = {}


class MagneticFlux(Quantity['MagneticFlux']):
    _baseunit = 'Wb'
    _units = {'pWb': 1.0E-12, 'nWb': 1.0E-9, 'muWb': 1.0E-6, 'μWb': 1.0E-6,
              'mWb': 0.001, 'cWb': 0.01, 'dWb': 0.1, 'daWb': 10.0, 'hWb': 100.0,
              'kWb': 1000.0, 'MWb': 1000000.0, 'GWb': 1.0E9, 'TWb': 1.0E12,
              'PWb': 1.0E15, 'Wb': 1.0, 'Mx': 1.0E-8}
    _displayunits = {'μWb': 'muWb'}
    _descriptions = {'pWb': 'picoweber', 'nWb': 'nanoweber',
                     'muWb': 'microweber', 'μWb': 'microweber',
                     'mWb': 'milliweber', 'cWb': 'centiweber',
                     'dWb': 'deciweber', 'daWb': 'decaweber',
                     'hWb': 'hectoweber', 'kWb': 'kiloweber',
                     'MWb': 'megaweber', 'GWb': 'gigaweber',
                     'TWb': 'teraweber', 'PWb': 'petaweber', 'Wb': 'weber',
                     'Mx': 'Maxwell'}
    _sisig = {'kg': 1, 'm': 2, 's':-2, 'A':-1}
    _mul = {}
    _div = {}


class RadioActivity(Quantity['RadioActivity']):
    _baseunit = 'Bq'
    _units = {'daBq': 10.0, 'hBq': 100.0, 'kBq': 1000.0, 'MBq': 1000000.0,
              'GBq': 1.0E9, 'TBq': 1.0E12, 'PBq': 1.0E15, 'Bq': 1.0,
              'Ci': 3.7E10, 'mCi': 3.7E7, 'muCi': 37000.0, 'μCi': 37000.0,
              'nCi': 37.0, 'Rd': 1000000.0}
    _displayunits = {'μCi': 'muCi'}
    _descriptions = {'daBq': 'decabecquerel', 'hBq': 'hectobecquerel',
                     'kBq': 'kilobequerel', 'MBq': 'megabequerel',
                     'GBq': 'gigabequerel', 'TBq': 'terabequerel',
                     'PBq': 'petabequerel', 'Bq': 'becquerel',
                     'Ci': 'curie', 'mCi': 'millicurie',
                     'muCi': 'microcurie', 'μCi': 'microcurie',
                     'nCi': 'nanocurie', 'Rd': 'rutherford'}
    _sisig = {'s':-1}
    _mul = {}
    _div = {}

# -----------------------------------------------------------------------------
# Multiplication and division of units to create new units
# -----------------------------------------------------------------------------


QUANTITIES = [Acceleration, Angle, AngularAcceleration, AngularVelocity,
              Area, Density, Dimensionless, Duration, ElectricalCharge,
              ElectricalCurrent, ElectricalPotential, ElectricalResistance,
              Energy, FlowMass, FlowVolume, Force, Frequency, Length,
              LinearDensity, Mass, Momentum, Power, Pressure, SolidAngle,
              Speed, Temperature, Torque, Volume, AbsorbedDose,
              AmountOfSubstance, CatalyticActivity, ElectricalCapacitance,
              ElectricalConductance, ElectricalInductance, EquivalentDose,
              Illuminance, LuminousFlux, LuminousIntensity,
              MagneticFluxDensity, MagneticFlux, RadioActivity]

AbsorbedDose._mul = {}
AbsorbedDose._div = {}

Acceleration._mul = {Mass: Force, Duration: Speed, Momentum: Power}
Acceleration._div = {Frequency: Speed, Speed: Frequency}

AngularVelocity._mul = {Duration: Angle, Frequency: AngularAcceleration}
AngularVelocity._div = {Angle: Frequency, Frequency: Angle,
        Duration: AngularAcceleration, AngularAcceleration: Duration}

AngularAcceleration._mul = {Duration: AngularVelocity}
AngularAcceleration._div = {Frequency: AngularVelocity,
        AngularVelocity: Frequency}

AmountOfSubstance._mul = {}
AmountOfSubstance._div = {CatalyticActivity: Duration,
        Duration: CatalyticActivity}

Angle._mul = {Frequency: AngularVelocity}
Angle._div = {Duration: AngularVelocity, AngularVelocity: Duration}

SolidAngle._mul = {LuminousIntensity: LuminousFlux}
SolidAngle._div = {}

Area._mul = {Length: Volume, LinearDensity: Length, Speed: FlowVolume,
        Pressure: Force, Illuminance: LuminousFlux}
Area._div = {LinearDensity: Volume, Volume: LinearDensity, Length: Length}

CatalyticActivity._mul = {Duration: AmountOfSubstance}
CatalyticActivity._div = {AmountOfSubstance: Frequency,
        Frequency: AmountOfSubstance}

Density._mul = {Volume: Mass, FlowVolume: FlowMass}
Density._div = {}

Duration._mul = {ElectricalCurrent: ElectricalCharge, FlowMass: Mass,
        FlowVolume: Volume, Acceleration: Speed, Power: Energy,
        Speed: Length, ElectricalPotential: MagneticFlux,
        ElectricalResistance: ElectricalInductance,
        ElectricalConductance: ElectricalCapacitance, AngularVelocity: Angle,
        AngularAcceleration: AngularVelocity}
Duration._div = {}

ElectricalCapacitance._mul = {ElectricalPotential: ElectricalCharge}
ElectricalCapacitance._div = {Duration: ElectricalConductance,
        ElectricalConductance: Duration}

ElectricalCharge._mul = {}
ElectricalCharge._div = {Duration: ElectricalCurrent,
        ElectricalCurrent: Duration,
        ElectricalPotential: ElectricalCapacitance,
        ElectricalCapacitance: ElectricalPotential}

ElectricalConductance._mul = {ElectricalPotential: ElectricalCurrent,
        Duration: ElectricalCapacitance}
ElectricalConductance._div = {}

ElectricalCurrent._mul = {ElectricalPotential: Power,
        Duration: ElectricalCharge,
        ElectricalResistance: ElectricalPotential}
ElectricalCurrent._div = {ElectricalPotential: ElectricalConductance,
        ElectricalConductance: ElectricalPotential}

ElectricalInductance._mul = {ElectricalCurrent: MagneticFlux}
ElectricalInductance._div = {}

ElectricalPotential._mul = {ElectricalCurrent: Power, Duration: MagneticFlux}
ElectricalPotential._div = {ElectricalCurrent: ElectricalResistance,
        ElectricalResistance: ElectricalCurrent}

ElectricalResistance._mul = {ElectricalCurrent: ElectricalPotential,
        Duration: ElectricalInductance}
ElectricalResistance._div = {}

Energy._mul = {LinearDensity: Force, Frequency: Power}
Energy._div = {Force: Length, Length: Force, Duration: Power,
        Power: Duration, Volume: Pressure, Pressure: Volume, Speed: Momentum,
        Momentum: Speed}

EquivalentDose._mul = {}
EquivalentDose._div = {}

FlowMass._mul = {Duration: Mass, Speed: Force, Length: Momentum}
FlowMass._div = {Frequency: Mass, Mass: Frequency, FlowVolume: Density,
        Density: FlowVolume}

FlowVolume._mul = {Duration: Volume, Density: FlowMass}
FlowVolume._div = {Frequency: Volume, Volume: Frequency, Area: Speed,
        Speed: Area}

Force._mul = {Length: Energy, Speed: Power}
Force._div = {LinearDensity: Energy, Energy: LinearDensity,
        Mass: Acceleration, Acceleration: Mass, Area: Pressure,
        Pressure: Area}

Frequency._mul = {Length: Speed, Speed: Acceleration, Energy: Power,
        Angle: AngularVelocity, AngularVelocity: AngularAcceleration}
Frequency._div = {}

Illuminance._mul = {Area: LuminousFlux}
Illuminance._div = {}

Length._mul = {Length: Area, Area: Volume, Force: Energy, Frequency: Speed,
        FlowMass: Momentum}
Length._div = {LinearDensity: Area, Area: LinearDensity, Duration: Speed,
        Speed: Duration}

LinearDensity._mul = {Area: Length, Energy: Force, Speed: Frequency}
LinearDensity._div = {}

LuminousFlux._mul = {}
LuminousFlux._div = {Area: Illuminance, Illuminance: Area,
        LuminousIntensity: SolidAngle, SolidAngle: LuminousIntensity}

LuminousIntensity._mul = {SolidAngle: LuminousFlux}
LuminousIntensity._div = {}

MagneticFluxDensity._mul = {Area: MagneticFlux}
MagneticFluxDensity._div = {}

MagneticFlux._mul = {}
MagneticFlux._div = {ElectricalPotential: Duration,
        Duration: ElectricalPotential, Area: MagneticFluxDensity,
        MagneticFluxDensity: Area, ElectricalCurrent: ElectricalInductance,
        ElectricalInductance: ElectricalCurrent}

Mass._mul = {Acceleration: Force, Frequency: FlowMass, Speed: Momentum}
Mass._div = {FlowMass: Duration, Duration: FlowMass, Density: Volume,
        Volume: Density}

Momentum._mul = {Speed: Energy, Acceleration: Power}
Momentum._div = {Speed: Mass, Mass: Speed, Length: FlowMass,
        FlowMass: Length}

Power._mul = {Duration: Energy}
Power._div = {Frequency: Energy, Energy: Frequency, Speed: Force,
        Force: Speed, ElectricalPotential: ElectricalCurrent,
        ElectricalCurrent: ElectricalPotential, Acceleration: Momentum,
        Momentum: Acceleration}

Pressure._mul = {Area: Force, Volume: Energy}
Pressure._div = {}

RadioActivity._mul = {}
RadioActivity._div = {}

Speed._mul = {Area: FlowVolume, Force: Power, Frequency: Acceleration,
        LinearDensity: Frequency, Duration: Length, FlowMass: Force,
        Mass: Momentum, Momentum: Energy}
Speed._div = {Length: Frequency, Frequency: Length, Duration: Acceleration,
        Acceleration: Duration}

Temperature._mul = {}
Temperature._div = {}

Torque._mul = {LinearDensity: Force, Frequency: Power}
Torque._div = {Force: Length, Length: Force, Duration: Power,
        Power: Duration, Volume: Pressure, Pressure: Volume}

Volume._mul = {Density: Mass, Pressure: Energy, LinearDensity: Area}
Volume._div = {Length: Area, Area: Length, Duration: FlowVolume,
        FlowVolume: Duration}

Dimensionless._mul = {q: q for q in QUANTITIES}
Dimensionless._div = {Duration: Frequency, Frequency: Duration}

for q in QUANTITIES:
    q._mul[Dimensionless] = q
    q._div[Dimensionless] = q
    q._div[q] = Dimensionless

