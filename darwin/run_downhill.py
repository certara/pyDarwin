import numpy as np
from copy import copy
from scipy.spatial import distance_matrix

from darwin.Log import log
from darwin.options import options
from darwin.utils import get_n_best_index, get_n_worst_index

from .Model import Model
from .runAllModels import run_all
from .ModelCode import ModelCode


def _get_distances(x, y) -> list:
    return distance_matrix(x, y)[0]


def _get_best_in_niche(pop: list):
    """find the best in each of num_niches, return the full model
    argument is pop - list of full models
    return value is list of models, of length num_niches"""

    crash_value = options.crash_value
    fitnesses = list(map(lambda m: m.fitness, pop))
    all_codes = list(map(lambda m: m.model_code.MinBinCode, pop))
    best = []  # hold the best in each niche
    best_fitnesses = [] 
    best_models = []
    not_in_niche = [True]*len(fitnesses) 

    for _ in range(options.num_niches):
        # below should exclude those already in a niche, as  the fitness should be set to 999999
        this_best = get_n_best_index(1, fitnesses)[0]

        # get the best in the current population
        cur_ind = copy(pop[this_best].model_code.MinBinCode)
        cur_fitness = pop[this_best].fitness

        # add the best in this_niche to the list of best
        best.append(cur_ind)
        best_fitnesses.append(cur_fitness) 
        best_models.append(pop[this_best])

        # get the distance of all from the best
        distance = _get_distances([cur_ind], all_codes)

        # get list of all < niche radius
        in_niche = (distance <= options.niche_radius)

        for i in range(len(in_niche)):
            if in_niche[i]:
                not_in_niche[i] = False
                fitnesses[i] = crash_value

        # set the fitness of all in this niche to large value, so they aren't in the next search for best
        if all(x == crash_value for x in fitnesses):  # check if all are already in a niche
            break

    return best, best_fitnesses, best_models


def run_downhill(pop: list, return_all=False):  # only return new models - best _in_niches
    """
    Run the downhill step, with full (2 bit) search if requested,
    arguments a population of full models
    return value is list of length num_niches full models after search 
    if return_all is true, will also return a list of ALL models
    to be used in GP only, to update the distribution, not helpful in other algorithms
    arguments are the current population of models
    and whether to return all models (not implemented, maybe can be used for GP??)
    return is the single best model, the worst models (length num_niches) +/- the entire list of models
    """
    generation = pop[0].generation
    template = pop[0].template
    this_step = 0
    fitnesses = list(map(lambda m: m.fitness, pop))
    done = [False]*options.num_niches
    best_min_binary, best_fitnesses, best_models_in_niches = _get_best_in_niche(pop)

    # may be less than num_niches
    current_num_niches = len(best_min_binary)
    last_niche = current_num_niches

    # while we're here, get the worst in the population, to replace them later
    worst = get_n_worst_index(options.num_niches, fitnesses)

    while not all(done) and this_step < 100:     # up to 99 steps
        test_models = [] 
        which_niche = []
        niches_this_loop = 0
        for this_niche in range(current_num_niches):
            if not done[this_niche]:  
                niches_this_loop += 1

                # only need to identify niches, so we can do downhill on the best in each niche
                cur_ind = copy(best_min_binary[this_niche])  # just code, no fitness

                log.message(f"code for niche (minimal binary) {this_niche} = {cur_ind},"
                            f" fitness = {best_fitnesses[this_niche]}")

                # will always be minimal binary at this point
                for this_bit in range(len(cur_ind)):
                    which_niche.append(this_niche)
                    # change this_bit
                    test_ind = copy(cur_ind)  # deep copy, not reference
                    test_ind[this_bit] = 1 - test_ind[this_bit]
                    test_models.append(test_ind)
                    # and run test_ind
                # and run all of them

        # need to create models
        models = []
        maxes = template.gene_max
        lengths = template.gene_length

        for thisMinBits, model_num in zip(test_models, range(len(test_models))):
            code = ModelCode(thisMinBits, "MinBinary", maxes, lengths)
            models.append(Model(template, code, model_num, str(generation) + "D" + str(this_step)))

        if len(models) > 0:
            log.message(f"Starting downhill step {this_step},"
                        f" total of {len(models)} in {niches_this_loop} niches to be run.")

            run_all(models)

            # check, for each niche, if any in the fitnesses is better, if so, that become the source for the next round
            # repeat until no more better (all(done))      
            for this_niche in range(current_num_niches):
                # check if any niches are done
                if not done[this_niche]:
                    # pull out fitness from just this niche
                    this_niche_indices = np.array([i for i, x in enumerate(which_niche) if x == this_niche])
                    cur_niche_fitnesses = [models[i].fitness for i in this_niche_indices]
                    new_best_in_niche = get_n_best_index(1, cur_niche_fitnesses)[0]
                    new_best_model_num = this_niche_indices[new_best_in_niche]

                    # create grid of all better than previous best for local search
                    if models[new_best_model_num].fitness < best_fitnesses[this_niche]:
                        best_min_binary[this_niche] = copy(models[new_best_model_num].model_code.MinBinCode)
                        best_models_in_niches[this_niche] = copy(models[new_best_model_num])
                        best_fitnesses[this_niche] = models[new_best_model_num].fitness

                        done[this_niche] = False
                    else:
                        done[this_niche] = True
        else:
            done = [True]*len(done)

        this_step += 1

    # best_in_niches is just minimal binary at this point

    if options["fullExhaustiveSearch_qdownhill"]:
        best_model_index = get_n_best_index(1, best_fitnesses)[0]
        model_for_search = copy(best_models_in_niches[best_model_index])
        last_best_fitness = model_for_search.fitness

        log.message(f"Begin local exhaustive search, search radius = {options.niche_radius},"
                    f" generation = {generation},step = {this_step}")
        log.message(f"Model for local exhaustive search = {model_for_search.generation},"
                    f" phenotype = {model_for_search.phenotype} model Num = {model_for_search.model_num},"
                    f" fitness = {model_for_search.fitness}")

        model_for_search = _full_search(model_for_search, generation, (this_step - 1))

        # fitness should already be added to all_results here, gets added by _full_search after call to run_all GA
        # and only use the fullbest  
        # replace the niche this one came from, to preserve diversity
        if model_for_search.fitness < last_best_fitness:
            best_models_in_niches[last_niche] = copy(model_for_search)

    if return_all:
        return best_models_in_niches, worst, -999  # returning all models not  yet implemented
    else:
        return best_models_in_niches, worst


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
    # get MinBinCode list
    # may be just 1 or a list 
    if type(source_models[0]) == int:
        base_models = source_models
        num_base_models = 1
    else: 
        base_models = []
        num_base_models = len(source_models[0])
        for i in range(len(source_models)):
            base_models.append(source_models[i])
              
    if radius > 2 or radius < 1 or not isinstance(radius, int):
        raise Exception('radius for full local search must be 1 or 2')

    radius += 1
    models = []
       
    for base_model_num in range(num_base_models):  # only upper triangle
        if num_base_models == 1:
            this_base_model = copy(base_models)
        else:
            this_base_model = copy(base_models[base_model_num]) 

        for this_bit in range(base_model_num, len(this_base_model)):  # only need upper triangle
            new_model = copy(this_base_model) 
            new_model[this_bit] = 1 - new_model[this_bit]

            models.append(copy(new_model))

    log.message(f"{len(models)} models in local exhaustive search, {radius-1} bits")

    return models, radius


def _full_search(best_pre: Model, base_generation, base_step) -> Model:
    """perform 2 bit search (radius should always be 2 bits), will always be called after run_downhill (1 bit search),
    argument is:
    best_pre - base model for search 
    Output:
    single best model """
    this_step = 0 
    best_pre_fitness = best_pre.fitness
    model_template = best_pre.template
    last_best_fitness = best_pre_fitness
    current_best_fitness = best_pre_fitness
    overall_best_model = best_pre
    current_best_model = best_pre.model_code.MinBinCode
    niche_radius = options.niche_radius

    while current_best_fitness < last_best_fitness or this_step == 0:  # run at least once
        full_generation = str(base_generation) + "S" + str(base_step) + "" + str(this_step)
        last_best_fitness = current_best_fitness
        radius = 1
        test_models = current_best_model  # start with just one, then call recursively for each radius

        while radius <= niche_radius:
            test_models, radius = _change_each_bit(test_models, radius)

        models = []

        maxes = model_template.gene_max
        lengths = model_template.gene_length

        for thisMinBits, model_num in zip(test_models, range(len(test_models))):
            code = ModelCode(thisMinBits, "MinBinary", maxes, lengths) 
            models.append(
                Model(model_template, code, model_num, full_generation))

        run_all(models)

        fitnesses = list(map(lambda m: m.fitness, models))

        best = get_n_best_index(1, fitnesses)[0]

        current_best_fitness = fitnesses[best]

        if current_best_fitness < last_best_fitness:
            current_best_model = models[best].model_code.MinBinCode
            current_best_fitness = models[best].fitness

        if current_best_fitness < overall_best_model.fitness:
            overall_best_model = copy(models[best])

        this_step += 1

    return overall_best_model
