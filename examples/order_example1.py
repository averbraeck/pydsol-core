"""
dsol_core example with event scheduling for ordering equipment with
stochastic intervals. The example demonstrates the basic setup of an
event-scheduling simulation with just a single replication.

This example makes maximum use of Python structures and minimizes the
use of objects. There is just one class: the OrderModel.
"""
from pydsol.core.experiment import SingleReplication
from pydsol.core.model import DSOLModel
from pydsol.core.simulator import DEVSSimulatorFloat


class OrderModel(DSOLModel):
    """Construction of the model: Scheduling order generation"""
                
    def construct_model(self):
        print("\nReplication starts...")
        self.simulator.schedule_event_now(self, "generate_order")

    def generate_order(self):
        order = ("television", 2)
        print(f"ordered {order} @ time={self.simulator.simulator_time}")
        self.simulator.schedule_event_rel(2.0, self, "generate_order")


"""main creates the simulation and starts it"""
if __name__ == "__main__":
        simulator = DEVSSimulatorFloat("sim")
        model = OrderModel(simulator)
        replication = SingleReplication("rep1", 0.0, 0.0, 100.0)
        simulator.initialize(model, replication)
        simulator.start()
