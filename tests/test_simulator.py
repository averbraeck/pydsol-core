"""
Test the Simulator classes for correct functioning.
""" 

from time import sleep

import pytest

from pydsol.experiment import SingleReplication
from pydsol.interfaces import SimulatorInterface, ReplicationInterface, \
    ModelInterface
from pydsol.model import DSOLModel
from pydsol.pubsub import EventListener, Event, TimedEvent
from pydsol.simevent import SimEvent
from pydsol.simulator import DEVSSimulator, RunState, ReplicationState, \
    DEVSSimulatorFloat
from pydsol.units import Duration
from pydsol.utils import DSOLError


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
    assert not model.constructed
    simulator.add_initial_method(model, 'inc')
    assert model.count == 0
    with pytest.raises(DSOLError):
        simulator.start() # uninitialized
    try:
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
    sim2: DEVSSimulator = DEVSSimulator('sim2', float, 0.0)
    mod2: ModelInterface = NoSimModel(simulator)
    rep2: ReplicationInterface = SingleReplication("rep2", 0.0, 0.0, 100.0)
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
        with pytest.raises(DSOLError):
            simulator.step() # uninitialized
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
        sleep(0.5)  # seconds
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
        assert not simulator.is_starting_or_running()
        assert simulator.is_stopping_or_stopped()
        assert simulator.run_state == RunState.STOPPED
        assert simulator.replication_state == ReplicationState.STARTED
    except Exception as e:
        raise e
    finally:
        simulator.cleanup()


def test_start_events():
    """test the sequence of events from a simulation run"""

    class Model(DSOLModel):

        def __init__(self, simulator: SimulatorInterface):
            super().__init__(simulator)
            
        def construct_model(self):
            self.simulator.schedule_event_now(self, "inc")
            
        def inc(self):
            self.simulator.schedule_event_rel(10.0, self, "inc")
    
    class Collector(EventListener):

        def __init__(self):
            self.events: list[Event] = [];
            
        def notify(self, event: Event):
            self.events.append(event)
            
    simulator: DEVSSimulator = DEVSSimulator('sim', float, 0.0)
    model: ModelInterface = Model(simulator)
    replication: ReplicationInterface = SingleReplication(
        'rep', 0.0, 5.0, 100.0)
    # add the subscriptions to the events
    collector: Collector = Collector()
    simulator.add_listener(SimulatorInterface.START_EVENT, collector)
    simulator.add_listener(SimulatorInterface.STARTING_EVENT, collector)
    simulator.add_listener(SimulatorInterface.STOP_EVENT, collector)
    simulator.add_listener(SimulatorInterface.STOPPING_EVENT, collector)
    simulator.add_listener(SimulatorInterface.TIME_CHANGED_EVENT, collector)
    simulator.add_listener(ReplicationInterface.START_REPLICATION_EVENT, collector)
    simulator.add_listener(ReplicationInterface.WARMUP_EVENT, collector)
    simulator.add_listener(ReplicationInterface.END_REPLICATION_EVENT, collector)
    
    # run the model
    try:
        simulator.initialize(model, replication)
        simulator.start()
        while simulator.is_starting_or_running():
            sleep(0.01)
    except Exception as e:
        raise e
    finally:
        simulator.cleanup()
            
    # Check if the events arrived in the right order
    ce: list[Event] = collector.events
    assert ce[0].event_type == ReplicationInterface.START_REPLICATION_EVENT
    assert ce[1].event_type == SimulatorInterface.STARTING_EVENT
    assert ce[2].event_type == SimulatorInterface.START_EVENT
    assert ce[3].event_type == SimulatorInterface.TIME_CHANGED_EVENT  # t=0
    assert ce[4].event_type == ReplicationInterface.WARMUP_EVENT  # t = 5
    for i in range(1, 11):
        assert ce[4 + i].event_type == SimulatorInterface.TIME_CHANGED_EVENT
        assert isinstance(ce[4 + i], TimedEvent)
        assert ce[4 + i].timestamp == 10 * i 
    assert ce[15].event_type == SimulatorInterface.STOP_EVENT
    assert ce[16].event_type == ReplicationInterface.END_REPLICATION_EVENT


def test_step_events():
    """test the sequence of events from a simulation step"""

    class Model(DSOLModel):

        def __init__(self, simulator: SimulatorInterface):
            super().__init__(simulator)
            
        def construct_model(self):
            self.simulator.schedule_event_now(self, "inc")
            
        def inc(self):
            self.simulator.schedule_event_rel(10.0, self, "inc")
    
    class Collector(EventListener):

        def __init__(self):
            self.events: list[Event] = [];
            
        def notify(self, event: Event):
            self.events.append(event)
            
    simulator: DEVSSimulator = DEVSSimulatorFloat('sim')
    model: ModelInterface = Model(simulator)
    replication: ReplicationInterface = SingleReplication(
        'rep', 0.0, 5.0, 100.0)
    # add the subscriptions to the events
    collector: Collector = Collector()
    simulator.add_listener(SimulatorInterface.START_EVENT, collector)
    simulator.add_listener(SimulatorInterface.STARTING_EVENT, collector)
    simulator.add_listener(SimulatorInterface.STOP_EVENT, collector)
    simulator.add_listener(SimulatorInterface.STOPPING_EVENT, collector)
    simulator.add_listener(SimulatorInterface.TIME_CHANGED_EVENT, collector)
    simulator.add_listener(ReplicationInterface.START_REPLICATION_EVENT, collector)
    simulator.add_listener(ReplicationInterface.WARMUP_EVENT, collector)
    simulator.add_listener(ReplicationInterface.END_REPLICATION_EVENT, collector)
    
    # run the model
    try:
        simulator.initialize(model, replication)
        
        # first step: t = 0
        simulator.step()
        while simulator.is_starting_or_running():
            sleep(0.01)
        # Check if the events arrived in the right order
        ce: list[Event] = collector.events
        assert ce[0].event_type == ReplicationInterface.START_REPLICATION_EVENT
        assert ce[1].event_type == SimulatorInterface.START_EVENT
        assert ce[2].event_type == SimulatorInterface.TIME_CHANGED_EVENT
        assert isinstance(ce[2], TimedEvent)
        assert ce[2].timestamp == 0.0
        assert ce[3].event_type == SimulatorInterface.STOP_EVENT
        assert len(ce) == 4

        # second step: t = 5: warmup event
        collector.events.clear()
        simulator.step()
        while simulator.is_starting_or_running():
            sleep(0.01)
        # Check if the events arrived in the right order
        ce: list[Event] = collector.events
        assert ce[0].event_type == SimulatorInterface.START_EVENT
        assert ce[1].event_type == SimulatorInterface.TIME_CHANGED_EVENT
        assert isinstance(ce[1], TimedEvent)
        assert ce[1].timestamp == 5.0
        assert ce[2].event_type == ReplicationInterface.WARMUP_EVENT
        assert isinstance(ce[2], TimedEvent)
        assert ce[2].timestamp == 5.0
        assert ce[3].event_type == SimulatorInterface.STOP_EVENT
        assert len(ce) == 4

        # third step: t = 10
        collector.events.clear()
        simulator.step()
        while simulator.is_starting_or_running():
            sleep(0.01)
        # Check if the events arrived in the right order
        ce: list[Event] = collector.events
        assert ce[0].event_type == SimulatorInterface.START_EVENT
        assert ce[1].event_type == SimulatorInterface.TIME_CHANGED_EVENT
        assert isinstance(ce[1], TimedEvent)
        assert ce[1].timestamp == 10.0
        assert ce[2].event_type == SimulatorInterface.STOP_EVENT
        assert len(ce) == 3

    except Exception as e:
        raise e
    finally:
        simulator.cleanup()

    
def test_devs_simulator():

    class Target:

        def method0(self):
            pass

        def method1(self, nr: int):
            pass

    simulator: DEVSSimulator = DEVSSimulatorFloat("sim")
    simulator._simulator_time = 10.0;
    assert simulator.eventlist().size() == 0
    simulator.schedule_event_now(Target, "method0", 4)
    assert simulator.eventlist().size() == 1
    event: SimEvent = simulator.eventlist().peek_first()
    assert event.target == Target
    assert event.method == "method0"
    assert event.priority == 4
    assert event.time == 10.0
    event2 = simulator.schedule_event_rel(10.0, Target, "method0", 7)
    assert simulator.eventlist().size() == 2
    assert event2.target == Target
    assert event2.method == "method0"
    assert event2.priority == 7
    assert event2.time == 20.0
    event3 = simulator.schedule_event_abs(15.0, Target, "method1", 2, nr=27)
    assert simulator.eventlist().size() == 3
    assert event3.target == Target
    assert event3.method == "method1"
    assert event3.priority == 2
    assert event3.time == 15.0
    assert event3.kwargs == {'nr': 27}

    with pytest.raises(DSOLError):
        simulator.schedule_event_now('Target', "method2")
    with pytest.raises(DSOLError):
        simulator.schedule_event_abs(5, 'Target', "method0")
    with pytest.raises(DSOLError):
        simulator.schedule_event(SimEvent(5, 'Target', "method0"))
    with pytest.raises(DSOLError):
        simulator.schedule_event_rel(-5, 'Target', "method0")

if __name__ == "__main__":
    pytest.main()
