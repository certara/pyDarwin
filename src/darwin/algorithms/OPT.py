import numpy as np
import pandas as pd
import skopt
import time
import logging
import heapq
import warnings
import itertools
from skopt import Optimizer

from multiprocessing import Pool
import traceback

from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import keep_going

import darwin.GlobalVars as GlobalVars

from darwin.ModelCode import ModelCode
from darwin.algorithms.run_downhill2 import run_downhill
from darwin.Template import Template
from darwin.Model import Model
from darwin.ModelRun import ModelRun
from darwin.Population import Population

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", message="The objective has been evaluated ")
warnings.filterwarnings("ignore", message="The optimal value found for ", append=True)


def _create_optimizer(template: Template, algorithm, chain_num) -> list:
    num_groups = [skopt.space.Categorical(categories=numerical_group, transform="onehot")
                  for numerical_group in template.get_search_space_coordinates()]

    opts = [Optimizer(num_groups, n_jobs=1, base_estimator=algorithm, random_state=rs)
            for rs in np.random.randint(0, 1000, chain_num)]

    return opts


def _opt_ask(opt: Optimizer, n_points: int) -> list:
    try:
        return opt.ask(n_points)
    # if we don't catch it, pool will do it silently
    except:
        traceback.print_exc()

    return []


def _ask_models(opts: list, n_points: int) -> list:
    if not keep_going():
        return []

    n_opts = len(opts)

    pool = Pool(n_opts)

    n_ask = int(n_points / n_opts)
    lens = [n_ask] * n_opts
    lens[-1] += n_points % n_opts

    asks = pool.starmap(_opt_ask, zip(opts, lens))

    pool.close()
    pool.join()

    return [x for xs in asks for x in xs]


def get_tokens_map(template, tokens):
        # TODO only deals with one level of nesting currently
        
        # Map tokens active in base template
        tokens_map = {}
        tokens_section_list = []
        for t_query_pos, t_query in enumerate(tokens.keys()):
            if ("{" + t_query) in template:
                # print(t_query, "here")
                tokens_section_list.append(t_query_pos)
        tokens_map["template"] = tokens_section_list

        # Map nested tokens active in token variables
        tokens_map["tokens"] = {}

        for t_pos, t_value in enumerate(tokens.keys()):
            
            t_value_map = {}
            
            for i, value in enumerate(tokens[t_value]):
                t_value_list = []
                
                value_str = " ".join(value)
                # print(value_str)
                
                
                for t_query_pos, t_query in enumerate(tokens.keys()):
                    if ("{" + t_query + "[") in value_str:
                        # print(t_query, "here. I:", i)
                        t_value_list.append(t_query_pos)
                
                t_value_map[i] = t_value_list
                
            # Collect t_value_maps
            tokens_map["tokens"][t_pos] = t_value_map

        return tokens_map


def collect_active_tokens(model_code, keys, tokens_map):

    # TODO update algorithm to run for model spaces with n nesting levels

        # # DEBUG CODE
        # if model_code == "10001111122100110":
        #     pass
        
        active_tokens = np.zeros(len(keys)).astype(int)

        # If model code isn't null
        if model_code == model_code:
            active_tokens = np.zeros(len(keys)).astype(int)
            active_token_set = set()
            active_token_set.update(tokens_map["template"])
            # print(active_token_set)
            
            # Add while loop to keep checking through until done
            for t_pos, t_value in enumerate(model_code):
                
                # print("t_pos", t_pos, "t_value", t_value)
                # Look up active tokens from the token map
                active_i = tokens_map["tokens"][t_pos][int(t_value)]
                # print(active_i)
                active_token_set.update(active_i)
                
            # Convert active_token_set to active tokens_vector
            for token_pos in active_token_set:
                active_tokens[token_pos] = 1
            
        return active_tokens


def get_duplicate_models(code_masked, search_cooridinates):


    # Get variables
    masked_variables = [pos for pos, char in enumerate(code_masked) if char == "*"]

    # Get token values for masked variables
    masked_variable_values = {}
    for mv in masked_variables:
        masked_variable_values[mv] = search_cooridinates[mv]
        token_vals = search_cooridinates[mv]
    
    # Get all equivelent variable sets
    token_vals = list(masked_variable_values.values())
    all_token_val_combinations = list(itertools.product(*token_vals))

    # Generate all equivlent model codes
    equivalent_model_codes = []
    for token_val_combo in all_token_val_combinations:

        model_code = list(code_masked)

        for i, v in enumerate(token_val_combo):
            token_pos = masked_variables[i]
            token_val = v
            model_code[token_pos] = str(token_val)
        
        equivalent_model_codes.append("".join(model_code))

    return equivalent_model_codes

def generate_masked_model_codes(codes, active_tokens_np):

    # Create masked model codes
    codes = np.array(codes).astype(int)
    codes_masked = np.where(active_tokens_np==0, "*", codes)
    codes_masked_str = codes_masked.astype(str)
    codes_masked_str = np.char.replace(codes_masked_str, '.0', '')
    codes_masked_str = np.char.replace(codes_masked_str, 'nan', '*')
    codes_masked_str = ["".join(x) for x in codes_masked_str]

    return codes_masked_str


# run parallel? https://scikit-optimize.github.io/stable/auto_examples/parallel-optimization.html
def run_skopt(model_template: Template) -> ModelRun:
    """
    Run one of the scikit optimize algorithms (GP, RF, GBRT). See https://scikit-optimize.github.io/stable/.

    :param model_template: Model template to be run
    :type model_template: Template
    :return: The best model from search
    :rtype: Model
    """

    max_optimisation_ask_rounds = 5
    max_random_ask_rounds = 2
    check_active_tokens = True

    if check_active_tokens:
        pass
        


    downhill_period = options.downhill_period

    if options.random_seed is not None:
        np.random.seed(options.random_seed)

    opts = _create_optimizer(model_template, options.algorithm, options.num_opt_chains)
    o_test = opts[0]

    # https://scikit-optimize.github.io/stable/auto_examples/ask-and-tell.html

    niter_no_change = 0
    population = Population(model_template, 0)

    # Keep track of active models
    active_models = []

    # Get token map
    tokens_map = get_tokens_map(model_template.template_text, model_template.tokens)

    for iteration in range(1, options.num_generations + 1):
        if not keep_going():
            break

        log.message(f"Starting iteration {iteration}")

        # SJR Change
        initial_models = False
        if iteration == 1 & initial_models:
            suggested = []

        else:
            suggested = []
            count = 0
            start_time_ask = time.time()
            while len(suggested) < options.population_size:
                
                num_ask = int(options.population_size * (count + 1)) # Ask for more points if needed
                # log.message(f"Ask iteration: {iteration}, Ask count: {count}, Number ask: {num_ask}")
                required = options.population_size - len(suggested)

                if count < max_optimisation_ask_rounds:
                    log.message(f"Ask iteration: {iteration}, Ask count: {count}, Number ask: {num_ask}")
                    suggested_initial = o_test.ask(num_ask)
                    suggested_initial = suggested_initial[num_ask - options.population_size:]
                else:
                    log.message(f"Ask iteration: {iteration}. Generating random candidates for remaining {required} suggestions")
                    # log.message(f"Generating new optimiser for remaining {required} suggestions")
                    random_opt = _create_optimizer(model_template, options.algorithm, 1)[0]
                    suggested_initial = random_opt.ask(options.population_size)

                # Get active suggested tokens
                active_tokens = [collect_active_tokens(x, model_template.tokens.keys(), tokens_map) for x in suggested_initial]
                active_tokens_np = np.vstack(active_tokens)

                # codes_masked_str = generate_masked_model_codes(suggested_initial, active_tokens_np)
                initial_df = pd.DataFrame()
                initial_df["numeric_code"] = suggested_initial
                initial_df["masked_code"] = generate_masked_model_codes(suggested_initial, active_tokens_np)

                # Get unique codes within group
                unique_df = initial_df.drop_duplicates("masked_code")
                # codes_masked_unique = list(set(codes_masked_str))

                # If no active codes recorded yet then use these codes
                if len(active_models) == 0:
                    active_models = unique_df["masked_code"].to_list()
                    suggested.extend(unique_df["numeric_code"].to_list())

                # If active codes exist then also check these
                else:
                    # Select new models as those which are not in the active model list
                    new_df = unique_df.loc[~unique_df["masked_code"].isin(active_models)]

                    # Clip number of suggestions if greater than population size
                    
                    if len(suggested) + len(new_df) > options.population_size:
                        # total_len = len(suggested) + len(suggested_new)
                        
                        new_df = new_df.iloc[:required]

                    # Add the unique models to the suggested codes
                    suggested.extend(new_df["numeric_code"].to_list())

                    # Add masked suggested models to active_models list
                    active_models.extend(new_df["masked_code"].to_list())

                if count == max_optimisation_ask_rounds + max_random_ask_rounds:
                    total_ask = num_ask + options.population_size
                    log.warn(f"Issue finding suggested models. After {num_ask} suggested candidates and {max_random_ask_rounds} rounds of random generation only {len(suggested)} unique models found.")
                count += 1

        end_time_ask = time.time()
        ask_time = end_time_ask - start_time_ask
        log.message(f"Done asking. Time taken: {int(ask_time)}s")

        if not keep_going():
            break

        # Original version
        if len(suggested) != 0:
            population = Population.from_codes(model_template, iteration, suggested, ModelCode.from_int,
                                            max_iteration=options.num_generations)
            population.run()

            if not keep_going():
                break

        downhill_runs = []

        if downhill_period > 0 and iteration % downhill_period == 0:
            # pop will have the fitnesses without the niche penalty here

            if GlobalVars.best_run is not None:
                population.runs.append(GlobalVars.best_run)

            log.message(f"Starting downhill, iteration = {iteration}")

            downhill_runs, active_models = run_downhill(model_template, population, tokens_map, active_models, return_all=False)

            if not keep_going():
                break

            suggested = [r.model.model_code.IntCode for r in population.runs]

        fitnesses = [r.result.fitness for r in population.runs]

        log.message(f"Tell...")

        opt = opts[0]


        # # Get equivalent active models
        # for i in suggested:
        #     print(i)
        #     model_code_str = "".join(str(i)).str.replace('[', '').str.replace(']', '')
        #     active_model_code = collect_active_tokens()


        if check_active_tokens:
            # TODO update to suggested + equivalents
            # Think the best appraoch would be to create a big list all in the same format
            # Maybe easier to test w/ larger population of models

            # equivalent_codes_fitness = get_equivalent_codes_fitness(equivalent_models, fitnesses)
            # opt.tell(equivalent_codes_fitness["codes"], equivalent_codes_fitness["fitness"])
            # opt.tell(suggested, fitnesses)
            o_test.tell(suggested, fitnesses)

        else:
            # opt.tell(suggested, fitnesses)
            o_test.tell(suggested, fitnesses)

        if downhill_runs:
            # opt.tell([r.model.model_code.IntCode for r in downhill_runs], [r.result.fitness for r in downhill_runs])
            o_test.tell([r.model.model_code.IntCode for r in downhill_runs], [r.result.fitness for r in downhill_runs])

        opts = [opt.copy(random_state=o.rng) for o in opts]

        log.message(f"Done telling")

        best_run = population.get_best_run()

        best_fitness = best_run.result.fitness

        best_run_overall = GlobalVars.best_run or best_run

        if best_fitness < best_run_overall.result.fitness:
            niter_no_change = 0
        else:
            niter_no_change += 1

        log.message(f"Best fitness this iteration = {best_fitness:4f}  at {time.asctime()}")
        log.message(f"Best overall fitness = {best_run_overall.result.fitness:4f},"
                    f" iteration {best_run_overall.generation}, model {best_run_overall.model_num}")

    if options.final_downhill_search and keep_going():
        log.message(f"Starting final downhill")

        population.name = 'FN'

        if GlobalVars.best_run is not None:
            population.runs.append(GlobalVars.best_run)

        _, active_models =run_downhill(model_template, population, tokens_map, active_models)

    if niter_no_change:
        log.message(f'No change in fitness in {niter_no_change} iterations')

    return GlobalVars.best_run
