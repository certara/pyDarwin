.. include:: .special.rst

.. _Options:

Options List
============

Note that the options are saved to a JSON file. JSON supports string, numeric and Boolen (true|false). 
String options must be in quotes. See `JSON <https://www.json.org/>`_ for details.

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

All fields marked with * are required.


.. _author_options_desc:

* **author** - *string*: Currently not used by pyDarwin, for documentation purposes only. 

.. _project_name_options_desc:

* **project_name** - *string*: Name of the project. Used to construct the default working directory, output directory and temp directory.

.. _algorithim_options_desc:

* **algorithim**\* - *string*: One of :ref:`EX<EX_desc>`, :ref:`GA<GA_desc>`, :ref:`GP<GP_desc>`, :ref:`RF<RF_desc>`, :ref:`GBRT<GBRT_desc>`

.. _GA_options_desc:

* **GA** - *JSON*

.. _elitist_num_options_desc:

    * **elitist_num**: Positive integer; How many of the best models from any generation to carry over unchanged to the next generation. Function like `Hall of Fame <https://deap.readthedocs.io/en/master/api/tools.html#hall-of-fame/>`_  in DEAP. 

.. _crossover_rate_options_desc:

    * **crossover_rate** - *int*: What fraction of the mating pairs will undergo cross over (real 0.0-1.0)

.. _mutation_rate_options_desc:

    * **mutation_rate** - *int*: Probability that at least one bit in the genome will be "flipped", 0 to 1, or 1 to 0, (real 0.0-1.0)

.. _sharing_alpha_options_desc:

    * **sharing_alpha** - *real*: Parameter of the niche penalty calculation

.. _selection_options_desc:

    * **selection** - *int*: Selection algorithm for GA, currently only "tournament" is available

.. _selection_size_options_desc:

    * **selection_size** - *int*: How many "parents" enter in the selection, 2 is highly recommended, experience with other values is very limited

.. _crossover_operator_options_desc:

    * **crossover_operator** - *int*: The algorithm for cross over, only "cxOnePoint" (single point cross over) is available

.. _mutate_options_desc:

    * **mutate** - *int*: The algorithm for mutation, currently only "flipBit" is available

.. _attribute_mutation_probability_options_desc:

    * **attribute_mutation_probability** - *real*: Probability of any bit being mutated, (real 0.0-1.0)

.. _niche_penalty_options_desc:

    * **niche_penalty**\* - *real*: Required if using GA. Require for calculation of the crowding penalty. 
      The niche penalty is calculate by first calculating the "distance matrix", the pair wise 
      `Mikowski distance <https://en.wikipedia.org/wiki/Minkowski_distance>`_ from the present model to all
      other models. The "crowding" quantity is then calculated a the sum of: (distance/niche_radius)**sharing_alpha
      for all other models in the generation for which the Mikowski distance is less than the niche radius.

      Finally, the penalty is calculated as: exp((crowding-1)*niche_penalty)-1. The objective of using a niche 
      penalty is to maintain diversity of models, to avoid premature convergence of the search, by penalizing when models are too 
      similar to other models in the current generation. A typical value for the penalty is 10. (positive real)

.. _random_seed_options_desc:

* **random_seed** - *int*: User defined seed for random number generator, not used for Exhaustive search (positive integer)

.. _num_parallel_options_desc:

* **num_parallel** - *int*: How many models to run in parallel (positive integer)

.. _num_generations_options_desc:

* **num_generations**\* - *int*: How many iterations or generations, not used for Exhaustive Search (positive integer)

.. _population_size_options_desc:

* **population_size**\* - *int*: Size of population, not used for Exhaustive search  (positive integer)

.. _num_opt_chains_options_desc:

* **num_opt_chains**\* - *int*: For GP,RF and GBRT multiple chains can be used. Using multiple chains will improve the 
  performance of the "ask" step. (positive integer)

.. _exhaustive_batch_size_options_desc:

* **exhaustive_batch_size** - *int*:  For a large exhaustive search, a complete list of all models may exceed the available memory. 
    The list of models will be run in batchs of this size. A typical value is 1000 to 10000. Smaller batch sizes will have a small effect on 
    performance, as all models in a batch must complete before the next batch starts.

.. _crash_value_options_desc:

* **crash_value** - *real*:  Value of fitness or reward assigned when model output is not generated. 
  Should be set larger than any anticipate completed model fitness (positive real)

.. _penalty_options_desc:

* **penalty** - *JSON*:

.. _theta_options_desc:

    * **theta** - *real*: Penalty added to fitness/reward for each estimated THETA. A value of 3.84 corresonds to a hypothesis test with
      1 df and p<0.05 (for nested models) a value of 2 for 1 df corresponds to the Akaike information criterion (real)

.. _omega_options_desc:

    * **omega** - *real*: Penalty added to fitness/reward for each estimated OMEGA element (real)

.. _sigma_options_desc:

    * **sigma** - *real*: Penalty added to fitness/reward for each estimated SIGMA element (real)

.. _convergence_options_desc:

    * **convergence** - *real*: Penalty added to fitness/reward for failing to converge (real)

.. _covariance_options_desc:

    * **covariance** - *real*: Penalty added to fitness/reward for failing the covariance step (real number). If a successful covariance step 
      is important, this can be set to a large value (e.g., 100), if successful covariance is not important, it can
      set to 0

.. _correlation_options_desc:

    * **correlation** - *real*: Penalty added to fitness/reward if any off diagonal element of the correlation matrix of estimate has absolute 
      value > 0.95 (real number). This penalty will be added if the covariance step fails or is not requested (real)

.. _condition_number_options_desc:

    * **condition_number** - *real*: Penalty added to fitness/reward if the condition number is > 1000
      This penalty will be added if the covariance step fails (or is not) requested, e.g. PRINT=E is not included in $COV (real)

.. _non_influential_tokens_options_desc:

    * **non_influential_tokens** - *real*: Penalty added to fitness/reward if any tokens do not influence the control file (relevant for nested tokens)
      Should be very small (e.g., 0.0001), as the purpose is only for the model with non-influential tokens to be minimially worse
      than the same model without the non influential token(s) to break a tie (real)

.. _downhill_period_options_desc:

* **downhill_period** - *int*: How often to run to run the downhill step default is to -1 meaning 'no periodic downhill' (integer)

.. _num_niches_options_desc:

* **num_niches** - *int*: Used for GA and downhill. A penalty is assigned for each model based on the number of similar models within a niche
  radius. This penalty is applied only to the selection process (not to the fitness of the model). The purpose
  is to insure maintaining a degree of diversity in the population (integer). num_niches is also used to select the number of models that are entered into the 
  dowhill step for all algorithms, except Exhaustive Search.

.. _niche_radius_options_desc:

* **niche_radius** - *real*:  The radius of the niches. See  :ref:`Niche Radius<Niche Radius>` (positive real)

.. _local_2_bit_search_options_desc:

* **local_2_bit_search** - *boolean*: Whether to perform the :ref:`two bit local search<Local Two bit Search>` . 
  The two bit local search substantially increase the robustness of the search. All downhill local seaches are done starting from :ref:`num_niches models<num_niches_options_desc>`. (true|false) 

.. _final_downhill_search_options_desc:

* **final_downhill_search** - *boolean*: Whether to perform a local search (1 and 2 bit) at the end of the global search (true|false)

.. _nmfe_path_options_desc:

* **nmfe_path** - *string*:  the command line for executing NONMEM (string)

.. _model_run_timeout_options_desc:

* **model_run_timeout** - *real*: Time after which the NONMEM execution will be terminated, and the crash value assigned. Default is 1200 seconds (positive real)

.. _model_run_priority_class_options_desc:

* **model_run_priority_class** - *string*: Priority class, below_normal is recommended to maintain user interface responsiveness (normal|below_normal)

.. _postprocess_options_desc:

* **postprocess** - *JSON*:

.. _use_r_options_desc:

* **use_r** - *boolean*: Whether user supplied R code is to be run after NONMEM execution (true|false)

.. _rscript_path_options_desc:

* **rscript_path** - *string*: Absolute path to Rscript.exe. Required if ``use_r`` is set to ``true``.

.. _post_run_r_code_options_desc:

* **post_run_r_code** - *string*: Path to R file (.r extension) to be run after each NONMEM execution.
      Required if ``use_r`` is set to ``true``.

.. _r_timeout_options_desc:

* **r_timeout** - *real*: Time out (seconds) for R code execution (positive real)

.. _use_python_options_desc:

* **use_python** - *boolean*: Whether user supplied Python code is to be run after NONMEM execution (true|false)

.. _post_run_python_code_options_desc:

* **post_run_python_code**\* - *string*: Path to python code file (.py extension) to be run after each NONMEM execution. Required if ``use_python`` is set to ``true``.

.. _use_saved_models_options_desc:

* **use_saved_models** - *boolean*: Whether to read the JSON file from a previous search and use those resuts, rather than rerunning the models. The models.json file will be found in the working directory. This file can be renamed/copied and then used for subsequent searches by setting use_saved_models to true and specifying the saved_models_file with that file name.

.. _saved_models_file_options_desc:

* **saved_models_file** - *string*: To restart an interupted search, copy the models.json file from the working directory and use that file name as the saved_models_file for subsequent searchs. 
    To use this file set :ref:`use_saved_models<use_saved_models_options_desc>` to 'true'

.. _saved_models_readonly_options_desc:

* **saved_models_readonly** - *boolean*: Do not overwrite the saved_models_file

.. _remove_run_dir_options_desc:

* **remove_run_dir** - *boolean*: if set to true all

.. _remove_temp_dir_options_desc:

* **remove_temp_dir** - *boolean*: If set to 'true', all NONMEM files (\*.mod, \*.lst, FDATA, $TABLE files) and the parent directory will be removed. 

.. _model_run_man_options_desc:

* **model_run_man** - *string*:

.. _model_cache_options_desc:

* **model_cache** - *string*:

.. _grid_adapter_options_desc:

* **grid_adapter** - *string*:

.. _engine_adapter_options_desc:

* **engine_adapter** - *string*:

.. _working_dir_options_desc:

* **working_dir** - *string*: Directory where some of the "working" files are kept, e.g., InterimControlFile.mod, InterimResultFile.lst,messages.txt, models.json

.. _data_dir_options_desc:

* **data_dir** - *string*: Directory where the data file(s) are kept, internal to pyDarwin

.. _output_dir_options_desc:

* **output_dir** - *string*: Directory where pyDarwin output will be placed (results.csv, finalcontrolfile.mod finalcontrolfile.lst)

.. _temp_dir_options_desc:

* **temp_dir** - *string*: Root directory for NONMEM model runs.

.. _generic_grid_adapter_options_desc:

* **generic_grid_adapter** - *JSON*:

.. _python_path_options_desc:

    * **python_path** :superscript:`required` - *string*: Path to your Python interpreter, preferably - to the instance of the interpreter located in :ref:`virtual environment<install_python_venv>` where pyDarwin is deployed. The path must be available to all grid nodes that run jobs.

.. _submit_command_options_desc:

    * **submit_command** :superscript:`required` - *string*: A command that submits individual runs to the grid queue. The actual command submitted to the queue is ``<python_path> -m darwin.run_model <input file> <output file> <options file>``, but you don't put it in the ``submit_command``. What you do put there is something like ``qsub -b y -o {results_dir}/{run_name}.out -e {results_dir}/{run_name}.err -N {job_name}``

.. _submit_search_command_options_desc:

    * **submit_search_command** :superscript:`required` - *string*: A command that submits search job to the grid queue. Similar to ``submit_command``, but for entire search. Required only for :ref:`grid search<running_grid_search>`. It may look like this: ``qsub -b y -o {project_dir}/out.txt -e {project_dir}/err.txt -N '{project_name}'``

.. _submit_job_id_re_options_desc:

    * **submit_job_id_re** :superscript:`required` - *string*: A regular expression to find a job id in ``submit_command`` output. Job id must be captured in first `capturing group <https://www.google.com/search?q=regular+expression+capturing+group>`_, like this: ``Your job (\\w+) \\(\".+?\"\\) has been submitted``

.. _poll_command_options_desc:

    * **poll_command** :superscript:`required` - *string*: A command that retrieves finished jobs from grid controller. If your controller/setup allows you to specify ids/patterns in polling commands, do it (see ``delete_command``). If it doesn’t, you have to poll ALL finished jobs: ``qstat -s z``

.. _poll_job_id_re_options_desc:

    * **poll_job_id_re** :superscript:`required` - *string*: A regular expression to find a job id in every line of ``poll_command`` output. Similar to ``submit_job_id_re``.

.. _poll_interval_options_desc:

    * **poll_interval** - *int*: How often to poll jobs. By default 10 (seconds).

.. _delete_command_options_desc:

    * **delete_command** - *string*: A command that deletes all unfinished jobs related to the search when you stop it. It may delete all of them by id (``qdel {job_ids}``) or by mask (``qdel {project_stem}-*``). Be careful when using a mask: if your mask matches search job name it may kill your search prematurely, e.g. during saving the cache data. 
