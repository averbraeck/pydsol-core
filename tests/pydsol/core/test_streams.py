"""
Test the classes in the streams module
""" 

import math

import pytest

from pydsol.core.streams import MersenneTwister, StreamInterface


streams_to_test: list[StreamInterface] = [MersenneTwister(101)]


def test_stream_float():
    nr: int = 100000
    for stream in streams_to_test:
        sumv = 0.0
        minv = 1.0
        maxv = 0.0
        for _ in range(nr):
            value = stream.next_float()
            assert value >= 0.0
            assert value <= 1.0
            sumv += value
            minv = min(minv, value)
            maxv = max(maxv, value)
        assert math.isclose(sumv / (1.0 * nr), 0.5, abs_tol=0.01)
        assert math.isclose(minv, 0.0, abs_tol=0.01)
        assert math.isclose(maxv, 1.0, abs_tol=0.01)
        assert minv >= 0
        assert maxv <= 1
    
    # errors
    with pytest.raises(TypeError):
        MersenneTwister('x')

  
def test_stream_int_0_to_9():
    nr: int = 100000
    for stream in streams_to_test:
        sumv = 0
        bins = [0] * 10
        minv = 10.0
        maxv = -1.0
        for _ in range(nr):
            value = stream.next_int(0, 9)
            bins[value] += 1
            sumv += value
            minv = min(minv, value)
            maxv = max(maxv, value)
        for i in range(0, 9):
            perc = 100.0 * bins[i] / (1.0 * nr)
            assert math.isclose(perc, 10.0, abs_tol=0.2)
        assert math.isclose(sumv / nr, 4.5, abs_tol=0.01)
        assert minv == 0
        assert maxv == 9


def test_stream_bool():
    nr: int = 100000
    for stream in streams_to_test:
        sumv = 0
        bins = [0] * 2
        for _ in range(nr):
            value = stream.next_bool()
            bins[value] += 1
            sumv += value
        assert math.isclose(bins[0] / nr, 0.5, abs_tol=0.01)
        assert math.isclose(bins[1] / nr, 0.5, abs_tol=0.01)
        assert math.isclose(sumv / nr, 0.5, abs_tol=0.01)


def test_seed_management():
    for stream in streams_to_test:
        assert stream.seed() == 101
        assert stream.original_seed() == 101
        stream.reset()
        assert stream.seed() == 101
        assert stream.original_seed() == 101
        f = stream.next_float()
        assert stream.seed() == 101
        assert stream.original_seed() == 101
        stream.reset()
        assert stream.next_float() == f
        stream.set_seed(102)
        stream.reset()
        assert stream.next_float() != f
        assert stream.seed() == 102
        assert stream.original_seed() == 101
        stream.set_seed(stream.original_seed())
        assert stream.seed() == 101
        assert stream.original_seed() == 101
        stream.reset()
        assert stream.next_float() == f
    # random seed
    assert MersenneTwister().next_float() != MersenneTwister().next_float() 


def test_save_restore():
    for stream in streams_to_test:
        for _ in range(20):
            stream.next_float()
        state = stream.save_state()
        nf = stream.next_float()
        for _ in range(20):
            stream.next_float()
        stream.restore_state(state)
        assert stream.next_float() == nf


if __name__ == '__main__':
    pytest.main()
