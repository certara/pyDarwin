

Implementation
==============================================
  
All 5 algorithms search a user defined discrete search space. The search space consists of N 
dimension, where each dimension is a set of options for the search. For example, if 
the user would like the search to include 1, or 2 or 3 compartments, this would be a dimesion with 
three values. Similarly, a dimension might include linear or Michaelis-Menten or combined 
linear an Michaelis-Menten. Two key notes:

** The search space is stricty categorical. While some search dimensions could be viewed 
as ordered categorical, they are all treated a unordered categorical.

** A point in the search space defines a model, this point will have exactly one value 
in each dimension. That is, the model will be one or two or three compartments, but must be 
exactly one of those.

The search space is set up identially for all search algorithms. 
For some algorithms (GP, RF, GBRT and exhuastive) 
the space is treated an an integer array, for others (GA and downhill) the space is coded 
as a bit array. 

Three files are required to define the search:

:ref:`The template file`

:ref:`The tokens file`

:ref:`The options file`   
 
Running pyDarwin
~~~~~~~~~~~~~~~~~~~~

Two methods of running pyDarwin will be described, command line and using Visual Studio code.

Command line
~~~~~~~~~~~~~~~

Window

Linux


Visual Studio code
~~~~~~~~~~~~~~~~~~~~
   Implementation

  
.. _startImplementation:

.. figure:: MLSelection.png

As you can see in the `startImplementation`_ image,  
   