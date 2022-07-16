
"""
Test the distribution function classes
""" 

import math

import pytest

from pydsol.core.distributions import Distribution, DistBeta, DistGamma, \
    DistConstant, DistErlang, DistExponential, DistPearson5, DistPearson6, \
    DistTriangular, DistUniform, DistWeibull
from pydsol.core.statistics import Tally
from pydsol.core.streams import MersenneTwister, StreamInterface
from pydsol.core.utils import beta


def c_dist(n: int, dist: Distribution, expected_mean: float,
            expected_variance: float, expected_min: float, expected_max: float,
            precision: float):
    tally: Tally = Tally("distTally " + str(dist))
    tally.initialize()
    for _ in range(n):
        d = dist.draw()
        if not math.isnan(expected_min):
            assert d >= expected_min
        if not math.isnan(expected_max):
            assert d <= expected_max
        tally.ingest(d)
    assert math.isclose(expected_mean, tally.population_mean(),
                abs_tol=precision)
    assert math.isclose(math.sqrt(expected_variance), tally.population_stdev(),
                abs_tol=precision)


def test_c_mean_variance():
    stream = MersenneTwister(12)
    nan = math.nan
    c_dist(100000, DistBeta(stream, 1.0, 2.0), 1.0 / (1.0 + 2.0),
           (1.0 * 2.0) / ((1.0 + 2.0) * (1.0 + 2.0) * (1.0 + 2.0 + 1.0)),
           0.0, 1.0, 0.1)
    c_dist(100000, DistConstant(stream, 12.1), 12.1, 0.0, 12.1,
           12.1, 0.001)
    c_dist(100000, DistErlang(stream, 2.0, 1), 2.0, 2.0 * 2.0,
           0.0, nan, 0.05)
    c_dist(100000, DistErlang(stream, 0.5, 4), 4.0 * 0.5,
           4.0 * 0.5 * 0.5, 0.0, nan, 0.05)
    c_dist(100000, DistErlang(stream, 0.5, 40), 40.0 * 0.5,
           40.0 * 0.5 * 0.5, 0.0, nan, 0.05)
    c_dist(100000, DistExponential(stream, 1.2), 1.2,
           1.2 * 1.2, 0.0, nan, 0.05)
    c_dist(100000, DistGamma(stream, 2.0, 4.0), 2.0 * 4.0,
           2.0 * 4.0 * 4.0, 0.0, nan, 0.5)
    c_dist(100000, DistGamma(stream, 3.0, 4.0), 3.0 * 4.0,
           3.0 * 4.0 * 4.0, 0.0, nan, 0.5)
    c_dist(100000, DistGamma(stream, 0.999, 2.0), 0.999 * 2.0,
           0.999 * 2.0 * 2.0, 0.0, nan, 0.5)
    c_dist(100000, DistGamma(stream, 1.0, 4.0), 1.0 * 4.0,
           1.0 * 4.0 * 4.0, 0.0, nan, 0.5)
    c_dist(100000, DistGamma(stream, 0.5, 0.2), 0.5 * 0.2,
           0.5 * 0.2 * 0.2, 0.0, nan, 0.1)
    c_dist(100000, DistPearson5(stream, 3, 1), 0.5, 0.25,
           0.0, nan, 0.01)
    c_dist(100000, DistPearson6(stream, 2, 3, 4), 4.0 * 2 / (3 - 1),
            4.0 * 4 * 2 * (2 + 3 - 1) / ((3 - 1) * (3 - 1) * (3 - 2)),
            0.0, nan, 0.5)  # wide range of outcomes for variance
    c_dist(100000, DistTriangular(stream, 1, 4, 9), (1 + 4 + 9) / 3.0,
            (1 * 1 + 4 * 4 + 9 * 9 - 1 * 4 - 1 * 9 - 4 * 9) / 18.0,
            1.0, 9.0, 0.01)
    c_dist(100000, DistUniform(stream, 0, 1), 0.5, 1.0 / 12.0,
           0.0, 1.0, 0.01)
    c_dist(100000, DistWeibull(stream, 1.5, 1), 0.9027, 0.3756, 0.0, nan, 0.01)


def test_beta():
    
    def dist_beta(a, b, x) -> float:
        """Calculate probability density of DistBeta(a, b) for value x. 
        From: https://mathworld.wolfram.com/BetaDistribution.html"""
        return (1 - x) ** (b - 1) * x ** (a - 1) / beta(a, b)
        
    stream: StreamInterface = MersenneTwister(10)
    dist: DistBeta = DistBeta(stream, 1.5, 2.5)
    assert stream == dist.stream
    assert dist.alpha1 == 1.5
    assert dist.alpha2 == 2.5
    assert "Beta" in str(dist)
    assert "1.5" in str(dist)
    assert "2.5" in repr(dist)
    value: float = dist.draw()
    assert value >= 0 and value <= 1
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value

    assert math.isclose(dist.probability_density(0.5),
            dist_beta(1.5, 2.5, 0.5), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(0.25),
            dist_beta(1.5, 2.5, 0.25), abs_tol=0.0001)
    assert dist.probability_density(0.0) == 0.0
    assert dist.probability_density(1.0) == 0.0
    assert dist.probability_density(2.0) == 0.0
    assert dist.probability_density(-0.1) == 0.0
    
    with pytest.raises(TypeError):
        DistBeta('x', 0.1, 2.0)
    with pytest.raises(TypeError):
        DistBeta(stream, 'x', 2.0)
    with pytest.raises(TypeError):
        DistBeta(stream, 0.1, 'x')
    with pytest.raises(ValueError):
        DistBeta(stream, -0.1, 2.0)
    with pytest.raises(ValueError):
        DistBeta(stream, 0.1, -2.0)


def test_constant():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistConstant = DistConstant(stream, 1.5)
    assert stream == dist.stream
    assert dist.constant == 1.5
    assert "Constant" in str(dist)
    assert "1.5" in str(dist)
    assert "1.5" in repr(dist)
    value: float = dist.draw()
    assert value == 1.5
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    dist: DistConstant = DistConstant(stream, 4)
    assert dist.draw() == 4

    dist: DistConstant = DistConstant(stream, 1.5)
    assert dist.probability_density(0.0) == 0.0
    assert dist.probability_density(1.0) == 0.0
    assert dist.probability_density(1.5) == 1.0

    dist: DistConstant = DistConstant(stream, 4)
    assert dist.probability_density(0.0) == 0.0
    assert dist.probability_density(1.0) == 0.0
    assert dist.probability_density(4) == 1.0

    with pytest.raises(TypeError):
        DistConstant('x', 0.1)
    with pytest.raises(TypeError):
        DistConstant(stream, 'x')

    
def test_erlang():

    def dist_erlang(k, scale, x) -> float:
        """Calculate probability density of DistErlang(k, scale) for value x. 
        From: https://mathworld.wolfram.com/ErlangDistribution.html"""
        la = 1.0 / scale
        return (la * ((la * x) ** (k - 1)) * math.exp(-la * x)
                / math.factorial(k - 1))
    
    stream: StreamInterface = MersenneTwister(10)
    dist: DistErlang = DistErlang(stream, 2.5, 3)
    assert stream == dist.stream
    assert dist.scale == 2.5
    assert dist.k == 3
    assert "Erlang" in str(dist)
    assert "2.5" in str(dist)
    assert "3" in repr(dist)

    # below 10
    value: float = dist.draw()
    assert value > 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    
    # above 10
    stream: StreamInterface = MersenneTwister(10)
    dist: DistErlang = DistErlang(stream, 2, 15)
    value: float = dist.draw()
    assert value > 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    
    # exactly 10
    stream: StreamInterface = MersenneTwister(10)
    dist: DistErlang = DistErlang(stream, 3.14, 10)
    value: float = dist.draw()
    assert value > 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value

    dist: DistErlang = DistErlang(stream, 2.5, 3)
    assert math.isclose(dist.probability_density(1.0),
            dist_erlang(3, 2.5, 1.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(2.0),
            dist_erlang(3, 2.5, 2.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(3.0),
            dist_erlang(3, 2.5, 3.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(4.0),
            dist_erlang(3, 2.5, 4.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(5.0),
            dist_erlang(3, 2.5, 5.0), abs_tol=0.0001)
    assert dist.probability_density(0.0) == 0.0
    assert dist.probability_density(-0.1) == 0.0

    with pytest.raises(TypeError):
        DistErlang('x', 0.1, 2)
    with pytest.raises(TypeError):
        DistErlang(stream, 'x', 2)
    with pytest.raises(TypeError):
        DistErlang(stream, 0.1, 'x')
    with pytest.raises(ValueError):
        DistErlang(stream, -0.1, 2)
    with pytest.raises(ValueError):
        DistErlang(stream, 0.1, -2)
    with pytest.raises(ValueError):
        DistErlang(stream, 0, 2)
    with pytest.raises(ValueError):
        DistErlang(stream, 0.1, 0)


def test_exponential():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistExponential = DistExponential(stream, 2.5)
    assert stream == dist.stream
    assert dist.mean == 2.5
    assert "Exponential" in str(dist)
    assert "2.5" in repr(dist)
    value: float = dist.draw()
    assert value >= 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    dist: DistExponential = DistExponential(stream, 2)
    value: float = dist.draw()
    assert value >= 0

    dist: DistExponential = DistExponential(stream, 2.5)
    l = 1 / 2.5
    assert math.isclose(dist.probability_density(0.0),
            l * math.exp(-l * 0.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(1.0),
            l * math.exp(-l * 1.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(2.0),
            l * math.exp(-l * 2.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(3.0),
            l * math.exp(-l * 3.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(4.0),
            l * math.exp(-l * 4.0), abs_tol=0.0001)
    assert dist.probability_density(-0.1) == 0.0
    
    with pytest.raises(TypeError):
        DistExponential('x', 0.1)
    with pytest.raises(TypeError):
        DistExponential(stream, 'x')
    with pytest.raises(ValueError):
        DistExponential(stream, -0.1)
    with pytest.raises(ValueError):
        DistExponential(stream, 0)


def test_gamma():
    
    def dist_gamma(alpha, theta, x) -> float:
        """Calculate probability density of DistErlang(k, scale) for value x. 
        From: https://mathworld.wolfram.com/GammaDistribution.html"""
        return ((x ** (alpha - 1)) * math.exp(-x / theta)
                / (math.gamma(alpha) * (theta ** alpha)))

    stream: StreamInterface = MersenneTwister(10)
    dist: DistGamma = DistGamma(stream, 1.5, 2.5)
    assert stream == dist.stream
    assert dist.shape == 1.5
    assert dist.scale == 2.5
    assert "Gamma" in str(dist)
    assert "1.5" in str(dist)
    assert "2.5" in repr(dist)
    value: float = dist.draw()
    assert value > 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    assert DistGamma(stream, 100, 0.1).draw() > 0
    assert DistGamma(stream, 1, 0.1).draw() > 0
    assert DistGamma(stream, 0.1, 0.1).draw() > 0
    assert DistGamma(stream, 0.9999, 0.1).draw() > 0
    assert DistGamma(stream, 0.0001, 1000.0).draw() > 0
    assert DistGamma(stream, 1000.0, 0.0001).draw() > 0

    dist: DistGamma = DistGamma(stream, 1.5, 2.5)
    assert math.isclose(dist.probability_density(0.5),
            dist_gamma(1.5, 2.5, 0.5), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(1.0),
            dist_gamma(1.5, 2.5, 1.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(2.0),
            dist_gamma(1.5, 2.5, 2.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(4.0),
            dist_gamma(1.5, 2.5, 4.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(8.0),
            dist_gamma(1.5, 2.5, 8.0), abs_tol=0.0001)
    assert dist.probability_density(0.0) == 0.0
    assert dist.probability_density(-0.1) == 0.0

    dist: DistGamma = DistGamma(stream, 0.5, 2.5)
    assert math.isclose(dist.probability_density(0.5),
            dist_gamma(0.5, 2.5, 0.5), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(1.0),
            dist_gamma(0.5, 2.5, 1.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(2.0),
            dist_gamma(0.5, 2.5, 2.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(4.0),
            dist_gamma(0.5, 2.5, 4.0), abs_tol=0.0001)
    assert math.isclose(dist.probability_density(8.0),
            dist_gamma(0.5, 2.5, 8.0), abs_tol=0.0001)
    assert dist.probability_density(0.0) == 0.0
    assert dist.probability_density(-0.1) == 0.0
    
    with pytest.raises(TypeError):
        DistGamma('x', 0.1, 2.0)
    with pytest.raises(TypeError):
        DistGamma(stream, 'x', 2.0)
    with pytest.raises(TypeError):
        DistGamma(stream, 0.1, 'x')
    with pytest.raises(ValueError):
        DistGamma(stream, -0.1, 2.0)
    with pytest.raises(ValueError):
        DistGamma(stream, 0.1, -2.0)

"""
Calculation of Pearson5(2, 1) probability density function in R with 
the following script:
    library(PearsonDS)
    options(digits=16)
    cat(dpearsonV(seq(0.1,4.0,by=0.1),shape=2,scale=1,location=0), sep="\n")
"""
PEARSON5_R = (
    0, 0,
    0.1, 0.0453999297624848,
    0.2, 0.842243374885683,
    0.3, 1.3212590128612,
    0.4, 1.28257810349841,
    0.5, 1.0826822658929,
    0.6, 0.874424087210934,
    0.7, 0.698691068343369,
    0.8, 0.559579681367558,
    0.9, 0.451567884510158,
    1, 0.367879441171442,
    1.1, 0.302697461704833,
    1.2, 0.25150359288604,
    1.3, 0.21091004516667,
    1.4, 0.178404394882271,
    1.5, 0.152123590824471,
    1.6, 0.130679059697019,
    1.7, 0.113027961123946,
    1.8, 0.0983802161758286,
    1.9, 0.0861317267679299,
    2, 0.0758163324640791,
    2.1, 0.0670710676617483,
    2.2, 0.0596108582776372,
    2.3, 0.0532099442823959,
    2.4, 0.04768812429112,
    2.5, 0.0429004829462809,
    2.6, 0.0387296539783446,
    2.7, 0.0350799446465025,
    2.8, 0.0318728378906309,
    2.9, 0.0290435225286957,
    3, 0.0265381966879181,
    3.1, 0.0243119573016754,
    3.2, 0.0223271371138501,
    3.3, 0.0205519858340651,
    3.4, 0.0189596177746153,
    3.5, 0.0175271671854294,
    3.6, 0.0162351064899898,
    3.7, 0.0150666930573313,
    3.8, 0.014007517979912,
    3.9, 0.0130451362502105,
    4, 0.0121687622354907
    )


def test_pearson5():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistPearson5 = DistPearson5(stream, 4, 2)
    assert stream == dist.stream
    assert dist.alpha == 4
    assert dist.beta == 2
    assert "Pearson5" in str(dist)
    assert "4.0" in str(dist)
    assert "2.0" in repr(dist)
    value: float = dist.draw()
    assert value >= 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    assert dist.probability_density(-1.0) == 0
    
    dist: DistPearson5 = DistPearson5(stream, 2, 1)
    for i in range(len(PEARSON5_R) // 2):
        assert math.isclose(dist.probability_density(PEARSON5_R[2 * i]),
                    PEARSON5_R[2 * i + 1], abs_tol=0.0001)

    with pytest.raises(TypeError):
        DistPearson5('x', 0.1, 2.0)
    with pytest.raises(TypeError):
        DistPearson5(stream, 'x', 2.0)
    with pytest.raises(TypeError):
        DistPearson5(stream, 0.1, 'x')
    with pytest.raises(ValueError):
        DistPearson5(stream, -0.1, 2.0)
    with pytest.raises(ValueError):
        DistPearson5(stream, 0.0, 2.0)
    with pytest.raises(ValueError):
        DistPearson5(stream, 0.1, -2.0)
    with pytest.raises(ValueError):
        DistPearson5(stream, 0.1, 0.0)

"""
Calculation of Pearson6(2, 3, 4) probability density function in R with 
the following script:
    library(PearsonDS)
    options(digits=16)
    cat(dpearsonVI(seq(0.0,10.0,by=0.1),a=2,b=3,scale=4,location=0), sep="\n")
"""
PEARSON6_R = (
    0, 0,
    0.1, 0.0662890715707137,
    0.2, 0.117528924970268,
    0.3, 0.156725692278776,
    0.4, 0.186276396917746,
    0.5, 0.208098358989991,
    0.6, 0.22372953088423,
    0.7, 0.234406672738247,
    0.8, 0.241126543209876,
    0.9, 0.244694005031216,
    1, 0.24576,
    1.1, 0.24485164420618,
    1.2, 0.242396166908613,
    1.3, 0.23874001913263,
    1.4, 0.234164177104221,
    1.5, 0.228896436532527,
    1.6, 0.223121318498244,
    1.7, 0.216988073020216,
    1.8, 0.210617162402749,
    1.9, 0.204105525863515,
    2, 0.19753086419753,
    2.1, 0.190955134197302,
    2.2, 0.184427404081944,
    2.3, 0.177986190901477,
    2.4, 0.171661376953125,
    2.5, 0.16547578327628,
    2.6, 0.159446463205313,
    2.7, 0.153585766922561,
    2.8, 0.147902218321985,
    2.9, 0.142401237764448,
    3, 0.137085738085321,
    3.1, 0.131956616196296,
    3.2, 0.127013158563227,
    3.3, 0.122253375549485,
    3.4, 0.117674276938075,
    3.5, 0.113272098765432,
    3.6, 0.109042489819672,
    3.7, 0.104980664699523,
    3.8, 0.101081529136102,
    3.9, 0.0973397822988683,
    4, 0.09375,
    4.1, 0.0903067020460723,
    4.2, 0.0870044064365618,
    4.3, 0.0838376726543463,
    4.4, 0.0808011359170598,
    4.5, 0.0778895339460241,
    4.6, 0.0750977275502468,
    4.7, 0.0724207161073927,
    4.8, 0.0698536488441549,
    4.9, 0.0673918326688645,
    5, 0.0650307371843723,
    5.1, 0.0627659974050269,
    5.2, 0.060593414614479,
    5.3, 0.0585089557282037,
    5.4, 0.0565087514636845,
    5.5, 0.0545890935701682,
    5.6, 0.0527464313271604,
    5.7, 0.0509773674850205,
    5.8, 0.0492786537910088,
    5.9, 0.0476471862189985,
    6, 0.0460799999999999,
    6.1, 0.0445742645330009,
    6.2, 0.0431272782408612,
    6.3, 0.0417364634236433,
    6.4, 0.0403993611514356,
    6.5, 0.0391136262301054,
    6.6, 0.0378770222662346,
    6.7, 0.0366874168515116,
    6.8, 0.0355427768818907,
    6.9, 0.0344411640227219,
    7, 0.0333807303276602,
    7.1, 0.032359714016377,
    7.2, 0.0313764354138156,
    7.3, 0.030429293051873,
    7.4, 0.029516759932897,
    7.5, 0.0286373799531814,
    7.6, 0.0277897644836961,
    7.7, 0.0269725891045436,
    7.8, 0.0261845904890693,
    7.9, 0.025424563433126,
    8, 0.0246913580246913,
    8.1, 0.0239838769488323,
    8.2, 0.023301072922885,
    8.3, 0.0226419462566635,
    8.4, 0.0220055425325047,
    8.5, 0.0213909504,
    8.6, 0.0207972994803356,
    8.7, 0.0202237583752675,
    8.8, 0.0196695327758789,
    8.9, 0.0191338636664075,
    9, 0.0186160256185815,
    9.1, 0.0181153251720602,
    9.2, 0.0176310992967414,
    9.3, 0.0171627139328636,
    9.4, 0.0167095626050008,
    9.5, 0.0162710651062133,
    9.6, 0.0158466662487842,
    9.7, 0.0154358346781359,
    9.8, 0.0150380617466766,
    9.9, 0.0146528604444849,
    10, 0.0142797643838876
    )


def test_pearson6():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistPearson6 = DistPearson6(stream, 4, 3, 2)
    assert stream == dist.stream
    assert dist.alpha1 == 4
    assert dist.alpha2 == 3
    assert dist.beta == 2
    assert "Pearson6" in str(dist)
    assert "4.0" in str(dist)
    assert "3.0" in str(dist)
    assert "2.0" in repr(dist)
    value: float = dist.draw()
    assert value >= 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value
    assert dist.probability_density(-1.0) == 0
    
    dist: DistPearson6 = DistPearson6(stream, 2, 3, 4)
    for i in range(len(PEARSON6_R) // 2):
        assert math.isclose(dist.probability_density(PEARSON6_R[2 * i]),
                    PEARSON6_R[2 * i + 1], abs_tol=0.0001)

    with pytest.raises(TypeError):
        DistPearson6('x', 1, 2, 3)
    with pytest.raises(TypeError):
        DistPearson6(stream, 'x', 2, 3)
    with pytest.raises(TypeError):
        DistPearson6(stream, 1, 'x', 3)
    with pytest.raises(TypeError):
        DistPearson6(stream, 1, 2, 'x')
    with pytest.raises(ValueError):
        DistPearson6(stream, -0.1, 2.0, 3.0)
    with pytest.raises(ValueError):
        DistPearson6(stream, 0.0, 2.0, 3.0)
    with pytest.raises(ValueError):
        DistPearson6(stream, 0.1, -2.0, 3.0)
    with pytest.raises(ValueError):
        DistPearson6(stream, 0.1, 0.0, 3.0)
    with pytest.raises(ValueError):
        DistPearson6(stream, 0.1, 2.0, -3.0)
    with pytest.raises(ValueError):
        DistPearson6(stream, 0.1, 2.0, 0.0)


def test_triangular():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistTriangular = DistTriangular(stream, 1, 2, 4)
    assert stream == dist.stream
    assert dist.lo == 1
    assert dist.mode == 2
    assert dist.hi == 4
    assert "Triangular" in str(dist)
    assert "4.0" in str(dist)
    assert "1.0" in str(dist)
    assert "2.0" in repr(dist)
    value: float = dist.draw()
    assert value >= 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value

    assert dist.probability_density(-1.0) == 0
    assert dist.probability_density(1.0) == 0
    assert dist.probability_density(4.0) == 0
    assert dist.probability_density(5.0) == 0

    for x in [xx / 100 for xx in range(0, 500, 2)]:
        if 1 <= x <= 2:
            assert math.isclose(dist.probability_density(x),
                2 * (x - 1) / ((4 - 1) * (2 - 1)), abs_tol=0.0001)
        elif 2 <= x <= 4:
            assert math.isclose(dist.probability_density(x),
                2 * (4 - x) / ((4 - 1) * (4 - 2)), abs_tol=0.0001)
        else:
            assert dist.probability_density(x) == 0

    with pytest.raises(TypeError):
        DistTriangular('x', 1, 2, 3)
    with pytest.raises(TypeError):
        DistTriangular(stream, 'x', 2, 3)
    with pytest.raises(TypeError):
        DistTriangular(stream, 1, 'x', 3)
    with pytest.raises(TypeError):
        DistTriangular(stream, 1, 2, 'x')
    with pytest.raises(ValueError):
        DistTriangular(stream, 2.5, 2.0, 3.0)
    with pytest.raises(ValueError):
        DistTriangular(stream, 0.0, 2.0, 1.0)
    with pytest.raises(ValueError):
        DistTriangular(stream, 3.0, 3.0, 3.0)
    with pytest.raises(ValueError):
        DistTriangular(stream, 1, 1, 1)


def test_uniform():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistUniform = DistUniform(stream, 1, 4)
    assert stream == dist.stream
    assert dist.lo == 1
    assert dist.hi == 4
    assert "Uniform" in str(dist)
    assert "4.0" in str(dist)
    assert "1.0" in repr(dist)
    value: float = dist.draw()
    assert value >= 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value

    assert dist.probability_density(-1.0) == 0
    assert dist.probability_density(0.999999) == 0
    assert math.isclose(dist.probability_density(1.0), 1 / 3, abs_tol=0.0001)
    assert math.isclose(dist.probability_density(2.5), 1 / 3, abs_tol=0.0001)
    assert math.isclose(dist.probability_density(4.0), 1 / 3, abs_tol=0.0001)
    assert dist.probability_density(4.000001) == 0
    assert dist.probability_density(5.0) == 0

    for x in [xx / 100 for xx in range(0, 500, 2)]:
        if 1 <= x <= 4:
            assert math.isclose(dist.probability_density(x), 1 / 3, abs_tol=0.0001)
        else:
            assert dist.probability_density(x) == 0

    with pytest.raises(TypeError):
        DistUniform('x', 1, 3)
    with pytest.raises(TypeError):
        DistUniform(stream, 'x', 2)
    with pytest.raises(TypeError):
        DistUniform(stream, 1, 'x')
    with pytest.raises(ValueError):
        DistUniform(stream, 2.5, 2.0)
    with pytest.raises(ValueError):
        DistUniform(stream, 3.0, 3.0)
    with pytest.raises(ValueError):
        DistUniform(stream, 1, 1)


def test_weibull():
    stream: StreamInterface = MersenneTwister(10)
    dist: DistWeibull = DistWeibull(stream, 3, 1)
    assert stream == dist.stream
    assert dist.alpha == 3
    assert dist.beta == 1
    assert "Weibull" in str(dist)
    assert "3.0" in str(dist)
    assert "1.0" in repr(dist)
    value: float = dist.draw()
    assert value >= 0
    assert dist.draw() != value
    dist.stream = MersenneTwister(10)
    assert dist.draw() == value

    assert dist.probability_density(-1.0) == 0
    assert dist.probability_density(0.0) == 0

    for a in [xx / 10 for xx in range(5, 55, 5)]:
        for b in [xx / 10 for xx in range(5, 55, 5)]:
            dist: DistWeibull = DistWeibull(stream, a, b)
            for x in [xx / 100 for xx in range(2, 1000, 2)]:
                if x == 0:
                    assert dist.probability_density(x) == 0
                else:
                    assert math.isclose(dist.probability_density(x),
                        a * math.pow(b, -a) * math.pow(x, a - 1) 
                        * math.exp(-math.pow(x / b, a)), abs_tol=0.001)

    with pytest.raises(TypeError):
        DistWeibull('x', 1, 3)
    with pytest.raises(TypeError):
        DistWeibull(stream, 'x', 2)
    with pytest.raises(TypeError):
        DistWeibull(stream, 1, 'x')
    with pytest.raises(ValueError):
        DistWeibull(stream, 0.0, 2.0)
    with pytest.raises(ValueError):
        DistWeibull(stream, -1.0, 3.0)
    with pytest.raises(ValueError):
        DistWeibull(stream, 1, 0)
    with pytest.raises(ValueError):
        DistWeibull(stream, 1, -1)


if __name__ == "__main__":
    pytest.main()
