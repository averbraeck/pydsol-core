"""
Test the classes in the utils module
""" 

import pytest
from pydsol.core.utils import DSOLError, sign, erf_inv, beta
import math


def test_sign():
    assert sign(10) == 1.0
    assert sign(-0.2) == -1.0
    assert sign(0.0) == 0.0
    assert math.isnan(sign(math.nan))
    assert sign(math.inf) == 1.0
    assert sign(-math.inf) == -1.0

    
def test_erf_inv():
    assert math.isclose(erf_inv(0.5), 0.47693672, abs_tol=0.0001)
    assert math.isinf(erf_inv(1.0))
    assert math.isinf(erf_inv(-1.0))
    assert erf_inv(0.0) == 0.0
    test_wikipedia = (0.02, 0.022564575, 0.04, 0.045111106, 0.06, 0.067621594,
                      0.08, 0.090078126, 0.1, 0.112462916, 0.2, 0.222702589,
                      0.3, 0.328626759, 0.4, 0.428392355, 0.5, 0.520499878,
                      0.6, 0.603856091, 0.7, 0.677801194, 0.8, 0.742100965,
                      0.9, 0.796908212, 1.0, 0.842700793, 1.1, 0.88020507,
                      1.2, 0.910313978, 1.3, 0.934007945, 1.4, 0.95228512,
                      1.5, 0.966105146, 1.6, 0.976348383, 1.7, 0.983790459,
                      1.8, 0.989090502, 1.9, 0.992790429, 2, 0.995322265,
                      2.1, 0.997020533, 2.2, 0.998137154, 2.3, 0.998856823,
                      2.4, 0.999311486, 2.5, 0.999593048)
    for i in range(len(test_wikipedia) // 2):
        assert math.isclose(math.erf(test_wikipedia[2 * i]),
                            test_wikipedia[2 * i + 1], abs_tol=0.0001)
        assert math.isclose(erf_inv(test_wikipedia[2 * i + 1]),
                            test_wikipedia[2 * i], abs_tol=0.0001)
    with pytest.raises(TypeError):
        erf_inv('x')
    with pytest.raises(ValueError):
        erf_inv(1.10)
    with pytest.raises(ValueError):
        erf_inv(-1.01)
        
        
def test_beta():
    for i in range(1, 20):
        for j in range(1, 20):
            x = math.factorial(i - 1);
            y = math.factorial(j - 1);
            z = math.factorial(i + j - 1);
            assert math.isclose(x * y / z, beta(i, j), 
                                abs_tol = 0.0001 * x * y / z)
    with pytest.raises(TypeError):
        beta('x', 1)
    with pytest.raises(TypeError):
        beta(1, 'x')
    with pytest.raises(ValueError):
        beta(-1, 1)
    with pytest.raises(ValueError):
        beta(1, -1)


def test_dsol_error():
    with pytest.raises(DSOLError, match="error text"):
        raise DSOLError("error text")


if __name__ == '__main__':
    pytest.main()
