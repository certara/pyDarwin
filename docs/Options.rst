.. _Options:

Options List
============

Note that the options are saved to a json file. Json supports string, numeric and Boolen (true|false). String options must be in quotes. See `JSON <https://www.json.org/>`_ for 
details.

Example JSON

.. parsed-literal:: 

    {
        :ref:`"author" <author_options_desc>`: "Charles Robert Darwin",
        :ref:`"project_name" <project_name_options_desc>`: "Delicious armadillos",

        :ref:`"algorithm" <algorithim_options_desc>`: "GA",

        :ref:`"GA" <GA_options_desc>`: {
            :ref:`"elitist_num" <elitist_num_options_desc>`: 2,
            :ref:`"crossover_rate" <crossover_rate_options_desc>`: 0.95,
            :ref:`"mutation_rate" <mutation_rate_options_desc>`: 0.95,
            :ref:`"sharing_alpha" <sharing_alpha_options_desc>`: 0.1,
            :ref:`"selection" <selection_options_desc>`: "tournament",
            :ref:`"selection_size" <selection_size_options_desc>`: 2,
            :ref:`"crossover_operator" <crossover_operator_options_desc>`: "cxOnePoint",
            :ref:`"mutate" <mutate_options_desc>`: "flipBit",
            :ref:`"attribute_mutation_probability" <attribute_mutation_probability_options_desc>`: 0.1,
            :ref:`"niche_penalty" <niche_penalty_options_desc>`: 10
        },

        :ref:`"random_seed" <random_seed_options_desc>`: 11,
        :ref:`"num_parallel" <num_parallel_options_desc>`: 4,
        :ref:`"num_generations" <num_generations_options_desc>`: 6,
        :ref:`"population_size" <population_size_options_desc>`: 4,

        :ref:`"num_opt_chains" <num_opt_chains_options_desc>`: 4,

        :ref:`"exhaustive_batch_size" <exhaustive_batch_size_options_desc>`: 100,

        :ref:`"crash_value" <crash_value_options_desc>`: 99999999,

        :ref:`"penalty" <penalty_options_desc>`: {
            :ref:`"theta" <theta_options_desc>`: 10,
            :ref:`"omega" <omega_options_desc>`: 10,
            :ref:`"sigma" <sigma_options_desc>`: 10,
            :ref:`"convergence" <convergence_options_desc>`: 100,
            :ref:`"covariance" <covariance_options_desc>`: 100,
            :ref:`"correlation" <correlation_options_desc>`: 100,
            :ref:`"condition_number" <condition_number_options_desc>`: 100,
            :ref:`"non_influential_tokens" <non_influential_tokens_options_desc>`: 0.00001
        },

        :ref:`"downhill_period" <downhill_period_options_desc>`: 2,
        :ref:`"num_niches" <num_niches_options_desc>`: 2,
        :ref:`"niche_radius" <niche_radius_options_desc>`: 2,
        :ref:`"local_2_bit_search" <local_2_bit_search_options_desc>`: true,
        :ref:`"final_downhill_search" <final_downhill_search_options_desc>`: true,

        :ref:`"nmfe_path" <nmfe_path_options_desc>`: "/opt/nm751/util/nmfe75",
        :ref:`"model_run_timeout" <model_run_timeout_options_desc>`: 1200,
        :ref:`"model_run_priority_class" <model_run_priority_class_options_desc>`: "below_normal",

        :ref:`"postprocess" <postprocess_options_desc>`: {
            :ref:`"use_r" <use_r_options_desc>`: true,
            :ref:`"rscript_path" <rscript_path_options_desc>`: "/some/R/path/rscript",
            :ref:`"post_run_r_code" <post_run_r_code_options_desc>`: "{project_dir}/simplefunc.r",
            :ref:`"r_timeout" <r_timeout_options_desc>`: 30,
            :ref:`"use_python" <use_python_options_desc>`: true,
            :ref:`"post_run_python_code" <post_run_python_code_options_desc>`: "{project_dir}/../simplefunc_common.py"
        },

        :ref:`"use_saved_models" <use_saved_models_options_desc>`: false,
        :ref:`"saved_models_file" <saved_models_file_options_desc>`: "{working_dir}/models0.json",
        :ref:`"saved_models_readonly" <saved_models_readonly_options_desc>`: false,

        :ref:`"remove_run_dir" <remove_run_dir_options_desc>`: false,
        :ref:`"remove_temp_dir" <remove_temp_dir_options_desc>`: true,

        :ref:`"model_run_man" <model_run_man_options_desc>`: "darwin.GridRunManager",
        :ref:`"model_cache" <model_cache_options_desc>`: "darwin.MemoryModelCache",
        :ref:`"grid_adapter" <grid_adapter_options_desc>`: "darwin.GenericGridAdapter",
        :ref:`"engine_adapter" <engine_adapter_options_desc>`: "nonmem",

        :ref:`"working_dir" <working_dir_options_desc>`: "~/darwin/Ex1",
        :ref:`"data_dir" <data_dir_options_desc>`: "{project_dir}/data",
        :ref:`"output_dir" <output_dir_options_desc>`: "{project_dir}/output",
        :ref:`"temp_dir" <temp_dir_options_desc>`: "{working_dir}/temp",

        :ref:`"generic_grid_adapter" <generic_grid_adapter_options_desc>`: {
            :ref:`"python_path" <python_path_options_desc>`: "~/darwin/venv/bin/python",
            :ref:`"submit_search_command" <submit_search_command_options_desc>`: "qsub -b y -o {project_dir}/out.txt -e {project_dir}/err.txt -N '{project_name}'",
            :ref:`"submit_command" <submit_command_options_desc>`: "qsub -b y -o {results_dir}/{run_name}.out -e {results_dir}/{run_name}.err -N {job_name}",
            :ref:`"submit_job_id_re" <submit_job_id_re_options_desc>`: "Your job (\\w+) \\(\".+?\"\\) has been submitted",
            :ref:`"poll_command" <poll_command_options_desc>`: "qstat -s z",
            :ref:`"poll_job_id_re" <poll_job_id_re_options_desc>`: "^\\s+(\\w+)",
            :ref:`"poll_interval" <poll_interval_options_desc>`: 5,
            :ref:`"delete_command" <delete_command_options_desc>`: "qdel {project_stem}-\*"
        }
    }


Description
^^^^^^^^^^^^^^

.. _author_options_desc:

* author: String; Author, currently not used, Default - blank

.. _project_name_options_desc:

* project_name: String; Name of the project

.. _algorithim_options_desc:

* algorithim: One of :ref:`EX<EX_desc>` , :ref:`GA<GA_desc>` , :ref:`GP<GP_desc>`, :ref:`RF<RF_desc>` , :ref:`GBRT<GBRT_desc>`

.. _GA_options_desc:

* GA: JSON

.. _elitist_num_options_desc:

    * elitist_num: Positive integer; How many of the best models from any generation to carry over unchanged to the next generation. Function like `Hall of Fame <https://deap.readthedocs.io/en/master/api/tools.html#hall-of-fame/>`_  in DEAP. 

.. _crossover_rate_options_desc:

    * crossover_rate: What fraction of the mating pairs will undergo cross over (real 0.0-1.0)

.. _mutation_rate_options_desc:

    * mutation_rate: Probability that at least one bit in the genome will be "flipped", 0 to 1, or 1 to 0, (real 0.0-1.0)

.. _sharing_alpha_options_desc:

    * sharing_alpha: Parameter of the niche penalty calculation

.. _selection_options_desc:

    * selection: Selection algorithm for GA, currently only "tournament" is available

.. _selection_size_options_desc:

    * selection_size: How many "parents" enter in the selection, 2 is highly recommended, very limited experience with other values

.. _crossover_operator_options_desc:

    * crossover_operator: The algorithm for cross over, only "cxOnePoint" (single point cross over) is available

.. _mutate_options_desc:

    * mutate: The algorithm for mutation, currently only "flipBit" is available

.. _attribute_mutation_probability_options_desc:

    * attribute_mutation_probability: Probability of any bit being mutated, (real 0.0-1.0)

.. _niche_penalty_options_desc:

    * niche_penalty: Numeric, required if using GA. Require for calculation of the crowding penalty. 
      The niche penalty is calculate by first calculating the "distance matrix", the pair wise 
      `Mikowski distance <https://en.wikipedia.org/wiki/Minkowski_distance>`_ from the present model to all
      other models. The "crowding" quantity is then calculated a the sum of: (distance/niche_radius)**sharing_alpha
      for all other models in the generation for which the Mikowski distance is less than the niche radius.

      Finally, the penalty is calculated as: exp((crowding-1)*niche_penalty)-1. The objective of using a niche 
      penalty is to maintain diversity of models, to avoid premature convergence of the search, by penalizing when models are too similar to other models in the current generation. A typical value for the penalty is 10. (positive real)

.. _random_seed_options_desc:

* random_seed: User defined seed for random number generator  (positive integer)

.. _num_parallel_options_desc:

* num_parallel: How many model to run in parallel  (positive integer)

.. _num_generations_options_desc:

* num_generations: How many iterations or generations, not used for Exhaustive Search (positive integer)

.. _population_size_options_desc:

* population_size: Size of population, not used for Exhaustive search  (positive integer)

.. _num_opt_chains_options_desc:

* num_opt_chains: For GP,RF and GBRT multiple chains can be used. Using multiple chains will improve the 
  performance of the "ask" step. (positive integer)

.. _exhaustive_batch_size_options_desc:

* exhaustive_batch_size:  For a large exhaustive search, a complete list of all models may exceed the available memory.
  Using and exhaustive_search_batch_size will limit the number of models generated at any time.
  There may be modest impact on performace as the batch size gets smaller. (positive integer)     

.. _crash_value_options_desc:

* crash_value:  Value of fitness or reward assigned when model output is not generated. 
  Should be set larger than any anticipate completed model fitness (positive real)

.. _penalty_options_desc:

* penalty: JSON

.. _theta_options_desc:

    * theta: Penalty added to fitness/reward for each estimated THETA. A value of 3.84 corresonds to a hypothesis test with
      1 df and p< 0.05 (for nested models) a value of 2 for 1 df corresponds to the Akaike information criterion (real)

.. _omega_options_desc:

    * omega: Penalty added to fitness/reward for each estimated OMEGA element (real)

.. _sigma_options_desc:

    * sigma: Penalty added to fitness/reward for each estimated SIGMA element (real)

.. _convergence_options_desc:

    * convergence: Penalty added to fitness/reward for failing to converge (real)

.. _covariance_options_desc:

    * covariance: Penalty added to fitness/reward for failing the covariance step (real number). If a successful covariance step 
      is important, this can be set to a large value (e.g., 100), if successful covariance is not important, it can
      set to 0

.. _correlation_options_desc:

    * correlation: Penalty added to fitness/reward if any off diagonal element of the correlation matrix of estimate has absolute 
      value > 0.95 (real number). This penalty will be added if the covariance step fails (or is not) requested (real)

.. _condition_number_options_desc:

    * condition_number: Penalty added to fitness/reward if the condition number is > 1000
      This penalty will be added if the covariance step fails (or is not) requested (real)

.. _non_influential_tokens_options_desc:

    * non_influential_tokens: Penalty added to fitness/reward if any tokens do not influence the control file (relevant for nested tokens)
      Should be very small, as the purpose is only for the model with non-influential tokens to be minimially worse
      than the same model without the non influential token(s) (real)

.. _downhill_period_options_desc:

* downhill_period: How often to run the downhill set, default is 2, meaning that 2 generations/iterations will be run, followed by the 
  downhill step, then an additional 2 generations/iterations. (integer)

.. _num_niches_options_desc:

* num_niches: Only used for GA. A penalty is assigned for each model based on the number of similar models within a niche
  radius. This penalty is applied only to the selection process (not to the fitness of the model). The purpose
  is to insure maintaining a degree of diversity in the population (integer)

.. _niche_radius_options_desc:

* niche_radius: The radius of the niches. See  :ref:`Niche Radius<Niche Radius>` (positive real)

.. _local_2_bit_search_options_desc:

* local_2_bit_search: Whether to perform the :ref:`two bit local search<Local Two bit Search>` . 
  The two bit local search substantially increase the robustness of the search. (true|false) 

.. _final_downhill_search_options_desc:

* final_downhill_search: Whether to perform a local search (1 and 2 bit) at the end of the global search (true|false)

.. _nmfe_path_options_desc:

* nmfe_path: Path to nmfe??.bat, the default command line for executing NONMEM (string)

.. _model_run_timeout_options_desc:

* model_run_timeout: Time after which the NONMEM execution will be terminated, and the crash value assigned. (positive real)

.. _model_run_priority_class_options_desc:

* model_run_priority_class: Priority class, below_normal is recommended to maintain user interface responsiveness (normal|below_normal)

.. _postprocess_options_desc:

* postprocess: JSON

.. _use_r_options_desc:

    * use_r: Whether user supplied R code is to be run after NONMEM execution (true|false)

.. _rscript_path_options_desc:

    * rscript_path: Absolute path to Rscript.exe  (string)

.. _post_run_r_code_options_desc:

    * post_run_r_code: Path to R file to be run after each NONMEM execution (string with .r extension)

.. _r_timeout_options_desc:

    * r_timeout: Time out (seconds) for R code execution (positive real)

.. _use_python_options_desc:

    * use_python: Whether user supplied Python code is to be run after NONMEM execution (true|false)

.. _post_run_python_code_options_desc:

    * post_run_python_code: Path to python code file to be run after each NONMEM execution  (string, with .py extension)

.. _use_saved_models_options_desc:

* use_saved_models:

.. _saved_models_file_options_desc:

* saved_models_file:

.. _saved_models_readonly_options_desc:

* saved_models_readonly:

.. _remove_run_dir_options_desc:

* remove_run_dir:

.. _remove_temp_dir_options_desc:

* remove_temp_dir:

.. _model_run_man_options_desc:

* model_run_man: 

.. _model_cache_options_desc:

* model_cache:

.. _grid_adapter_options_desc:

* grid_adapter:

.. _engine_adapter_options_desc:

* engine_adapter:

.. _working_dir_options_desc:

* working_dir:

.. _data_dir_options_desc:

* data_dir:

.. _output_dir_options_desc:

* output_dir:

.. _temp_dir_options_desc:

* temp_dir:

.. _generic_grid_adapter_options_desc:

* generic_grid_adapter: JSON

.. _python_path_options_desc:

    * python_path:

.. _submit_search_command_options_desc:

    * submit_search_command:

.. _submit_command_options_desc:

    * submit_command:

.. _submit_job_id_re_options_desc:

    * submit_job_id_re:

.. _poll_command_options_desc:

    * poll_command:

.. _poll_job_id_re_options_desc:

    * poll_job_id_re:

.. _poll_interval_options_desc:

    * poll_interval:

.. _delete_command_options_desc:

    * delete_command:
