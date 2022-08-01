

Example 5: PK Model, DMAG by GP
==============================================
  

.. _startpk5:

Example 5 is very similar to :ref:`Example 4<startpk4>`. The important difference is the use of :ref:`Gaussian Process<GP_desc>` rather than 
:ref:`Genetic Algoritm<GA_desc>`. As noted in :ref:`Example 4<startpk4>` the `ask step <https://scikit-optimize.github.io/stable/modules/optimizer.html#>`_ 
for large cumulative sample sizes (> 500) will become very long. In this example, the population/sample size is reduced to 20 from 80. This improves the 
execution time for the ask step, but note that the best model isn't found until the 2nd round of 2 it local search, 
whereas in :ref:`Example 4<startpk4>` it was found after the first round of 2 bit local search. 
