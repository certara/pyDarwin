.. _The Algorithms:

###############
Algorithms
###############

For problems with larger search spaces, and greater number of model evaluations, :ref:`Genetic algorithm<GA_desc>` or :ref:`Random Forest <RF_desc>` may 
be more appropriate.

Below is a list of recommendations for algorithm selection.

 - Fast execution, large search space (> 100,000 models, expected sample > 1000 models) – :ref:`GA<GA_desc>` or :ref:`RF<RF_desc>`
 - Small search space (<100,000, expected # of samples < 1000) - :ref:`Gaussian Process<GP_desc>`.
 - Very small search space (< 500 models), many cores (> 20) – :ref:`Exhaustive Search <EX_desc>`.

.. _EX_desc:

*******************
Exhaustive Search
*******************

The exhaustive search algorithm is simple to understand. The search space is initially represented as a string of integers - one for each dimension. To facilitate the search, 
this integer string is coded into a "minimal binary".
 
.. _GA_desc:

*******************
Genetic Algorithm
*******************

Genetic Algorithm (GA) is a reproduction of the mathematics of evolution/survival of the fittest. A more detailed discussion `on GA can be found here <https://en.wikipedia.org/wiki/Genetic_algorithm>`_, and 
a very readable (but somewhat dated) reference is Genetic Algorithms in Search, Optimization and Machine Learning 13th ed. Edition by David Goldberg. Details of the options (not all of which are available in pyDarwin) 
can be found `here <https://deap.readthedocs.io/en/master/>`_.
Briefly, GA presents the search space as a bit string, with each "gene" being a binary number that is decoded into the integer value for that option. For example, for a dimension of Additive vs Additive + proportional 
residual error, the integer codes would be:

#. Additive error (e.g., +EPS(1))
#. Additive + proportional error (e.g., EXP(EPS(1))+EPS(s))

It is straightforward enough to code these values [1,2] into a binary [0,1]. For dimensions with more than 2 values, more than 1 bit will be needed. For example, if 1 or 2 or 3 compartments are searched, the 
string representation might be:

#. One compartment (ADVAN1)
#. Two compartment (ADVAN3)
#. Three compartment (ADVAN11)

and the bit string representation might be:

* 1 - [0,0]
* 2 - [0,1] and [1,0]
* 3 - [1,1]

The bit strings for each gene are concatenated into a "chromosome". The search starts with a population of random bit strings. These bit strings are decoded, and NONMEM control files are constructed from the :ref:`template file<template>` 
by substituting the selected text from the :ref:`token set<token set>`. The resulting NONMEM control file is run and the :ref:`fitness <fitness>` is calculated. 
The next generations is created by randomly selecting sets of parent candidates from the population. These parent candidates are then selected based on :ref:`Tournament selection <Tournament selection>`. 
Once the sets of parents are selected, they undergo crossover and mutation, and a new generation is created. This process is repeated until no further improvement is seen.

.. _GP_desc:

*******************
Gaussian Process
*******************

Gaussian Process is one of the two options used in `Bayesian Optimization <https://en.wikipedia.org/wiki/Bayesian_optimization#>`_. The Gaussian Process specifies the form of the prior and posterior distribution. 
Initially the distribution is random, as is the case for all the global search algorithms. Once some models have been run, the distribution can be updated (the "tell" step) and new, more informative samples can be 
generated (the "tell" step).

.. _RF_desc:

*******************
Random Forest
*******************

`Random Forest <https://en.wikipedia.org/wiki/Random_forests>`_ consists of splitting the search space (based on the "goodness" of each model in this case), thus continuously dividing the 
search space into "good" and "bad" regions. As before, the initial divisions are random, but become increasingly well-informed as real values for the fitness/reward of models are 
included.

.. _GBRT_desc:

******************************
Gradient Boosted Random Tree
******************************

`Gradient Boosted Random Tree <https://towardsdatascience.com/decision-trees-random-forests-and-gradient-boosting-whats-the-difference-ae435cbb67ad>`_ 
is similar to Random Forest, but may increase the precision of the tree building by progressively building the tree and calculating a gradient of the reward/fitness with respect to each decision. 

.. _PSO_desc:

**********************************
Particle Swarm Optimization (PSO)
**********************************

Particle swarm optimization (PSO [#f4]_) is another approach to optimization that, like Genetic Algorithm,
attempts to reproduce a natural optimization process. In the case of PSO, the natural process is the
swarm behavior of birds and fish, although the specifics of the relationship to bird and fish behavior
is largely speculation. Each particle (candidate NONMEM model in this case) moves through the search
space, as one might imagine individuals in a school of fish or a flock of birds moving together,
but also each bird/fish moving somewhat independently.

The velocity of each particle's movement is based on two factors:

#. Random movement
#. Coordinated movement.

The coordinated movement is in turn, defined by the following parameters in the :ref:`Options List<Options>`:

* :ref:`inertia<inertia_options_desc>` (:math:`\\w`): the particle tends to continue moving in the same direction as the previous velocity
* :ref:`cognitive<cognitive_options_desc>` (:math:`c_1`): the particle tends to move in the direction toward its own best known position
* :ref:`social<social_options_desc>` (:math:`c_2`): the particle tends to move in the direction toward the current best known position among all particles

Other parameters for PSO include: :ref:`population_size <population_size_options_desc>`, :ref:`neighbor_number <neighbor_num_options_desc>`,
:ref:`p_norm <p_norm_options_desc>`, and :ref:`break_on_no_change <break_on_no_change_options_desc>`.

As with other optimization algorithms, the downhill step may also be implemented.
The topology defines the region of the swarm whereby individual particles (models in this case) exchange information and thereby act in coordination.
The "star" topology is the only implementation currently available in pyDarwin. The star topology permits particles (model) to coordinate with a set of nearest neighbors in a
sort of star shape, up to the number of neighbors specified in :ref:`neighbor_number <neighbor_num_options_desc>`.


.. [#f4] J Kennedy and R.C. Eberhart. 1995  Particle Swarm Optimization. Proceedings of the IEEE International Joint Conference on Neural Networks, 4:1942-1948

