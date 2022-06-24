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
no futher improvement is seen. In pyDarwin, GA is implmented using the :ref:`DEAP <DEAP>` package. `GA on Wikipedia <https://en.wikipedia.org/wiki/Genetic_algorithm>`_


.. _GP:

**GP - Gaussian Process (Bayesian optimization)**


.. _GBRT:

**GBRT - Gradient Boosted Random Tree:** Random Forest optimization `Gradient Boosting on Wikipedia <https://en.wikipedia.org/wiki/Gradient_boosting>`_


.. _home directory:

**home directory:** The home directory (specified as "homeDir" in the :ref:`options file<options file>`) will serve as the root directory for all model runs. Within the 
home directory will be one or more generation directories, and within each generation directory will be model directories. Model are run in the model directory. Typically, 
the NMTRAN data file(s) will be in the home directory, and therefore the relative path to the data file specified in the $DATA block will be two directories up, e.g.,

::

   $DATA ..\..\data.csv.

Alternatively, the absolute path can be specified. 

.. _Parameter sorting:

**Parameter sorting:** The merged template file-tokens files-phenotype is first merged. In this merged file the parameters in the searched text are indexed only with 
text, e.g., THETA(ALAG). This is necessary as the integer indices assigned to each parameter cannot be determined until the control file is merged. Once this is done the 
number and sequence of searched THETA/OMEGA/SIGMA values in the control file can be determined and the correct parameter indices assigned. Essential rules for parsing the 
merged template are:

1. Fixed parameter initial estimates MUST be placed before the searched parameter initial estimates. E.g.:
   
::

   $THETA

   (0,1)  ; THETA(1) Clearance

   {ALAG[2]}

   (0,1)  ; THETA(2) Volume


is **NOT** permited, as a searched parameter initial estimate ({ALAG[2]}) occurs before a fixed initial estimated ((0,1)  ; THETA(2) Volume)

1. Each parameter initial estimate must be one a separate line
2. Parameter estimate must be enclosed in parentheses, e.g, (0,1)



.. _Nested Tokens:

**Nested Tokens:** XXXXXXX

.. _Options file:

**Options File:** Specified the options for the search, inculding the algorith, the :ref:`fitness/reward criteria <fitness>`, the population size, the number 
of iterations/generations and whether the downhill search is to be executed.



.. _Phenotype:

**Phenotype:** XXXXXXX

.. _reward:

**Reward:** A number representing the overall "goodness" of the candidate. Called fitness in GA. 


.. _RF:

**RF - Random Forest:** Random Forest optimization `Random Forest on Wikipedia <https://en.wikipedia.org/wiki/Random_forest>`_

https://scikit-optimize.github.io/stable/

.. _scikit-optimized: 

**scikit-optimize:** `Optimization package <https://scikit-optimize.github.io/stable/>`_

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
token key-text pair, the text {:ref:`token stem <token stem>` [n]} in the :ref:`template <template>` is replaced 
by the corresponding values in the token key-text pair. Note that the token key is surrounded by curly braces in the template file. 
For example, if the :ref:`template <template>` contains these two tokens:

{ALAG[1]}

in the $PK block 

and

{ALAG[2]}

in the $THETA block the :ref:`token stem <token stem>` would be ALAG. Again, note that om the template file the "token stem[n]" is enclosed in curly braces. 
N is the index of the token within the token set. While indices to token can be duplicated and indices can be skipped, it is recommended 
that they start at 1 be numbered sequentially through the template file. The ALAG :ref:`token group <token group>` 
would be required in the tokens files. Exactly one :ref:`token set <token set>` would 
be selected (by the search algorithm) for substitution into the template file. If the first 
token set is selected, and this token set contains these token key-text pairs:

ALAG[1] -> "ALAG1=THETA(ALAG)"

ALAG[2] -> "(0,1) ;; initial estimate for ALAG1"

The text "ALAG[1]" in the template file would be replaced by "ALAG1=THETA(ALAG)" and 
the "ALAG[2]" text in the template would be replace by "(0,1) ;; initial estimate for ALAG1". This would then 
result in syntactically correct NMTRAN code.



.. _token stem:

**Token stem:** XXXXXX
