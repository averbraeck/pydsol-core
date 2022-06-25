"""
pydsol_core contains the base classes for discrete-event simulation. The 
project is based on the Java implementation of DSOL (Distributed 
Simulation Object Library), first documented in 2002. Information about 
both libraries can be found at https://simulation.tudelft.nl

Modules
-------
exceptions
    generic exception for DSOL-specific problems.
simevent
    reference implementation of a simulation event with delayed method
    invocation on a target object instance through the execute() method.
eventlist
    reference implementation of an event list for simulation, using 
    a heap storage model that is faster than a red-black tree in Python.
pubsub
    strongly typed publish / subscribe pattern with events and timed
    events, where time can be linked to the simulator time.
model
    classes to help constructing models, provide input and parameters 
    for a model, and collect output from a model
experiment
    classes to define experiments, replications and run control for
    experimental design for model runs.
units
    quantities and units to use in simulations, with 'Duration' as the
    most important one as it can be used as for specifying time in a
    simulation.
    
Dependencies
------------
pydsol_core is only dependent on standard Python libraries. 
For the unit tests, pytest is used, potentially with pytest-cov to assess 
the test coverage.
"""
