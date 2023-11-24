==============
Basic Tutorial
==============

## Introduction to Event Scheduling in Simulation

Event scheduling is a core concept in discrete event simulation where events occur at specific points in time, changing the state of the system. This tutorial will guide you through creating a simple event-scheduling simulation using DSOL (Distributed Simulation Object Library) in Python.

## Objective

We will develop a simulation to model an equipment ordering process with stochastic intervals. We'll use Python and DSOL's core libraries to demonstrate a basic event-scheduling setup.

## Prerequisites

- Python installed on your system.
- Basic understanding of Python programming.
- Familiarity with concepts of discrete event simulation.

## Step-by-Step Guide

### 1. Setting Up Your Environment

First, ensure you have the pydsol-core library installed. You can install it via pip:

.. code-block:: bash

    pip install pydsol-core

### 2. Understanding the Code Structure

Our simulation will have two primary components:

- `OrderModel`: A class representing our simulation model.
- Main Execution Block: Where we initialize and run the simulation.

### 3. Implementing the OrderModel Class

.. code-block:: python
    :linenos:

        from pydsol.core.model import DSOLModel

        class OrderModel(DSOLModel):
            """Construction of the model: Scheduling order generation"""

            def construct_model(self):
                print("\nReplication starts...")
                self.simulator.schedule_event_now(self, "generate_order")

            def generate_order(self):
                order = ("television", 2)
                print(f"ordered {order} @ time={self.simulator.simulator_time}")
                self.simulator.schedule_event_rel(2.0, self, "generate_order")

### 4. Setting Up the Main Execution Block

- We create a simulator instance.
- Initialize the `OrderModel`.
- Define a single replication experiment.
- Start the simulation.

.. code-block:: python
    :linenos:

        from pydsol.core.experiment import SingleReplication
        from pydsol.core.simulator import DEVSSimulatorFloat

        if __name__ == "__main__":
            simulator = DEVSSimulatorFloat("sim")
            model = OrderModel(simulator)
            replication = SingleReplication("rep1", 0.0, 0.0, 100.0)
            simulator.initialize(model, replication)
            simulator.start()

### 5. Running Your Simulation

Run your Python script. The output will display ordered items and their order times, illustrating the event-scheduling process.

### 6. Experimenting and Learning

Try modifying the intervals or the items being ordered to see how the simulation reacts. This hands-on approach is a great way to understand event scheduling in simulation.

## Conclusion

Congratulations! You've successfully built and run a basic event-scheduling simulation using DSOL in Python. This tutorial serves as a foundation for more complex simulations involving event scheduling.

## Next Steps

- Explore more features of the DSOL library.
- Integrate more complex logic into the OrderModel.
- Experiment with different types of replications and simulations.

Happy Simulating!