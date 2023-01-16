"""
Stream and seed management is core to any good experimental design for
a simulation study. Simulation experiments should be fully reproducible
for scientific reasons. Yet, we also want different replications to use
different values for the stochastic variables. Seed management and the 
ability to set and change seeds is needed to accomplish this. To use 
techniques for variance reduction such as Common Random Numbers, multiple 
so-called streams of random values need to be defined in the simulation model. 
The StreamInterface and MersenneTwister implementation in this module make
it possible to have multiple random number streams, to reset the streams
independent of each other, and to save and retrieve the state of a random 
number generator.

This module contains one implementation of a Random Number Generator (RNG),
the Mersenne Twister that is considered the standard for modern stochastic
model implementations. The MersenneTwister class in the streams module wraps
the Random class from Python that already contains a decent implementation 
of the Mersenne Twister. Other RNGs can be easily added by extending the
StreamInterface Abstract Base Class, and implementing the abstract methods.

In addition to providing RNGs, the streams module also contains helper 
classes for stream and seed management. Again, when modelers want to use
a different algorithm than the ones provided here, it is sufficient to 
extend the StreamUpdater Abstract Base Class and implement the update_seed 
method. After this, the seed management class can be seamlessly used in
the model and experiment modules.         
"""

from abc import ABC, abstractmethod
from random import Random
import time
from typing import Dict, List

from pydsol.core.utils import get_module_logger
import math

__all__ = [
    "StreamInterface",
    "MersenneTwister",
    "StreamInformation",
    "StreamSeedInformation",
    "StreamUpdater",
    "StreamSeedUpdater",
    "SimpleStreamUpdater",
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
        bool
            a pseudo-random boolean with 50/50 chance for true or false
        """

    @abstractmethod
    def next_float(self) -> float:
        """
        Return a pseudo-random number from the stream over the interval [0,1) 
        using this stream, after advancing its state by one step.

        Returns
        -------
        float
            a pseudo-random number between 0 and 1
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
        int
            a value between lo and hi (both inclusive)
        """

    @abstractmethod
    def seed(self) -> int:
        """
        Return the seed of the generator.
        
        Returns
        -------
        int
            the seed
        """

    @abstractmethod
    def original_seed(self) -> int:
        """
         Return the original seed of the generator with which it has been 
         first initialized.

        Returns
        -------
        int
            the original seed of the generator when it was first initialized
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
    def save_state(self) -> object:
        """
        Save the state of the RNG into a byte array, e.g. to roll it 
        back to this state.
        
        Returns
        -------
        object
            the state as an object specific to the RNG.
        """

    @abstractmethod
    def restore_state(self, state: object):
        """
        Restore the state from an earlier saved state object.
        
        Parameters
        ----------
        state: object
            state Object; the earlier saved state to which the RNG rolls back.
        """


class MersenneTwister(StreamInterface):
    """
    The MersenneTwister class is the default random stream in pydsol. The
    class wraps the builtin Random class of Python, to enforce the fixed and
    stable StreamInterface for the random number class. 
    
    Attributes
    ----------
    _original_seed: int
        The seed value that the random stream has been initialized with 
        originally.
    _random: Random
        The wrapped Python implementation of the Mersenne Twister.
    """
    
    def __init__(self, seed:int=None):
        """
        Create a new random stream to be used in a simulation. The model can
        define and use as many different and independent random streams as 
        needed.
        
        Note
        ----
        Note that when no initial seed is given, the class uses the
        current time in milliseconds as the seed -- an unknown number, but
        still reproducible when the stream uses calls reset(), or saves and
        retrieves its state.
        
        Parameters
        ----------
        seed: int (optional)
            
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
        bool
            a pseudo-random boolean with 50/50 chance for true or false
        """
        return self._random.random() < 0.5

    def next_float(self) -> float:
        """
        Return a pseudo-random number from the stream over the interval [0,1) 
        using this stream, after advancing its state by one step.

        Returns
        -------
        float
            a pseudo-random number between 0 and 1
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
            the maximum value (inclusive)
            
        Returns
        -------
        int
            a value between lo and hi (both inclusive)
        """
        return lo + math.floor((hi - lo + 1) * self._random.random())
    
    def seed(self) -> int:
        """
        Return the seed of the generator.
        
        Returns
        -------
        int
            the seed
        """
        return self._seed

    def original_seed(self) -> int:
        """
         Return the original seed of the generator with which it has been 
         first initialized.

        Returns
        -------
        int
            the original seed of the generator when it was first initialized
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
        object
            the state as an object specific to the RNG.
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


class StreamInformation:
    """
    StreamInformation contains information about Random Streams that exists 
    before the model has been constructed. The model can use the (named)
    streams from this class. The Experiment can automatically take care 
    of updating the seeds of the Random Number Generators that are used
    in the model for each new replication or experiment.
    
    Attributes
    ----------
    _streams: dict[str, StreamInterface]
        dictionary of streams that are maintained for the model. Each stream
        is identified by a unique id in the dict.
    """
    
    def __init__(self, default_stream: StreamInterface=None):
        """
        Construct a StreamInformation object that can be used to pass 
        information about streams to to a model.
        
        Parameters
        ----------
        default_stream: StreamInterface
            The default stream that can be retrieved with the name "default"
            When default_stream is not provided, it will be created and 
            initialized with a fixed seed.
            
        Raises
        ------
        TypeError
            when default_stream is not implementing StreamInterface
        """
        self._streams: Dict[str, StreamInterface] = {}
        if default_stream is None:
            self._streams["default"] = MersenneTwister(10)
        elif isinstance(default_stream, StreamInterface):
            self._streams["default"] = default_stream
        else:
            raise TypeError("default_stream is not a stream object")
    
    def add_stream(self, stream_id: str, stream: StreamInterface):
        """
        Add a new stream, based on a stream id, possibly overwriting a 
        previous existing stream with the same stream_id. No warning will be 
        given if previous information is overwritten.
        
        Parameters
        ----------
        stream_id: str
            The name (id) of the stream to be added 
        stream: StreamInterface
            The stream to be added with the given stream_id
            
        Raises
        ------
        TypeError
            when stream_id is not a string
        TypeError
            when stream is not implementing StreamInterface
        """
        if not isinstance(stream_id, str):
            raise TypeError(f"stream_id {stream_id} is not a string")
        if not isinstance(stream, StreamInterface):
            raise TypeError("stream is not a StreamInterface object")
        self._streams[stream_id] = stream

    def get_streams(self) -> Dict[str, StreamInterface]:
        """
        Return the dict with streams of this model, where stream ids are
        mapped to the streams.
        
        Returns
        -------
        dict[str, StreamInterface]
            The dict with streams of this model
        """
        return self._streams
    
    def get_stream(self, stream_id: str) -> StreamInterface:
        """
        Return a specific stream, based on a stream id, or None when 
        no stream with that id is present.
        
        Parameters
        ----------
        stream_id: str
            The name (id) to look up the stream for
        
        Returns
        -------
        StreamInterface
            The stream belonging to the stream_id, or None if not present
        
        Raises
        ------
        TypeError
            when stream_id is not a string
        """
        if not isinstance(stream_id, str):
            raise TypeError(f"stream_id {stream_id} is not a string")
        return self._streams[stream_id]


class StreamSeedInformation(StreamInformation):
    """
    StreamSeedInformation stores information about the streams, but also 
    about the way the seeds have to be updated for each replication. 
    The StreamSeedUpdater class uses this StreamSeedInformation class to 
    make the seed updates. The seeds are predetermined and stored for
    each replication number in a list.
    
    Attributes
    ----------
    _stream_seeds: dict[str, list[int]]
        Dictionary of lists of seed values per replication that are 
        maintained for the model. Each list of seeds is identified by a 
        unique id in the dict that has to match a key in the _streams
        attribute in the parent StreamInformation class.
    """
    
    def __init__(self, default_stream: StreamInterface=None):
        """
        Construct a StreamSeedInformation object that can be used to pass 
        information about streams to to a model, and information about the
        seed values for each replication to the Experiment.
        
        Parameters
        ----------
        default_stream: StreamInterface
            The default stream that can be retrieved with the name "default"
            When default_stream is not provided, it will be created and 
            initialized with a fixed seed.
            
        Raises
        ------
        TypeError
            when default_stream is not implementing StreamInterface
        """
        super().__init__(default_stream)
        self._seeds: Dict[str, List[int]] = {}
        
    def add_seed_values(self, stream_id: str, seeds: List[int]):
        """
        Add a new seed list for a stream, based on a stream id, possibly 
        overwriting a previous existing seed list with the same stream_id. 
        No warning will be given is previous information is overwritten.
        
        Parameters
        ----------
        stream_id: str
            The id of the stream that has to already exist in the class.
        seeds: list[int]
            The list of seed values per replication number, 0-based.
            
        Raises
        ------
        TypeError
            when stream_id is not a string
        TypeError
            when seeds is not a list or seeds contains non-integers
        ValueError
            when the stream information with the given stream_id does not exist 
        """
        if not isinstance(stream_id, str):
            raise TypeError(f"stream_id {stream_id} is not a string")
        if not isinstance(seeds, list):
            raise TypeError("seeds is not a list")
        for seed in seeds:
            if not isinstance(seed, int):
                raise TypeError(f"seed {seed} is not an int")
        if self._streams[stream_id] == None:
            raise ValueError(f"stream with stream_id {stream_id} not found")
        self._seeds[stream_id] = seeds
        
    def get_seeds(self) -> Dict[str, List[int]]:
        """
        Return the dict with seed lists of this model, where stream ids are
        mapped to the seed lists.
        
        Returns
        -------
        dict[str, list[int]]
            The dict with seed lists of this model
        """
        return self._seeds
    
    def get_seed_values(self, stream_id: str) -> List[int]:
        """
        Return a specific set of seed values, based on a stream id, 
        or None when no seed values with that id are present.
        
        Returns
        -------
        list[int]: 
            The list of seed values belonging to the stream_id, or None if 
            not present
        
        Raises
        ------
        TypeError
            when stream_id is not a string
        """
        if not isinstance(stream_id, str):
            raise TypeError(f"stream_id {stream_id} is not a string")
        return self._seeds[stream_id]


class StreamUpdater(ABC):
    """
    The StreamUpdater abstract class defines the methods that determine 
    how to update the seed values for a replication.
    """
    
    def update_seeds(self, streams: Dict[str, StreamInterface],
                     replication_nr: int):
        """
        Update all seeds for the given replication number. The method should 
        be fully reproducible, and can be based on the previous seed values, 
        possibly the String representation, and the replication number.
        
        Parameters
        ----------
        streams: dict[str, StreamInterface]
            A dict mapping stream ids onto streams. This dict can come
            from the StreamInformation or StreamSeedInformation class, but
            that is not enforced. Any dict with this info will do. Note 
            that the structure of the dict is not checked.
        replication_nr: int
            The replication number for which to set the seed values.
            
        Raises
        ------
        TypeError
            when replication_nr is not an int
        """
        if not isinstance(replication_nr, int):
            raise TypeError(f"replication_nr {replication_nr} is not an int")
        for key in streams.keys():
            self.update_seed(key, streams[key], replication_nr)
    
    @abstractmethod
    def update_seed(self, key: str, stream: StreamInterface,
                    replication_nr: int):
        """
        Update one seed for the given streamId and replication number. 
        The method should be fully reproducible, and can be based on the 
        previous seed value of the stream, possibly the String 
        representation, and the replication number.
        """

    
class StreamSeedUpdater(StreamUpdater):
    """
    StreamSeedUpdater updates the seed for the streams in the replications
    based on a stored map of replication numbers to seed numbers.
    
    Attributes
    ----------
    _stream_seeds: dict[str, list[int]]
        The dict that maps the stream id on the seed lists for this 
        model where the seed list is indexed on the replication number.
    _fallback_stream_updater: StreamUpdater
        The updater that will be used to generate seed numbers for
        replications of streams that are not contained in the _stream_seeds 
        dict. 
    """
    
    def __init__(self, stream_seeds: Dict[str, List[int]]):
        """
        Construct a new StreamSeedUpdater object an initialize it with
        the seed map.
        
        Parameters
        ----------
        stream_seeds: dict[str, list[int]]: 
            The dict that maps the stream id on the seed lists for this 
            model where the seed list is indexed on the replication number.
            
        Raises
        ------
        TypeError
            when stream_seeds is not a dict
        TypeError
            when a key in stream_seeds is not a string
        TypeError
            when a value stream_seeds is not a list
        TypeError
            when a list with seeds is not containing only integers
        """
        if not isinstance(stream_seeds, dict):
            raise TypeError("stream_seeds is not a dict")
        for key in stream_seeds.keys():
            if not isinstance(key, str):
                raise TypeError(f"key {key} is not a string")
            if not isinstance(stream_seeds[key], list):
                raise TypeError(f"stream_seeds[{key}] value is not a list")
            for seed in stream_seeds[key]:
                if not isinstance(seed, int):
                    raise TypeError(f"seed {seed} is not an int")
        self._stream_seeds = stream_seeds
        self._fallback_stream_updater = SimpleStreamUpdater()
    
    def update_seed(self, stream_id: str, stream: StreamInterface,
                    replication_nr: int):
        """
        Update one seed for the given stream_id and replication number. 
        The method should be fully reproducible, and can be based on the 
        previous seed value of the stream, possibly the String 
        representation, and the replication number. The update guarantees
        random number reproducibility across runs and platforms for the
        given replication and random stream. When the stream_id is not 
        defined, the fallback updater will be used.
        
        Parameters
        ----------
        stream_id: str
            The id of the stream
        stream: StreamInterface
            The stream that needs to be updated
        replication_nr: int
            The replication to update the seed for
            
        Raises
        ------
        TypeError
            when stream_id is not a string
        TypeError
            when stream does not implement StreamInterface
        TypeError
            when replication_nr is not an int
        ValueError
            when replication_nr < 0 or > stored seed value list length
        """
        if not isinstance(stream_id, str):
            raise TypeError("stream_id is not a string")
        if not isinstance(stream, StreamInterface):
            raise TypeError("stream does not implement StreamInterface")
        if not isinstance(replication_nr, int):
            raise TypeError("replication_nr is not an int")
        if replication_nr < 0:
            raise ValueError("replication_nr < 0")
        if self._stream_seeds[stream_id] is None:
            self._fallback_stream_updater.update_seed(stream_id, stream,
                                                      replication_nr)
        else:
            if replication_nr >= len(self._stream_seeds[stream_id]):
                raise ValueError("replication_nr > seed list length")
            stream.set_seed(self._stream_seeds[stream_id][replication_nr])
        
    def set_fallback_stream_updater(self, stream_updater: StreamUpdater):
        """
        Set the fallback stream updater that can generate seed numbers for
        replications of streams that are not contained in the _stream_seeds 
        dict.
        
        Parameters
        ----------
        stream_updater: StreamUpdater
            The fallback stream updater that can generate seed numbers for
            replications of streams that are not contained in the 
            _stream_seeds dict.
            
        Raises
        ------
        TypeError
            when stream_updater does not implement StreamUpdater
        """
        if not isinstance(stream_updater, StreamUpdater):
            raise TypeError("stream_updater should implement StreeamUpdater")
        self._fallback_stream_updater = stream_updater
        
    def get_fallback_stream_updater(self) -> StreamUpdater:
        """
        Return the fallback stream updater that can generate seed numbers for
            replications of streams that are not contained in the 
            _stream_seeds dict.
            
        Returns
        -------
        The fallback stream updater that can generate seed numbers for
            replications of streams that are not contained in the 
            _stream_seeds dict.
        """
        return self._fallback_stream_updater
    
    def get_stream_seeds(self) -> Dict[str, List[int]]:
        """
        Return the dict that maps the stream names on the seed lists for this 
        model where the seed list is indexed on the replication number.
        
        Returns
        -------
        The dict that maps the stream names on the seed lists for this 
        model where the seed list is indexed on the replication number.
        """
        return self._stream_seeds


class SimpleStreamUpdater(StreamUpdater):
    """
    SimpleStreamUpdater updates the seed value for a replication based on 
    the hashCode of the name of the stream and the replication number.
    """
    
    def update_seed(self, stream_id: str, stream: StreamInterface,
                    replication_nr: int):
        """
        Update one seed for the given stream_id and replication number. 
        The method should be fully reproducible, and uses the the hashCode 
        of the id of the stream and the replication number to generate
        a seed value. The update guarantees random number reproducibility 
        across runs and platforms for the given replication and random stream.
        
        Parameters
        ----------
        stream_id: str
            The id of the stream
        stream: StreamInterface
            The stream that needs to be updated
        replication_nr: int
            The replication to update the seed for
            
        Raises
        ------
        TypeError
            when stream_id is not a string
        TypeError
            when stream does not implement StreamInterface
        TypeError
            when replication_nr is not an int
        ValueError
            when replication_nr < 0
        """
        if not isinstance(stream_id, str):
            raise TypeError("stream_id is not a string")
        if not isinstance(stream, StreamInterface):
            raise TypeError("stream does not implement StreamInterface")
        if not isinstance(replication_nr, int):
            raise TypeError("replication_nr is not an int")
        if replication_nr < 0:
            raise ValueError("replication_nr < 0")
        stream.set_seed(stream.original_seed() + replication_nr * 
                        (1_000_037 + hash(stream_id)))

