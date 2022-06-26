"""
Test the classes that represent quantities and units in the units module
""" 

import pytest

from pydsol.core.utils import Assert, DSOLError


def test_assert():
    s = "abc"
    f = 4.0
    Assert.istype(s, 's', str)
    Assert.istype(f, 'f', float)
    with pytest.raises(DSOLError, match="parameter s is not of type int"):
        Assert.istype(s, 's', int)
    Assert.subtype(s, 's', str)
    with pytest.raises(DSOLError,
            match="parameter s is not an instance of int"):
        Assert.subtype(s, 's', int)
    Assert.anytype(f, 'f', [float, int])
    with pytest.raises(DSOLError,
            match="parameter s is not an instance of \\['int', 'float'\\]"):
        Assert.anytype(s, 's', [int, float])
    Assert.that(f == 4.0, DSOLError, "f should be 4")
    with pytest.raises(DSOLError, match="f should be 3"):
        Assert.that(f == 3.0, DSOLError, "f should be 3")

    Assert.istype(f, 'f', float, TypeError)
    with pytest.raises(TypeError, match="parameter s is not of type int"):
        Assert.istype(s, 's', int, TypeError)
    Assert.subtype(s, 's', str, TypeError)
    with pytest.raises(TypeError,
            match="parameter s is not an instance of int"):
        Assert.subtype(s, 's', int, TypeError)
    Assert.anytype(f, 'f', [float, int], TypeError)
    with pytest.raises(TypeError,
            match="parameter s is not an instance of \\['int', 'float'\\]"):
        Assert.anytype(s, 's', [int, float], TypeError)
    Assert.that(f == 4.0, TypeError, "f should be 4")
    with pytest.raises(TypeError, match="f should be 3"):
        Assert.that(f == 3.0, TypeError, "f should be 3")


if __name__ == '__main__':
    pytest.main()
