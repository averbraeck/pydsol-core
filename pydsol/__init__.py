"""
pydsol_core contains the base classes for discrete-event simulation. The 
project is based on the Java implementation of DSOL (Distributed 
Simulation Object Library), first documented in 2002. Information about 
both libraries can be found at https://simulation.tudelft.nl

Modules
-------
distributions
    Stochastic distributions for simulations.
eventlist
    Reference implementation of an event list for discrete-event simulation, 
    using a heap storage model that is faster than a red-black tree in Python.
experiment
    Classes to define experiments, replications and run control for
    experimental design for model runs.
interfaces
    Common interfaces for classes to avoid circular references. The equivalent
    of the .h files in C++.
model
    Classes to help constructing models, provide input and parameters 
    for a model, and collect output from a model
parameters
    Input parameters for a simulation study.
pubsub
    Strongly typed publish / subscribe pattern with events and timed
    events, where time can be linked to the simulator time.
simevent
    Reference implementation of a simulation event with delayed method
    invocation on a target object instance through the execute() method.
simulator
    Simulator that can execute an experiment on a discrete-event simulation
    model.
statistics
    Output statistics of a simulation study, plus general statistical objects.
streams
    Random streams and seed management for experiments and replications.
units
    Quantities and units to use in simulations, with 'Duration' as the
    most important one as it can be used as for specifying simulation time.
utils
    Utilities and functions that are missing in the Python distribution. 
    

Dependencies
------------
pydsol_core is only dependent on standard Python libraries. 
For the unit tests, pytest is used, potentially with pytest-cov to assess 
the test coverage.
"""
