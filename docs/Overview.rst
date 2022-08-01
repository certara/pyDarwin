Overview
=========
 
.. _startTheory:
 
pyDarwin implements a number of machine learning algorithms for model selection. Machine learning algorithms are broadly divided into two categories:
 - Supervised learning
 - Unsupervised learning

For supervised learning, the algorithm "learns" to associate certain patterns (e.g., a collection of bitmap pictures) with a set of labeled examples. For example, if one has
10,000 pictures of cats and dogs (a training set), with each image labeled as "cat" or "dog", an artificial neural network (ANN) can find patterns in 
the 0's and 1's that are associated with "catness" or "dogness", and can be fairly successful at predicting for any similar set of bitmaps (a test set) which is a 
cat and which is a dog. 

In contrast, unsupervised learning has no labeled training set. Linear regression is a simple example of supervised learning. 
There is an input (X's) and an output (Y's) and the algorithm identified patterns that match the inputs to the output (intercept and slope(s)). However, 
looking for the best independent variables to include in a linear regression model is an unsupervised learning problem, there is not training set of examples 
with the "correct" list of independnet variables to include. 
The traditional model selection/building process for pop pk models is similarly unsupervised. There is no "labeled" training data set, no collection of data sets 
that are known to be 1 compartment, with Volume~WT. Rather each data set is a new learning and the algorithm must discover relationships based just on that data set. 
In the case of model selection, the inputs (X's) are the "features" of the model search (not the model, but the model search) 
(number of compartments, covariates, random effects etc) and the output is some measure of model goodness. 

For pyDarwin the model goodness is a user defined function, with a base of the -2LL output, with user defined penalties, including parsimony (penalties for estimate parameters), convergence, successful covariance step plus optional 
user written R or python code that can be excuted after each run (postRunRCode or postRunPythonCode). This post run code is useful, for example if the  user wants to add 
a penalty for under or over prediction of Cmax (basically a penalty for `posterior predictive check <https://link.springer.com/article/10.1023/A:1011555016423>`_). 

Supervised learning includes algorithms such as regression, artificial neural networks (ANN), decision trees/random forest and k-nearest neighbor. 
Recently, hybrid supervised/unsupervised learning algorithm have been introduced and have proven to be very powerful. The best know of these is deep q network/reinforcement 
learning(DQN/RL). DQN/RL is a deep neural network (a slightly more complex ANN). However, unlike traditional supervised ANN, there is no training set. 
Rather, the method starts with a randomly selected set of weights for nodes in the ANN. Then, based on this (random) ANN predicts the best model. Initially, this 
model will be far from the "true" optimal model. But, running a single model then provides a very small "training set", and the ANN is now trained on this model. 
This process is repeated until the current best predicted model no longer improves. This approach (start with a random representation of the search space, run a few models, 
then train the representation) has been adapted to other traditionally supervised methods including Bayesian optimization (Gaussian process - GP), 
Random Forest (RF) and gradient boosted random trees (GBRT). These three hybrid algorithms (:ref:`GP<GP_desc>`, :ref:`RF<RF_desc>` , :ref:`GBRT<GBRT_desc>`) have been include in the algorithms in pyDarwin 
along with the more traditional Genetic Algorithm (:ref:`GA<GA_desc>`) and exhaustive search (:ref:`EX<EX_desc>`). 

Traditional pop pk/pd model selection uses the "downhill method", starting usually, at a trival model, then adding
"features" (compartments, lag times, non linear elimination, covariate effects) and accepting the new model if it is better ("downhill"), based on some user defined, and somewhat informal criteria. 
Typicaly, this user defined criteria will include a lower -2LL + usually some penalty for added parameters + some other criteria the user feels important. The downhill method is easily the 
most effiicent methods (fewest evaluations of the reward/fitness to reach the convergence) but has been shown to be very prone to local minima. However, downhill does play a role in a very efficient 
local search, in combination with a global search algorithm (e.g., :ref:`EX<EX_desc>` , :ref:`GA<GA_desc>` , :ref:`GP<GP_desc>`, :ref:`RF<RF_desc>` , :ref:`GBRT<GBRT_desc>`). 

Central to understanding the model selection process (with manual or machine learning), is the concept of the search space. The search space is an n dimensional 
space where each dimension represents a set of mutually exclusive options. That is, there likely will be a dimension for "number of compartments", with possible 
values of 1, 2 or 3. Exactly one of these is required (ignoring the possibility of `Bayesian model averaging <https://onlinelibrary.wiley.com/doi/abs/10.1111/insr.12243>`_ .

Another dimension might be the absorption model, with values of first order, zero order, first order with absorption lag time etc). Similarly candidate  
relationship between weight and volume might be [no relationship or linear or power model]. In addition to structural and statistical "features", other features 
of the model, such as initial estimates for parameters can be searched on. Note that each of these dimension are discrete, and mostly strictly 
categorical (not ordered categorical, first order isn't "more than" zero order). With this exception the model search space is analogous to the 
parameter search space used in non-linear regression. An important difference is that the continuous space in non-linear 
regression has derivatives, and quasi-Newton methods can be used to to a "downhill search" in that space. Please note that quasi-Newton methods are 
also at risk of finding local minima, and therefore are sensitive to the initial estimates. In the case of parameter estimation (non linear regression), efforts are made to start 
the search at a location in the search space near the final estimate, greatly reducing the chances ending up in a local minima. No such effort is 
made in the downhill model selection method. Rather, the search is usually start at a trivial model, which is likely far from the global minimum. 

As the discrete space of model search does not have derivatives, other search methods must be used. The simplest, and the one traditionally used in 
model selection, is downhill. While efficient it can be demonstrated that this method is not robust [#f1]_ [#f2]_. This lack of robustness is due to 
the violation of convexity assumption. That is, the downhill search, in either a continuous space (parameter estimation) or a discrete space (model selection) 
assumes that the optimal solution is continuously downhill from every other point in the search space. That is, there are no local minima, and you can start anywhere 
and you'll end up in the same place - the global minimum, the results is not sensitive to the "initial estimates". With this assumption, a covariate will or will not be 
"downhill", regardless of whether tested in a one compartment, two compartment; first order of zero order or any other base model, it's all downhill, it doesn't 
matter in what sequence you test hypotheses, the answer will be the same. Wade [#f1]_ showed that the results of tests of hypotheses do indeed depend on other 
features in the model and Chen [#f2]_ showed that different sequences of tests will commonly yield different final models.


In contrast to the traditional downhill/local search, all algorithms implemented in pyDarwin are global search algorithms that are expected to have a greater 
degree of robustness to local minima than downhill search. Note howwever that all search algorithms (with the exception of exhaustive search) make assumptions about 
the search space. While none of the algorithms in pyDarwin assume convexity, none are completely robust, 
and search spaces can be deceptive.[#f3]_. For all algorithms, the basic process is the same, start at one or more random. 
 
The search space is key to implementation of each algorithm. The overall representation is the same for all algorithms - an n dimensional discrete search space. The values in each 
dimension are then coded into several forms, bit strings and integer string. Ultimately, the model is constructed from the integer string, e.g., values for the number 
of compartment dimenion are 1|2|3. However,for GA, this must be coded as bitstring. There is one additional representation, refered to as a minimal binary string, 
which is used for the downhill step.

The overall process is shown in Figure 1 below:

 .. figure:: MLSelection.png

The same 3 files are required for any search, whether exhausitve, :ref:`EX<EX_desc>` , :ref:`GA<GA_desc>` , :ref:`GP<GP_desc>`, :ref:`RF<RF_desc>` or :ref:`GBRT<GBRT_desc>`. 
These file are described in :ref:`required files. <startRequiredFiles>`

.. _The Algorithms:

Algorithms
~~~~~~~~~~~~~

.. _EX_desc:

Exhaustive Search
------------------
The exhausitve search algorithm is simple to understand. The search space is initally represented as a string of integers - one for each dimension. To facilitate the search, 
this interger string is coded into a "minimal binary". T 
 
.. _GA_desc:

Genetic Algorithm
-------------------------

Genetic Algorithm (GA) is a reproduction of the mathematics of evoluation/survival of the fitest. A more detailed discussion `on GA can be found here <https://en.wikipedia.org/wiki/Genetic_algorithm>`_, and 
a very readable (but somewhat dated) reference is Genetic Algorithms in Search, Optimization and Machine Learning 13th ed. Edition by David Goldberg. Details of the options (not all of which are available in pyDarwin) 
can be found at `here <https://deap.readthedocs.io/en/master/>`_.
Briefly, GA presents the search space as a bit string, with each "gene" being a binary number that is decoded into the integer value for that option. For example, for a dimension of Additive vs Additive + proportional 
residual error, the intger codes would be:

#. Additive error (e.g., +EPS(1))
#. Additive + proportional error (e.g., EXP(EPS(1))+EPS(s))

It is straightforward enough to code these value [1,2] into a binary [0,1]. For dimenions with more than 2 values, more than 1 bit will be needed. For example, if 1 or 2 or 3 compartments are the searched, the bit 
string representation might be:

#. One compartment (ADVAN1)
#. Two compartment (ADVAN3)
#. Three compartment (ADVAN11)

and the bit string representation might be:

* 1 - [0,0]
* 2 - [0,1] and [1,0]
* 3 - [1,1]

The bit strings for each gene are concatenate into a "chromosome". The search starts with a popuation of random bit strings. These bit strings are decoded, and NONMEM control files constructed from the :ref:`template file<template>` 
by substituting the selected text from the :ref:`token set<token set>`. The resulting NONMEM control file is run and the :ref:`fitness <fitness>` is calculated. 
The next generations is created by randomly selecting sets of parent candidates from the population. These parent candidates are then selected based on :ref:`Tournament selection <Tournament selection>`. 
Once the sets of parents are selected, they undergo cross over and mutation and a new generation is created. This process is repeated until no further improvement is seen.

.. _GP_desc:

Gaussian Process
-------------------------

Gaussian Process is one of the two options used in `Baysian Optimization <https://en.wikipedia.org/wiki/Bayesian_optimization#>`_. The Gaussian Process specifies the form of the prior and posterior distribution. 
Initially the distribtion is random, as is the case for all the the global serach algorithms. Once some models have been run, the distribtion can be updated (the "tell" step) and new, more imformative samples can be 
generated (the "tell" step).

.. _RF_desc:

Random Forest
-------------------------
.. _GBRT_desc:

Gradient Boosted Random Tree
------------------------------
  
.. [#f1] Wade JR, Beal SL, Sambol NC. 1994  Interaction between structural, statistical, and covariate models in population pharmacokinetic analysis. J Pharmacokinet Biopharm. 22(2):165-77 
 
.. [#f2] PAGE 30 (2022) Abstr 10091 [https://www.page-meeting.org/?abstract=10091]

.. [#f3] PAGE 30 (2022) Abstr 10053 [https://www.page-meeting.org/default.asp?abstract=10053]


File Structure and Naming
~~~~~~~~~~~~~~~~~~~~~~~~~~~

NONMEM control, executable and output file naming

Saving NONMEM outputs
---------------------
NONMEM generates a great deal of file output. For a search of perhaps up to 10,000 models, this can become an isssue for disc space. 
By default, key NONMEM output files are retained. Most temporary files (e.g., FDATA, FCON) and the temp_dir are always removed to save disc space. 
In addition, the data file(s) are not copied to the run directory, but all models use the same copy of the data file(s).
Users should take caution and ensure only required tables are generated (as specified in ``template.txt``), as table files can become quite 
large, and will not be removed by pyDarwin. 

File Structure
---------------
Three user defined file locations can be set in the :ref:`options file<Options>`. In addition to the folders that are user defined
the project directory (project_dir) is the folder where template, token and options files are located. The user define folders are:

#. output_dir - Folder where all the files that considered as results will be put, such as results.csv and Final* files. Default value is working_dir/output. May make sense to be set to project_dir if version control of the project and the results is intended.

#. temp_dir - NONMEM models are run in subfolders of this folder Default value is working_dir/temp. May be deleted after search finished/stopped if remove_temp_dir is set to true.  

#. working_dir - Folder where all intermediate files will be created, such as models.json (model run cache), messages.txt (log file), Interim* files and stop files. Default value - %USER_HOME%/pydarwin/project_name where project name is defined in the :ref:`options file<Options>`
 

Model/folder naming
--------------------


A model stem is generated from the current generation/iteration and model number or the form NM_genration_model_num. For example, if this is iteration 2, model 3 the model stem would be 
NM_2_3. For the 1 bit downhill, the model stem is NM_generationDdownhillstep_modelnum, and for the 2 bit local search the model stem is NM_generationSdownhillstepSearchStep_modelnum. Final downhill 
model stem is NM_FNDDownhillStep_ModelNum. This model stem is then used to name the .exe file, the .mod file, the .lst file etc. This results in unique names for all models in the search. Models 
are also frequently duplicated. Duplicated files are not rerun, and so those will not appear in the file structure.

Run folders are similarly named for the generation/iteration and model number. Below is a folder tree for :ref:`Example 2<startpk2>`

.. figure:: FileStructure.png

Saving models
-------------

Model results are by default saved in a JSON file so that searches can be restarted or rerun with different algorithms more efficients. The name of the saved JSON file can be set by the user. A .csv 
file describing the course of the search is also save to results.csv. This file can be used to monitor the progress of the search. 
