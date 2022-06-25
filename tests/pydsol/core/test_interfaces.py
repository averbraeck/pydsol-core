"""
Test the interface classes that prevent circular referencing. Note that the 
static events are defined here so they are accessible to all other classes.
""" 
from pydsol.core.interfaces import SimulatorInterface, ReplicationInterface,\
    ExperimentInterface, ModelInterface
from pydsol.core.pubsub import EventType


def test_simulator():
    assert type(SimulatorInterface.START_EVENT) == EventType
    assert SimulatorInterface.START_EVENT.name == "START_EVENT"
    assert type(SimulatorInterface.STARTING_EVENT) == EventType
    assert SimulatorInterface.STARTING_EVENT.name == "STARTING_EVENT"
    assert type(SimulatorInterface.STOP_EVENT) == EventType
    assert SimulatorInterface.STOP_EVENT.name == "STOP_EVENT"
    assert type(SimulatorInterface.STOPPING_EVENT) == EventType
    assert SimulatorInterface.STOPPING_EVENT.name == "STOPPING_EVENT"
    assert type(SimulatorInterface.TIME_CHANGED_EVENT) == EventType
    assert SimulatorInterface.TIME_CHANGED_EVENT.name == "TIME_CHANGED_EVENT"


def test_replication():
    assert type(ReplicationInterface.START_REPLICATION_EVENT) == EventType
    assert ReplicationInterface.START_REPLICATION_EVENT.name == "START_REPLICATION_EVENT"
    assert type(ReplicationInterface.END_REPLICATION_EVENT) == EventType
    assert ReplicationInterface.END_REPLICATION_EVENT.name == "END_REPLICATION_EVENT"
    assert type(ReplicationInterface.WARMUP_EVENT) == EventType
    assert ReplicationInterface.WARMUP_EVENT.name == "WARMUP_EVENT"


def test_experiment():
    assert type(ExperimentInterface.START_EXPERIMENT_EVENT) == EventType
    assert ExperimentInterface.START_EXPERIMENT_EVENT.name == "START_EXPERIMENT_EVENT"
    assert type(ExperimentInterface.END_EXPERIMENT_EVENT) == EventType
    assert ExperimentInterface.END_EXPERIMENT_EVENT.name == "END_EXPERIMENT_EVENT"


def test_model():
    assert getattr(ModelInterface, "construct_model", None) != None


if __name__ == '__main__':
    pytest.main()
