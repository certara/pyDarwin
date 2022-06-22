.. pyDarwin documentation master file, created by
   sphinx-quickstart on Thu Jun  9 08:53:00 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Glossary
====================================

.. _DEAP: 

**DEAP:** Distributed Evolutionary Algorithms in Python `DEAP github <https://github.com/DEAP/deap>`_

**fitness:** A number representing the overall "goodness" of the candidate. Called fitness in GA 
more in most other algorithms is called "reward".

.. _fitness:

**fitness:** A number representing the overall "goodness" of the candidate. Called fitness in GA 
more in most other algorithms is called "reward".

.. _GA:

**GA - Genetic Algorithm:** An unsupervised search algorithm that mimicks the mathetmatics 
of 'survival of the fittest'. A population of candidates is generated randomly, an the "fitness" 
of each candidate is evaluated. A subsequent population is candidate is then generated with the 
present generation as "parents", with selection a function of fitness, with the more 
fit individual being more likely to be selected as parents. The parents are then paired of, undergo 
cross over and mutation and a new generation created. This process is continued until 
no futher improvement is seen. `GA on Wikipedia <https://en.wikipedia.org/wiki/Genetic_algorithm>`_


.. _GP:

**GP - Gaussian Process (Bayesian optimization)**


.. _GBRT:

**GBRT - Gradient Boosted Random Tree:** Random Forest optimization `Gradient Boosting on Wikipedia <https://en.wikipedia.org/wiki/Gradient_boosting>`_



.. _Options file:

**Options File:** Specified the options for the search, inculding the algorith, the :ref:`fitness/reward criteria <fitness>`, the population size, the number 
of iterations/generations and whether the downhill search is to be executed.

.. _reward:

**Reward:** A number representing the overall "goodness" of the candidate. Called fitness in GA. 


.. _RF:

**RF - Random Forest:** Random Forest optimization `Random Forest on Wikipedia <https://en.wikipedia.org/wiki/Random_forest>`_



.. _template:

**Template:** XXXXX

.. _token:

**Token:** XXXXX
 

.. _tokens file:

**Tokens file:** XXXXX

.. _token group:

**Token group:** XXXXX

.. _token set:

**Token set**: one for each option in the that dimension

.. _token key-text pair:

**Token key-text pair:** A :ref:`token set <token set>` contains two or more token key-text pairs. These 
pairs are very analagous to JSON key-value pairs, except that only text values are permitted. For each 
token key-text pair, the :ref:`token stem <token stem>` [n] in the :ref:`template <template>` is replaced 
by the corresponding values in the token key-text pair. For example, if the :ref:`template <template>` 
contains these two tokens:

ALAG[1]

in the $PK block 

and

ALAG[2]

in the $THETA block 
the :ref:`token stem <token stem>` would be ALAG. The ALAG :ref:`token group <token group>` 
would be required in the tokens files. Exactly one :ref:`token set <token set>` would 
be selected (by the search algorithm) for substitution into the template file. If the first 
token set is selected, and this token set contains these token key-text pairs:

ALAG[1] -> "ALAGA1=THETA(ALAG)"

ALAG[2] -> "(0,1) ;; initial estimate for ALAG1"

The text "ALAG[1]" in the template file would be replaced by "ALAGA1=THETA(ALAG)" and 
the "ALAG[2]" text in the template would be replace by "(0,1) ;; initial estimate for ALAG1". This would then 
result in syntactically correct NMTRAN code.



.. _token stem:

**Token stem:** XXXXXX
