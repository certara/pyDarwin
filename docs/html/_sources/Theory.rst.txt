

ML Model Selection, Theory and implementation
=============================================
 
 
.. _startTheory:
 
pyDarwin implements a number of machine learning algorithms for model selection. Machine learning algorithms are broadly divided into two categories:
 - Supervised learning
 - Unsupervised learning

For supervised learning, the algorithm "learns" to associate certain patterns (e.g., a collection of bitmap pictures) with a set of labeled examples. For example, if one has
10,000 pictures of cats and dogs (a training set), with each image labeled as "cat" or "dog", a artificial neural network (ANN) can find patterns in 
the 0's and 1's that are associated with "catness" or "dogness", and can be fairly successful at predicting for any similar set of bitmaps (a test set) which is a 
cat and which is a dog. In contrast, unsupervised learning has no labeled training set. Linear regression is a simple example of supervised learning. 
There is an input (X's) and an output (y's) and the algorithm identified patterns that match the inputs to the output (intercept and slope(s)). 
The traditional model selection/building process for pop pk models is unsupervised. There is no "labeled" training data set, no collection of data sets 
that are known to be 1 compartment, with Volume~WT. Rathar each data set is a new learning and the algorithm must discover relationships based just on that data set. 
In the case of model selection, the inputs (X's) are the "features" of the model 
(number of compartments, covariates, random effects etc) and the output is some measure of model goodness. For pyDarwin the model goodness is a user defined value, 
with a base of the -2LL output, with user defined penalty, including parsimony (penalties for estimate parameters), convergence, successful covariance step plus optional 
user written R or python code that can be excuted after each run. This post run code is useful for example if the  user wants to add a penalty for under or over prediction of 
Cmax.
Supervised learning includes algorithms such as regression, artifial neural networks (ANN), decision trees/random forest and k-nearest neighbor. 
Recently, hybrid supervised/unsuprevised learning algorithm have been introduced and have proven to be very powerful. The best know of these is deep q network/reinforcement 
learning(DQN/RL). DQN/RL is a deep neural network (a slightly more complex ANN). However, unlike traditional supervised ANN, there is no training set. 
Rather, the method starts with a randomly selected set of weights for nodes. Then based on this (random) ANN predicts the best model. Initially, this 
model will be far from the "true" optimal model. But, running a single model then provides a very small "training set", and the ANN is now trained on this model. 
This process is repeated until the "best" model no longer improves. This approach (start with a random representation of the search space, run a few models, 
then train the representation) has been adapted to other traditionally supervised methods including Bayesian optimization (Gaussian process - GP), 
Random Forest (RF) and gradient boosted random trees (GBRT).  These three hybrid algorithms (GP, RF and GBRT) have been include in the algorithms in pyDarwin 
along with the more traditional Genetic Algorithm (GA) and exhaustive search. 

Traditional pop pk/pd model selection uses the "downhill method", starting usually, at a trival model, then adding
"features" (compartments, lag times, non linear elimination, covariate effects) and accepting the new model if it is better ("downhill"), 
lower -2LL + some other criteria the user feels important). The downhill method is easily the most effiicent methods (fewest evaluations of the 
reward/fitness to reach the convergence) but has been shown to be very prone to local minima. However, downhill does play a role in a very efficient 
local search, in combination with a global search algorithm (GP, RF, GBRT or GA). 


Central to understanding the model selection process (with manual or machine learning), is the concept of the search space. The search space is an n dimensional 
space where each dimension represents 
a set of mutually exclusive options. That is, there likely will be a dimension for "number of compartments", with possible values of 1, 2 or 3. 
Exactly one of these is required (ignoring the possibility of 

`Bayesian model averaging <https://onlinelibrary.wiley.com/doi/abs/10.1111/insr.12243>`

Another dimension might be the absorption model, with values of first order, zero order, first order with absorption lag time etc). Similarly candidate  
relationship between weight and volume might be (none|linear|power model). In addition to structural and statistical "features", other features 
of the model, such as initial estimates for parameters can be searched on. Note that each of these dimension are discrete, and mostly strictly 
categorical (not ordered categorical, first order isn't "more than" zero order). With this exception the model search space is very analogous to the 
parameter search space used in non-linear regression. An important difference is that the continuous space in non-linear 
regression has a derivativee, and quadi-Newton methods can be used to to a "downhill search" in that space. Please note that quasi-Newton methods are 
also at risk of finding local minima, and therefore are sensitive to the initial estimates. In the case of parameter estimation, efforts are made to start 
the search at a location in the search space near the final estimate, greatly reducing the chances ending up in a local minima. No such effort is 
made in the downhill model selection method. Rather, the search is usually start at a trivial model. 

As the discrete space of model search does not have a derivative, other search methods must be used. The simplest, and the one traditionally used in 
model selection, is downhill. While efficient it can be demonstrated that this method is not robust [#f1]_ [#f2]_. This lack of robustness is due to 
the violation of convexity assumption. That is, the downhill search, in either a continuous space (parameter estimation) or a discrete space (model selection) 
assumes that the optimal solution is continuously downhill from every other point in the search space. That is, there are no local minima, and you can start anywhere 
and you'll end up in the same place. With this assumption, a covariate will or will not be "downhill", regardless of whether tested in a one compartment, 
two compartment; first order of zero order or any other base model, it's all downhill, it doesn't matter in what sequence you test 
hypotheses, the answer will be the same. Wade [#f1]_ showed that the results of tests of hypotheses do indeed depend on other features in the model and 
Chen [#f2]_ showed that different sequences of tests will commonly yield different models.


In contrast to the traditional downhill/local search, all algorithms implemented in pyDarwin are global search algorithms that are expected to have a greater 
degree of robustness to local minima than downhill search. Note howwever that all search algorithms (with the exception of exhaustive search) make assumptions about the search space. While none of the algorithms in pyDarwin assume convexity, none are completely robust, 
and search spaces can be deceptive.[#f3]_ 
For all algorithms, the basic process is the same, start at one or more random. Figure 1 depicts the process common to all algorithms.
 
The search space is key to implementation of each algorithm. The overall representation is the same - and n dimensional discrete search space. The values in each 
dimension are then coded into several forms, bit strings and integer string. Ultimately, the model is constructed from the integer string, e.g., values for the number 
of compartment dimenion are 1|2|3. However,for GA, this must be coded as bitstring. There is one additional representation, refered to as a minimal binary string, 
which is used for the downhill step.

The overall process is shown below:

 .. figure:: MLSelection.png

The same 3 files are required for any search, whether exhausitve, GA, GP, RF or GBRF. These file are described in :ref:`required files. <startRequiredFiles>`


.. _The Algorithms:


.. _Exhaustive Search:

Exhaustive Search
------------------
The exhausitve search algorithm is simple to understand. The search space is initally represented as a string of integers - one for each dimension. To facilitate the search, 
this interger string is coded into a "minimal binary". T 
 
.. _Genetic Algorithm:

Genetic Algorithm
-------------------------
 
.. _Gaussian Process (Bayesian Optimization):

Gaussian Process
-------------------------
.. _Random Forest:

Random Forest
-------------------------
.. _Gradient Boosted Random Tree:

Gradient Boosted Random Tree
------------------------------
  
.. [#f1] Wade JR, Beal SL, Sambol NC. 1994  Interaction between structural, statistical, and covariate models in population pharmacokinetic analysis. J Pharmacokinet Biopharm. 22(2):165-77 
 
.. [#f2] PAGE 30 (2022) Abstr 10091 [https://www.page-meeting.org/?abstract=10091]

.. [#f3] PAGE 30 (2022) Abstr 10053 [https://www.page-meeting.org/default.asp?abstract=10053]