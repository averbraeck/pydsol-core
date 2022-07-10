from abc import ABC, abstractmethod
from random import Random
import time

from pydsol.core.utils import get_module_logger
import math


__all__ = [
    "StreamInterface",
    "MersenneTwister",
    ]

logger = get_module_logger('streams')


class StreamInterface(ABC):
    """
    The StreamInterface defines the random streams to be used within the 
    pydsol project. The interface of the random package has changed quite 
    a lot over time, so this interface provides a stable wrapper.
    """

    @abstractmethod
    def next_bool(self) -> bool:
        """
        Return the next pseudo-random, uniformly distributed boolean value.
         
        Returns
        -------
        bool: a pseudo-random boolean with 50/50 chance for true or false
        """

    @abstractmethod
    def next_float(self) -> float:
        """
        Return a pseudo-random number from the stream over the interval [0,1) 
        using this stream, after advancing its state by one step.

        Returns
        -------
        float: a pseudo-random number between 0 and 1
        """

    @abstractmethod
    def next_int(self, lo:int, hi:int) -> int:
        """
        Return pseudo-random number from the stream between the 
        integers lo (inclusive) and hi (inclusive).
        
        Parameters
        ----------
        lo: int
            the minimal value (inclusive)
        hi: int
            the maximum value (nnclusive)
            
        Returns
        -------
        int: a value between lo and hi (both inclusive)
        """

    @abstractmethod
    def seed(self) -> int:
        """
        Return the seed of the generator.
        
        Returns
        -------
        int: the seed
        """

    @abstractmethod
    def original_seed(self) -> int:
        """
         Return the original seed of the generator with which it has been 
         first initialized.

        Returns
        -------
        int: the original seed of the generator when it was first initialized
        """

    @abstractmethod
    def set_seed(self, seed: int):
        """
        Set the seed of the generator.
        
        Parameters
        ----------
        seed: int
            the new seed
        """

    @abstractmethod
    def reset(self):
        """
        Reset the stream to use the original seed with which it was 
        initialized.
        """

    @abstractmethod
    def save_state(self) -> bytearray:
        """
        Save the state of the RNG into a byte array, e.g. to roll it 
        back to this state.
        
        Returns
        -------
        bytearray: the state as an object specific to the RNG.
        """

    @abstractmethod
    def restore_state(self, state: bytearray):
        """
        Restore the state from an earlier saved state object.
        
        Parameters
        ----------
        state: bytearray
            state Object; the earlier saved state to which the RNG rolls back.
        """


class MersenneTwister(StreamInterface):
    """
    The MersenneTwister class is the default random stream in pydsol. The
    class wraps the builtin Random class of Python, to enforce the fixed and
    stable StreamInterface for the random number class. 
    """
    
    def __init__(self, seed:int=None):
        """
        Create a new random stream to be used in a simulation. The model can
        define and use as many different and independent random streams as 
        needed. Note that when no initial seed is given, the class uses the
        current time in milliseconds as the seed -- an unknown number, but
        still reproducible when the stream uses calls reset(), or saves and
        retrieves its state. 
        """
        if seed is None:
            seed: int = round(time.time() * 1000)
            time.sleep(0.002)  # to avoid same seed in rapid succession
        else:
            if not isinstance(seed, int):
                raise TypeError(f"seed {seed} not an int")
            seed: int = seed
        self._original_seed: int = seed
        self._random: Random = Random()
        self.set_seed(seed)

    def next_bool(self) -> bool:
        """
        Return the next pseudo-random, uniformly distributed boolean value.
         
        Returns
        -------
        bool: a pseudo-random boolean with 50/50 chance for true or false
        """
        return self._random.random() < 0.5

    def next_float(self) -> float:
        """
        Return a pseudo-random number from the stream over the interval [0,1) 
        using this stream, after advancing its state by one step.

        Returns
        -------
        float: a pseudo-random number between 0 and 1
        """
        return self._random.random()
    
    def next_int(self, lo:int, hi:int) -> int:
        """
        Return pseudo-random number from the stream between the 
        integers lo (inclusive) and hi (inclusive).
        
        Parameters
        ----------
        lo: int
            the minimal value (inclusive)
        hi: int
            the maximum value (nnclusive)
            
        Returns
        -------
        int: a value between lo and hi (both inclusive)
        """
        return lo + math.floor((hi - lo + 1) * self._random.random())
    
    def seed(self) -> int:
        """
        Return the seed of the generator.
        
        Returns
        -------
        int: the seed
        """
        return self._seed

    def original_seed(self) -> int:
        """
         Return the original seed of the generator with which it has been 
         first initialized.

        Returns
        -------
        int: the original seed of the generator when it was first initialized
        """
        return self._original_seed

    def set_seed(self, seed: int):
        """
        Set the seed of the generator.
        
        Parameters
        ----------
        seed: int
            the new seed
        """
        self._seed: int = seed
        self._random.seed(seed)

    def reset(self):
        """
        Reset the stream to use the seed value. Note: when the seed has been
        changed, this method returns the seed to the changed value, not to 
        the original seed defined in the __init__ method.
        """
        self.set_seed(self._seed)

    def save_state(self) -> object:
        """
        Save the state of the RNG into an object, e.g. to roll it back to 
        this state. Note that the type of object can differ between RNGs.
        
        Returns
        -------
        object: the state as an object specific to the RNG.
        """
        return self._random.getstate()

    def restore_state(self, state: object):
        """
        Restore the state from an earlier saved state object. Note that the 
        type of object can differ between RNGs.
        
        Parameters
        ----------
        state: object
            state object; the earlier saved state to which the RNG rolls back.
        """
        self._random.setstate(state)
