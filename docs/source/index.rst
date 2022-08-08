.. pydsol-core documentation master file, original file created by
   sphinx-quickstart on Sat Jul 16.

=========================
pydsol-core documentation
=========================

pydsol-core is the core library for disscrete simulation bsed on the Java 
DSOL (Distributed Simulation Object Library) framework. pydsol is a library
to quickly build simulation models, ranging from extremely simple queueing
models to extended discrete-event or agent-based models. The pydsol
framework is fully object oriented, so a model is built by building and 
instantiating Pyton classes.

pydsol-core provides a rich set of classes in a number of basic basic modules 
to construct and run a basic discrete simulation model:

* model.py: the **Model** that contains the logic of the simulation to run.
* simulator.py: the **Simulator** that can execute the discrete model.
* eventlist.py: the core event scheduling data structure of the Simulator.
* simevent.py: the events that are scheduled on the event list. 
* experiment.py: the **Experiment** that defines the experimental design.
* parameters.py: the input parameters for the simulation model.
* statistics.py: calculation of the output results of the simulation model.
* distributions.py: stochastic distributions to use in stochastic models.
* streams.py: random number streams that the experiment and distributions use.
* units.py: strongly types quantities such as Length and Speed for modeling.
* supporting modules include interfaces.py and utils.py with generic functions.

The basic idea of the pydsol framework is that a *Simulator* executes an 
*Experiment* for a *Model*. The Experiment defines *Random Streams* for 
stochastic *Distributions*. *Input Parameters* and *Statistics* define the 
inputs and outpus of the model. This framework links exactly to the formal
definition of simulation models, e.g. according to `Zeigler et al. (2000)
<https://dl.acm.org/doi/10.5555/580780>`__.  

.. toctree::
   :maxdepth: 1
   :caption: Getting Started:
   
   ./overview.rst
   ./installation.rst


.. toctree::
   :maxdepth: 1
   :caption: User Guide:
   
   ./tutorial.rst
   ./examples.rst
   

.. toctree::
   :maxdepth: 2
   :caption: API Documentation

   ./api_index.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
