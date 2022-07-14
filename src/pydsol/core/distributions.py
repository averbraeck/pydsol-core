from abc import ABC, abstractmethod
import math
from typing import Union

from pydsol.core.streams import StreamInterface
from pydsol.core.utils import get_module_logger

__all__ = [
    "Distribution",
    "DistBernoulli",
    "DistBeta",
    "DistGamma",
    ]

logger = get_module_logger('distributions')


class Distribution(ABC):
    """
    The Distribution defines the interface for both discrete and continuous
    distributions.
    """
    
    def __init__(self, stream: StreamInterface):
        """Initialize the distribution with a random stream."""
        self._set_stream(stream)
        
    @abstractmethod
    def draw(self) -> Union[int, float]:
        """
        Draw a random value from the distribution function. For discrete
        distributions, this function will return an int, for continuous
        distributions it will return a float.
        """
    
    @property
    def stream(self) -> StreamInterface:
        """Return the current random stream for this distribution."""
        return self._stream
    
    @stream.setter
    def stream(self, stream: StreamInterface):
        """Set a new random stream for this distribution."""
        self._set_stream(stream)
        
    def _set_stream(self, stream: StreamInterface):
        """Internal method that can be overridden to initialize the 
        underlying distributions when a new random stream is set for 
        this distribution."""
        if not isinstance(stream, StreamInterface):
            raise TypeError(f"stream {stream} not a random stream")
        self._stream: StreamInterface = stream


class DistBernoulli(Distribution):
    """
    The Bernoulli distribution is a discrete distribution function with
    a single trial with a probability p for success (X = 1) and a probability
    1-p for failure (X = 0). 
    """
    
    def __init__(self, stream: StreamInterface, p:float):
        """
        Constructs a new Bernoulli distribution, with p as the probability 
        for success (X=1), where failure is associated with X=0.
        
        Parameters
        ----------
        stream StreamInterface
            the random stream to use for this distribution
        p: float
            the probability for success of the Bernoulli distribution
            
        Raises
        ------
        TypeError when stream is not implementing StreamInterface
        TypeError when p is not a float
        ValueError when p < 0 or p > 1
        """
        super().__init__(stream)
        if not isinstance(p, float):
            raise TypeError(f"parameter p {p} is not a float")
        if not 0 <= p <= 1:
            raise ValueError(f"parameter p {p} not between 0 and 1")
        self._p = p
        
    def draw(self) -> int:
        """
        Draw a value from the Bernoulli distribution, where 1 denotes
        success (probability p) and 0 indicates failure (probability 1 - p).
        """
        if self._stream.next_float() <= self._p:
            return 1
        return 0
    
    @property
    def p(self):
        """Return the parameter value p"""
        return self._p
    
    def __str__(self):
        return f"DistBernoulli[p={self._p}]"
    
    def __repr__(self):
        return str(self)


class DistBeta(Distribution):
    """
    The Beta distribution is a continuous distribution that is bound between 
    0 and 1 for the outcome, and has two shape parameters alpha 1 and alpha2. 
    For informattion see https://mathworld.wolfram.com/BetaDistribution.html
    """
    
    def __init__(self, stream: StreamInterface,
                     alpha1: float, alpha2: float):
        """
        Constructs a new Beta distribution, with two shape parameters alpha1
        and alpha2. The Beta distribution is a continuous distribution and
        will return a number between 0 and 1 as the result.
        
        Parameters
        ----------
        stream StreamInterface
            the random stream to use for this distribution
        alpha1: float or int
            the first shape parameter
        alpha2: float or int
            the second shape parameter
            
        Raises
        ------
        TypeError when stream is not implementing StreamInterface
        TypeError when alpha1 or alpha2 is not a float or int
        ValueError when alpha1 <= 0 or alpha2 <= 0
        """
        if not (isinstance(alpha1, float) or isinstance(alpha1, int)):
            raise TypeError(f"parameter alpha1 {alpha1} is not a float")
        if not (isinstance(alpha2, float) or isinstance(alpha2, int)):
            raise TypeError(f"parameter alpha2 {alpha2} is not a float")
        if alpha1 <= 0:
            raise ValueError(f"parameter alpha1 {alpha1} should be > 0")
        if alpha2 <= 0:
            raise ValueError(f"parameter alpha2 {alpha2} should be > 0")
        self._alpha1 = float(alpha1)
        self._alpha2 = float(alpha2)
        self._dist1 = None
        self._dist2 = None
        super().__init__(stream)  # after setting alpha1 and alpha2
        
    def draw(self) -> float:
        """
        Draw a value from the Beta distribution. Based on the algorithm in 
        Law & Kelton, Simulation Modeling and Analysis, 1991, pages 492-493.
        """
        y1 = self._dist1.draw()
        y2 = self._dist2.draw()
        return y1 / (y1 + y2)

    def _set_stream(self, stream: StreamInterface):
        """Internal method to initialize the underlying distributions when
        a new random stream is set for this distribution."""
        super()._set_stream(stream)
        self._dist1 = DistGamma(self._stream, self._alpha1, 1.0)
        self._dist2 = DistGamma(self._stream, self._alpha2, 1.0)

    @property
    def alpha1(self):
        """Return the parameter value alpha1"""
        return self._alpha1

    @property
    def alpha2(self):
        """Return the parameter value alpha2"""
        return self._alpha2
    
    def __str__(self):
        return f"DistBeta[alpha1={self._alpha1}, alpha2={self._alpha2}]"
    
    def __repr__(self):
        return str(self)


class DistBinomial(Distribution):
    """
    The Binomial distribution is a discrete distribution function that models
    the probability of the number of successes in a sequence of n 
    independent experiments, each with success (probability p) or failure 
    (probability q = 1 − p). For more information on this distribution see 
    https://mathworld.wolfram.com/BinomialDistribution.html. 
    """
    
    def __init__(self, stream: StreamInterface, n: int, p: float):
        """
        Constructs a Binomial distribution. It calculates the probability 
        for a number of successes in n independent Bernoulli trials with 
        probability p of success on each trial.
        
        Parameters
        ----------
        stream StreamInterface
            the random stream to use for this distribution
        n: int
            the number of independent trials for the Binomial distribution
        p: float
            the probability for success for each individual trial
            
        Raises
        ------
        TypeError when stream is not implementing StreamInterface
        TypeError when p is not a float
        TypeError when n is not an int
        ValueError when p < 0 or p > 1 or n <= 0
        """
        super().__init__(stream)
        if not isinstance(p, float):
            raise TypeError(f"parameter p {p} is not a float")
        if not isinstance(n, int):
            raise TypeError(f"parameter n {n} is not an int")
        if not 0 <= p <= 1:
            raise ValueError(f"parameter p {p} not between 0 and 1")
        if n <= 0:
            raise ValueError(f"parameter n {n} <= 0")
        self._p = p
        self._n = n
        
    def draw(self) -> int:
        """
        Draw a value from the Binomial distribution, where the return value is
        th number of successes in n independent Bernoulli trials.
        """
        x: int = 0
        for _ in range(self._n):
            if self._stream.next_float() <= self._p:
                x += 1
        return x
    
    @property
    def p(self):
        """Return the parameter value p"""
        return self._p
    
    @property
    def n(self):
        """Return the parameter value n"""
        return self._n
    
    def __str__(self):
        return f"DisBinomial[p={self._p}, n={self._n}]"
    
    def __repr__(self):
        return str(self)

class DistDiscreteUniform(Distribution):
    """
    The Discrete Uniform distribution is a discrete distribution function 
    that models the probability of drawing from a range of integer numbers 
    with equal probabilities. Rolling a dice is an example of such a
    distribution.  
    """
    
    def __init__(self, stream: StreamInterface, lo: int, hi: float):
        """
        Constructs a Discrete uniform distribution. The distribution
        draws from a range of integer numbers with equal probabilities. 
        Rolling a dice is an example of such a distribution.  
        
        Parameters
        ----------
        stream StreamInterface
            the random stream to use for this distribution
        lo: int
            the lowest value to draw (inclusive)
        hi: int
            the highest value to draw (inclusive)
            
        Raises
        ------
        TypeError when stream is not implementing StreamInterface
        TypeError when lo or hi is not an int
        ValueError when lo >= hi
        """
        super().__init__(stream)
        if not isinstance(lo, int):
            raise TypeError(f"parameter lo {lo} is not an int")
        if not isinstance(hi, int):
            raise TypeError(f"parameter hi {hi} is not an int")
        if lo >= hi:
            raise ValueError(f"lo >= hi")
        self._lo = lo
        self._hi = hi
        
    def draw(self) -> int:
        """
        Draw a value from the Discrete Uniform distribution.
        """
        return self._stream.next_int(self._lo, self._hi)
    
    @property
    def lo(self):
        """Return the parameter value lo (lowest value, inclusive)"""
        return self._lo
    
    @property
    def hi(self):
        """Return the parameter value hi (highest value, inclusive)"""
        return self._hi
    
    def __str__(self):
        return f"DisDiscreteUniform[lo={self._lo}, hi={self._hi}]"
    
    def __repr__(self):
        return str(self)


class DistConstant(Distribution):
    """
    The Constant distribution is a continuous distribution that always returns
    the same value. It can be used in situations where a distribution function
    is expected, but actually a fixed value is used.
    """
    
    def __init__(self, stream: StreamInterface, constant: Union[float, int]):
        """
        Constructs a new Constant distribution that always returns the same 
        value.
        
        Parameters
        ----------
        stream StreamInterface
            the random stream to use for this distribution
        constant: float or int
            the value to return
            
        Raises
        ------
        TypeError when stream is not implementing StreamInterface
        TypeError when constant is not a float or int
        """
        super().__init__(stream)
        if not (isinstance(constant, float) or isinstance(constant, int)):
            raise TypeError(f"parameter constant {constant} is not a float")
        self._constant = float(constant)
        
    def draw(self) -> float:
        """
        Draw a value from the Beta distribution. Based on the algorithm in 
        Law & Kelton, Simulation Modeling and Analysis, 1991, pages 492-493.
        """
        self._stream.next_float()
        return self._constant
    
    @property
    def constant(self):
        """Return the parameter value constant"""
        return self._constant

    def __str__(self):
        return f"DistConstant[constant={self._constant}]"
    
    def __repr__(self):
        return str(self)


class DistGamma(Distribution):
    """
    The Gamma distribution is a continuous distribution that yields positive
    numbers. The gamma distribution represents the time to complete some task, 
    e.g. customer service or machine repair. The parameters are not 
    rate-related, but average-related, so the mean is (shape * scale) and the 
    variance is (shape * scale ** 2).
    """

    def __init__(self, stream: StreamInterface, shape: float, scale: float):
        """
        Constructs a new Beta distribution, with two shape parameters shape
        and scale. The Beta distribution is a continuous distribution and
        will return a number between 0 and 1 as the result.
        
        Parameters
        ----------
        stream StreamInterface
            the random stream to use for this distribution
        shape: float or int
            the shape parameter, also called alpha or k
        scale: float or int
            the scale parameter, also  called beta or theta
            
        Raises
        ------
        TypeError when stream is not implementing StreamInterface
        TypeError when shape or scale is not a float or int
        ValueError when shape <= 0 or scale <= 0
        """
        super().__init__(stream)
        if not (isinstance(shape, float) or isinstance(shape, int)):
            raise TypeError(f"parameter shape {shape} is not a float")
        if not (isinstance(scale, float) or isinstance(scale, int)):
            raise TypeError(f"parameter scale {scale} is not a float")
        if shape <= 0:
            raise ValueError(f"parameter shape {shape} should be > 0")
        if scale <= 0:
            raise ValueError(f"parameter scale {scale} should be > 0")
        self._shape = float(shape)
        self._scale = float(scale)
        
    def draw(self) -> float:
        """
        Draw a value from the Gamma distribution. Based on the algorithm in 
        Law & Kelton, Simulation Modeling and Analysis, 1991, pages 488-489.
        """
        if self._shape < 1.0:
            b: float = (math.e + self._shape) / math.e
            counter: int = 0
            while counter < 1000:
                #  step 1.
                p: float = b * self._stream.next_float()
                if p <= 1.0:
                    #  step 2.
                    y: float = p ** (1.0 / self._shape)
                    u2: float = self._stream.next_float()
                    if u2 <= math.exp(-y):
                        return self._scale * y
                else:
                    #  step 3.
                    y: float = -math.log((b - p) / self._shape)
                    u2: float = self._stream.next_float()
                    if u2 <= y ** (self._shape - 1.0):
                        return self._scale * y
                counter += 1
            logger.info("Gamma distribution -- 1000 tries for alpha<1.0")
            return 1.0
        elif self._shape > 1.0:
            a: float = 1.0 / math.sqrt(2.0 * self._shape - 1.0)
            b: float = self._shape - math.log(4.0)
            q: float = self._shape + (1.0 / a)
            theta: float = 4.5
            d: float = 1.0 + math.log(theta)
            counter: int = 0
            while counter < 1000:
                #  step 1.
                u1: float = self._stream.next_float()
                u2: float = self._stream.next_float()
                #  step 2.
                v = a * math.log(u1 / (1.0 - u1))
                y = self._shape * math.exp(v)
                z = u1 * u1 * u2
                w = b + q * v - y
                #  step 3.
                if (w + d - theta * z) >= 0.0:
                    return self._scale * y
                #  step 4.
                if w > math.log(z):
                    return self._scale * y
                counter += 1
            logger.info("Gamma distribution -- 1000 tries for alpha>1.0")
            return 1.0
        else:
            #  shape == 1.0
            #  Gamma(1.0, scale) ~ exponential with mean = scale
            return -self._scale * math.log(self._stream.next_float())

    @property
    def shape(self):
        """Return the parameter value shape, also called alpha or k"""
        return self._shape

    @property
    def scale(self):
        """Return the parameter value scale, also  called beta or theta"""
        return self._scale
    
    def __str__(self):
        return f"DistGamma[shape={self._shape}, scale={self._scale}]"
    
    def __repr__(self):
        return str(self)
