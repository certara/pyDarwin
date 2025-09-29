from copy import copy
from scipy.spatial import distance_matrix
import numpy as np
import pandas as pd
import itertools

from darwin.Log import log
from darwin.options import options
from darwin.utils import get_n_best_index, get_n_worst_index
from darwin.ExecutionManager import keep_going

from darwin.Template import Template
from darwin.ModelRun import ModelRun
from darwin.Population import Population
from darwin.ModelCode import ModelCode


def _get_distances(x, y) -> list:
    return distance_matrix(x, y)[0]


class _Niche:
    def __init__(self, best_run: ModelRun):
        self.best_run = best_run
        self.runs_start = self.runs_finish = None
        self.done = False


def _get_niches(runs: list) -> list:
    """
    find the best in each of num_niches, return the full model
    argument is pop - list of full models
    return value is list of models, of length num_niches
    """
    # TODO update distance measure to consider active codes

    crash_value = options.crash_value

    fitnesses = [r.result.fitness for r in runs]
    all_codes = [r.model.model_code.MinBinCode for r in runs]

    best_runs = []

    for _ in range(options.num_niches):
        # below should exclude those already in a niche, as  the fitness should be set to 999999
        best_run = runs[get_n_best_index(1, fitnesses)[0]]

        # get the best in the current population
        best_code = best_run.model.model_code.MinBinCode

        # add the best in this_niche to the list of best
        best_runs.append(best_run)

        # get the distance of all from the best
        distance = _get_distances([best_code], all_codes)

        # get list of all < niche radius
        in_niche = (distance <= options.niche_radius)

        for i in range(len(in_niche)):
            if in_niche[i]:
                fitnesses[i] = crash_value

        # set the fitness of all in this niche to large value, so they aren't in the next search for best
        if all(x == crash_value for x in fitnesses):  # check if all are already in a niche
            break

    return [_Niche(run) for run in best_runs]


def collect_active_tokens(feature_code, tokens, template):
    active_features = set(template)
    queue = list(template)
    # logger.debug("queue: %s", queue)
  
    # Iteratively activate dependencies
    while queue:
        # Get 1st item in queue
        # logger.debug("queue while: %s", queue)
        feature = queue.pop(0)
        # logger.debug("feature: %s", feature)
  
        # Get the value of this feature from the model code
        feature_val = feature_code[feature]
        # logger.debug("feature val: %s", feature_val)
  
        # Get activated features
        features_mentioned = tokens[feature][int(feature_val)]
        # logger.debug("activated features: %s", features_mentioned)
  
        if len(features_mentioned) > 0:
            for fm in features_mentioned:
                # logger.debug("fm: %s", fm)
                if fm not in active_features:
                    # logger.debug("NOT IN")
                    active_features.add(fm)
                    queue.append(fm)
  
    # Convert active_features to list of zeroes
    active_tokens = np.zeros(len(feature_code))
    # logger.debug("active_tokens: %s", active_tokens)
  
    for token_pos in active_features:
        active_tokens[token_pos] = 1
  
    return active_tokens.astype(int)


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


def filter_active_models(test_models, active_models, template, tokens_map):

    # Loop through each binary model code
    maxes = template.gene_max
    lengths = template.gene_length
    active_tokens_list = []
    int_codes  = [] 
    for code in test_models:

        # Convert binary model code to int code
        code_full = ModelCode.from_min_binary(code, maxes, lengths)
        int_code = code_full.IntCode
        int_codes.append(int_code)

        # Get active tokens
        active_tokens = collect_active_tokens(int_code, tokens_map["tokens"], tokens_map["template"])
        active_tokens_list.append(active_tokens)
        active_tokens_np = np.vstack(active_tokens_list)

    # Generate masked code
    masked_codes = generate_masked_model_codes(int_codes, active_tokens_np)

    # Drop duplicate codes in set
    # Need to find positon of duplicates in masked codes
    # Then drop duplicates in test models list
    df = pd.DataFrame()
    df["masked_codes"] = masked_codes
    df["int_codes"] = int_codes
    df["binary_codes"] = test_models
    df = df.reset_index()
    df_unique = df.drop_duplicates("masked_codes")

    # Get list of unique model positions
    unique_model_pos = list(df_unique.index)

    # Get unique models in group
    test_models_unique = df_unique["binary_codes"]
    # test_models_unique = np.array(test_models)[unique_model_pos].tolist()

    # Get models which havn't been run yet
    # Get positions of unique suggested model codes
    new_pos = [x[0] for x in enumerate(list(df_unique["masked_codes"])) if x[1] not in active_models]

    # Create list of unique model codes which haven't been run
    df_new = df_unique.iloc[new_pos]
    # test_models_new = np.array(test_models_unique)[new_pos].tolist()
    # masked_codes_new = np.array(list(df_unique["masked_codes"]))[new_pos].tolist()

    # # Add suggested models to active_models list
    active_models.extend(list(df_new["masked_codes"]))

    return {
        "binary_codes": list(df_new["binary_codes"]), 
        "active_models": active_models}


def run_downhill(template: Template, pop: Population, tokens_map, active_models, return_all: bool = False) -> list:
    """
    Run the downhill step, with full (2 bit) search if requested.
    Finds N <= :mono_ref:`num_niches <num_niches_options_desc>` niches in pop and replaces N worst models in pop
    with best models from the niches.
    If *return_all* is true, will return a list of ALL models.
    """
    this_step = 0

    generation = pop.name
    fitnesses = [r.result.fitness for r in pop.runs]

    # while we're here, get the worst in the population, to replace them later
    worst = get_n_worst_index(options.num_niches, fitnesses)

    niches = _get_niches(pop.runs)

    all_runs = []

    for this_step in range(1, 100):     # up to 99 steps
        if all([n.done for n in niches]):
            break

        # test_models_n = []
        test_models = []
        niches_this_loop = 0

        for niche in niches:
            if niche.done:
                continue
            
            test_models_n = []
            niche.runs_start = len(test_models)

            niches_this_loop += 1

            # only need to identify niches, so we can do downhill on the best in each niche
            best_run = niche.best_run
            best_code = best_run.model.model_code.MinBinCode

            log.message(f"code for niche (minimal binary) {niches_this_loop} = {best_code},"
                        f" fitness = {best_run.result.fitness}")

            # NOTE This appears to be where models for the 1st downhill step are generated. 
            # FND
            # TODO add filtter here
            # This is where the models to test are found
            # will always be minimal binary at this point

            for this_bit in range(len(best_code)):
                # change this_bit
                test_ind = copy(best_code)  # deep copy, not reference
                test_ind[this_bit] = 1 - test_ind[this_bit]
                test_models_n.append(test_ind)
            
            log.message(f"Downhill step: {this_step}, niche: {niches_this_loop}, number of models pre-filter: {len(test_models_n)}")
            # TODO add code to filter binaries here
            out = filter_active_models(test_models_n, active_models, template, tokens_map)
            test_models_n = out["binary_codes"]
            active_models = out["active_models"]
            log.message(f"Downhill step: {this_step}, niche: {niches_this_loop}, number of downhill post-filter: {len(test_models_n)}")
            test_models.extend(test_models_n)
            niche.runs_finish = len(test_models)
        
        population = Population.from_codes(template, str(generation) + "D" + f'{this_step:02d}',
                                           test_models, ModelCode.from_min_binary)

        log.message(f"Starting downhill step {this_step},"
                    f" total of {len(population.runs)} in {niches_this_loop} niches to be run.")

        population.run()

        if not keep_going():
            break

        runs = population.runs

        if return_all:
            all_runs.extend(runs)

        # check, for each niche, whether any in the fitnesses is better
        # if so, that become the source for the next round
        # repeat until there's no better runs
        for niche in niches:
            if niche.done:
                continue

            # pull out fitness from just this niche
            niche_fitnesses = [r.result.fitness for r in runs[niche.runs_start:niche.runs_finish]]

            best_in_niche = get_n_best_index(1, niche_fitnesses)[0]

            new_best_run = runs[niche.runs_start + best_in_niche]

            if new_best_run.result.fitness < niche.best_run.result.fitness:
                niche.best_run = new_best_run
            else:
                niche.done = True

    if options.local_2_bit_search and keep_going():
        best_niche_fitnesses = [niche.best_run.result.fitness for niche in niches]
        best_niche = get_n_best_index(1, best_niche_fitnesses)[0]

        run_for_search = niches[best_niche].best_run
        last_best_fitness = run_for_search.result.fitness

        log.message(f"Begin local exhaustive 2-bit search, generation = {generation}, step = {this_step}")
        log.message(f"Model for local exhaustive search = {run_for_search.generation},"
                    f" phenotype = {run_for_search.model.phenotype} model Num = {run_for_search.model_num},"
                    f" fitness = {run_for_search.result.fitness}")

        if "search_radius" in options._options:
            search_radius = options._options["search_radius"]
        else:
            search_radius = 2
        if "duplicate_models" in options._options:
            duplicate_models = options._options["duplicate_models"]
        else:
            duplicate_models = False

        run_for_search, runs, active_models = _full_search(
            template, run_for_search, generation, template, tokens_map, 
            active_models, search_radius, duplicate_models, return_all)

        all_runs.extend(runs)

        # replace the niche this one came from, to preserve diversity
        if run_for_search.result.fitness < last_best_fitness:
            niches[best_niche].best_run = run_for_search

    for i in range(len(niches)):
        pop.runs[worst[i]] = niches[i].best_run

    return all_runs, active_models


def _change_each_bit2(source_models: list, radius: int):  # only need upper triangle, add start row here

    models = []

    # bitLength = 3
    # test = map(lambda b: n ^ (1 << b), range(bitLength))

    # bits = 8
    # flip_bits = 2 ** np.arange(bits)
    # np.bitwise_xor.outer(source_models, flip_bits) 

    for i, base_model in enumerate(source_models):

        # print("i", i)
        # print("base_model", base_model)

        base_model_neighbors = []

        models_r = [base_model]

        count = 1
        for bm in models_r:

            if count > radius:
                break

            for pos, val in enumerate(bm):
                new_val = val^1
                new_model = bm.copy()
                new_model[pos] = new_val
                models_r.append(new_model)


            count += 1
            base_model_neighbors.extend(models_r)

        models.extend(base_model_neighbors)


    models = np.unique(np.array(models), axis=0)

    return models.tolist()


def _change_each_bit3(source_models: list):  # only need upper triangle, add start row here

    models = []

    # bitLength = 3
    # test = map(lambda b: n ^ (1 << b), range(bitLength))

    # bits = 8
    # flip_bits = 2 ** np.arange(bits)
    # np.bitwise_xor.outer(source_models, flip_bits) 

    for i, base_model in enumerate(source_models):

        # print("i", i)
        # print("base_model", base_model)

        base_model_neighbors = [base_model]

        for pos, val in enumerate(base_model):
            new_val = val^1
            new_model = base_model.copy()
            new_model[pos] = new_val
            base_model_neighbors.append(new_model)

        models.extend(base_model_neighbors)


    models = np.unique(np.array(models), axis=0)

    return models.tolist()


def _change_each_bit(source_models: list, radius: int):  # only need upper triangle, add start row here
    """loop over either 1 or 2 radius 
    raised exception if radius is not 1 or 2
    if, e.g, numbits is 16, and radius is 2, the number of models is 136 (16+15+14 + ...)
    if 50 bits, then 1275 models (probably not doable??)
    arguments are:
    source_models - list o MinBinCode (not full models)
    radius - integer of both wide to search, should always be 2?
    returns:
    list of all MinBinCode and radius"""

    models = []
       
    for i in range(len(source_models)):  # only upper triangle
        base_model = source_models[i]

        for this_bit in range(i, len(base_model)):  # only need upper triangle
            new_model = copy(base_model)
            new_model[this_bit] = 1 - new_model[this_bit]

            models.append(copy(new_model))

    log.message(f"{len(models)} models in local exhaustive search, {radius} bits")

    radius += 1

    return models, radius


def _full_search(model_template: Template, best_pre: ModelRun, base_generation, template, tokens_map, active_models, search_radius, duplicate_models,  return_all: bool = False):
    """perform 2 bit search (radius should always be 2 bits), will always be called after run_downhill (1 bit search),
    argument is:
    best_pre - base model for search 
    Output:
    single best model """
    this_step = 1
    best_pre_fitness = best_pre.result.fitness
    last_best_fitness = best_pre_fitness
    current_best_fitness = best_pre_fitness
    overall_best_run = best_pre
    current_best_model = best_pre.model.model_code.MinBinCode
    current_best_model_int = best_pre.model.model_code.IntCode
    # best_pre.model.model_code.IntCode

    # # Generate masked code
    # active_tokens = collect_active_tokens(current_best_model_int, template.tokens.keys(), tokens_map)
    # # active_tokens_list.append(active_tokens)
    # active_tokens_np = np.vstack([active_tokens])

    # # Generate masked code
    # masked_codes = generate_masked_model_codes(current_best_model_int, active_tokens_np)

    all_runs = []

    while current_best_fitness < last_best_fitness or this_step == 1:  # run at least once
        full_generation = str(base_generation) + f"S{this_step:02d}"
        last_best_fitness = current_best_fitness
        radius = 2

        test_models = [current_best_model]  # start with just one, then call recursively for each radius


        if duplicate_models:
            # Generate masked code for best model
            active_tokens = collect_active_tokens(current_best_model_int, template.tokens.keys(), tokens_map)
            masked_codes = generate_masked_model_codes(current_best_model_int, np.vstack([active_tokens]))
            duplicate_models = get_duplicate_models(masked_codes[0], model_template.get_search_space_coordinates())
            duplicate_models = [list((x)) for x in duplicate_models]
            duplicate_models = np.array(duplicate_models).astype(int).tolist()
            maxes = template.gene_max
            lengths = template.gene_length
            duplicate_model_codes = [ModelCode.from_int(x, maxes, lengths) for x in duplicate_models]
            duplicate_bin_codes = [x.MinBinCode for x in duplicate_model_codes]
            test_models.extend(duplicate_bin_codes)

        # search_radius = 2
        radius = 1
        while radius <= search_radius:
            test_models = _change_each_bit(test_models, radius)
            radius += 1


        # # NOTE Want to edit radius to something larger if I can filter models
        # while radius <= search_radius:
        #     test_models, radius = _change_each_bit(test_models, radius)


        # NOTE this is where the models can be filtered
        # Want to filter test_models in a similar fashion to how previously done in local search

        log.message(f"Downhill step: {this_step} number of downhill models pre-filter: {len(test_models)}")
        out = filter_active_models(test_models, active_models, template, tokens_map)
        test_models = out["binary_codes"]
        active_models = out["active_models"]
        log.message(f"Downhill step: {this_step} number of downhill models post-filter: {len(test_models)}")

        population = Population.from_codes(model_template, full_generation, test_models, ModelCode.from_min_binary)

        population.run()

        if not keep_going():
            break

        if return_all:
            all_runs.extend(population.runs)

        best = population.get_best_run()

        current_best_fitness = best.result.fitness
        
        if current_best_fitness < last_best_fitness:
            current_best_model = best.model.model_code.MinBinCode
            current_best_model_int = best.model.model_code.IntCode

        if current_best_fitness < overall_best_run.result.fitness:
            overall_best_run = copy(best)

        this_step += 1

    return overall_best_run, all_runs, active_models


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