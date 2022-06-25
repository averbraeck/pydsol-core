"""
dsol_core example with event scheduling for ordering equipment with
stochastic intervals. The example demonstrates the basic setup of an
event-scheduling simulation with just a single replication.

This example uses a full object-oriented way of creating and
implementing the simulation, with notification of the application object on
the completion of the simuation.
"""
import sys

from pydsol.core.experiment import SingleReplication, Replication
from pydsol.core.interfaces import ReplicationInterface
from pydsol.core.model import DSOLModel
from pydsol.core.pubsub import EventListener, Event
from pydsol.core.simulator import DEVSSimulatorFloat, DEVSSimulator


class Order:
    """Stores information about the order: product and amount"""

    def __init__(self, product: str, amount: int):
        self.product = product
        self.amount = amount
    
    def __repr__(self):
        return f"Order[{self.product}: {self.amount}]"

    
class Customer:
    """Customers regularly generate orders"""

    def __init__(self, simulator: DEVSSimulatorFloat):
        self.simulator = simulator
        self.simulator.schedule_event_now(self, "generate_order")
        
    def generate_order(self):
        order: Order = Order("television", 2)
        print(f"ordered {order} @ time={self.simulator.simulator_time}")
        self.simulator.schedule_event_rel(2.0, self, "generate_order")


class OrderModel(DSOLModel):
    """Contruction of the model: Creating a Customer"""

    def __init__(self, simulator: DEVSSimulator):
        super().__init__(simulator)
                
    def construct_model(self):
        print("\nReplication starts...")
        Customer(self.simulator)


class OrderApp(EventListener):
    """Application class that creates the whole simulation"""

    def __init__(self):
        simulator: DEVSSimulator = DEVSSimulatorFloat("sim")
        model: DSOLModel = OrderModel(simulator)
        replication: Replication = SingleReplication("rep1", 0.0, 0.0, 100.0)
        simulator.initialize(model, replication)
        simulator.add_listener(ReplicationInterface.END_REPLICATION_EVENT, self)
        simulator.start()
    
    def notify(self, event: Event):
        if event.event_type == ReplicationInterface.END_REPLICATION_EVENT:
            sys.exit(0)


"""main just creates the Application class"""
if __name__ == "__main__":
    OrderApp()
