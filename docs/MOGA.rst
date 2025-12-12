.. _moga-label:

MOGA
====
The MOGA option, specified in the options.json file directs pyDarwin to use the NSGA-II algorithm for selecting 
non-dominated models. No user defined code is required or accepted. Two objectives are used, the OFV and the 
total number of parameters (esimtated thetas, omega elements and, for NONMEM, sigma). The template.txt and 
tokens.json file are idential to those for other algorithms. Note that there are no penalties, as there isn't 
a composite fitness function.

Options.json
------------
The options.json file specified the MOGA algorithm and options. NONMEM and NLME are specified identically 
with regard to the MOGA options. An example for NONMEM is given below:

 .. code-block:: JSON

    {
       "MOGA" : {
          "attribute_mutation_probability" : 0.1, 
          "crossover" : "single",
          "crossover_rate" : 0.95,
          "mutation_rate" : 0.95,
          "partitions" : 6
       },
       "algorithm" : "MOGA",
       "author" : "Certara", 
       "downhill_period" : 3,
       "engine_adapter" : "nonmem",
       "final_downhill_search" : true, 
       "keep_extensions" : [],
       "keep_files" : [],
       "local_2_bit_search" : false,
       "model_run_timeout" : 1200,
       "niche_radius" : 2,
       "local_grid_search" : false,
       "num_generations" : 6,
       "num_niches" : 2,
       "num_parallel" : 4,
       "population_size" : 30,
       "nmfe_path": "c:/nm75g64/util/nmfe75.bat",
       "project_name" : "MOGA-nonmem",
       "random_seed" : 51424319, 
       "working_dir" : "{project_dir}"
    }

Note that the path to rscript.exe is not required for MOGA with NONMEM.
A comparable options.json file for NLME is given below

.. code-block:: JSON

    {
	   "MOGA" : {
		  "attribute_mutation_probability" : 0.1, 
		  "crossover" : "single",
		  "crossover_rate" : 0.95,
		  "mutation_rate" : 0.95,
		  "partitions" : 6
	   },
	   "algorithm" : "MOGA",
	   "author" : "Certara", 
	   "downhill_period" : 3,
	   "engine_adapter" : "nlme",
	   "final_downhill_search" : true,
	   "gcc_dir" : "C:\\Program Files\\Certara\\mingw64",
	   "keep_extensions" : [],
	   "keep_files" : [],
	   "local_2_bit_search" : false,
	   "model_run_timeout" : 1200,
	   "niche_radius" : 2,
	   "nlme_dir" : "C:\\Program Files\\Certara\\NLME_Engine",
	   "num_generations" : 6,
	   "num_niches" : 2,
	   "num_parallel" : 4,
	   "population_size" : 30,
	   
	   "project_name" : "MOGA-nlme",
	   "random_seed" : 51424319,
	   "rscript_path" : "C:/Program Files/R/R-4.5.1/bin/Rscript.exe",
	   "working_dir" : "{project_dir}"
	}

The path to Rscript.exe is required for all NLME searches, regardless of whether post-run 
R code is used.



 