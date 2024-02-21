PYDSOL - Python Distributed Simulation Object Library
=====================================================

What is pydsol?
    
* pydsol is an open source suite for discrete-event simulation and
  multi-formalism simulation.
     
* Originally it was programmed fully in Java, and it was introduced at 
  the Winter Simulation Conference in 2002.

* The starting points for DSOL were that it should be possible to create 
  simulation models that are inherently distributed, and simulation models 
  that are built on the premises of object oriented principles.
      
* DSOL is based on Zeigler's (2000) framework for modeling and simulation, 
  which means that the basic entities in a simulation study are a model 
  and a simulator, governed for experimentation by an experiment. 
    
* All these elements are present in the pydsol-core simulation framework: 
  the DSOLModel class that is extended by the user, the Simulator with 
  several implementations such as the DEVSSimulator, and the Experiment 
  class for defining the simulation experiment.


Implemented formalisms
======================
    
At the moment, only the event scheduling formalism has been implemented in 
pydsol-core. The process interaction, differential equations, flow modeling, 
classical DEVS, Port-based DEVS, hierarchical DEVS, and agent-based modeling
are all possible as extensions and will be added shortly. In the Java version
of DSOL, differential equations, process modeling, and various DEVS variants 
were implemented, which will be ported to Python.

An additional layer of pydsol-core is the package ``pydsol-model`` that provides standard model objects suitable for
developing a discrete event simulation model. Standard model objects are source, server
using resources, sink, node, link, entity and vehicle. Source code is available on
https://github.com/imvs95/pydsol-model.

Installation
=============

You can install the latest version of the ``pydsol-core`` package using pip::

    pip install pydsol-core

Alternatively, you can install the latest development version directly from GitHub::

    pip install git+https://github.com/averbraeck/pydsol-core

Documentation of ``pydsol-core`` is available at https://pydsol-core.readthedocs.io/en/latest/index.html.

DSOL license
============

DSOL has an open source BSD 3-clause license.

* Third party components used in DSOL can not have a license that is 
  more restrictive than permissive licenses such as BSD, Apache, MIT, 
  LGPL, Eclipse.

* pydsol can be incorporated in part or in full in other products for 
  any use (educational, commercial, whatever).

* pydsol may be extended or adapted by anyone into anything else 
  for any purpose.
