"""
Test the Simulator classes for correct functioning.
""" 

import pytest

from pydsol.core.simulator import DEVSSimulator, RunState, ReplicationState
from pydsol.core.units import Duration
from pydsol.core.utils import DSOLError
from pydsol.core.model import DSOLModel
from pydsol.core.interfaces import SimulatorInterface, ReplicationInterface, \
    ModelInterface
from pydsol.core.experiment import SingleReplication
from time import sleep


def test_simulator_base():
    s: DEVSSimulator = DEVSSimulator('sim', float, 0.0)
    assert s.name == 'sim'
    assert s.time_type == float
    assert s.simulator_time == 0.0
    assert s.initial_time == 0.0
    assert not s.is_initialized()
    assert not s.is_starting_or_running()
    assert s.is_stopping_or_stopped()
    assert s.run_state == RunState.NOT_INITIALIZED
    assert s.replication_state == ReplicationState.NOT_INITIALIZED
    
    with pytest.raises(DSOLError):
        DEVSSimulator(1, float, 0.0)
    with pytest.raises(DSOLError):
        DEVSSimulator('sim2', str, 0.0)
    with pytest.raises(DSOLError):
        DEVSSimulator('sim2', Duration, 0.0)


def test_initialize():

    class Model(DSOLModel):

        def __init__(self, simulator: SimulatorInterface):
            super().__init__(simulator)
            self.constructed = False
            self.count = 0
            
        def construct_model(self):
            self.constructed = True
            
        def inc(self):
            self.count += 1

    simulator: DEVSSimulator = DEVSSimulator('sim', float, 0.0)
    model: ModelInterface = Model(simulator)
    replication: ReplicationInterface = SingleReplication(
        'rep', 0.0, 10.0, 100.0)
    try:
        assert not model.constructed
        simulator.add_initial_method(model, 'inc')
        assert model.count == 0
        simulator.initialize(model, replication)
        assert simulator.simulator_time == 0.0
        assert simulator.initial_time == 0.0
        assert simulator.is_initialized()
        assert not simulator.is_starting_or_running()
        assert simulator.is_stopping_or_stopped()
        assert simulator.run_state == RunState.INITIALIZED
        assert simulator.replication_state == ReplicationState.INITIALIZED
        assert simulator.model == model
        assert simulator.replication == replication
        assert model.constructed
        assert model.count == 1
        # check wrong args for initialize 
        with pytest.raises(DSOLError):
            simulator.initialize('xyz', replication)
        with pytest.raises(DSOLError):
            simulator.initialize(model, 'xyz')
        # test if inbetwee cleanup is without errors 
        simulator.initialize(model, replication)
    except Exception as e:
        raise e
    finally:
        simulator.cleanup()


def test_run():

    class Model(DSOLModel):

        def __init__(self, simulator: SimulatorInterface):
            super().__init__(simulator)
            self.constructed = False
            self.count = 0
            
        def construct_model(self):
            self.constructed = True
            self.simulator.schedule_event_now(self, "inc")
            
        def inc(self):
            self.count += 1
            self.simulator.schedule_event_rel(10.0, self, "inc")

    simulator: DEVSSimulator = DEVSSimulator('sim', float, 0.0)
    model: ModelInterface = Model(simulator)
    replication: ReplicationInterface = SingleReplication(
        'rep', 0.0, 10.0, 100.0)
    try:
        assert not model.constructed
        simulator.initialize(model, replication)
        assert model.count == 0
        simulator.start()
        while simulator.is_starting_or_running():
            sleep(0.01)
        assert model.count == 11  # (0, 10, ..., 100)
        assert simulator.simulator_time == 100.0
        assert simulator.is_initialized()
        assert not simulator.is_starting_or_running()
        assert simulator.is_stopping_or_stopped()
        assert simulator.run_state == RunState.ENDED
        assert simulator.replication_state == ReplicationState.ENDED
        # cannot start simulator that has ended
        with pytest.raises(DSOLError):
            simulator.start()
        # cannot step simulator that has ended
        with pytest.raises(DSOLError):
            simulator.step()
        # cannot stop simulator that has ended
        with pytest.raises(DSOLError):
            simulator.stop()
    except Exception as e:
        raise e
    finally:
        simulator.cleanup()

    
def test_step():

    class Model(DSOLModel):

        def __init__(self, simulator: SimulatorInterface):
            super().__init__(simulator)
            self.constructed = False
            self.count = 0
            
        def construct_model(self):
            self.constructed = True
            self.simulator.schedule_event_now(self, "inc")
            
        def inc(self):
            self.count += 1
            self.simulator.schedule_event_rel(10.0, self, "inc")

    simulator: DEVSSimulator = DEVSSimulator('sim', float, 0.0)
    model: ModelInterface = Model(simulator)
    # warmup at 50 to avoid extra event
    replication: ReplicationInterface = SingleReplication(
        'rep', 0.0, 50.0, 100.0)
    try:
        assert not model.constructed
        simulator.initialize(model, replication)
        assert model.count == 0
        simulator.step()
        while simulator.is_starting_or_running():
            sleep(0.01)
        assert model.count == 1
        assert simulator.simulator_time == 0.0
        simulator.step()
        while simulator.is_starting_or_running():
            sleep(0.01)
        assert model.count == 2
        assert simulator.simulator_time == 10.0
    except Exception as e:
        raise e
    finally:
        simulator.cleanup()
    
    
def test_devs_simulator():
    pass


if __name__ == "__main__":
    pytest.main()
