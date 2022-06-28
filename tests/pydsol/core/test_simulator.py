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

    class NoSimModel(DSOLModel):

        def __init__(self, simulator: SimulatorInterface):
            pass
        
        def construct_model(self):
            pass

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
    
    # check error when model constructor does not call super().__init__
    sim2 : DEVSSimulator = DEVSSimulator('sim2', float, 0.0)
    mod2 : ModelInterface = NoSimModel(simulator)
    rep2 : ReplicationInterface = SingleReplication("rep2", 0.0, 0.0, 100.0)
    with pytest.raises(DSOLError):
        sim2.initialize(mod2, rep2)


def test_start():

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


def test_stop():

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
        'rep', 0.0, 10.0, 1E15)
    try:
        assert not model.constructed
        simulator.initialize(model, replication)
        assert model.count == 0
        simulator.start()
        sleep(0.5) # seconds
        assert simulator.simulator_time > 0
        assert simulator.is_starting_or_running()
        assert not simulator.is_stopping_or_stopped()
        assert simulator.run_state == RunState.STARTED
        assert simulator.replication_state == ReplicationState.STARTED
        # cannot re-initialize simulator that is running
        with pytest.raises(DSOLError):
            simulator.initialize(model, replication)
        # cannot start simulator that is running
        with pytest.raises(DSOLError):
            simulator.start()
        # cannot step simulator that is running
        with pytest.raises(DSOLError):
            simulator.step()
        # but we can stop!
        simulator.stop()
        sleep(0.1) # seconds
        assert not simulator.is_starting_or_running()
        assert simulator.is_stopping_or_stopped()
        assert simulator.run_state == RunState.STOPPED
        assert simulator.replication_state == ReplicationState.STARTED
    except Exception as e:
        raise e
    finally:
        simulator.cleanup()

    
def test_devs_simulator():
    pass


if __name__ == "__main__":
    pytest.main()
