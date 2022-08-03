


.. _startpk6:

Example 6: PK Model, DMAG by RF with post-run Python code
=========================================================

Example 6 is again the same data and search as Example 4 and 5, but using :ref:`Random Forest<RF_desc>` for search, and python code for 
post run PPC penalty calculation.
   
The template file can be downloaded :download:`here <../examples/user/Example6/template.txt>`

and the tokens file :download:`here <../examples/user/Example6/tokens.json>`

As before, that to run in the enviroment used for this example, the directories are set to:

::
        
    "working_dir": "u:/pyDarwin/example5/working",
    "temp_dir": "u:/pyDarwin/example5/rundir",
    "output_dir": "u:/pyDarwin/example5/output",

It is recommended that the user set the directories to something appropriate for their enviroment. If directories are not set 
the default is:


::

	{user_dir}\pydarwin\{project_name}

In either case, the folder names are given in the initial and final output to facilitate finding the files and debuggins.

The options file is given here:

::

    {
    "author": "Certara",
    "algorithm": "RF",
    "num_opt_chains": 4,

    "random_seed": 11,
    "population_size": 80,
    "num_parallel": 4,
    "num_generations": 7,

    "downhill_period": 5,
    "num_niches": 2,
    "niche_radius": 2,
    "local_2_bit_search": true,
    "final_downhill_search": true,

    "crash_value": 99999999,

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

    "remove_run_dir": false,

    "nmfe_path": "c:/nm744/util/nmfe74.bat",
    "model_run_timeout": 1200,

    "postprocess": {
        "use_python": true,
        "post_run_python_code": "{project_dir}/CmaxPPC.py"
    }
    }


and can be downloaded :download:`here <../examples/user/Example6/options.json>`
 

Starting the search and command line output:


:ref:`Starting the search is covered here<Execution>`

The initialization output should look similar to this:

::

        
    [06:15:40] Options file found at ..\examples\user\Example6\options.json
    [06:15:40] Preparing project working folder...
    [06:15:40] Preparing project output folder...
    [06:15:40] Preparing project temp folder...
    [06:15:40] Model run priority is below_normal
    [06:15:40] Using darwin.MemoryModelCache
    [06:15:40] Project dir: C:\fda\pyDarwin\examples\user\Example6
    [06:15:40] Data dir: C:\fda\pyDarwin\examples\user\Example6
    [06:15:40] Project working dir: u:/pyDarwin/example6/working
    [06:15:40] Project temp dir: u:/pyDarwin/example6/rundir
    [06:15:40] Project output dir: u:/pyDarwin/example6/output
    [06:15:40] Writing intermediate output to u:/pyDarwin/example6/output\results.csv
    [06:15:40] Models will be saved in u:/pyDarwin/example6/working\models.json
    [06:15:40] Template file found at ..\examples\user\Example6\template.txt
    [06:15:40] Tokens file found at ..\examples\user\Example6\tokens.json
    [06:15:40] Search start time = Tue Aug  2 06:15:40 2022
    [06:15:40] Algorithm is RF



and the final output should look something like this:

::

    [15:14:32] Iteration = FNS060, Model   271,   Duplicate(1),    fitness = 8477.831,    message = From NM_5D05_12: No important warnings
    [15:14:32] Iteration = FNS060, Model   272,           Done,    fitness = 8534.422,    message = From NM_5D06_21: No important warnings
    [15:14:32] Iteration = FNS060, Model   273,           Done,    fitness = 99999999,    message = From NM_5S070_273: No important warnings
    [15:14:32] Iteration = FNS060, Model   274,   Duplicate(1),    fitness = 8477.831,    message = From NM_5D05_12: No important warnings
    [15:14:32] Iteration = FNS060, Model   275,           Done,    fitness = 10088.210,    message = From NM_5S070_275: No important warnings
    [15:14:32] Iteration = FNS060, Model   276,   Duplicate(1),    fitness = 8477.831,    message = From NM_5D05_12: No important warnings
    [15:14:36] No change in fitness in 7 iterations
    [15:14:36] Final output from best model is in u:/pyDarwin/example6/output\FinalResultFile.lst
    [15:14:36] Number of unique models to best model = 536
    [15:14:36] Time to best model = 283.0 minutes
    [15:14:36] Best overall fitness = 8477.831400, iteration 5D05, model 12
    [15:14:36] Elapsed time = 538.9 minutes