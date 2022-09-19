from pydsol.simulator import Simulator, DEVSSimulatorFloat
from pydsol.model import DSOLModel
from pydsol.experiment import SingleReplication

"""
This example shows that start and stop can be called quickly after
another, without leading to deadlocks or threading problems with the
Simulator and the SimulatorWorkerThread.
"""

if __name__ == "__main__":
    
    sim: Simulator = DEVSSimulatorFloat('sim')

    class Model(DSOLModel):

        def __init__(self, simulator: Simulator):
            super().__init__(simulator)
            self.value = 0
        
        def construct_model(self):
            self.simulator.schedule_event_now(self, 'inc')
            
        def inc(self):
            self.value += 1
            self.simulator.schedule_event_rel(1.0, self, 'inc')
        
    model: Model = Model(sim)
    rep: SingleReplication = SingleReplication('rep', 0, 0, 1E20)
    sim.initialize(model, rep)
    
    while model.value < 250000:
        sim.start()
        print(f"start val={model.value}")
        sim.stop()
        print(f"stop  val={model.value}")
    sim.end_replication()