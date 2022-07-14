"""
This module contains generic utilities for the pydsol code. 
"""
import logging
import math
import sys

__all__ = [
    "DSOLError",
    "Assert",
    ]


class DSOLError(Exception):
    """General Exception class for pydsol."""
    pass


logging.basicConfig(level=logging.DEBUG,
        format='%(levelname)s: %(module)s.%(funcName)s: %(message)s')


def get_module_logger(mod_name: str, level=logging.CRITICAL):
    logger = logging.getLogger(mod_name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler(stream=sys.stdout)
        logger.addHandler(handler)
    msg_format = '%(levelname)s: %(module)s.%(funcName)s: %(message)s'
    formatter = logging.Formatter(fmt=msg_format)
    for handler in logger.handlers:
        handler.setFormatter(formatter)
    logger.setLevel(level)
    return logger


logger = get_module_logger('utils')


def sign(x: float) -> float:
    """
    Return the sign of x. Analogous to other programming languages, the
    following convention is used:
    * return -1  for negative x
    * return +1  for positive x
    * return 0   when x s zero
    * return nan when x is nan
    """
    if math.isnan(x):
        return math.nan
    if x > 0:
        return 1.0
    if x < 0:
        return -1.0
    return 0.0


def erf_inv(y: float) -> float:
    """
    Approximates the inverse error function (erf) based on the C-algorithm
    at http://www.naic.edu/~jeffh/inverse_cerf.c.
    
    Raises
    ------
    TypeError when y is not a number
    ValueError when y is not between -1 and 1 (inclusive)
    """
    if not isinstance(y, (float, int)):
        raise TypeError(f"Parameter y {y} is not a number")
    if not -1.0 <= y <= 1.0:
        raise ValueError(f"Parameter y {y} not between 0 and 1 (inclusive)")

    ax = abs(y)
    
    if ax <= 0.75:
        # This approximation, taken from Table 10 of Blair et al., is valid
        # for |x|<=0.75 and has a maximum relative error of 4.47 x 10^-8.
        p = (-13.0959967422, 26.785225760, -9.289057635)
        q = (-12.0749426297, 30.960614529, -17.149977991, 1.00000000)
        t = ax * ax - 0.75 * 0.75
        r = (ax * (p[0] + t * (p[1] + t * p[2])) 
             / (q[0] + t * (q[1] + t * (q[2] + t * q[3]))))
        
    elif 0.75 <= ax <= 0.9375:
        # This approximation, taken from Table 29 of Blair et al., is valid 
        # for .75<=|x|<=.9375 and has a maximum relative error of 4.17 x 10^-8.
        p = (-.12402565221, 1.0688059574, -1.9594556078, .4230581357)
        q = (-.08827697997, .8900743359, -2.1757031196, 1.0000000000)
        t = ax * ax - 0.9375 * 0.9375
        r = (ax * (p[0] + t * (p[1] + t * (p[2] + t * p[3]))) 
             / (q[0] + t * (q[1] + t * (q[2] + t * q[3]))))
        
    elif ax >= 0.9375 and ax <= (1.0 - 1.0e-9):
        # This approximation, taken from Table 50 of Blair et al., is valid 
        # for .9375<=|x|<=1-10^-100 and has a maximum relative error of 
        # 2.45 x 10^-8.
        p = (.1550470003116, 1.382719649631, .690969348887, -1.128081391617,
             .680544246825, -.16444156791)
        q = (.155024849822, 1.385228141995, 1.000000000000)
        t = 1.0 / math.sqrt(-math.log(1.0 - ax))
        r = ((p[0] / t + p[1] + t * (p[2] + t * (p[3] + t * (p[4] + t * p[5])))) 
             / (q[0] + t * (q[1] + t * (q[2]))))
    
    else:
        r = math.inf
    
    return sign(y) * r

    
def beta(z: float, w: float) -> float:
    """
    Calculates Beta(z, w) where Beta(z, w) = Gamma(z) * Gamma(w) / Gamma(z + w).
    
    Raises
    ------
    TypeEsception when z or w are not numbers 
    ValueException when z < 0 or w < 0
    """
    if not isinstance(w, (float, int)):
        raise TypeError(f"Parameter w {w} is not a number")
    if not isinstance(z, (float, int)):
        raise TypeError(f"Parameter z {z} is not a number")
    if z < 0 or w < 0:
        raise ValueError(f"Parameter z {z} or w {w} < 0")
    return math.exp(math.lgamma(z) + math.lgamma(w) - math.lgamma(z + w))

