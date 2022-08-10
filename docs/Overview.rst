
.. _startTheory:

Overview
=========

pyDarwin implements a number of machine learning algorithms for model selection. Machine learning algorithms are broadly divided into two categories:
 - Supervised learning
 - Unsupervised learning

For supervised learning, the algorithm "learns" to associate certain patterns (e.g., a collection of bitmap pictures) with a set of labeled examples. 
For example, if one has 10,000 pictures of cats and dogs (a training set), with each image labeled as "cat" or "dog", an artificial neural network (ANN) 
can find patterns in the 0s and 1s that are associated with "catness" or "dogness", and can be fairly successful at predicting for any similar set of bitmaps
(a test set) which is a cat and which is a dog. 

In contrast, unsupervised learning has no labeled training set. Linear regression is a simple example of supervised learning. 
There is an input (X) and an output (Y) and the algorithm identified patterns that match the inputs to the output (intercept and slope(s)). However, 
looking for the best independent variables to include in a linear regression model is an unsupervised learning problem, there is no training set of examples 
with the "correct" list of independent variables to include. 

The traditional model selection/building process for pop pk models is similarly unsupervised. There is no "labeled" training dataset, no collection of datasets 
that are known to be 1 compartment, with Volume~WT. Rather, each dataset facilitates a new learning process and the algorithm must discover relationships across different datasets. 
In the case of model selection, the inputs (Xs) are the "features" of the model search (not the model, but the model search) 
(number of compartments, covariates, random effects, etc.) and the output is some measure of model goodness. 

For ``pyDarwin``, the model goodness is a user-defined function, with a base of the -2LL output, with user-defined penalties, including parsimony (penalties for estimate parameters), convergence, successful covariance step, plus optional 
user-written ``R`` or ``Python`` code that can be executed after each run (:ref:`"use_r" <use_r_options_desc>` or :ref:`"use_python" <use_python_options_desc>`). This post run code is useful, for example, if the  user wants to add 
a penalty for under or over prediction of Cmax (basically a penalty for `posterior predictive check <https://link.springer.com/article/10.1023/A:1011555016423>`_). 

Supervised learning includes algorithms such as regression, artificial neural networks (ANN), decision trees/random forest, and k-nearest neighbor. 
Recently, hybrid supervised/unsupervised learning algorithms have been introduced and have proven to be very powerful. The best known of these is deep q network/reinforcement 
learning(DQN/RL). DQN/RL is a deep neural network (a slightly more complex ANN). However, unlike traditional supervised ANN, there is no training set. 
Rather, the method starts with a randomly selected set of weights for nodes in the ANN. Then, based on this random selection, ANN predicts the best model. 

At the start, this model will be far from the "true" optimal model. Starting with a single model, however, provides a very small "training set", and the ANN is now trained on this model. 
This process is repeated until the current best predicted model no longer improves. This approach (start with a random representation of the search space, run a few models, 
then train the representation) has been adapted to other traditionally supervised methods including Bayesian optimization (Gaussian process - GP), 
Random Forest (RF) and gradient boosted random trees (GBRT). These three hybrid algorithms (:ref:`GP<GP_desc>`, :ref:`RF<RF_desc>` , :ref:`GBRT<GBRT_desc>`) have been included in ``pyDarwin``'s
algorithm options along with the more traditional Genetic Algorithm (:ref:`GA<GA_desc>`) and exhaustive search (:ref:`EX<EX_desc>`). 

Traditional pop pk/pd model selection uses the "downhill method", starting, usually at a trivial model, then adding
"features" (compartments, lag times, nonlinear elimination, covariate effects), and accepting the new model if it is better ("downhill"), based on some user-defined, and somewhat informal criteria. 
Typically, this user-defined criteria will include a lower -2LL plus usually penalty for added parameters plus some other criteria that the user may feel is important. The downhill method is easily the 
most efficient methods (fewest evaluations of the reward/fitness to reach the convergence) but is highly prone to local minima. However, downhill does play a role in a very efficient 
local search, in combination with a global search algorithm (e.g., :ref:`GA<GA_desc>` , :ref:`GP<GP_desc>`, :ref:`RF<RF_desc>` , :ref:`GBRT<GBRT_desc>`). 

Central to understanding the model selection process (with manual or machine learning), is the concept of the search space. The search space is an n-dimensional 
space where each dimension represents a set of mutually exclusive options. That is, there likely will be a dimension for "number of compartments", with possible 
values of 1, 2, or 3. Exactly one of these is required (ignoring the possibility of `Bayesian model averaging <https://onlinelibrary.wiley.com/doi/abs/10.1111/insr.12243>`_). 
Another dimension might be the absorption model, with values of first order, zero order, first order with absorption lag time etc). Similarly candidate  
relationship between weight and volume might be: no relationship, linear, or power model. In addition to structural and statistical "features", other features 
of the model, such as initial estimates for parameters, can be searched on. Note that each of these dimensions are discrete, and strictly 
categorical (not ordered categorical i.e., first order isn't "more than" zero order). With this exception, the model search space is analogous to the 
parameter search space used in nonlinear regression. An important difference is that the continuous space in nonlinear 
regression has derivatives, and quasi-Newton methods can be used to do a "downhill search" in that space. Please note that quasi-Newton methods are 
also at risk of finding local minima, and therefore are sensitive to the initial estimates. In the case of parameter estimation (nonlinear regression), efforts are made to start 
the search at a location in the search space near the final estimate, greatly reducing the chances ending up in a local minimum. No such effort is 
made in the traditional downhill model selection method. Rather, the search is usually started at a trivial model, which is likely far from the global minimum. 

As the discrete space of model search does not have derivatives, other search methods must be used. The simplest, and the one traditionally used in 
model selection, is downhill. While efficient,  it can be demonstrated that this method is not robust [#f1]_ [#f2]_. This lack of robustness is due to 
the violation of convexity assumption. That is, the downhill search, in either a continuous space (parameter estimation) or a discrete space (model selection) 
assumes that the optimal solution is continuously downhill from every other point in the search space. That is, there are no local minima, you can start anywhere 
and you'll end up in the same place - the global minimum (the results are not sensitive to the "initial estimates"). With this assumption, a covariate will be 
"downhill", regardless of whether tested in a one compartment, two compartment; first order of zero order or any other base model, it's all downhill, it doesn't 
matter in what sequence you test hypotheses, the answer will be the same. Wade [#f1]_ showed that the results of tests of hypotheses do indeed depend on other 
features in the model and Chen [#f2]_ showed that different sequences of tests will commonly yield different final models.

In contrast to the traditional downhill/local search, all algorithms implemented in pyDarwin are global search algorithms that are expected to have a greater 
degree of robustness to local minima than downhill search. Note, however, that all search algorithms (except exhaustive search) make assumptions about 
the search space. While none of the algorithms in pyDarwin assume convexity, none are completely robust, 
and search spaces can be deceptive [#f3]_. For all algorithms, the basic process is the same, start at one or more random models. Then, test those models and learn a little about 
the search space to decide which models to test next. The algorithms differ in how they decide which models will be subsequently tested.

While the global search algorithm provides substantial protection from a local minimum in the model search, the global search algorithm is typically not very 
good at finding the one or two final changes that results in the best model. This is illustrated in :ref:`Genetic Algorithm<GA_desc>` in that the final change likely 
must be made by mutations, a rare event, not by crossover. The solution to this problem is to combine the strength of a global search (robustness to local 
minima) with the efficiency of local downhill, or even local exhaustive search. Thus, the global search gets close to the final best solution (much like providing good 
initial estimates to NONMEM), and the local search finds the best solution in that local volume of the search space. 

The search space is key to the implementation of each algorithm. The overall representation is the same for all algorithms - an n-dimensional discrete search space. The values in each 
dimension are then coded into several forms, bit strings and integer string. Ultimately, the model is constructed from the integer string, e.g., values for the number 
of compartment dimensions are 1|2|3. However, for GA, this must be coded as bit string. There is one additional representation, referred to as a minimal binary string, 
which is used for the local exhaustive step.

The overall process is shown in Figure 1 below:

 .. figure:: MLSelection.png

The same 3 files are required for any search, whether :ref:`EX<EX_desc>` , :ref:`GA<GA_desc>` , :ref:`GP<GP_desc>`, :ref:`RF<RF_desc>` or :ref:`GBRT<GBRT_desc>`. 
These file are described in :ref:`required files. <startRequiredFiles>`

.. _The Algorithms:

Algorithms
~~~~~~~~~~~~~

Note the essentially linear increase in the ask step time (time to generate samples for next iteration) as the dataset size increases.
For problems with larger search spaces, and greater number of model evaluations, :ref:`Genetic algorithm<GA_desc>` or :ref:`Random Forest <RF_desc>` may 
be more appropriate.

Below is a list of recommendations for algorithm selection.

 - Fast execution, large search space (> 100,000 models, expected sample > 1000 models) – :ref:`GA<GA_desc>` or :ref:`RF<RF_desc>`
 - Small search space (<100,000, expected # of samples < 1000) - :ref:`Gaussian Process<GP_desc>`.
 - Very small search space (< 500 models), many cores (> 20) – :ref:`exhaustive search <EX_desc>`.

.. _EX_desc:

Exhaustive Search
------------------
The exhaustive search algorithm is simple to understand. The search space is initially represented as a string of integers - one for each dimension. To facilitate the search, 
this integer string is coded into a "minimal binary".
 
.. _GA_desc:

Genetic Algorithm
-------------------------

Genetic Algorithm (GA) is a reproduction of the mathematics of evolution/survival of the fittest. A more detailed discussion `on GA can be found here <https://en.wikipedia.org/wiki/Genetic_algorithm>`_, and 
a very readable (but somewhat dated) reference is Genetic Algorithms in Search, Optimization and Machine Learning 13th ed. Edition by David Goldberg. Details of the options (not all of which are available in pyDarwin) 
can be found at `here <https://deap.readthedocs.io/en/master/>`_.
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

The bit strings for each gene are concatenated into a "chromosome". The search starts with a population of random bit strings. These bit strings are decoded, and NONMEM control files constructed from the :ref:`template file<template>` 
by substituting the selected text from the :ref:`token set<token set>`. The resulting NONMEM control file is run and the :ref:`fitness <fitness>` is calculated. 
The next generations is created by randomly selecting sets of parent candidates from the population. These parent candidates are then selected based on :ref:`Tournament selection <Tournament selection>`. 
Once the sets of parents are selected, they undergo crossover and mutation and a new generation is created. This process is repeated until no further improvement is seen.

.. _GP_desc:

Gaussian Process
-------------------------

Gaussian Process is one of the two options used in `Bayesian Optimization <https://en.wikipedia.org/wiki/Bayesian_optimization#>`_. The Gaussian Process specifies the form of the prior and posterior distribution. 
Initially the distribution is random, as is the case for all the global search algorithms. Once some models have been run, the distribution can be updated (the "tell" step) and new, more imformative samples can be 
generated (the "tell" step).

.. _RF_desc:

Random Forest
-------------------------

`Random Forest <https://en.wikipedia.org/wiki/Random_forests>`_ consists of splitting the search space (based on the "goodness" of each model in this case) thus continuously dividing the 
search space into "good" and "bad" regions. As before, the initial divisions are random, but become increasingly well informed as real values for the fitness/reward of models are 
included.

.. _GBRT_desc:

Gradient Boosted Random Tree
------------------------------

`Gradient Boosted Random Tree <https://towardsdatascience.com/decision-trees-random-forests-and-gradient-boosting-whats-the-difference-ae435cbb67ad>`_ 
is similar to Random Forest, but may increase the precision of the tree building by progressively building the tree, and calculating a gradient of the reward/fitness with respect to each decision. 

  
.. [#f1] Wade JR, Beal SL, Sambol NC. 1994  Interaction between structural, statistical, and covariate models in population pharmacokinetic analysis. J Pharmacokinet Biopharm. 22(2):165-77 
 
.. [#f2] PAGE 30 (2022) Abstr 10091 [https://www.page-meeting.org/?abstract=10091]


.. [#f3] PAGE 30 (2022) Abstr 10053 [https://www.page-meeting.org/default.asp?abstract=10053]



File Structure and Naming
~~~~~~~~~~~~~~~~~~~~~~~~~~~

NONMEM control, executable, and output file naming

Saving NONMEM output
---------------------
NONMEM generates a great deal of file output. For a search of up to 10,000 models, this can become an issue for disc space. 
By default, key NONMEM output files are retained. Most temporary files (e.g., FDATA, FCON) and the temp_dir are always removed to save disc space. 
In addition, the data file(s) are not copied to the run directory, but all models use the same copy of the data file(s).
Users should take caution and ensure only required tables are generated (as specified in ``template.txt``), as table files can become quite 
large, and will not be removed by pyDarwin unless :ref:`remove_temp_dir <remove_temp_dir_options_desc>` is set to true. 

File Structure
---------------
Three user-defined file locations can be set in the :ref:`options file<Options>`.

#. output_dir - Folder where the results files will be stored, such as results.csv and Final* files.

#. temp_dir - NONMEM models are run in subfolders of this folder.

#. working_dir - Folder where all intermediate files will be created, such as models.json (model run cache), messages.txt (log file), Interim* files and stop files. 

See :ref:`Options List<Options>` for additional details.
 

Model/folder naming
--------------------

A model stem is generated from the current generation/iteration and model number of the form NM_generation_model_num. For example, if this is iteration 2, model 3, the model stem would be 
NM_2_3 (or similar, pyDarwin will count the number of models to be generated and used, e.g., nm_02_03 if needed). For the 1 bit downhill, the 
model stem is NM_generationDdownhillstep_modelnum, and for the 2 bit local search the model stem is NM_generationSdownhillstepSearchStep_modelnum. Final downhill 
model stem is NM_FNDDownhillStep_ModelNum. This model stem is then used to name the .exe file, the .mod file, the .lst file, etc. This results in unique names for all models in the search. Models 
are also frequently duplicated. Duplicated files are not rerun, and so those will not appear in the file structure.

Run folders are similarly named for the generation/iteration and model number. Below is a folder tree for :ref:`Example 2<startpk2>` with the "temp_dir" option set to c:\\example2\\rundir and 
"remove_temp_dir" set to false.

.. figure:: FileStructure.png

Saving models
-------------

Model results are, by default, saved in a JSON file so that searches can be restarted or rerun with different algorithms more efficiently. The name of the saved JSON file can be set by 
the user. A .csv file describing the course of the search is also saved to results.csv. This file can be used to monitor the progress of the search. 
