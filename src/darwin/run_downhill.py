from copy import copy
from scipy.spatial import distance_matrix

from darwin.Log import log
from darwin.options import options
from darwin.utils import get_n_best_index, get_n_worst_index
from darwin.execution_man import keep_going

from .Template import Template
from .ModelRun import ModelRun
from .Population import Population
from .ModelCode import ModelCode


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


def run_downhill(template: Template, pop: Population):  # only return new models - best _in_niches
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
    this_step = 0

    generation = pop.name
    fitnesses = [r.result.fitness for r in pop.runs]

    # while we're here, get the worst in the population, to replace them later
    worst = get_n_worst_index(options.num_niches, fitnesses)

    niches = _get_niches(pop.runs)

    for this_step in range(100):     # up to 99 steps
        if all([n.done for n in niches]):
            break

        test_models = []
        niches_this_loop = 0

        for niche in niches:
            if niche.done:
                continue

            niche.runs_start = len(test_models)

            niches_this_loop += 1

            # only need to identify niches, so we can do downhill on the best in each niche
            best_run = niche.best_run
            best_code = best_run.model.model_code.MinBinCode

            log.message(f"code for niche (minimal binary) {niches_this_loop} = {best_code},"
                        f" fitness = {best_run.result.fitness}")

            # will always be minimal binary at this point
            for this_bit in range(len(best_code)):
                # change this_bit
                test_ind = copy(best_code)  # deep copy, not reference
                test_ind[this_bit] = 1 - test_ind[this_bit]
                test_models.append(test_ind)

            niche.runs_finish = len(test_models)

        population = Population.from_codes(template, str(generation) + "D" + str(this_step),
                                           test_models, ModelCode.from_min_binary)

        log.message(f"Starting downhill step {this_step},"
                    f" total of {len(population.runs)} in {niches_this_loop} niches to be run.")

        population.run()

        if not keep_going():
            break

        runs = population.runs

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

        run_for_search = _full_search(template, run_for_search, generation, this_step)

        # fitness should already be added to all_results here, gets added by _full_search after call to run_all GA
        # and only use the fullbest  
        # replace the niche this one came from, to preserve diversity
        if run_for_search.result.fitness < last_best_fitness:
            niches[-1].best_run = run_for_search

    for i in range(len(niches)):
        pop.runs[worst[i]] = niches[i].best_run


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


def _full_search(model_template: Template, best_pre: ModelRun, base_generation, base_step) -> ModelRun:
    """perform 2 bit search (radius should always be 2 bits), will always be called after run_downhill (1 bit search),
    argument is:
    best_pre - base model for search 
    Output:
    single best model """
    this_step = 0 
    best_pre_fitness = best_pre.result.fitness
    last_best_fitness = best_pre_fitness
    current_best_fitness = best_pre_fitness
    overall_best_run = best_pre
    current_best_model = best_pre.model.model_code.MinBinCode

    while current_best_fitness < last_best_fitness or this_step == 0:  # run at least once
        full_generation = str(base_generation) + "S" + str(base_step) + "" + str(this_step)
        last_best_fitness = current_best_fitness
        radius = 1
        test_models = [current_best_model]  # start with just one, then call recursively for each radius

        while radius <= 2:
            test_models, radius = _change_each_bit(test_models, radius)

        population = Population.from_codes(model_template, full_generation, test_models, ModelCode.from_min_binary)

        population.run()

        if not keep_going():
            break

        best = population.get_best_run()

        current_best_fitness = best.result.fitness

        if current_best_fitness < last_best_fitness:
            current_best_model = best.model.model_code.MinBinCode

        if current_best_fitness < overall_best_run.result.fitness:
            overall_best_run = copy(best)

        this_step += 1

    return overall_best_run
