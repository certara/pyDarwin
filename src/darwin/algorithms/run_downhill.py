from copy import copy
from scipy.spatial import distance_matrix

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


def run_downhill(template: Template, pop: Population, return_all: bool = False) -> list:
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

    for this_step in range(1, 100):  # up to 99 steps
        if all([n.done for n in niches]):
            break

        test_models = []
        niches_this_loop = 0
        all_starts = []  # may need to modify for deleted models if effect_limit is used

        for niche in niches:
            if niche.done:
                continue

            niche.runs_start = len(test_models)
            # need to adjust runs_start for models deleted due > effect_limit

            niches_this_loop += 1

            # only need to identify niches, so we can do downhill on the best in each niche
            best_run = niche.best_run
            best_code = best_run.model.model_code.MinBinCode

            log.message(f"code for niche (minimal binary) {niches_this_loop} = {best_code},"
                        f" fitness = {best_run.result.fitness}, model #  {best_run.file_stem}")

            # will always be minimal binary at this point
            for this_bit in range(len(best_code)):
                # change this_bit
                test_ind = copy(best_code)  # deep copy, not reference
                test_ind[this_bit] = 1 - test_ind[this_bit]
                test_models.append(test_ind)

            niche.runs_finish = len(test_models)

            all_starts.append(niche.runs_start)

        population, new_starts = Population.from_codes(template, str(generation) + "D" + f'{this_step:02d}',
                                                       test_models, ModelCode.from_min_binary, all_starts=all_starts)

        if options.use_effect_limit:
            for this_niche in range(len(new_starts)-1):
                niches[this_niche].runs_start = new_starts[this_niche]
                niches[this_niche].runs_finish = new_starts[this_niche+1]

        log.message(f"Starting downhill step {this_step},"
                    f" total of {len(population.runs)} in {niches_this_loop} niches to be run.")

        for i in range(1, len(new_starts)):
            log.message(f"{new_starts[i] - new_starts[i - 1]} models in niche {i}")

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

            if len(niche_fitnesses) > 0:
                best_in_niche = get_n_best_index(1, niche_fitnesses)[0]
                new_best_run = runs[niche.runs_start + best_in_niche]

                if new_best_run.result.fitness < niche.best_run.result.fitness:
                    niche.best_run = new_best_run
                else:
                    niche.done = True
            else:
                niche.done = True

    if options.local_2_bit_search and keep_going():
        best_niche_fitnesses = [niche.best_run.result.fitness for niche in niches]
        best_niche = get_n_best_index(1, best_niche_fitnesses)[0]

        run_for_search = niches[best_niche].best_run
        last_best_fitness = run_for_search.result.fitness

        log.message(f"Begin local exhaustive 2-bit search, generation = {generation}, step = {this_step}")
        log.message(f"Model for local exhaustive search = {run_for_search.file_stem}, "
                    f"fitness = {run_for_search.result.fitness}")
        log.message(f"phenotype = {run_for_search.model.phenotype}")

        run_for_search, runs = _full_search(template, run_for_search, generation, return_all)

        all_runs.extend(runs)

        # replace the niche this one came from, to preserve diversity
        if run_for_search.result.fitness < last_best_fitness:
            niches[best_niche].best_run = run_for_search

        log.message(f"2-bit search, best model for step {this_step} = {run_for_search.file_stem}, "
                    f"fitness = {run_for_search.result.fitness}")

    for i in range(len(niches)):
        pop.runs[worst[i]] = niches[i].best_run

    return all_runs


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


def _full_search(model_template: Template, best_pre: ModelRun, base_generation, return_all: bool = False):
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

    all_runs = []

    while current_best_fitness < last_best_fitness or this_step == 1:  # run at least once
        full_generation = str(base_generation) + f"S{this_step:02d}"
        last_best_fitness = current_best_fitness
        radius = 1
        test_models = [current_best_model]  # start with just one, then call recursively for each radius

        while radius <= 2:
            test_models, radius = _change_each_bit(test_models, radius)

        population = Population.from_codes(model_template, full_generation, test_models, ModelCode.from_min_binary)

        population.run()

        if not keep_going():
            break

        if return_all:
            all_runs.extend(population.runs)

        best = population.get_best_run()
        log.message(f"Model for local exhaustive search = {best.file_stem}, "
                    f"fitness = {best.result.fitness}")
        current_best_fitness = best.result.fitness

        if current_best_fitness < last_best_fitness:
            current_best_model = best.model.model_code.MinBinCode

        if current_best_fitness < overall_best_run.result.fitness:
            overall_best_run = copy(best)

        this_step += 1

    return overall_best_run, all_runs
