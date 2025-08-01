.. include:: .special.rst

.. _Options:

Options List
============

Note that the options are saved to a JSON file. JSON supports string, numeric, and boolean (true|false). 
String options must be in quotes. See `JSON <https://www.json.org/>`_ for details.

Below is an example JSON file that demonstrates every possible option. Note, some settings are only 
applicable given algorithm selection and execution environment e.g., GA and grid options.

.. parsed-literal:: 

    {
        :ref:`"author" <author_options_desc>`: "Charles Robert Darwin",
        :ref:`"project_name" <project_name_options_desc>`: "Delicious armadillos",

        :ref:`"algorithm" <algorithm_options_desc>`: "GA",

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
            :ref:`"niche_penalty" <niche_penalty_options_desc>`: 20
        },

        :ref:`"MOGA" <MOGA_options_desc>`: {
            :ref:`"objectives" <objectives_options_desc>`: 3,
            :ref:`"names" <objective_names_options_desc>`: ["objective 1", "objective 2", "objective 3"],
            :ref:`"constraints" <constraints_options_desc>`: 0,
            :ref:`"partitions" <partitions_options_desc>`: 6,
            :ref:`"crossover" <crossover_options_desc>`: "single",
            :ref:`"crossover_rate" <crossover_rate_options_desc>`: 0.95,
            :ref:`"mutation_rate" <mutation_rate_options_desc>`: 0.95,
            :ref:`"attribute_mutation_probability" <attribute_mutation_probability_options_desc>`: 0.1
        },

        :ref:`"PSO" <PSO_options_desc>`: {
            :ref:`"inertia" <inertia_options_desc>`: 0.4,
            :ref:`"cognitive" <cognitive_options_desc>`: 0.5,
            :ref:`"social" <social_options_desc>`: 0.5,
            :ref:`"neighbor_num" <neighbor_num_options_desc>`: 20,
            :ref:`"p_norm" <p_norm_options_desc>`: 2,
            :ref:`"break_on_no_change" <break_on_no_change_options_desc>`: 5
        },

        :ref:`"search_omega_blocks" <search_omega_blocks_options_desc>`: false,
        :ref:`"search_omega_bands" <search_omega_bands_options_desc>`: false,
        :ref:`"max_omega_band_width" <max_omega_band_width_options_desc>`: 0,
        :ref:`"search_omega_sub_matrix" <search_omega_sub_matrix_options_desc>`: false,
        :ref:`"max_omega_sub_matrix" <max_omega_sub_matrix_options_desc>`: 4,
        :ref:`"individual_omega_search" <individual_omega_search_options_desc>`: true,
        :ref:`"max_omega_search_len" <max_omega_search_len_options_desc>`: 8,

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

        :ref:`"effect_limit" <effect_limit_options_desc>`: 6,

        :ref:`"downhill_period" <downhill_period_options_desc>`: 2,
        :ref:`"num_niches" <num_niches_options_desc>`: 2,
        :ref:`"niche_radius" <niche_radius_options_desc>`: 2,
        :ref:`"local_2_bit_search" <local_2_bit_search_options_desc>`: true,
        :ref:`"final_downhill_search" <final_downhill_search_options_desc>`: true,

        :ref:`"local_grid_search" <local_grid_search_options_desc>`: true,
        :ref:`"max_local_grid_search_bits" <max_local_grid_search_bits_options_desc>`: 3,

        :ref:`"nmfe_path" <nmfe_path_options_desc>`: "/opt/nm751/util/nmfe75",
        :ref:`"model_run_timeout" <model_run_timeout_options_desc>`: 1200,
        :ref:`"model_run_priority_class" <model_run_priority_class_options_desc>`: "below_normal",

        :ref:`"postprocess" <postprocess_options_desc>`: {
            :ref:`"use_r" <use_r_options_desc>`: true,
            :ref:`"post_run_r_code" <post_run_r_code_options_desc>`: "{project_dir}/simplefunc.r",
            :ref:`"r_timeout" <r_timeout_options_desc>`: 30,
            :ref:`"use_python" <use_python_options_desc>`: true,
            :ref:`"post_run_python_code" <post_run_python_code_options_desc>`: "{project_dir}/../simplefunc_common.py"
        },

        :ref:`"use_saved_models" <use_saved_models_options_desc>`: false,
        :ref:`"saved_models_file" <saved_models_file_options_desc>`: "{working_dir}/models0.json",
        :ref:`"saved_models_readonly" <saved_models_readonly_options_desc>`: false,

        :ref:`"keep_key_models" <keep_key_models_options_desc>`: false,
        :ref:`"keep_best_models" <keep_best_models_options_desc>`: true,
        :ref:`"rerun_key_models" <rerun_key_models_options_desc>`: false,

        :ref:`"rerun_front_models" <rerun_front_models_options_desc>`: false,

        :ref:`"remove_run_dir" <remove_run_dir_options_desc>`: false,
        :ref:`"remove_temp_dir" <remove_temp_dir_options_desc>`: true,

        :ref:`"keep_files" <keep_files_options_desc>`: ["dmp.txt", "posthoc.csv"],
        :ref:`"keep_extensions" <keep_extensions_options_desc>`: ["shk", "coi", "cor", "cov"],

        :ref:`"use_system_options" <use_system_options_options_desc>`: true,

        :ref:`"model_cache" <model_cache_options_desc>`: "darwin.MemoryModelCache",
        :ref:`"model_run_man" <model_run_man_options_desc>`: "darwin.GridRunManager",
        :ref:`"grid_adapter" <grid_adapter_options_desc>`: "darwin.GenericGridAdapter",
        :ref:`"engine_adapter" <engine_adapter_options_desc>`: "nonmem",

        :ref:`"skip_running" <skip_running_options_desc>`: false,

        :ref:`"rscript_path" <rscript_path_options_desc>`: "C:/Program Files/R/R-4.3.1/bin/Rscript.exe",
        :ref:`"nlme_dir" <nlme_dir_options_desc>`: "C:/Program Files/Certara/NLME_Engine",
        :ref:`"gcc_dir" <gcc_dir_options_desc>`: "C:/Program Files/Certara/mingw64",

        :ref:`"working_dir" <working_dir_options_desc>`: "~/darwin/Ex1",
        :ref:`"data_dir" <data_dir_options_desc>`: "{project_dir}/data",
        :ref:`"output_dir" <output_dir_options_desc>`: "{project_dir}/output",
        :ref:`"temp_dir" <temp_dir_options_desc>`: "{working_dir}/temp",
        :ref:`"key_models_dir" <key_models_dir_options_desc>`: "{working_dir}/key_models",
        :ref:`"non_dominated_models_dir" <non_dominated_models_dir_options_desc>`: "{working_dir}/non_dominated_models",

        :ref:`"generic_grid_adapter" <generic_grid_adapter_options_desc>`: {
            :ref:`"python_path" <python_path_options_desc>`: "~/darwin/venv/bin/python",
            :ref:`"submit_search_command" <submit_search_command_options_desc>`: "qsub -b y -cwd -o {project_dir}/out.txt -e {project_dir}/err.txt -N '{project_name}'",
            :ref:`"submit_command" <submit_command_options_desc>`: "qsub -b y -o {results_dir}/{run_name}.out -e {results_dir}/{run_name}.err -N {job_name}",
            :ref:`"submit_job_id_re" <submit_job_id_re_options_desc>`: "Your job (\\\\w+) \\\\(\\".+?\\"\\\\) has been submitted",
            :ref:`"poll_command" <poll_command_options_desc>`: "qstat -s z",
            :ref:`"poll_job_id_re" <poll_job_id_re_options_desc>`: "^\\\\s+(\\\\w+)",
            :ref:`"poll_interval" <poll_interval_options_desc>`: 5,
            :ref:`"delete_command" <delete_command_options_desc>`: "qdel {project_stem}-\*"
        }
    }


Description
-------------

Here is the list of all available options. Note that many of the options have default values and are not required to be specified directly in the options file.

.. _author_options_desc:

* | :opt_name:`author` -- *string*: The author of the project.
  | Aliased as :mono_ref:`{author}<author_alias>`.

.. _project_name_options_desc:

* | :opt_name:`project_name` -- *string*: Name of the project. By default, it is set to the name of the parent folder of the options file.
  | Aliased as :mono_ref:`{project_name}<project_name_alias>`. See also :mono_ref:`{project_stem}<project_stem_alias>`.

.. _algorithm_options_desc:

* :opt_name:`algorithm` :sup:`required` -- *string*: One of :ref:`EX<EX_desc>`, :ref:`GA<GA_desc>`, :ref:`GP<GP_desc>`, :ref:`RF<RF_desc>`, :ref:`GBRT<GBRT_desc>`, :ref:`PSO<PSO_desc>`, :ref:`MOGA<MOGA_desc>`, :ref:`MOGA3<MOGA3_desc>`.

.. _GA_options_desc:

* :opt_name:`GA` -- *JSON*: Options specific to GA. Ignored for all other algorithms.

.. _elitist_num_options_desc:

    * | :opt_name:`elitist_num` -- *positive int*: Number of best models from any generation to carry over, unchanged, to the next generation. Functions like `Hall of Fame <https://deap.readthedocs.io/en/master/api/tools.html#hall-of-fame/>`_  in DEAP. 
      | *Default*: 4

.. _crossover_rate_options_desc:

    * | :opt_name:`crossover_rate` -- *real*: Fraction of mating pairs that will undergo crossover (real 0.0--1.0).
      | *Default*: 0.95

.. _mutation_rate_options_desc:

    * | :opt_name:`mutation_rate` -- *real*: Probability that at least one bit in the genome will be "flipped", 0 to 1, or 1 to 0, (real 0.0--1.0).
      | *Default*: 0.95

.. _sharing_alpha_options_desc:

    * | :opt_name:`sharing_alpha` -- *real*: Parameter of the niche penalty calculation.
      | *Default*: 0.1

.. _selection_options_desc:

    * | :opt_name:`selection` -- *string*: Selection algorithm for GA. Currently only "tournament" is available.
      | *Default*: ``"tournament"``

.. _selection_size_options_desc:

    * | :opt_name:`selection_size` -- *positive int*: Number of "parents" to enter in the selection. 2 is highly recommended, experience with other values is very limited.
      | *Default*: 2

.. _crossover_operator_options_desc:

    * | :opt_name:`crossover_operator` -- *string*: The algorithm for crossover. Only "cxOnePoint" (single point crossover) is available.
      | *Default*: ``"cxOnePoint"``

.. _mutate_options_desc:

    * | :opt_name:`mutate` -- *string*: The algorithm for mutation. Currently only "flipBit" is available.
      | *Default*: ``"flipBit"``

.. _attribute_mutation_probability_options_desc:

    * | :opt_name:`attribute_mutation_probability` -- *real*: Probability of any bit being mutated, (real 0.0--1.0).
      | *Default*: 0.1

.. _niche_penalty_options_desc:

    * | :opt_name:`niche_penalty` -- *positive real*: Used for calculation of the crowding penalty. 
        The niche penalty is calculated by first finding the "distance matrix", the pair-wise 
        `Mikowski distance <https://en.wikipedia.org/wiki/Minkowski_distance>`_ from the present model to all
        other models. The "crowding" quantity is then calculated as the sum of: (distance/niche_radius)**sharing_alpha
        for all other models in the generation for which the Mikowski distance is less than the niche radius.
      | Finally, the penalty is calculated as: exp((crowding--1)*niche_penalty)--1. The objective of using a niche 
        penalty is to maintain diversity of models, to avoid premature convergence of the search by penalizing when models are too 
        similar to other models in the current generation.
      | *Default*: 20

.. _MOGA_options_desc:

* :opt_name:`MOGA` -- *JSON*: Options specific to MOGA and MOGA3. Ignored for all other algorithms.

.. _objectives_options_desc:

    * | :opt_name:`objectives` -- *positive int*: Number of objectives. Objectives must be provided by :ref:`postprocessing <postprocess_options_desc>` (either R or Python).
      | Applicable only for MOGA3. For MOGA this option is ignored, 2 objectives are used.
      | *Default*: 3

.. _constraints_options_desc:

    * | :opt_name:`constraints` -- *positive int*: Number of constraints. See https://pymoo.org/constraints/index.html
      | Constraints must be provided by :ref:`postprocessing <postprocess_options_desc>` (either R or Python).
      | Applicable only for MOGA3, ignored for MOGA.
      | *Default*: 0

.. note::
   For MOGA3 the postprocessing script must return 2 lists: the first list contains objectives, the second -- constraints. If there are no constraints, the second list must be empty.

.. _objective_names_options_desc:

    * | :opt_name:`names` -- *list of strings*: List of names of the objectives. Must be the size of :ref:`objectives<objectives_options_desc>`. If empty or of a different size, generic names will be used.
      | The names are used only in results.csv.
      | Applicable only for MOGA3, ignored for MOGA.

.. _partitions_options_desc:

    * | :opt_name:`partitions` -- *positive int*: Number of partitions. See https://pymoo.org/misc/reference_directions.html
      | Applicable only for MOGA3, ignored for MOGA.
      | *Default*: 12

.. _crossover_options_desc:

    * | :opt_name:`crossover` -- *string*: Crossover algorithm for MOGA. When set to single, SinglePointCrossover is used. Otherwise, TwoPointCrossover. See https://pymoo.org/operators/crossover.html#Point-Crossover
      | *Default*: ``"single"``

.. _PSO_options_desc:

* :opt_name:`PSO` -- *JSON*: Options specific to PSO. Ignored for all other algorithms.

.. _inertia_options_desc:

    * | :opt_name:`inertia` -- *real*: Particle coordination movement as it relates to the previous velocity. Commonly denoted as :math:`\\w`.
      | *Default*: 0.4

.. _cognitive_options_desc:

    * | :opt_name:`cognitive` -- *real*: Particle coordination movement as it relates to it's own best known position. Commonly denoted as :math:`c_1`.
      | *Default*: 0.5

.. _social_options_desc:

    * | :opt_name:`social` -- *real*: Particle coordination movement as it relates to current best known position across all particles. Commonly denoted as :math:`c_2`.
      | *Default*: 0.5

.. _neighbor_num_options_desc:

    * | :opt_name:`neighbor_num` -- *positive int*: Number of neighbors that any particle interacts with to determine the social component of the velocity of the next step.
      | Smaller number of neighbors results in  a more thorough search (as the neighborhoods tend to move more independently, allowing the swarm to cover a larger
      | section of the total search space) but will converge more slowly.
      | *Default*: 20

.. _p_norm_options_desc:

    * | :opt_name:`p_norm` -- *positive int*: Minkowski p-norm to use. A Value of 1 is the sum-of-absolute values (or L1 distance) while 2 is the Euclidean (or L2) distance.
      | *Default*: 2

.. _break_on_no_change_options_desc:

    * | :opt_name:`break_on_no_change` -- *positive int*: Number of iterations used to determine whether the optimization has converged.
      | *Default*: 5

.. _search_omega_blocks_options_desc:

* | :opt_name:`search_omega_blocks` -- *boolean*: Set to ``true`` to search omega blocks. (Similar to ``search_omega_bands``, but for NLME)
  | *Default*: false

.. _search_omega_bands_options_desc:

* | :opt_name:`search_omega_bands` -- *boolean*: Set to ``true`` to search omega bands.
  | *Default*: false

.. _max_omega_band_width_options_desc:

* | :opt_name:`max_omega_band_width` -- *positive int*: Maximum size of omega band to use in search.
  | *Default*: 0

.. _search_omega_sub_matrix_options_desc:

* | :opt_name:`search_omega_sub_matrix` -- *boolean*: Set to ``true`` to search omega sub matrix.
  | *Default*: false

.. _max_omega_sub_matrix_options_desc:

* | :opt_name:`max_omega_sub_matrix` -- *positive int*: Maximum size of sub matrix to use in search.
  | *Default*: 4

.. _individual_omega_search_options_desc:

* | :opt_name:`individual_omega_search` -- *boolean*: If ``true``, every omega search block will be handled individually: each block will have a separate gene and max omega search length (either calculated automatically or set explicitly with :mono_ref:`max_omega_search_len<max_omega_search_len_options_desc>`).
  | When ``individual_omega_search`` is set to ``false``, the omega search will be performed uniformly, that is, all search blocks will have the same pattern of block omegas.
  | Only search blocks placed directly in the template file can be calculated individually. If any search block is found in tokens, ``individual_omega_search`` is reset to ``false``.
  | *Default*: true

.. _max_omega_search_len_options_desc:

* | :opt_name:`max_omega_search_len` -- *int [2, 16]*: Maximum amount of omegas in a single omega search block. If not set, it will be calculated automatically.

.. _random_seed_options_desc:

* | :opt_name:`random_seed` -- *positive int*: A seed value for random number generator. Used by all machine learning algorithms.
  | The random_seed is also used to generate off-diagonal estimates when :ref:`Searching Omega Structure<omega_search_usage_target>`, regardless if using one of the machine learning algorithms or performing an :ref:`Exhaustive Search<EX_desc>`.

.. _num_parallel_options_desc:

* | :opt_name:`num_parallel` -- *positive int*: Number of models to execute in parallel, i.e., how many threads to create to handle model runs.
  | If the models are run locally, then it's the maximum number of models running at the same time and should not exceed number of cores (logical/virtual processors).
  | For grid runs, it's the number of models to send to the queue and read from results at any given time. Execution itself is performed by grid nodes, 
    so actual throughput is managed by the grid engine. In this case, 4 threads are enough.
  | *Default*: 4

.. _num_generations_options_desc:

* | :opt_name:`num_generations` :sup:`required` -- *positive int*: Number of iterations or generations of the search algorithm to run.
  | Not used/required for :ref:`EX<EX_desc>`.

.. _population_size_options_desc:

* | :opt_name:`population_size` :sup:`required` -- *positive int*: Number of models to create in every generation.
  | Not used/required for :ref:`EX<EX_desc>`.

.. _num_opt_chains_options_desc:

* | :opt_name:`num_opt_chains` :sup:`required` -- *positive int*: Number of parallel processes to perform :ref:`the "ask" step<GP_ask_tell>` (to increase performance).
  | Required only for GP, RF and GBRT.

.. _exhaustive_batch_size_options_desc:

* :opt_name:`exhaustive_batch_size` -- *positive int*: Since there are no iterations in :ref:`EX<EX_desc>`, and the amount of all models in the search space might be enormous (millions?), the models are run in batches of more manageable size, so, essentially, :ref:`EX<EX_desc>` is split into pseudo-iterations. This setting is the size of those batches.
  Several things to take into consideration when choosing the size:

  * typical value is 50 to 1000
  * in general, the size should be at least 10 to 20 times bigger than the number of models you can run in parallel
  * anything less than 50 is considered ineffective from CPU/grid utilization perspective, as all models in a batch must complete before the next batch starts
  * if you submit model runs to a grid, the size shouldn't be too big to avoid overwhelming or monopolizing your grid queue
  * for local runs, you may batch as many models as you want if you don't mind losing some cached models in case of any accident (model cache is dumped to a file at the
    end of every batch); unlike grid runs, any parallel searches won't be affected by this setting since the main influence in the case of local runs
    is made by :mono_ref:`num_parallel <num_parallel_options_desc>`

  | *Default*: 100

.. _crash_value_options_desc:

* | :opt_name:`crash_value` -- *positive real*:  Value of fitness or reward assigned when model output is not generated. Should be set larger than any anticipated completed model fitness.
  | *Default*: 99999999

.. _penalty_options_desc:

* :opt_name:`penalty` -- *JSON*:

.. _theta_options_desc:

    * | :opt_name:`theta` -- *real*: Penalty added to fitness/reward for each estimated THETA. A value of 3.84 corresponds to a hypothesis test with
        1 df and p < 0.05 (for nested models) a value of 2 for 1 df corresponds to the Akaike information criterion
      | *Default*: 10

.. _omega_options_desc:

    * | :opt_name:`omega` -- *real*: Penalty added to fitness/reward for each estimated OMEGA element
      | *Default*: 10

.. _sigma_options_desc:

    * | :opt_name:`sigma` -- *real*: Penalty added to fitness/reward for each estimated SIGMA element
      | *Default*: 10

.. _convergence_options_desc:

    * | :opt_name:`convergence` -- *real*: Penalty added to fitness/reward for failing to converge
      | *Default*: 100

.. _covariance_options_desc:

    * | :opt_name:`covariance` -- *real*: Penalty added to fitness/reward for failing the covariance step. If a successful covariance step is important,
        this can be set to a large value (e.g., 100), or if a successful covariance step is not at all important, set to 0. Note that if the covariance
        step is not requested, (and therefore cannot be successful), the penalty is added. If a covariance step is not requested, it is suggested that
        the covariance penalty be set to 0.
      | *Default*: 100

.. _correlation_options_desc:

    * | :opt_name:`correlation` -- *real*: Penalty added to fitness/reward if any off-diagonal element of the correlation matrix of estimate has absolute
        value > 0.95. This penalty will be added if the covariance step is requested but fails or if the covariance step is not requested (as in these cases,
        the off-diagonal elements are not available). If a covariance step is not requested, it is suggested that the correlation penalty be set to 0.
      | *Default*: 100

.. _condition_number_options_desc:

    * | :opt_name:`condition_number` -- *real*:  Penalty added to fitness/reward if the covariance step fails or is not requested of if the covariance step
        is successful and the condition number is greater than 1000. If a covariance step is not requested, it is suggested that the condition_number penalty
        be set to 0.
      | *Default*: 100

.. _non_influential_tokens_options_desc:

    * | :opt_name:`non_influential_tokens` -- *real*: Penalty added to fitness/reward if any tokens do not influence the control file (relevant for nested tokens).
        Should be very small (e.g., 0.0001), as the purpose is only for the model with non-influential tokens to be slightly worse
        than the same model without the non-influential token(s) to break a tie.
      | *Default*: 0.00001

.. _effect_limit_options_desc:

* | :opt_name:`effect_limit` -- *int*: Limits :ref:`number of effects<Number of effects>`. If < 1, effect limit is turned off.
  | Applicable only for NONMEM GA/MOGA/MOGA3 searches.
  | *Default*: -1

.. _downhill_period_options_desc:

* | :opt_name:`downhill_period` -- *int*: How often to run the :ref:`downhill step<Local One bit Search>`. If < 1, no periodic downhill search will be performed.
  | *Default*: -1

.. _num_niches_options_desc:

* | :opt_name:`num_niches` -- *int*: Used for GA and downhill. A penalty is assigned for each model based on the number of similar models within a niche
    radius. This penalty is applied only to the selection process (not to the fitness of the model). The purpose
    is to insure maintaining a degree of diversity in the population (integer). num_niches is also used to select the number of models that are entered into the 
    downhill step for all algorithms, except :ref:`EX<EX_desc>`.
  | *Default*: 2

.. _niche_radius_options_desc:

* | :opt_name:`niche_radius` -- *positive real*:  The radius of the niches. See :ref:`"Niche Radius"<Niche Radius>`.
  | *Default*: 2

.. _local_2_bit_search_options_desc:

* | :opt_name:`local_2_bit_search` -- *boolean*: Whether to perform the :ref:`two bit local search<Local Two bit Search>`.
    The two bit local search substantially increases the robustness of the search. All downhill local searches are done starting from :ref:`num_niches models<num_niches_options_desc>`.
  | Ignored for MOGA and MOGA3.
  | *Default*: ``false``

.. _final_downhill_search_options_desc:

* | :opt_name:`final_downhill_search` -- *boolean*: Whether to perform a :ref:`local search<Local Search>` (1 and 2 bit) at the end of the global search.
  | *Default*: ``false``

.. _local_grid_search_options_desc:

* | :opt_name:`local_grid_search` -- *boolean*: Whether to perform a local grid search during downhill.
  | At each downhill step, after local 1-bit search iteration, in every niche:

  * up to N = :ref:`max_local_grid_search_bits<max_local_grid_search_bits_options_desc>` models better than the best model in the niche are determined; N can be less than that if fewer better models are found
  * if no better models found, the niche is done, otherwise
  * for each better model, the first bit that is different to the best model is found
  * those bits are then flipped in all possible ways (2^N permutations)
  * resulting 2^N models replace original models in the niche (the best model in the niche is still the same)
  * new niche models are run
  * new best model is determined, local 1-bit search is repeated for the niches that are not done yet

  | The same is true for MOGA and MOGA3, except:

  * niches best models = front models
  * the 1-bit iterations continue until the front is unchanged (since there is no best model per se)
  * better runs are found by every objective, which makes it up to 2^(:ref:`objectives<objectives_options_desc>` * :ref:`max_local_grid_search_bits<max_local_grid_search_bits_options_desc>`) new models per niche; this can get out of control pretty fast: with 8 niches, 3 objectives and 5 bits you might get up to 8*2^15=262144 models
  * only unique runs are added to the updated niche to not oversaturate the algorithm


  | *Default*: ``false``

.. _max_local_grid_search_bits_options_desc:

* | :opt_name:`max_local_grid_search_bits` -- *positive int*: How many bits to flip.
  | *Default*: 5

.. _nmfe_path_options_desc:

* | :opt_name:`nmfe_path` :sup:`required` -- *string*:  The command line for executing NONMEM. Usually, it's a full path to nmfe script.
  | Required if there are actual NONMEM model runs performed. It's completely ignored until the first model run starts.

.. _model_run_timeout_options_desc:

* | :opt_name:`model_run_timeout` -- *positive real*: Time (seconds) after which the NONMEM execution will be terminated, and the crash value assigned.
  | *Default*: 1200

.. _model_run_priority_class_options_desc:

* | :opt_name:`model_run_priority_class` :sup:`Windows only` -- ``"normal"`` | ``"below_normal"``: Priority class for child processes that build and run models as well as run R postprocess script. ``below_normal`` is recommended to maintain user interface responsiveness.
  | *Default*: ``"below_normal"``

.. _postprocess_options_desc:

* :opt_name:`postprocess` -- *JSON*:

.. _use_r_options_desc:

    * | :opt_name:`use_r` -- *boolean*: Whether user-supplied R code is to be run after NONMEM execution.
      | *Default*: ``false``

    * | :opt_name:`rscript_path` :sup:`deprecated` -- *string*: *Absolute path to Rscript.exe.*
      | Use :mono_ref:`rscript_path <rscript_path_options_desc>` instead.

.. _post_run_r_code_options_desc:

    * | :opt_name:`post_run_r_code` :sup:`required` -- *string*: Path to R file (.r extension) to be run after each NONMEM execution.
      | Required if ``use_r`` is set to ``true``.
      | The script is run in the :ref:`run directory <model_run_dir>`. It must return either a vector, containing a penalty value and a text (will be added to the output file), or, for :ref:`MOGA3<MOGA3_desc>`, :ref:`2 vectors<objectives_options_desc>`.
      | Available aliases are: :ref:`all common aliases<common_aliases>`.

.. _r_timeout_options_desc:

    * | :opt_name:`r_timeout` -- *positive real*: Timeout (seconds) for R code execution.
      | *Default*: 90

.. _use_python_options_desc:

    * | :opt_name:`use_python` -- *boolean*: Whether user-supplied Python code is to be run after NONMEM execution.
      | *Default*: ``false``

.. _post_run_python_code_options_desc:

    * | :opt_name:`post_run_python_code` :sup:`required` -- *string*: Path to python code file (.py extension) to be run after each NONMEM execution.
      | Required if ``use_python`` is set to ``true``.
      | The script must contain either ``post_process2`` or ``post_process`` function (when it has both, ``post_process2`` is used). ``post_process2`` takes a ``ModelRun`` as an argument, ``post_process`` takes a run directory. Both of them must return a tuple containing either a penalty value and some text (will be added to the output file) or, for :ref:`MOGA3<MOGA3_desc>`, :ref:`2 lists<objectives_options_desc>`.
      | Available aliases are: :ref:`all common aliases<common_aliases>`.

.. note::
   Postprocessing is not used for MOGA.

.. _use_saved_models_options_desc:

* | :opt_name:`use_saved_models` -- *boolean*: Whether to restore saved :ref:`Model Cache <api_model_cache>` from file. The file is specified with ``saved_models_file``.
  | *Default*: ``false``

.. _saved_models_file_options_desc:

* | :opt_name:`saved_models_file` -- *string*: The file from which to restore Model Cache.
  | Will only have an effect if ``use_saved_models`` is set to ``true``.
  | By default, the cache is saved in ``{working_dir}/models.json`` and cleared every time the search is started. To use saved runs, rename ``models.json`` or copy it to a different location.
  | Available aliases are: :ref:`all common aliases<common_aliases>`.

.. warning::
   Don't set ``saved_models_file`` to ``{working_dir}/models.json``.

.. _saved_models_readonly_options_desc:

* | :opt_name:`saved_models_readonly` -- *boolean*: Do not overwrite the ``saved_models_file`` content.
  | *Default*: ``false``

.. _keep_key_models_options_desc:

* | :opt_name:`keep_key_models` -- *boolean*: Whether to save the best model from every generation. Models are copied to :mono_ref:`key_models_dir <key_models_dir_options_desc>`.
  | *Default*: ``false``

.. _keep_best_models_options_desc:

* | :opt_name:`keep_best_models` -- *boolean*: Save only key models that improve fitness value, i.e. the models better than previous overall best model. Unlike ``keep_key_models`` this option may skip some generations.
  | When set to ``true`` overrides ``keep_key_models`` to ``true`` as well.
  | *Default*: ``true``

.. note::
   Since ``keep_best_models`` is on by default you have to set it to ``false`` explisitly if you want key models to be saved.

.. note::
   ``keep_key_models``/``keep_best_models`` are not applicable to Exhaustive search.

.. _rerun_key_models_options_desc:

* | :opt_name:`rerun_key_models` -- *boolean*: Sometimes saved key models don't have any output:

    * when a model is restored from the cache file it has only fitness value

    * when a model is not better than the overall best model to the moment its run folder is cleaned up after the run

  | In order to obtain desired output (e.g. tables) such models need to be re-run. To do so set ``rerun_key_models`` to ``true``.
  | All the models that don't have their output stored will be re-run after the entire search.
  | *Default*: ``false``

.. note::
  | ``rerun_key_models`` doesn't have effect if none of ``keep_key_models``/``keep_best_models`` is ``true``.

.. _rerun_front_models_options_desc:

* | :opt_name:`rerun_front_models` -- *boolean*: Same to :ref:`rerun_key_models <rerun_key_models_options_desc>`, but for non-dominated models.
  | *Default*: ``true``

.. _remove_run_dir_options_desc:

* | :opt_name:`remove_run_dir` -- *boolean*: If ``true``, will delete the entire model :ref:`run directory <model_run_dir>`, otherwise - only unnecessary files inside it.
  | *Default*: ``false``

.. _remove_temp_dir_options_desc:

* | :opt_name:`remove_temp_dir` -- *boolean*: Whether to delete entire :mono_ref:`temp_dir <temp_dir_options_desc>` after the search is finished or stopped. Doesn't have any effect when search is :ref:`run on a grid <grid_execution>`.
  | *Default*: ``false``

.. _keep_files_options_desc:

* | :opt_name:`keep_files` -- *list of strings*: Keep files with exact names when cleaning up run directories.

.. _keep_extensions_options_desc:

* | :opt_name:`keep_extensions` -- *list of strings*: Keep ``{run_name}.{ext}`` when cleaning up run directories, where ``{ext}`` is one of the list items.

.. _use_system_options_options_desc:

* | :opt_name:`use_system_options` -- *boolean*: Whether to :ref:`override options <settings_override>` with environment-specific values.
  | *Default*: ``true``

.. _model_cache_options_desc:

* | :opt_name:`model_cache` -- *string*: ModelCache subclass to be used.
  | Currently there are only :data:`darwin.MemoryModelCache <darwin.MemoryModelCache.MemoryModelCache>`
    and :data:`darwin.AsyncMemoryModelCache <darwin.MemoryModelCache.AsyncMemoryModelCache>`.
  | You can create your own and use it (e.g., a cache that stores model runs in a database. The name is quite arbitrary and doesn't have any convention/constraints).
  | *Default*: ``darwin.MemoryModelCache``

.. _model_run_man_options_desc:

* | :opt_name:`model_run_man` -- *string*: ModelRunManager subclass to be used.
  | Currently there are only :data:`darwin.LocalRunManager <darwin.LocalRunManager.LocalRunManager>` and :data:`darwin.GridRunManager <darwin.grid.GridRunManager.GridRunManager>`.
  | *Default*: ``darwin.LocalRunManager``

.. _grid_adapter_options_desc:

* | :opt_name:`grid_adapter` -- *string*: GridAdapter subclass to be used.
  | Currently only :data:`darwin.GenericGridAdapter <darwin.grid.GenericGridAdapter.GenericGridAdapter>` is available.
  | *Default*: ``darwin.GenericGridAdapter``

.. _engine_adapter_options_desc:

* | :opt_name:`engine_adapter` -- *string*: ModelEngineAdapter subclass to be used.
  | Currently ``nonmem`` and ``nlme`` are available.
  | *Default*: ``nonmem``

.. _skip_running_options_desc:

* | :opt_name:`skip_running` -- *boolean*: If set, no actual NM/NLME runs will be performed, pyDarwin will create a control file and proceed to postprocessing. OFV in this case will be a sum of R and Python postprocessing penalties.
  | *Default*: ``false``

.. _rscript_path_options_desc:

* | :opt_name:`rscript_path` :sup:`required` -- *string*: Absolute path to Rscript.exe.
  | Required if either of :mono_ref:`use_r <use_r_options_desc>` is set to ``true`` or ``engine_adapter`` is set to ``nlme``.

.. _nlme_dir_options_desc:

* | :opt_name:`nlme_dir` :sup:`required` -- *string*: Absolute path to NLME Engine installation.
  | Required if ``engine_adapter`` is set to ``nlme``.

.. _gcc_dir_options_desc:

* | :opt_name:`gcc_dir` :sup:`required` -- *string*: Absolute path to GCC root directory.
  | Required if ``engine_adapter`` is set to ``nlme``.

.. _working_dir_options_desc:

* | :opt_name:`working_dir` -- *string*: The project's working directory, where all the necessary files and folders are created. Also, it's a default location of output and temp folders.
  | By default, it is set to ':mono_ref:`\<pyDarwin home\><pydarwin_home>`/:mono_ref:`{project_stem} <project_stem_alias>`'.
  | Aliased as :mono_ref:`{working_dir}<working_dir_alias>`.
  | Available aliases are: :mono_ref:`{project_dir}<project_dir_alias>`.

.. _data_dir_options_desc:

* | :opt_name:`data_dir` -- *string*: Directory where datasets are located. Must be available for individual model runs.
  | *Default*: ``{project_dir}``
  | Aliased as :mono_ref:`{data_dir}<data_dir_alias>`.
  | Available aliases are: :mono_ref:`{project_dir}<project_dir_alias>`, :mono_ref:`{working_dir}<working_dir_alias>`.

.. _output_dir_options_desc:

* | :opt_name:`output_dir` -- *string*: Directory where pyDarwin output will be placed.
  | *Default*: ``{working_dir}/output``
  | Aliased as :mono_ref:`{output_dir}<output_dir_alias>`.
  | Available aliases are: :mono_ref:`{project_dir}<project_dir_alias>`, :mono_ref:`{working_dir}<working_dir_alias>`.

.. _temp_dir_options_desc:

* | :opt_name:`temp_dir` -- *string*: Parent directory for all model runs' run directories, i.e., where all folders for every iteration is located.
  | *Default*: ``{working_dir}/temp``
  | Aliased as :mono_ref:`{temp_dir}<temp_dir_alias>`.
  | Available aliases are: :mono_ref:`{project_dir}<project_dir_alias>`, :mono_ref:`{working_dir}<working_dir_alias>`.

.. _key_models_dir_options_desc:

* | :opt_name:`key_models_dir` -- *string*: Directory where key/best models will be saved.
  | *Default*: ``{working_dir}/key_modlels``
  | Available aliases are: :mono_ref:`{project_dir}<project_dir_alias>`, :mono_ref:`{working_dir}<working_dir_alias>`.

.. _non_dominated_models_dir_options_desc:

* | :opt_name:`non_dominated_models_dir` -- *string*: Directory where non-dominated models will be saved.
  | *Default*: ``{working_dir}/non_dominated_models``
  | Available aliases are: :mono_ref:`{project_dir}<project_dir_alias>`, :mono_ref:`{working_dir}<working_dir_alias>`.

.. _generic_grid_adapter_options_desc:

* | :opt_name:`generic_grid_adapter` -- *JSON*: These settings are necessary only when you use ``darwin.GridRunManager`` as :mono_ref:`model_run_man <model_run_man_options_desc>`.
  | Examples for different workload managers can be found :ref:`here<generic_grid_adapter_examples>`
  | For local runs this entire section is ignored.

.. _python_path_options_desc:

    * | :opt_name:`python_path` :sup:`required` -- *string*: Path to your Python interpreter, preferably to the instance of the interpreter located in :ref:`virtual environment<install_python_venv>` where pyDarwin is deployed. The path must be available to all grid nodes that run jobs.
      | Alternatively it may be set to a :ref:`custom script<customizing_python_script>`.

.. _submit_command_options_desc:

    * | :opt_name:`submit_command` :sup:`required` -- *string*: A command that submits individual runs to the grid queue. The actual command submitted to the queue is ``<python_path> -m darwin.run_model <input file> <output file> <options file>``, but you don't put it in the ``submit_command``.
      | Example: ``qsub -b y -o {results_dir}/{run_name}.out -e {results_dir}/{run_name}.err -N {job_name}``
      | Available aliases are: :ref:`all common aliases<common_aliases>`, :ref:`job submit aliases<job_submit_aliases>`.

.. _submit_search_command_options_desc:

    * | :opt_name:`submit_search_command` :sup:`required` -- *string*: A command that submits search job to the grid queue. Similar to ``submit_command``, but for entire search.
      | Example: ``qsub -b y -cwd -o {project_stem}_out.txt -e {project_stem}_err.txt -N '{project_name}'``
      | Required only for :ref:`grid search<running_grid_search>`.
      | Available aliases are: :ref:`all common aliases<common_aliases>`, :ref:`{darwin_cmd} <darwin_cmd_alias>`.

    .. note::
       No directories are created at the point of submitting the search job. So even if it's possible to use ``{working_dir}``, ``{out_dir}``, and ``{temp_dir}`` in ``submit_search_command``, it's not recommended. There may be cases where the directories do exist (if you set those settings to existing folders or run the search locally before submitting it to the grid), which is why these aliases are not prohibited.

.. _submit_job_id_re_options_desc:

    * | :opt_name:`submit_job_id_re` :sup:`required` -- *string*: A regular expression to find a job id in ``submit_command`` output. Job id must be captured with first `capturing group <https://www.google.com/search?q=regular+expression+capturing+group>`_.
      | May look like this: ``Your job (\\w+) \\(\".+?\"\\) has been submitted``

.. _poll_command_options_desc:

    * | :opt_name:`poll_command` :sup:`required` -- *string*: A command that retrieves finished jobs from grid controller. If your controller/setup allows you to specify ids/patterns in polling commands, do it (see ``delete_command``). If it doesn’t, you must poll ALL finished jobs: ``qstat -s z``
      | Available aliases are: :ref:`all common aliases<common_aliases>`, :mono_ref:`{job_ids}<job_ids_alias>`.

.. _poll_job_id_re_options_desc:

    * :opt_name:`poll_job_id_re` :sup:`required` -- *string*: A regular expression to find a job id in every line of ``poll_command`` output. Similar to ``submit_job_id_re``.

.. _poll_interval_options_desc:

    * | :opt_name:`poll_interval` -- *int*: How often to poll jobs (seconds).
      | *Default*: 10

.. _delete_command_options_desc:

    * | :opt_name:`delete_command` -- *string*: A command that deletes all unfinished jobs related to the search when you stop it. It may delete all of them by id (``qdel {job_ids}``) or by mask (``qdel {project_stem}-*``).
      | Available aliases are: :ref:`all common aliases<common_aliases>`, :mono_ref:`{job_ids}<job_ids_alias>`.

    .. warning::
       Be careful when using a mask: if your mask matches the search job name, it may kill your search prematurely, e.g., during saving the cache.


Aliases
-------------

| An alias is essentially a substitute text for some keyword. Their main purpose is to unify and to simplify configuration of various projects through different environments.

| We encourage you to become familiar with them and to use them instead of explicit values, e.g., paths to your projects and their internals.

.. _common_aliases:

Common aliases
~~~~~~~~~~~~~~~~~~

| These aliases are applicable to several different options, so it's easier to refer to them as a group.
| They also can be used in :ref:`templates <template_file_target>`.

.. _project_dir_alias:

  * | :opt_name:`{project_dir}` -- Project folder. Cannot be set directly. It's set to either the folder argument of ``run_search_in_folder`` (function or module) or the parent folder of options file passed to ``run_search`` (function or module).
    | Can be used in: :mono_ref:`data_dir <data_dir_options_desc>`, :mono_ref:`output_dir <output_dir_options_desc>`, :mono_ref:`temp_dir <temp_dir_options_desc>`,
      :mono_ref:`saved_models_file <saved_models_file_options_desc>`, :mono_ref:`submit_search_command <submit_search_command_options_desc>`,
      :mono_ref:`submit_command <submit_command_options_desc>`, :mono_ref:`poll_command <poll_command_options_desc>`, :mono_ref:`delete_command <delete_command_options_desc>`.

.. _project_name_alias:

  * | :opt_name:`{project_name}` -- Alias for the :mono_ref:`project_name<project_name_options_desc>` setting.
    | Can be used in: :mono_ref:`saved_models_file <saved_models_file_options_desc>`, :mono_ref:`submit_search_command <submit_search_command_options_desc>`,
      :mono_ref:`submit_command <submit_command_options_desc>`, :mono_ref:`poll_command <poll_command_options_desc>`, :mono_ref:`delete_command <delete_command_options_desc>`.

.. _project_stem_alias:

  * | :opt_name:`{project_stem}` -- A file system friendly representation of the project name in a way that it will be easy to manage as a folder name where all non-letters and non-digits are replaced with underscores, i.e.,  ``Some reasonable(ish) name`` becomes ``Some_reasonable_ish__name``. This cannot be set directly.
    | Can be used in: :mono_ref:`saved_models_file <saved_models_file_options_desc>`, :mono_ref:`submit_search_command <submit_search_command_options_desc>`,
      :mono_ref:`submit_command <submit_command_options_desc>`, :mono_ref:`poll_command <poll_command_options_desc>`, :mono_ref:`delete_command <delete_command_options_desc>`.

.. _working_dir_alias:

  * | :opt_name:`{working_dir}` -- Alias for the :mono_ref:`working_dir<working_dir_options_desc>` setting.
    | Can be used in: :mono_ref:`data_dir <data_dir_options_desc>`, :mono_ref:`output_dir <output_dir_options_desc>`, :mono_ref:`temp_dir <temp_dir_options_desc>`,
      :mono_ref:`saved_models_file <saved_models_file_options_desc>`, :mono_ref:`submit_search_command <submit_search_command_options_desc>`,
      :mono_ref:`submit_command <submit_command_options_desc>`, :mono_ref:`poll_command <poll_command_options_desc>`, :mono_ref:`delete_command <delete_command_options_desc>`.

.. _data_dir_alias:

  * | :opt_name:`{data_dir}` -- Alias for the :mono_ref:`data_dir<data_dir_options_desc>` setting.
    | Can be used in: :mono_ref:`saved_models_file <saved_models_file_options_desc>`, :mono_ref:`submit_search_command <submit_search_command_options_desc>`,
      :mono_ref:`submit_command <submit_command_options_desc>`, :mono_ref:`poll_command <poll_command_options_desc>`, :mono_ref:`delete_command <delete_command_options_desc>`.

.. _output_dir_alias:

  * | :opt_name:`{output_dir}` -- Alias for the :mono_ref:`output_dir<output_dir_options_desc>` setting.
    | Can be used in: :mono_ref:`saved_models_file <saved_models_file_options_desc>`, :mono_ref:`submit_search_command <submit_search_command_options_desc>`,
      :mono_ref:`submit_command <submit_command_options_desc>`, :mono_ref:`poll_command <poll_command_options_desc>`, :mono_ref:`delete_command <delete_command_options_desc>`.

.. _temp_dir_alias:

  * | :opt_name:`{temp_dir}` -- Alias for the :mono_ref:`temp_dir<temp_dir_options_desc>` setting.
    | Can be used in: :mono_ref:`saved_models_file <saved_models_file_options_desc>`, :mono_ref:`submit_search_command <submit_search_command_options_desc>`,
      :mono_ref:`submit_command <submit_command_options_desc>`, :mono_ref:`poll_command <poll_command_options_desc>`, :mono_ref:`delete_command <delete_command_options_desc>`.

.. _algorithm_alias:

  * | :opt_name:`{algorithm}` -- Alias for the :mono_ref:`algorithm<algorithm_options_desc>` setting.
    | Can be used in: :mono_ref:`saved_models_file <saved_models_file_options_desc>`, :mono_ref:`submit_search_command <submit_search_command_options_desc>`,
      :mono_ref:`submit_command <submit_command_options_desc>`, :mono_ref:`poll_command <poll_command_options_desc>`, :mono_ref:`delete_command <delete_command_options_desc>`.

.. _author_alias:

  * | :opt_name:`{author}` -- Alias for the :mono_ref:`author<author_options_desc>` setting.
    | Can be used in: :mono_ref:`saved_models_file <saved_models_file_options_desc>`, :mono_ref:`submit_search_command <submit_search_command_options_desc>`,
      :mono_ref:`submit_command <submit_command_options_desc>`, :mono_ref:`poll_command <poll_command_options_desc>`, :mono_ref:`delete_command <delete_command_options_desc>`.


Grid job aliases
~~~~~~~~~~~~~~~~~~

.. _job_submit_aliases:

Job submit aliases
""""""""""""""""""""

These aliases are only applicable to :mono_ref:`submit_command <submit_command_options_desc>`.

.. _results_dir_alias:

  * :opt_name:`{results_dir}` -- Alias for the ``{working_dir}/run_results``, where the results of individual runs are stored as ModelRun objects serialized to JSON files.

.. _job_name_alias:

  * :opt_name:`{job_name}` -- Alias for the default job name, which is ``{project_name}-{run_name}``. *Default* here doesn't mean it will be assigned to a job automatically, it's up to the user to decide whether to use it or generate their own using other available aliases, e.g., ``{project_name}-{generation}-{run_number}``.

.. _run_name_alias:

  * :opt_name:`{run_name}` -- Alias for the :mono_ref:`ModelRun.file_stem <model_run_stem>`.

.. _generation_alias:

  * :opt_name:`{generation}` -- Alias for the :mono_ref:`ModelRun.generation <model_run_generation>`.

.. _run_number_alias:

  * :opt_name:`{run_number}` -- Alias for the :mono_ref:`ModelRun.model_num <model_run_num>`.

.. _run_dir_alias:

  * :opt_name:`{run_dir}` -- Alias for the :mono_ref:`ModelRun.run_dir <model_run_dir>`.

.. _darwin_cmd_alias:

  * :opt_name:`{darwin_cmd}` -- Alias for the command sequence that runs a pyDarwin command. Depending on the context it can execute ``run_search``, ``run_search_in_folder``, or ``run_model``. By default the sequence is added to the end of :mono_ref:`submit_command <submit_command_options_desc>`/:mono_ref:`submit_search_command <submit_search_command_options_desc>`. Using this alias you can put the sequence wherever you want in the command. For example Slurm requires the command being wrapped, so the settings may be like this:

    ..  code-block:: json

      "generic_grid_adapter" : {
        "submit_search_command" : "sbatch -D {project_dir} --job-name '{project_name}' --output {project_stem}.out --error {project_stem}.err --wrap '{darwin_cmd}'",
        "submit_command" : "sbatch --job-name '{job_name}' --output {results_dir}/{run_name}.out --error {results_dir}/{run_name}.err --wrap {darwin_cmd}",
        "submit_job_id_re" : "Submitted batch job (\\d+)",
        "poll_command" : "squeue -t CD",
        "poll_job_id_re" : "^(\\d+)",
        "poll_interval" : 10,
        "delete_command" : "scancel {job_ids}"
      }

.. note::
   Due to different mechanisms of calling the command ``{darwin_cmd}`` must be enclosed in single quotes for ``submit_search_command`` and not enclosed for ``submit_command``.


Job delete/poll aliases
""""""""""""""""""""""""

.. _job_ids_alias:

  * | :opt_name:`{job_ids}` -- Alias for a whitespace delimited list of ids of all unfinished jobs that were submitted from the current population.
    | Can be used in: :mono_ref:`poll_command <poll_command_options_desc>`, :mono_ref:`delete_command <delete_command_options_desc>`.


Environment variables
------------------------

There are a few environment variables that you may want to set in order to facilitate ``pyDarwin`` ease of use.

.. _pydarwin_home_env_var:

PYDARWIN_HOME
~~~~~~~~~~~~~~~~~~

This environment variable allows you to change :ref:`pyDarwin home<pydarwin_home>` to an arbitrary **existing** directory.

.. tabs::

   .. group-tab:: cmd.exe

      .. code-block:: bat

         set PYDARWIN_HOME=C:\workspace\pydarwin

   .. group-tab:: bash

      .. code-block:: bash

         export PYDARWIN_HOME=/mnt/parallel-universe/my-evil-twin/pydarwin

.. note::
   It's not advised to put pyDarwin home inside temp folder for a variety of reasons.

.. _pydarwin_options_env_var:

PYDARWIN_OPTIONS
~~~~~~~~~~~~~~~~~~

This environment variable allows you to :ref:`override settings <settings_override>`.

.. tabs::

  .. group-tab:: cmd.exe

    .. code-block:: bat

       set PYDARWIN_OPTIONS=C:\workspace\darwin\system_options.json

  .. group-tab:: bash

    .. code-block:: bash

       export PYDARWIN_OPTIONS=~/darwin/system_options.json


.. _settings_override:

Settings override
------------------------

At some point you may start running your projects in different environments. It may become quite annoying to edit ``nmfe_path`` and ``rscript_path`` every time you copy the project back and forth between Windows and Linux.

To avoid this, you can create a separate options file for every environment (even every user if you wish) and place all the environment-specific settings inside this file. Then, you can just set PYDARWIN_OPTIONS to the path of that file, and every setting from that file will override corresponding settings in any options.json of any project you run in that environment.
Overriding can be switched off by :mono_ref:`use_system_options <use_system_options_options_desc>` set to ``false``.

.. note::
   Set ``use_system_options`` in the project's :file:`options.json`, not in the common one.

Good candidates to put into common options file are:

* ``nmfe_path``
* ``rscript_path``
* ``num_parallel``
* ``author``
* ``random_seed``

Basically, any setting can be overridden. However, be cautious to not override the algorithm or penalties (unless this is intended).

When you override nested settings, you don't have to specify every single value in the section, only those you want to be changed.

For example:

.. tabs::

  .. group-tab:: options.json

    ..  code-block:: json

        {
            "author": "Mark Sale",
            "project_name": "Example 11",

            "algorithm": "GA",

            "random_seed": 11,
            "num_parallel": 40,
            "num_generations": 14,
            "population_size": 140,

            "remove_run_dir": true,

            "nmfe_path": "C:/nm744/util/nmfe74.bat",

            "postprocess": {
                "use_r": true,
                "post_run_r_code": "{project_dir}/Cmaxppc.r",
                "rscript_path": "C:\\Program Files\\R\\R-4.1.3\\bin\\Rscript.exe"
            }
        }

  .. group-tab:: system_options.json

    ..  code-block:: json

        {
            "author": "Certara",

            "random_seed": 11,
            "num_parallel": 4,

            "remove_run_dir": false,

            "nmfe_path": "C:/nm74g64/util/nmfe74.bat",

            "postprocess": {
                "rscript_path": "C:/Program Files/R/R-4.0.2/bin/Rscript.exe"
            }
        }

  .. group-tab:: resulting content

    ..  code-block:: json

        {
            "author": "Certara",
            "project_name": "Example 11",

            "algorithm": "GA",

            "random_seed": 11,
            "num_parallel": 4,
            "num_generations": 14,
            "population_size": 140,

            "remove_run_dir": false,

            "nmfe_path": "C:/nm74g64/util/nmfe74.bat",

            "postprocess": {
                "use_r": true,
                "post_run_r_code": "{project_dir}/Cmaxppc.r",
                "rscript_path": "C:/Program Files/R/R-4.0.2/bin/Rscript.exe"
            }
        }

In terms of options priority, ``pyDarwin`` loads options.json, then system_options.json, then merges those two together so values from system_options overwrite the original ones. After that, all default values are applied, and resulting options values are used.

.. note::
   When running models on a grid, individual models are run on different nodes (in different environments). You must ensure that you either override settings on every node, or don't override it at all.
