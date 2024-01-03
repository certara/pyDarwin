:orphan:

.. _startpd8:

###########################################################
Example 8: Emax Model, PSO
###########################################################

Example 8 uses the :ref:`PSO<PSO_desc>` algorithm on a simulated dataset using an Emax model
with Body Weight (BW) having a power effect on E0, Sex and Race having an exponential effect
on E0, sigmodicity = 1, and a proportional error model. Additionally, a final downhill search is
performed.

The template file can be downloaded :download:`here <../examples/NONMEM/user/Example8/template.txt>`
and the tokens file :download:`here <../examples/NONMEM/user/Example8/tokens.json>`.

The options file looks like:

::

    {
      "author": "Certara",
      "algorithm": "PSO",
      "PSO": {
        "cognitive": 0.5,
        "social": 0.9,
        "inertia": 0.9,
        "neighbor_num": 2,
        "p_norm": 1
      },
      "num_parallel": 4,
      "random_seed": 11,
      "population_size": 10,
      "num_generations": 7,
      "downhill_period": -1,
      "num_niches": 2,
      "niche_radius": 2,
      "local_2_bit_search": false,
      "final_downhill_search": true,
      "penalty": {
        "theta": 5,
        "omega": 5,
        "sigma": 5,
        "convergence": 100,
        "covariance": 100,
        "correlation": 100,
        "condition_number": 100,
        "non_influential_tokens": 0.00001
      },
      "crash_value": 99999999999,
      "remove_run_dir": false,
      "nmfe_path": "c:/nm74g64/util/nmfe74.bat",
      "model_run_timeout": 1200
    }



and can be downloaded :download:`here <../examples/NONMEM/user/Example8/options.json>`.
 

******************************************
Execute Search
******************************************

Usage details for starting a search in ``pyDarwin`` can be found :ref:`here<Execution>`.

See :ref:`"Examples"<examples_target>` for additional details about accessing example files.

Initialization output should look like:

::

    [12:56:38] Model run priority is below_normal
    [12:56:38] Using darwin.MemoryModelCache
    [12:56:38] Algorithm is PSO
    [12:56:38] Project dir: C:\Workspace\Example8
    [12:56:38] Data dir: C:\Workspace\Example8
    [12:56:38] Project working dir: C:\Users\jcraig\pydarwin\Example8
    [12:56:38] Project temp dir: C:\Users\jcraig\pydarwin\Example8\temp
    [12:56:38] Project output dir: C:\Users\jcraig\pydarwin\Example8\output
    [12:56:38] Writing intermediate output to C:\Users\jcraig\pydarwin\Example8\output\results.csv
    [12:56:38] Models will be saved in C:\Users\jcraig\pydarwin\Example8\models.json
    [12:56:38] Template file found at template.txt
    [12:56:38] Tokens file found at tokens.json
    [12:56:38] Search start time = Fri Dec 16 12:56:38 2022
    [12:56:38] NMFE found: c:/nm74g64/util/nmfe74.bat
    [12:56:38] Not using Post Run R code
    [12:56:38] Not using Post Run Python code
    [12:56:38] Checking files in C:\Users\jcraig\pydarwin\Example8\temp\0\02
    [12:56:38] Data set # 1 was found: C:\Workspace\Example8\PDdata.csv
    [12:57:03] Iteration = 0, Model     2,           Done,    fitness = -619.152,    message = No important warnings
    [12:57:05] Iteration = 0, Model     4,           Done,    fitness = -2475.044,    message = No important warnings
    [12:57:11] Iteration = 0, Model     3,           Done,    fitness = -723.686,    message = No important warnings



and the final output should look like:

::

    [13:13:01] Iteration = 6D03, Model    15,           Done,    fitness = -2822.644,    message = No important warnings
    [13:13:05] Iteration = 6D03, Model    16,           Done,    fitness = -2821.427,    message = No important warnings
    [13:13:14] Iteration = 6D03, Model    20,           Done,    fitness = -2820.297,    message = No important warnings
    [13:13:14] best fitness -2829.911515459548, model [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1]
    [13:13:14] Final output from best model is in C:\Users\jcraig\pydarwin\Example8\output\FinalResultFile.lst
    [13:13:14] Number of unique models to best model = 72
    [13:13:14] Time to best model = 13.4 minutes
    [13:13:14] Best overall fitness = -2829.911515, iteration 6D02, model 6
    [13:13:14] Elapsed time = 16.6 minutes
    