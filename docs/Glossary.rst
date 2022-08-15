
.. include:: .special.rst

########
Glossary
########
 
.. _Crash Value:

**Crash Value**: Anyone with experience in Population PK modeling has experience with crashes. There are many possible sources for a crash, including:

- syntax errors in the control file
- math errors (divide by zero, log(negative value))
- numerical error in execution

Significant effort was made to capture these errors and display them to the user the console and in the messages.txt file (in the working directory).
For debugging purposes, these errors can be reproduced by going to the run directory (:file:`run_dir/generation/model_num`) and rerunning the model from the command line.

In addition, errors may occur in running post run R or python code. Finally, the NONMEM or R code may time out, producing no final results.
In all of these cases, the fitness/reward value assigned is called the crash_value. The crash value is set in the options file and should be substantially higher 
than any anticipated fitness/reward from a model that ran to completion, regardless of the "goodness" of the model.


.. _Data Directory:

**Data Directory:** Folder where datasets are located. Used if the template file specifies datasets as {data_dir}/datafileName, which is the preferred method.
May be an absolute or a relative path, default value is {project_dir}. Keep in mind that NONMEM doesn’t allow dataset path to be longer than 80 characters and must be in quotes if 
it contains spaces.


.. _DEAP: 

**DEAP:** Distributed Evolutionary Algorithms in Python `DEAP github <https://github.com/DEAP/deap>`_. DEAP is a python package that includes several evolutionary algorithms, 
including the Genetic Algorithm - the GA option in the :ref:`options file<options file>`.

 
.. _fitness:

**fitness:** A number representing the overall "goodness" of the candidate. Called fitness in GA. 
In other algorithms, it is called "reward" or "cost", or sometimes "loss function". All algorithms in pyDarwin are designed to minimize this value.

.. _full binary:

| **full binary**: The full binary is a representation of a specific model coded such that all possible values of the bit string are permitted. In general, this will result in 
  redundancy of the matching of bit strings with the :ref:`integer representation<integer representation>`. For example, if a given :ref:`token group<token group>` included 3 
  :ref:`token sets<token set>`, two bits would be required (one bit can only specify two options). Two bits have 4 possible values, while only 3 are needed. Therefore, some duplication 
  of the matching of the full binary [(0,0),(0,1),(1,0) and (1,1)] to the integer representation [1,2,3] is required. Managing this redundancy is handled internally by pyDarwin. The full binary is used only by :ref:`Genetic algorithm<GA>`.
| The minimal binary contrasts with the :ref:`full binary <full binary>`.

.. _GA:

**GA - Genetic Algorithm:** An unsupervised search algorithm that mimics the mathematics 
of 'survival of the fittest'. A population of candidates is generated randomly, and the "fitness" 
of each candidate is evaluated. A subsequent population of candidates is then generated using the 
present generation as "parents", with selection a function of fitness (i.e., the more 
fit individual being more likely to be selected as parents). The parents are then paired off, undergo 
crossover and mutation and a new generation created. This process is continued until 
no further improvement is seen. In pyDarwin, GA is implemented using the :ref:`DEAP <DEAP>` package. `GA on Wikipedia <https://en.wikipedia.org/wiki/Genetic_algorithm>`_


.. _GBRT:

**GBRT - Gradient Boosted Random Tree:** `Similar to Random Forests <https://towardsdatascience.com/decision-trees-random-forests-and-gradient-boosting-whats-the-difference-ae435cbb67ad>`_ ,
Gradient Boosted Random Trees use `Gradient Boosting <https://en.wikipedia.org/wiki/Gradient_boosting>`_ for optimization and 
may increase the precision of the tree building by progressively building the tree, and calculating a gradient of the reward/fitness with respect to each decision. 

.. _GP:

**GP - Gaussian Process (Bayesian optimization)**
Gaussian Process is implemented in the scikit-optimize package and described `here. <https://scikit-optimize.github.io/stable/auto_examples/bayesian-optimization.html>`_  
GP is well-suited to the problem of model selection, as (according to `Wikipedia <https://en.wikipedia.org/wiki/Bayesian_optimization>`_)
it is well-suited to black box function with expensive reward calculations. Indeed, experience to date suggests that GP, along with :ref:`GA <GA>`, are the most robust and 
efficient of the ML algorithms, especially if used in combination with a local 1 and 2 bit exhaustive search. 

**Home:** See :ref:`pyDarwin home <pydarwin_home>`.
 
.. _Integer representation:

**Integer representation:** The integer representation of a given model is what is used to construct the control file. Specifically, the integer representation is a string 
of integers, with each integer specifying which :ref:`token set<token set>` is to be substituted into the :ref:`template<template>`. For example, an integer string of [0,1,2] would substitute the 
0th token set in the template for the first :ref:`token group<token group>`, the 1st token set for the 2nd token group and the 3rd token set for the 3rd token group. The integer representation 
is managed internally by ``pyDarwin``, and in the case of :ref:`Genetic algorithm<GA>`, derived from the :ref:`full binary<full binary>` representation.  


.. _Local One bit Search: 

**Local One bit Search:** In 1 bit local search, first the :ref:`minimal binary representation<minimal binary>` of the model(s) to be searched are generated. 
Then each bit in that bit string is 'flipped'. So, a search with 30 bits will generate 30 models in each iteration of the 1 bit search. 
This process is continued, searching on the best model from the previous step until improvement no longer occurs.

.. _Local Two bit Search: 

**Local Two bit Search:** The 2 bit local search is like the :ref:`1 bit local search<Local One bit Search>` except that every 2 bit change of the :ref:`minimal binary representation<minimal binary>` 
is generated in each step, and all 2 bit change combinations are generated and run. 
This results in a much larger number of models to search, (N^2+n)/2. This process is again repeated until no further improvement occurs.

.. _Local Search: 

**Local Search:** It has been `demonstrated <https://www.page-meeting.org/default.asp?abstract=10053>`_  that all of the available algorithms are insufficiently robust at finding the 
final best model. To some degree, the global search algorithms serve to essentially find good initial estimates, to make finding the global minimum (and not a local minimum) 
more likely. To supplement the global search algorithms, 2 local search algorithms are used. These local search algorithms systematically change each bit in the :ref:`minimal binary representation <minimal binary>` 
of the model and run that model. The user can specify whether this local search is done on some interval or generations/iterations and/or at the end of the global search. 
First a 1 bit local search :ref:`Local One bit Search<Local One bit Search>` (also called downhill search) is done, then, if requested, a :ref:`Local Two bit Search<Local Two bit Search>` is done.

.. _minimal binary:

**Minimal Binary**: The minimal binary is one of three representations of a model phenotype. The minimal binary is simply a binary that has some possible values removed to avoid duplications. For example, 
if the search space includes a dimension for 1, 2, or 3 compartments, 2 bits will be needed to code this. With the required 2 bits, some redundancy is unavoidable. So, the mapping might be::

   [0,0] -> 1
   [0,1] -> 2
   [1,0] -> 2
   [1,1] -> 3

with 2 bit strings mapped to a value of 2. In the minimal binary, the mapping is simply::

  [0,0] -> 1
  [0,1] -> 2
  [1,0] -> 3

and a bit string of [1,1] isn't permitted. This eliminates running the same model (from different bit strings). The minimal binary representation is used for the downhill and local 2 bit search.


The minimal binary contrasts with the :ref:`full binary <full binary>`.

.. _Niche Penalty:

**Niche Penalty:** The niche penalty is computed by first calculating the “distance matrix”, the pair-wise Mikowski distance from the present model to all other models. The 
“crowding” quantity is then calculated as the sum of: (distance/niche_radius)**sharing_alpha for all other models in the generation for which the Mikowski distance is less than 
the niche radius. Finally, the penalty is calculated as: exp((crowding-1)*niche_penalty)-1. The objective of using a niche penalty is to maintain diversity of models, 
to avoid premature convergence of the search, by penalizing when models are too similar to other models in the current generation. A typical value for the penalty is 20 (the default). 


.. _Niche Radius:

**Niche Radius:** The niche radius is used to define how similar pairs of models are. This is used to select models for the :ref:`Local search<Local Search>`, as requested, and to calculate the sharing penalty for 
:ref:`Genetic Algorithm<GA_desc>`.

.. _Parameter sorting:

**Parameter sorting:** The tokens are first merged into the template file. In this merged file, the parameters in the searched text are indexed only with 
text, e.g., THETA(ALAG). This is necessary as the integer indices assigned to each parameter cannot be determined until the control file is merged. Once this is done, the 
number and sequence of searched THETA/OMEGA/SIGMA values in the control file can be determined and the correct parameter indices assigned. Essential rules for parsing the 
merged template are:

Fixed parameter initial estimates should be placed before the searched parameter initial estimates. For example,
the following is not recommended (although it may work).

   $THETA
   (0,1)  ; THETA(1) Clearance
   {ALAG[2]}
   (0,1)  ; THETA(2) Volume
   

A searched parameter initial estimate ({ALAG[2]}) occurs before a fixed initial estimated ((0,1)  ; THETA(2) Volume).

Each parameter initial estimate must be on a separate line. Parameter estimates must be enclosed in parentheses, e.g., (0,1).

.. _Nested Tokens:

**Nested Tokens:** ``pyDarwin`` permits nested tokens to be used in the :ref:`tokens file<tokens file_s>`. This permits one token to contain another token, to an arbitrary level. Note that 
using nested tokens does **not** reduce the search space size, it only reduces the number of token sets the user needs to generate, and simplifies the logic (although, commonly, the logic quickly 
becomes impenetrable). For example, assume that the search is to contain one compartment 
(ADVAN2) and two compartment (ADVAN4), and if ADVAN4 is selected, search whether K23 and K32 are functions of weight. K23 is not a parameter of a one compartment model. One option would be to simply write out 
all possible models:

1 compartment::

   ["ADVAN2 ;; advan2",
	   ";; PK 1 compartment ",
	   ";; THETA 1 compartment"
	],


2 compartment - without K23~weight::

   ["ADVAN4 ;; advan4",
	   "K23=THETA(ADVANA)\n  K32=THETA(ADVANB)",
	   "(0.001,0.02)  \t ; THETA(ADVANA) K23 \n (0.001,0.3) \t ; THETA(ADVANB) K32 "
	],


2 compartment - with K23~weight::

  ["ADVAN4 ;; advan4",
     "K23=THETA(ADVANA)*CWT**THETA(K23~WT)\n  K32=THETA(ADVANB)*CWT**THETA(K23~WT)",
     "(0.001,0.02)  \t ; THETA(ADVANA) K23 \n (0.001,0.3) \t ; THETA(ADVANB) K32 \n (0,0.1) \t; THETA(K23~WT) K23~WT" "
  ],


2 bits would be required to specify these 3 options. 

An alternative is to have one token group for a number of compartments:

1 compartment vs 2 compartment, and have the K32~WT nested within the ADVAN4::

   ["ADVAN2 ;; advan2",
	    ";; PK 1 compartment ",
	    ";; THETA 1 compartment"
	],

	["ADVAN4 ;; advan4",
	    "K23=THETA(ADVANA)**{K23~WT[1]}**\n  K32=THETA(ADVANB)**{K23~WT[1]}**",
	    "(0.001,0.02)  \t ; THETA(ADVANA) K23 \n (0.001,0.3) \t ; THETA(ADVANB) K32 \n{K23~WT[2]} \t ; init for K23~WT "
   ],

and another token set (nested within the ADVAN token set) for K23 and K32~WT::

   [
		["",
		 ""
		],
		["*WTKG**THETA(K23~WT)",
			"(0,0.1) \t; THETA(K23~WT) K23~WT"
		]
	],

This also requires 2 bits, one for the ADVAN token group, one for the K23~WT token group. Using nested tokens can reduce the number of token sets in a token group, at the expense of more token
groups. While more than one level of nested tokens is permitted, the logic of constructing them quickly becomes very complicated.   


The full example is given in :ref:`example 4<startpk4>`.

.. _nmfe_path:

**nmfe_path:**
The path to nmfe??.bat (Windows) or just nmfe?? (Linux). Must be provided in the :mono_ref:`nmfe_path<nmfe_path_options_desc>`. Only NONMEM 7.4 and 7.5 are supported.

.. _Options file:

**Options File:** Specifies :ref:`the options <Options>` for the search, including the algorithm, the :ref:`fitness/reward criteria <fitness>`, the population size, the number 
of iterations/generations and whether the downhill search is to be executed.


.. _Output Directory:

| **Output Directory:** Folder in which all the results files, such as ``results.csv`` and Final ``.mod`` and ``.lst`` files are saved. Default value is
  ':mono_ref:`{working directory}<working directory>`/output'.
| A reasonable value ``{project_dir}/output`` may be used if you want to version control the project and the results.

.. _Phenotype:

**Phenotype:** The integer string representation for any model.


.. _Project Directory:


**Project Directory** - Folder where the template, token, and options files are located (and maybe datasets, see :ref:`Data Directory <Data Directory>`).
Can be provided as an argument for ``run_search_in_folder`` or determined by path to :file:`options.json` (as parent folder). This cannot be set in options file.

.. _pydarwin_home:

**pyDarwin home** Default location for every project's :mono_ref:`{working_dir}<working directory>`. Usually is set to ``<user home dir>/pydarwin``. Can be relocated using :ref:`PYDARWIN_HOME<pydarwin_home_env_var>`.

.. _reward:

**Reward:** A number representing the overall "goodness" of the candidate, the sum of -2LL and the user-defined penalties. Called "fitness" in GA. 


.. _RF:

**RF - Random Forest:** `Random Forest <https://en.wikipedia.org/wiki/Random_forests>`_ consists of splitting the search space (based on the "goodness" of each model, in this case), thus continuously dividing the 
search space into "good" and "bad" regions. As before, the initial divisions are random, but become increasingly well-informed as real values for the fitness/reward of models are 
included.

.. _scikit-optimized: 

**scikit-optimize:** `Optimization package <https://scikit-optimize.github.io/stable/>`_
The python package that includes :ref:`GP<GP_desc>`, :ref:`RF<RF_desc>`, and :ref:`GBRT<GBRT_desc>`.

.. _temp_dir:

**temp_dir:** Folder where all iterations/runs are performed, i.e., where all NONMEM files are written.
Default value is ':mono_ref:`{working_dir}<working directory>`/temp'. May be deleted after search finished/stopped, if :mono_ref:`remove_temp_dir <remove_temp_dir_options_desc>` is set to true.

.. _template:

**Template:** A text string, saved in the :ref:`template file<template_file_target>` that forms the basis for the models to be run. The template file is similar to a NONMEM control file, but with :ref:`tokens<token>`
that are replaced by text strings specified in the :ref:`tokens file<tokens_file_target>`.

.. _token:

**Token:** A token is a text string that appears in the :ref:`Template<template_file_target>`.  The format of the string is {:ref:`token stem<token stem>` [index]}, where *token stem* identifies the :ref:`token group<token group>` and index identifies which :ref:`token key-text pair<token key-text pair>` within the :ref:`token set<token set>` is to be substituted. 
 

.. _tokens file_s:

**Tokens file:** See :ref:`"Tokens file" <tokens_file_target>`.

.. _token group:

**Token group:**
A token group is a collection of :ref:`token sets<token set>` that defines a single dimension in the search space. For any model, exactly one of the tokens sets will be selected to be substituted 
into the template file.

.. _token set:

**Token set**: One for each option in the dimension.

.. _token key-text pair:

**Token key-text pair:** A :ref:`token set <token set>` contains two or more token key-text pairs. These 
pairs are very analogous to JSON key-value pairs, except that only text values are permitted. For each 
token key-text pair, the text {:ref:`token stem <token stem>` [n]} in the :ref:`template <template>` is replaced 
by the corresponding values in the token key-text pair. Note that the token key is surrounded by curly braces in the template file. 
For example, if the :ref:`template <template>` contains these two tokens::

   {ALAG[1]}

in the $PK block 

and::

   {ALAG[2]}

in the $THETA block, the :ref:`token stem <token stem>` would be ALAG. Again, note that in the template file the "token stem[n]" is enclosed in curly braces. 
N is the index of the token within the token set. While indices to token can be duplicated and indices can be skipped, it is recommended 
that they start at 1 and be numbered sequentially through the template file. The ALAG :ref:`token group <token group>` 
would be required in the tokens files. Exactly one :ref:`token set <token set>` would 
be selected (by the search algorithm) for substitution into the template file. If the first 
token set is selected, and this token set contains the following token key-text pairs::

   ALAG[1] -> "ALAG1=THETA(ALAG)"

   ALAG[2] -> "(0,1) ;; initial estimate for ALAG1"

the text "ALAG[1]" in the template file would be replaced by "ALAG1=THETA(ALAG)" and 
the "ALAG[2]" text in the template would be replaced by "(0,1) ;; initial estimate for ALAG1". This would 
result in syntactically correct NMTRAN code (except that the index to THETA is still a text string). The appropriate 
index for THETA can be determined only after all the features/token sets are selected. This is handled by ``pyDarwin``. Similar 
logic (ETAs index by text strings, which are replaced by integers) applies for ETAs and EPSs. It is most convenient to use the :ref:`token stem<token stem>` to 
index the parameters, e.g., for the CL~WT tokens set, one might use THETA(CL~WT). If more than one THETA is used in a token set, one can 
simply add an integer (e.g., THETA(CL~WT1) and THETA(CL~WT2)), but the THETA text indices must be unique, to generate unique integer values. Any 
duplication of THETA text indices is permitted (e.g., if you want the same exponent for CL and Q) but will result in duplication of the integer indices, e.g.,

:: 
   
   {*WTKG**THETA(CL~WT)} ;; for clearance

and

::
   
   {*WTKG**THETA(CL~WT)} ;; for Q

would result in

::

   CL=THETA(1)*WT**THETA(2) ;; for clearance

and

:: 

   Q =THETA(2)*WT**THETA(2) ;; for Q

Duplicate text indices will yield duplicate integer indices. By the same logic, comments can be put into initial estimates by including 
THETA(CL~WT) after a ";" in the $THETA block, e.g., :: 

   (0,0.75) \t; THETA(CL~WT) exponent on clearances 

will result in ::

   (0,0.75)    ;THETA(2) exponent on clearances 

as the THETA(CL~WT) is similarly replaced by THETA(2).


.. _token stem:

**Token stem:**
The token stem is a unique identifier for the :ref:`token group<token group>`. This text string is used to link the tokens in the template file to the 
:ref:`token sets<token set>`. 
In the json code file for tokens:

.. figure:: tokens.png
 
.. _Tournament selection:

**Tournament Selection**
An algorithm used in :ref:`GA<GA_desc>` when there are two or more "parents". The one with the highest fitness (lowest penalized -2LL) wins and enters into the next 
generation.

.. _working directory:

**Working directory** Folder where all project's intermediate files are created, such as models.json (model run cache), messages.txt (log file), interim model files, and stop files.
It is also a default location of output and temp folders. Can be set with :mono_ref:`working_dir <working_dir_options_desc>` option.
By default, it is set to ':mono_ref:`\<pyDarwin home\><pydarwin_home>`/:mono_ref:`{project_stem} <project_stem_alias>`'.
