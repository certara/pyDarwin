:orphan:

.. _startpk7:

###########################################################
Example 7: PK Model, Exhaustive Omega Search
###########################################################

Example 7 uses `dataExample1.csv` for an Exhaustive search of omega structures across candidate models.
   
The template file can be downloaded :download:`here <../examples/user/Example7/template.txt>` and the
tokens file :download:`here <../examples/user/Example7/tokens.json>`.

It is recommended that the user set the directories to something appropriate for their environment. If directories are not set, 
the default is:

::

	{user_dir}\pydarwin\{project_name}

where {user_dir} is the user's home directory and {project_name} is the name of the project.

The options file looks like:

::

    {
      "author": "Certara",
      "algorithm": "EXHAUSTIVE",
      "exhaustive_batch_size": 500,
      "num_parallel": 4,
      "crash_value": 99999999,
      "random_seed": 11,
      "penalty": {
        "theta": 10,
        "omega": 10,
        "sigma": 10,
        "convergence": 100,
        "covariance": 100,
        "correlation": 100,
        "condition_number": 100,
        "non_influential_tokens": 0.00001
      },
      "search_omega_bands": true,
      "max_omega_band_width": 1,
      "search_omega_sub_matrix": true,
      "max_omega_sub_matrix": 2,
      "remove_run_dir": false,
      "nmfe_path": "c:/nm74g64/util/nmfe74.bat",
      "model_run_timeout": 1200
    }


and can be downloaded :download:`here <../examples/user/Example7/options.json>`.

Note the usage of additional options for omega search: :ref:`"search_omega_bands"<search_omega_bands_options_desc>`,
:ref:`"max_omega_sub_matrix"<max_omega_sub_matrix_options_desc>`, :ref:`"search_omega_sub_matrix"<search_omega_sub_matrix_options_desc>`,
and :ref:`"max_omega_sub_matrix"<max_omega_sub_matrix_options_desc>`.

******************************************
Execute Search
******************************************

Usage details for starting a search in ``pyDarwin`` can be found :ref:`here<Execution>`.

See :ref:`"Examples"<examples_target>` for additional details about accessing example files.

Initialization output should look like:

::

    [10:49:51] Including search of band OMEGA, with width up to 1
    [10:49:51] Including search for OMEGA submatrices, with size up to 2
    [10:49:51] Search start time = Wed Jan  4 10:49:51 2023
    [10:49:51] Total of 32 to be run in exhaustive search
    [10:49:51] NMFE found: c:/nm74g64/util/nmfe74.bat
    [10:49:51] Not using Post Run R code
    [10:49:51] Not using Post Run Python code
    [10:49:51] Checking files in C:\Users\jcraig\pydarwin\Example7\temp\0\01
    [10:49:51] Data set # 1 was found: C:\Workspace\Example7/dataExample1.csv



and the final output should appear similar to:

::

    [10:56:58] Iteration = 0, Model    32,           Done,    fitness = 4873.801,    message = No important warnings
    [10:57:00] Iteration = 0, Model    30,           Done,    fitness = 4892.377,    message = No important warnings
    [10:57:02] Iteration = 0, Model    29,           Done,    fitness = 4862.237,    message = No important warnings
    [10:57:44] Iteration = 0, Model    31,           Done,    fitness = 4959.865,    message = No important warnings
    [10:57:44] Current Best fitness = 4838.492760373933
    [10:57:44] Final output from best model is in .\Example7\output\FinalResultFile.lst
    [10:57:44] Number of unique models to best model = 6
    [10:57:44] Time to best model = 0.5 minutes
    [10:57:44] Best overall fitness = 4838.492760, iteration 0, model 3
    [10:57:44] Elapsed time = 7.9 minutes
    