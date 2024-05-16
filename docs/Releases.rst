.. include:: .special.rst

######################
Releases
######################

**********************
pyDarwin-Certara 2.0.1
**********************

Issues Corrected
====================

* Estimated OMEGAS are now used when calculating OMEGA penalty, fixed OMEGAS are ignored.
* Estimated SIGMAS are now used when calculating SIGMA penalty, fixed SIGMAS are ignored.
* Unnecessary memory allocation when calculating size of total search space.


**********************
pyDarwin-Certara 2.0
**********************

What's New
====================

* Added NLME Engine support, including :ref:`Omega Block Search <omega_block_search_target>`.

* Introduced :mono_ref:`{darwin_cmd} <darwin_cmd_alias>` alias for Linux Grid runs.

* Introduced :mono_ref:`search_info <search_info>` command.

* Introduced estimations of number of models and remaining time. The former is shown in the beginning of the search as well as in the ``search_info`` output (except for Exhaustive search), the latter -- in the beginning of every but first iteration.
  Those may be not too accurate since they assume a certain amount of Downhill Search iterations (if it is requested) and that a model run time is on average the same (which is not always the case due to duplicates that sometimes make up a large part of the iteration).

* Added tokens consistency check before running the search.

* Added NONMEM license expiration error to the visible errors.

* Updated and renamed columns in **results.csv**.

* Introduced new model statuses:

    - Clone -- a sibling with the same genotype

    - Twin -- a sibling with the same phenotype

    - Restored -- a model run picked from the cache, when the cache was loaded form a file and the model was picked for the first time

    - Cache -- a model run picked from the cache in all other cases

* Improved :ref:`Omega Structure Search <omega_search_usage_target>`, e.g.:

    - added :ref:`individual omega structure search <individual_omega_search_options_desc>`

    - increased number of possible omega block patterns

    - reduced number of model runs by adding the omega structure to the model phenotype, detecting twins, and looking for duplicates in model cache by phenotype

* Introduced key models retention: best models from every iteration :ref:`can be saved <keep_key_models_options_desc>` with all the necessary output in a :ref:`separate folder <key_models_dir_options_desc>` for further analysis.

* Changed :ref:`Final Downhill <final_downhill_search_options_desc>` and :ref:`2-bit search <Local Two bit Search>` iteration names.

* Removed unnecessary 0 generation from :ref:`Genetic Algorithm <GA_desc>`.

* Reorganized examples folder, added NONMEM and :mono:`NLME subfolders`.

* If :mono_ref:`random_seed <random_seed_options_desc>` is not set in the options file it will be initialized with a random number.

* :mono_ref:`working_dir <working_dir_options_desc>` must be an absolute path.

Issues Fixed
====================

* Removed commas and new lines from translation and runtime messages so they won't break CSV structure anymore.

* Corrected calculation of 'Number of unique models to best model'.


**********************
pyDarwin-Certara 1.1.1
**********************

What's New
====================

* The condition_number penalty is now added to the fitness value for the case when the covariance step is successful and condition_number > 1000.
  Previously, the condition_number penalty was added to fitness value only for the case when covariance was unsuccessful or not requested.

Issues Fixed
====================

* An issue was corrected where the correlation penalty does not get added to the resulting fitness value for cases when it should.


********************
pyDarwin-Certara 1.1
********************

What's New
====================

* pyDarwin now supports additional options for :ref:`Searching Omega Structure<omega_search_usage_target>`, including:

    * Band matrix

    * Submatrices

* pyDarwin now supports usage of the :ref:`Particle Swarms Optimization (PSO)<PSO_desc>` algorithm to search for a global optimal solution in the candidate model search space.


Issues Fixed
====================

* An issue has been fixed that could cause the search to fail if the covariance step ($COV) was not specified in template.txt.

********************
pyDarwin-Certara 1.0
********************

Initial release of pyDarwin-Certara offers the Python module `darwin` to
perform a search over a candidate model space using one of the following
machine learning :ref:`algorithms<The algorithms>`:

* :ref:`Genetic Algorithm (GA)<GA_desc>`
* :ref:`Gradient Boosted Random Trees (GBRT)<GBRT_desc>`
* :ref:`Random Forest (RF)<RF_desc>`
* :ref:`Gaussian Process (GP)<GP_desc>`

Users can alternatively select the :ref:`Exhaustive Search (EX) <EX_desc>` to execute
all potential candidate models in a given search space without machine learning
optimization.

Two primary functions to execute the search have been made available:

.. code:: python

    python -m darwin.run_search <template_path> <tokens_path> <options_path>

To execute, call the ``darwin.run_search`` function and provide the paths to the following files as arguments:

1. :ref:`Template file <template_file_target>` (e.g., template.txt) - basic shell for NONMEM control files
2. :ref:`Tokens file <tokens_file_target>` (e.g., tokens.json) - json file describing the dimensions of the search space and the options in each dimension
3. :ref:`Options file <options_file_target>` (e.g., options.json) - json file describing algorithm, run options, and post-run penalty code configurations.


Alternatively, you may execute the :ref:`darwin.run_search_in_folder <darwin.run_search_in_folder>` function,
specifying the path to the folder containing the ``template.txt``, ``tokens.json``, and ``options.json`` files
as a single argument:

.. code:: python

    python -m darwin.run_search_in_folder <folder_path>

