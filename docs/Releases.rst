
######################
Releases
######################


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

