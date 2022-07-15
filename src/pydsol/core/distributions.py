from abc import ABC, abstractmethod
import math
from typing import Union

from pydsol.core.streams import StreamInterface
from pydsol.core.utils import get_module_logger, beta, erf_inv

__all__ = [
    "Distribution",
    "DistContinuous",
    "DistSiscrete",
    "DistBernoulli",
    "DistBeta",
    "DistBinomial",
    "DistConstant",
    "DistDiscreteUniform",
    "DistErlang",
    "DistExponential",
    "DistGamma",
    "DistGeometric",
    "DistLogNormal",
    "DistLogNormalTrunc",
    "DistNegBinomial",
    "DistNormal",
    "DistNormalTrunc",
    "DistPearson5",
    "DistPearson6",
    "DistPoisson",
    "DistTriangular",
    "DistUniform",
    "DistWeibull",
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


class DistContinuous(Distribution):
    """
    The Continuous distribution. For more information on this distribution 
    see https://mathworld.wolfram.com/ContinuousDistribution.html. 
    """

    def __init__(self, stream: StreamInterface):
        """Initialize the distribution with a random stream."""
        super().__init__(stream)

    @abstractmethod
    def probability_density(self, x: float) -> float:
        """Returns the probability density value for value x."""


class DistDiscrete(Distribution):
    """
    The Discrete distribution. For more information on this distribution 
    see https://mathworld.wolfram.com/DiscreteDistribution.html. 
    """

    def __init__(self, stream: StreamInterface):
        """Initialize the distribution with a random stream."""
        super().__init__(stream)

    @abstractmethod
    def probability(self, observation: int) -> float:
        """Returns the probability of the observation for the distribution."""


class DistBernoulli(DistDiscrete):
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

    def probability(self, observation: int) -> float:
        """Returns the probability of the observation for the distribution."""
        if observation == 0:
            return 1.0 - self._p
        elif observation == 1:
            return self._p
        return 0.0
            
    @property
    def p(self) -> float:
        """Return the parameter value p"""
        return self._p
    
    def __str__(self) -> str:
        return f"DistBernoulli[p={self._p}]"
    
    def __repr__(self) -> str:
        return str(self)


class DistBeta(DistContinuous):
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
        if not isinstance(alpha1, (float, int)):
            raise TypeError(f"parameter alpha1 {alpha1} is not a float")
        if not isinstance(alpha2, (float, int)):
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

    def probability_density(self, x: float) -> float:
        """Returns the probability density value for value x."""
        if 0 < x < 1:
            return (x ** (self.alpha1 - 1) * (1.0 - x) ** (self.alpha2 - 1)
                    / beta(self._alpha1, self._alpha2))
        return 0.0

    def _set_stream(self, stream: StreamInterface):
        """Internal method to initialize the underlying distributions when
        a new random stream is set for this distribution."""
        super()._set_stream(stream)
        self._dist1 = DistGamma(self._stream, self._alpha1, 1.0)
        self._dist2 = DistGamma(self._stream, self._alpha2, 1.0)

    @property
    def alpha1(self) -> float:
        """Return the parameter value alpha1"""
        return self._alpha1

    @property
    def alpha2(self) -> float:
        """Return the parameter value alpha2"""
        return self._alpha2
    
    def __str__(self) -> str:
        return f"DistBeta[alpha1={self._alpha1}, alpha2={self._alpha2}]"
    
    def __repr__(self) -> str:
        return str(self)


class DistBinomial(DistDiscrete):
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
        the number of successes in n independent Bernoulli trials.
        """
        x: int = 0
        for _ in range(self._n):
            if self._stream.next_float() <= self._p:
                x += 1
        return x

    def probability(self, observation: int) -> float:
        """Returns the probability of the observation for the distribution."""
        if isinstance(observation, int) and 0 <= observation <= self._n:
            return (math.comb(self._n, observation) * self._p ** observation
                    * (1.0 - self._p) ** (self._n - observation))
        return 0.0;

    @property
    def p(self) -> float:
        """Return the parameter value p"""
        return self._p
    
    @property
    def n(self) -> int:
        """Return the parameter value n"""
        return self._n
    
    def __str__(self) -> str:
        return f"DistBinomial[p={self._p}, n={self._n}]"
    
    def __repr__(self) -> str:
        return str(self)


class DistDiscreteUniform(DistDiscrete):
    """
    The Discrete Uniform distribution is a discrete distribution function 
    that models the probability of drawing from a range of integer numbers 
    with equal probabilities. Rolling a dice is an example of such a
    distribution.  
    """
    
    def __init__(self, stream: StreamInterface, lo: int, hi: int):
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

    def probability(self, observation: int) -> float:
        """Returns the probability of the observation for the distribution."""
        if isinstance(observation, int) and self._lo <= observation <= self._hi:
            return 1.0 / (self._hi - self._lo + 1.0)
        return 0.0;

    @property
    def lo(self) -> int:
        """Return the parameter value lo (lowest value, inclusive)"""
        return self._lo
    
    @property
    def hi(self) -> int:
        """Return the parameter value hi (highest value, inclusive)"""
        return self._hi
    
    def __str__(self) -> str:
        return f"DistDiscreteUniform[lo={self._lo}, hi={self._hi}]"
    
    def __repr__(self) -> str:
        return str(self)


class DistConstant(DistContinuous):
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
        if not isinstance(constant, (float, int)):
            raise TypeError(f"constant {constant} is not a float / int")
        self._constant = constant
        
    def draw(self) -> float:
        """
        Draw a value from the Beta distribution. Based on the algorithm in 
        Law & Kelton, Simulation Modeling and Analysis, 1991, pages 492-493.
        """
        self._stream.next_float()
        return self._constant

    def probability_density(self, x: float) -> float:
        """Returns the probability density value for value x."""
        if x == self._constant:
            return 1.0  # actually this shoudl be math.inf...
        return 0.0
    
    @property
    def constant(self) -> Union[float, int]:
        """Return the parameter value constant"""
        return self._constant

    def __str__(self) -> str:
        return f"DistConstant[constant={self._constant}]"
    
    def __repr__(self) -> str:
        return str(self)


class DistErlang(DistContinuous):
    """
    The Erlang distribution is the distribution of a sum of k independent 
    exponential variables with the scale parameter as the mean. The scale 
    parameter is equal to 1/rate or 1/lambda;, giving the entire Erlang 
    distribution a mean of k*scale. For more information on this distribution 
    see https://mathworld.wolfram.com/ErlangDistribution.html.
    """
    
    GAMMATHRESHOLD = 10
    """the threshold above which we use a gamma function and below we use
    repeated drawing"""
    
    def __init__(self, stream: StreamInterface, scale: float, k: int):
        """
        Construct a new Erlang distribution with k and a mean (so not k and 
        a rate) as parameters. It is the distribution of a sum of k 
        independent exponential variables with the scale parameter as the mean. 
        The scale parameter is equal to 1/rate or 1/lambda, giving the 
        entire Erlang distribution a mean of k*scale.
        
        Parameters
        ----------
        stream StreamInterface
            the random stream to use for this distribution
        scale: float
            the mean of a single sample from the exponential distribution, 
            of which k are summed. Equal to 1/rate or 1/lambda.
        k: int
            the shape parameter of the Erlang distribution. The shape k is 
            the number of times a drawing is done from the exponential 
            distribution, where the Erlang distribution is the sum of these 
            k independent exponential variables.
            
        Raises
        ------
        TypeError when stream is not implementing StreamInterface
        TypeError when scale is not a float or int
        TypeError when k is not an int
        ValueError when k <= 0 or scale <= 0
        """
        if not isinstance(scale, (float, int)):
            raise TypeError(f"parameter scale {scale} is not a float")
        if not isinstance(k, int):
            raise TypeError(f"parameter k {k} is not an int")
        if scale <= 0:
            raise ValueError(f"parameter scale {scale} <= 0")
        if k <= 0:
            raise ValueError(f"parameter k {k} <= 0")
        self._scale = float(scale)
        self._k = k
        self._lambda = 1.0 / scale
        super().__init__(stream)  # after setting k and scale
        
    def draw(self) -> float:
        """
        Draw a value from the Erlang distribution. Based on the algorithm in 
        Law & Kelton, Simulation Modeling and Analysis, 1991.
        """
        if self._k < self.GAMMATHRESHOLD:
            # according to Law and Kelton, Simulation Modeling and Analysis
            # repeated drawing and composition is usually faster for k<=10
            product: float = 1.0
            for _ in range(self._k):
                product *= self._stream.next_float()
            return -self._scale * math.log(product)
        return self._dist_gamma.draw()

    def _set_stream(self, stream: StreamInterface):
        """Internal method to initialize the underlying distribution when
        a new random stream is set for this distribution."""
        super()._set_stream(stream)
        if self._k < self.GAMMATHRESHOLD:
            self._dist_gamma = None
        else:
            self._dist_gamma = DistGamma(stream, self._k, self._scale)

    def probability_density(self, x: float) -> float:
        """Returns the probability density value for value x."""
        if x >= 0:
            return (self._lambda * math.exp(-self._lambda * x) 
                    * (self._lambda * x) ** (self._k - 1) 
                    / math.factorial(self._k - 1))
        return 0.0

    @property
    def scale(self) -> float:
        """Return the parameter value scale"""
        return self._scale
    
    @property
    def k(self) -> int:
        """Return the parameter value k"""
        return self._k
    
    def __str__(self) -> str:
        return f"DistErlang[scale={self._scale}, k={self._k}]"
    
    def __repr__(self) -> str:
        return str(self)


class DistExponential(DistContinuous):
    """
    The exponential distribution describes the interarrival times of 
    entities to a system that occur randomly at a constant rate. The 
    exponential distribution here is characterized by the mean interarrival 
    time, but can also be characterized by this rate parameter lambda where
    mean = 1 / lambda. For more information on this distribution see 
    https://mathworld.wolfram.com/ExponentialDistribution.html.
    """
    
    def __init__(self, stream: StreamInterface, mean: float):
        """
        Construct a new exponential distribution. The exponential 
        distribution describes the interarrival times of entities to a
         system that occur randomly at a constant rate. The exponential 
         distribution can also be characterized by this rate parameter lambda
         where mean = 1 / lambda.
        
        Parameters
        ----------
        stream StreamInterface
            the random stream to use for this distribution
        mean: float
            the mean of the interarrival time. Equal to 1/rate or 1/lambda.
            
        Raises
        ------
        TypeError when stream is not implementing StreamInterface
        TypeError when mean is not a float or int
        ValueError when mean <= 0
        """
        super().__init__(stream)
        if not isinstance(mean, (float, int)):
            raise TypeError(f"parameter mean {mean} is not a float or int")
        if mean <= 0:
            raise ValueError(f"parameter mean {mean} <= 0")
        self._mean = float(mean)
        
    def draw(self) -> float:
        """
        Draw a value from the Exponential distribution.
        """
        return -self._mean * math.log(self._stream.next_float())

    def probability_density(self, x: float) -> float:
        """Returns the probability density value for value x."""
        if x >= 0:
            return (1.0 / self._mean) * math.exp(-x / self._mean) 
        return 0.0

    @property
    def mean(self) -> float:
        """Return the parameter value mean"""
        return self._mean
    
    def __str__(self) -> str:
        return f"DistExponential[mean={self._mean}]"
    
    def __repr__(self) -> str:
        return str(self)


class DistGamma(DistContinuous):
    """
    The Gamma distribution is a continuous distribution that yields positive
    numbers. The gamma distribution represents the time to complete some task, 
    e.g. customer service or machine repair. The parameters are not 
    rate-related, but average-related, so the mean is (shape * scale) and the 
    variance is (shape * scale ** 2).
    """

    def __init__(self, stream: StreamInterface, shape: float, scale: float):
        """
        Constructs a new Gamma distribution, with two parameters: shape
        and scale. The Gamma distribution is a continuous distribution and
        will return a positive number. The Gamma distribution represents 
        the time to complete some task, e.g. customer service or machine 
        repair. The parameters are not rate-related, but average-related, 
        so the mean is (shape * scale) and the variance is (shape * scale ** 2).
        
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
        if not isinstance(shape, (float, int)):
            raise TypeError(f"parameter shape {shape} is not a float")
        if not isinstance(scale, (float, int)):
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

    def probability_density(self, x: float) -> float:
        """Returns the probability density value for value x."""
        if x > 0:
            return ((self._scale ** -self._shape) * (x ** (self._shape - 1))
                    * math.exp(-1.0 * x / self._scale)
                    / math.gamma(self._shape)) 
        return 0.0

    @property
    def shape(self) -> float:
        """Return the parameter value shape, also called alpha or k"""
        return self._shape

    @property
    def scale(self) -> float:
        """Return the parameter value scale, also  called beta or theta"""
        return self._scale
    
    def __str__(self) -> str:
        return f"DistGamma[shape={self._shape}, scale={self._scale}]"
    
    def __repr__(self) -> str:
        return str(self)


class DistGeometric(DistDiscrete):
    """
    The Geometric distribution is the only discrete memoryless random 
    distribution. It is a discrete analog of the exponential distribution. 
    There are two variants, one that indicates the number of Bernoulli trials 
    to get the first success (1, 2, 3, ...), and one that indicates the 
    number of failures before the first success (0, 1, 2, ...). In line
    with Law & Kelton, the version of the number of failures before 
    the first success is modeled here, so X ={0, 1, 2, ...}.
    For more information on this distribution see 
    https://mathworld.wolfram.com/GeometricDistribution.html. 
    """
    
    def __init__(self, stream: StreamInterface, p: float):
        """
        Construct a new geometric distribution for a repeated set of 
        Bernoulli trials, indicating the number of failures before the first 
        success with probability p of success on each trial.
        
        Parameters
        ----------
        stream StreamInterface
            the random stream to use for this distribution
        p: float
            the probability for success for each individual Bernoulli trial
            
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
        self._lnp = math.log(1.0 - self._p)
        
    def draw(self) -> int:
        """
        Draw a value from the Binomial distribution, where the return value is
        the number of failures of independent Bernoulli trials until the
        first success.
        """
        u = self._stream.next_float()
        return math.floor(math.log(u) / self._lnp)

    def probability(self, observation: int) -> float:
        """Returns the probability of the observation for the distribution."""
        if isinstance(observation, int) and observation >= 0:
            return self._p * (1.0 - self._p) ** observation
        return 0.0;

    @property
    def p(self) -> float:
        """Return the parameter value p, the probability for success 
        for each individual Bernoulli trial"""
        return self._p
    
    def __str__(self) -> str:
        return f"DistGeometric[p={self._p}]"
    
    def __repr__(self) -> str:
        return str(self)


class DistNegBinomial(DistDiscrete):
    """
    The Negative Binomial distribution, also known as the Pascal distribution 
    or Polya distribution. It gives the probability of x failures where 
    there are s-1 successes in a total of x+s-1 Bernoulli trials, and 
    trial (x+s) is a success. The chance for success is p for each trial. 
    For more information on this distribution see
    https://mathworld.wolfram.com/NegativeBinomialDistribution.html.
    """
    
    def __init__(self, stream: StreamInterface, s: int, p: float):
        """
        Constructs a Negative Binomial distribution. It gives the probability 
        of x failures where there are s-1 successes in a total of x+s-1 
        Bernoulli trials, and trial (x+s) is a success
        
        Parameters
        ----------
        stream StreamInterface
            the random stream to use for this distribution
        s: int
            the number of successes in the sequence of (x+n) trials, 
            where trial (x+n) is a success.
        p: float
            the probability of success for each individual trial
            
        Raises
        ------
        TypeError when stream is not implementing StreamInterface
        TypeError when p is not a float
        TypeError when s is not an int
        ValueError when p < 0 or p > 1 or s <= 0
        """
        super().__init__(stream)
        if not isinstance(p, float):
            raise TypeError(f"parameter p {p} is not a float")
        if not isinstance(s, int):
            raise TypeError(f"parameter s {s} is not an int")
        if not 0 <= p <= 1:
            raise ValueError(f"parameter p {p} not between 0 and 1")
        if s <= 0:
            raise ValueError(f"parameter s {s} <= 0")
        self._p = p
        self._s = s
        # helper variable equal to ln(1-p) to avoid repetitive calculation.
        self._lnp = math.log(1.0 - self._p)
        
    def draw(self) -> int:
        """
        Draw a value from the Binomial distribution, where the return value is
        the number of successes in n independent Bernoulli trials.
        """
        x: int = 0
        for _ in range(self._s):
            u = self._stream.next_float()
            x += math.floor(math.log(u) / self._lnp)
        return x

    def probability(self, observation: int) -> float:
        """Returns the probability of the observation for the distribution."""
        if isinstance(observation, int) and observation >= 0:
            return (math.comb(self._s + observation - 1, observation) 
                    * self._p ** self._s * (1.0 - self._p) ** (observation))
        return 0.0;

    @property
    def p(self) -> float:
        """Return the parameter value p, the probability of success for 
        each individual trial in the negative binomial distribution."""
        return self._p
    
    @property
    def s(self) -> int:
        """Return the parameter value s, the number of successes in the 
        sequence of (x+n) trials, where trial (x+n) is a success."""
        return self._s
    
    def __str__(self) -> str:
        return f"DistNegBinomial[p={self._p}, s={self._s}]"
    
    def __repr__(self) -> str:
        return str(self)


class DistNormal(DistContinuous):
    """
    The Normal distribution is a continuous distribution that plays an 
    important role in statistics. When adding (samples from) one or more
    distributions, the distribution of the sum and of the sample average 
    becomes normally distributed as a result of the Central Limit Theorem.
    Still, the Normal distribution is not used often in (discrete event)
    simulation because it is unbounded and can return negative values. 
    Therefore, its use for processing times and inter-arrival times, but
    even something like a length, should be discouraged. Instead, 
    distributions like Exponential, Gamma, Erlang, Pearson, or Weibull 
    (bounded by 0 -- always positive) or Triangular, Uniform or Beta
    (bounded by a minimum and maximum value) are to be preferred.
    """

    def __init__(self, stream: StreamInterface, mu: float=0.0,
                 sigma: float=1.0):
        """
        Constructs a new Normal distribution, with two parameters mu for
        the mean, and sigma for the standard deviation. The Normal 
        distribution is a continuous distribution and will return a number 
        between minus infinity and infinity as the result. When the parameters
        are not specified, the so-called standard-normal distribution is
        created, with mu equal to 0.0, and sigma equal to 1.0.
        
        Parameters
        ----------
        stream StreamInterface
            the random stream to use for this distribution
        mu: float or int
            the mean of the Normal distribution
        sigma: float or int
            the standard deviation of the Normal distribution
            
        Raises
        ------
        TypeError when stream is not implementing StreamInterface
        TypeError when mu or sigma is not a float or int
        ValueError when sigma <= 0
        """
        super().__init__(stream)
        if not isinstance(mu, (float, int)):
            raise TypeError(f"parameter mu {mu} is not a float or int")
        if not isinstance(sigma, (float, int)):
            raise TypeError(f"parameter sigma {sigma} is not a float or int")
        if sigma <= 0:
            raise ValueError(f"parameter sigma {sigma} should be > 0")
        self._mu: float = float(mu)
        self._sigma: float = float(sigma)
        self._saved_gaussian: float = 0.0  # helper variable
        self._have_saved_gaussian = False  # helper variable
        
    def draw(self) -> float:
        """
        Draw a value from the Normal distribution with mean mu and standard
        deviation sigma.
        """
        return self._mu + self._sigma * self._next_gaussian()

    def probability_density(self, x: float) -> float:
        """Returns the probability density value for value x."""
        return (1.0 / (self._sigma * math.sqrt(2.0 * math.pi))
                * math.exp(-0.5 * ((x - self._mu) / self._sigma) ** 2))
        
    def cumulative_probability(self, x: float) -> float:
        """Return the cumulative probability of x for this Normal distribution""" 
        return (0.5 + 0.5 * math.erf((x - self._mu) 
                / (math.sqrt(2.0) * self._sigma)))

    def inverse_cumulative_probability(self, y: float) -> float:
        """Return the x-value of the given cumulative probability y."""
        return self._mu + self._sigma * math.sqrt(2.0) * erf_inv(2.0 * y - 1.0)

    def _set_stream(self, stream: StreamInterface):
        """Internal method to initialize the underlying distribution when
        a new random stream is set for this distribution."""
        super()._set_stream(stream)
        self._have_saved_gaussian = False  # helper variable

    def _next_gaussian(self) -> float:
        """
        Generates the next pseudorandom, Gaussian (normally) distributed 
        float value, with mean 0.0 and standard deviation 1.0.
        See section 3.4.1 of The Art of Computer Programming, Volume 2 by 
        Donald Knuth.
        """
        if self._have_saved_gaussian:
            self._have_saved_gaussian = False
            return self._saved_gaussian
        s = 1.0
        while s >= 1.0:
            v1 = 2.0 * self._stream.next_float() - 1.0  # between -1 and 1
            v2 = 2.0 * self._stream.next_float() - 1.0  # between -1 and 1
            s = v1 * v1 + v2 * v2
        norm = math.sqrt(-2.0 * math.log(s) / s)
        self._saved_gaussian = v2 * norm
        self._have_saved_gaussian = True
        return v1 * norm
        
    @property
    def mu(self) -> float:
        """Return the parameter value mu, the mean of the Normal distribution"""
        return self._mu

    @property
    def sigma(self) -> float:
        """Return the parameter value sigma, the standard deviation of the
        Normal distribution"""
        return self._sigma
    
    def __str__(self) -> str:
        return f"DistNormal[mu={self._mu}, sigma={self._sigma}]"
    
    def __repr__(self) -> str:
        return str(self)


class DistNormalTrunc(DistContinuous):
    """
    The Truncated Normal distribution. For more information on the truncated 
    normal distribution see:  
    https://en.wikipedia.org/wiki/Truncated_normal_distribution.
    """

    def __init__(self, stream: StreamInterface, mu: float=0.0,
                 sigma: float=1.0, lo: float=-math.inf, hi: float=math.inf):
        """
        Constructs a new Truncated Normal distribution, with two parameters 
        mu for the mean, and sigma for the standard deviation. A lo and hi 
        x-value indicate where the distribution will be 'cut off'. 
        
        Parameters
        ----------
        stream StreamInterface
            the random stream to use for this distribution
        mu: float or int
            the mean of the Normal distribution, , before applying the 
            cutoff by the lo and hi values
        sigma: float or int
            the standard deviation of the Normal distribution, before applying
            the cutoff by the lo and hi values
        lo: float or int
            lowest value of the 'remaining' distribution
        hi: float or int
            highest value of the 'remaining' distribution
            
        Raises
        ------
        TypeError when stream is not implementing StreamInterface
        TypeError when mu, sigma, lo or hi are not float or int
        ValueError when sigma <= 0
        ValueError when max <= min
        ValueError when the probabilities are so small that drawing becomes 
            impossible. The cutoff point is at an interval with an overall 
            probability of less than 1E-6
        """
        super().__init__(stream)
        if not isinstance(mu, (float, int)):
            raise TypeError(f"parameter mu {mu} is not a float or int")
        if not isinstance(sigma, (float, int)):
            raise TypeError(f"parameter sigma {sigma} is not a float or int")
        if not isinstance(lo, (float, int)):
            raise TypeError(f"parameter lo {lo} is not a float or int")
        if not isinstance(hi, (float, int)):
            raise TypeError(f"parameter hi {hi} is not a float or int")
        if sigma <= 0:
            raise ValueError(f"parameter sigma {sigma} should be > 0")
        if hi <= lo:
            raise ValueError(f"parameter hi {hi} <= lo {lo}")
        self._mu: float = float(mu)
        self._sigma: float = float(sigma)
        self._lo = float(lo)
        self._hi = float(hi)
        self._cum_prob_lo = self.cumulative_probability_not_truncated(lo)
        self._cum_prob_diff = self.cumulative_probability_not_truncated(hi) \
                            -self._cum_prob_lo
        if self._cum_prob_diff < 1E-6:
            raise ValueError(f"the indicated interval on this normal "\
            +f"distribution has a very low probability of {self._cum_prob_diff}")
        self._prob_dens_factor = 1.0 / self._cum_prob_diff
        
    def draw(self) -> float:
        """
        Draw a value from the Normal distribution with mean mu and standard
        deviation sigma on the interval (lo, hi)
        """
        d: float = (
            self.inverse_cumulative_probability_not_truncated(self._cum_prob_lo 
            +self._cum_prob_diff * self._stream.next_float()))
        # if inverse cumulative probability gets close to 1, inf is returned.
        # This corresponds to a value of 'max' for the truncated distribution.
        if math.isinf(d):
            if d < 0:
                return self._lo
            else:
                return self._hi
        if d < self._lo:
            # rounding error?
            if abs(d - self._lo) < 1E-6 * abs(self._lo):
                return self._lo
            else:
                raise ValueError(f"drawn value {d} outside of interval "\
                    f"[min, max] = [{self._lo}, {self._hi}]") 
        if d > self._hi:
            # rounding error?
            if abs(d - self._hi) < 1E-6 * abs(self._hi):
                return self._hi
            else:
                raise ValueError(f"drawn value {d} outside of interval "\
                    f"[min, max] = [{self._lo}, {self._hi}]") 
        return d
    
    def probability_density(self, x: float) -> float:
        """Returns the probability density value for value x."""
        if x < self._lo or x > self._hi:
            return 0.0
        return (self._prob_dens_factor / (self._sigma * math.sqrt(2.0 * math.pi))
                * math.exp(-0.5 * ((x - self._mu) / self._sigma) ** 2))

    def cumulative_probability(self, x: float) -> float:
        """Return the cumulative probability of x for the truncated 
        distribution""" 
        if x < self._lo:
            return 0.0
        if x > self._hi:
            return 1.0
        return ((self.cumulative_probability_not_truncated(x) 
                -self._cum_prob_lo) * self._prob_dens_factor)  

    def cumulative_probability_not_truncated(self, x: float) -> float:
        """Return the cumulative probability of x for the non-truncated  
        distribution""" 
        return (0.5 + 0.5 * math.erf((x - self._mu) 
                / (math.sqrt(2.0) * self._sigma)))

    def inverse_cumulative_probability(self, y: float) -> float:
        """Return the x-value of the given cumulative probability y
        for the truncated distribution."""
        if y < 0 or y > 1:
            raise ValueError(f"probability {y} not inn interval [0, 1]")
        # For extreme cases we return the min and max directly. The method 
        # inverse_cumulative_probability_not_truncated() can only return 
        # values from "mu - 10*sigma" to "mu + 10*sigma". If min or max is 
        # beyond these values, those values would show erroneous results. For 
        # any cumulative probability that is slightly above 0.0 or slightly  
        # below 1.0, values in the range from "mu - 10*sigma" to 
        # "mu + 10*sigma" will always provide a sensible result.
        if y == 0:
            return self._lo
        if y == 1:
            return self._hi
        return self.inverse_cumulative_probability_not_truncated(
                        self._cum_prob_lo + y * self._cum_prob_diff)

    def inverse_cumulative_probability_not_truncated(self, y: float) -> float:
        """Return the x-value of the given cumulative probability y
        for the non-truncated distribution."""
        return self._mu + self._sigma * math.sqrt(2.0) * erf_inv(2.0 * y - 1.0)
       
    @property
    def mu(self) -> float:
        """Return the parameter value mu, the mean of the Normal distribution"""
        return self._mu

    @property
    def sigma(self) -> float:
        """Return the parameter value sigma, the standard deviation of the
        Normal distribution"""
        return self._sigma

    @property
    def lo(self) -> float:
        """Return the lower bound of the truncated distribution"""
        return self._lo

    @property
    def hi(self) -> float:
        """Return the upper bound of the truncated distribution"""
        return self._hi
    
    def __str__(self) -> str:
        return f"DistNormalTrunc[mu={self._mu}, sigma={self._sigma}" + \
               f", lo={self._lo}, hi={self._hi}]"
    
    def __repr__(self) -> str:
        return str(self)


class DistLogNormal(DistNormal):
    """
    The LogNormal distribution for random variable X is such that 
    ln(X) ~ Normal(mu, sigma).
    For more information on this distribution see
    https://mathworld.wolfram.com/LogNormalDistribution.html.
    """

    def __init__(self, stream: StreamInterface, mu: float=0.0,
                 sigma: float=1.0):
        """
        Constructs a new LogNormal distribution, with two parameters: mu for
        the mean of the underlying Normal distribution, and sigma for the 
        standard deviation of the underlying Normal distribution. The 
        LogNormal distribution is a continuous distribution that yields 
        positive values. The LogNormal distribution for random variable X 
        is such that ln(X) ~ Normal(mu, sigma).
        
        Parameters
        ----------
        stream StreamInterface
            the random stream to use for this distribution
        mu: float or int
            the mean of the underlying Normal distribution
        sigma: float or int
            the standard deviation of the underlying Normal distribution
            
        Raises
        ------
        TypeError when stream is not implementing StreamInterface
        TypeError when mu or sigma is not a float or int
        ValueError when sigma <= 0
        """
        super().__init__(stream, mu, sigma)
        # the constant in the lognormal calculation: 2 * sigma^2.
        self._c2sigma2 = 2.0 * sigma * sigma
        # the constant in the lognormal calculation: SQRT(2 * pi * sigma^2).
        self._c2pisigma2 = math.sqrt(math.pi * self._c2sigma2)

    def draw(self) -> float:
        """
        Draw a value from the LogNormal distribution with mean mu and standard
        deviation sigma for the underlying Normal distribution.
        """
        return math.exp(super().draw())

    def probability_density(self, x: float) -> float:
        """Returns the probability density value for value x."""
        if x > 0.0:
            xminmu = math.log(x) - self._mu
            return (math.exp(-1 * xminmu * xminmu / self._c2sigma2) 
                    / (x * self._c2pisigma2))
        return 0.0 
        
    def cumulative_probability(self, x: float) -> float:
        """Return the cumulative probability of x for this LogNormal 
        distribution""" 
        if x > 0.0:
            return super().cumulative_probability(math.log(x)) 
        return 0.0 

    def inverse_cumulative_probability(self, y: float) -> float:
        """Return the x-value of the given cumulative probability y."""
        return math.exp(super().inverse_cumulative_probability(y))

    @property
    def mu(self) -> float:
        """Return the parameter value mu, note that this is the mean of the
        underlying Normal distribution"""
        return self._mu

    @property
    def sigma(self) -> float:
        """Return the parameter value sigma, note that this is the standard
        deviation of the underlying Normal distribution"""
        return self._sigma
    
    def __str__(self) -> str:
        return f"DistLogNormal[Normal.mu={self._mu}, Mormal.sigma={self._sigma}]"
    
    def __repr__(self) -> str:
        return str(self)

