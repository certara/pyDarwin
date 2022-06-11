

ML Model Selection
================================== 
 
 
.. _starterTheory:
 
pyDarwin implements a number of machine learning algorithms for model selection. Machine learning algorithms are broadly divided into two categories:
* Supervised learning
* Unsupervised learning

For supervised learning, the algorithm "learns" to associate certain patterns (e.g., a collection of bit map pictures) with a set of labeled examples. For example, if one has
10,000 pictures of cats and dogs (a training set), with each impage labeled as "cat" or "dog", a artificial neural network (ANN) can find patterns in the 0's and 1's that are associated with "catness" 
or "dogness", and can be fairly successful at predicting for any similar set of bitmaps (the test set) which is a cat and which is a dog.
In contrast, Unsupervised learning has no labeled training set. The traditional model selection/building process for pop pk models is unsupervied. Rathan than the pattern matching 
algorithms of supervised learning, Unsupervised learning is a search. Traditional pop pk/pd model selection uses the "downhill method", starting, usually, at a trival model, then adding
"features" (compartment, lag times, non linear elimination, covariate effects) and accepting the new model if it is better ("downhill"), lower -2LL + some other criteria the use feels important).
To further complicate the taxonomy, recently added is semi-supervised learning. As expected, semi-supervised learning is a mixture of supervised and unsupervised, and 3 of the 4 algorithms 
implemented in pyDarwin are semi-supervised (Gaussian Process, Random Forest and Gradient booste random tree), while 1 is strictly unsupervied (Genetic algorithm). In semi-supervised learning, rather than
training on a data set, such as setting the weights of a ANN based on that training, the weights are initially set randomly. Based on this initial (and non sensical) random ANN, the "best"
model is chosen and run. Now there is a small (N=1) training data set, and the ANN can be trained on this single datum. The ANN is still likely to have a very poor match between inputs (number of compartments,
absorption models, covariates etc) and output (model "goodness"), but with each iteration, the fit should improve.

Central to understanding the model selection process (with manual or machine learning), is the concept of the search space. The search space is an n dimensional space where each dimension represents 
a set of mutually exclusive options. That is, there likely will be a dimension for "number of compartments", with possible values of 1, 2 or 3. Exactly one of these is required (ignoring the possibility of 
Baysian model averaging). Another dimension might be the absorption model, with values of first order, zero order, first order with absorption lag time etc). Similarly the relationship 
between weight and volume (none|linear|power model). Note that each of these dimension are discrete, and mostly stricly categorical (not ordered categorical, first order isn't "more than" zero order).
With this exception the model search space is very analogous to the parameter search space used in non-linear regression. An important difference is that the continuous space in non-linear 
regression has a derivatie, and quadi-Newton methods can be used to to a "downhill search" in that space. Please note that quasi-Newton methods are at risk of finding local minima, and therefore
are sensitive to the initial estimates. 

As the discrete space of model search does not have a derivative, other search methods must be used. The simplest, and the one traditionally used in model selection, is downhill. While efficient (requiring the fewest 
function evaluations [models] to get the solution), it can be demonstrated that this method is not robust [#f1]_ [#f2]_. This lack of robustness is due to the violation of convexity assumption. That is, the downhill search assumes 
that the optimal solution is continuously downhill from every other point in the search space. That is, there are no local minima, and you can start anywhere and you'll end up in the same place. With this assumption, 
a covariate will or will not be "downhill", regardless of whether tested in a one compartment, two compartment; first order of zero order or any other base model, it's all downhill, it doesn't matter what sequence you test 
hypotheses in, the answer will be the same. Wade [#f1]_ showed that the results of tests of hypotheses do indeed depend on other features in the model and Chen [#f2]_ showed that different sequences of tests will commonly yield different models.
   

In contrast to the traditional downhill/local search, all algorithms implemented in pyDarwin are global search algorithms that are expected to have a greater degree of robustness to local minima than downhill search. 
Note howwever that all search algorithms (with the exception of exhaustive search) make assumptions about the search space. While none of the algorithms in pyDarwin assume convexity, none are completely robust, 
and search spaces can be deceptive.[#f3]_ 
For all algorithms, the basic process is the same, start at one or more random. Figure 1 depicts the process common to all algorithms.
 
 
 .. figure:: MLSelection.png

  
.. [#f1] Wade JR, Beal SL, Sambol NC. 1994  Interaction between structural, statistical, and covariate models in population pharmacokinetic analysis. J Pharmacokinet Biopharm. 22(2):165-77 
 
.. [#f2] PAGE 30 (2022) Abstr 10091 [https://www.page-meeting.org/?abstract=10091]

.. [#f3] PAGE 30 (2022) Abstr 10053 [https://www.page-meeting.org/default.asp?abstract=10053]