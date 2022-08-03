

Example 5: PK Model, DMAG by GP
==============================================
  

.. _startpk5:

Example 5 is very similar to :ref:`Example 4<startpk4>`. The important difference is the use of :ref:`Gaussian Process<GP_desc>` rather than 
:ref:`Genetic Algoritm<GA_desc>`. As noted in :ref:`Example 4<startpk4>` the `ask step <https://scikit-optimize.github.io/stable/modules/optimizer.html#>`_ 
for large cumulative sample sizes (> 500) will become very long. In this example, the population/sample size is reduced to 20 from 80. This improves the 
execution time for the ask step, but note that the best model isn't found until the 2nd round of 2 it local search, 
whereas in :ref:`Example 4<startpk4>` it was found after the first round of 2 bit local search. 

The template and tokens files are the same as for :ref:`Example 4<startpk4>`. The options file reflects the use of :ref:`Gaussian Process<GP_desc>` 
and the required option; num_opt_chains. Other changes are the population size of 20

The template file can be downloaded :download:`here <../examples/user/Example5/template.txt>`

and the tokens file :download:`here <../examples/user/Example5/tokens.json>`

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


::

    {
    "author": "Certara",
    "algorithm":"GP",
    "num_opt_chains": 4,

    "random_seed": 11,
    "population_size": 20,
    "num_parallel": 4,
    "num_generations": ,

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
    "model_run_timeout": 1200
    }



Starting the search:
------------------------

:ref:`Starting the search is covered here<Execution>`