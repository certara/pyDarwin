from copy import copy
from scipy.spatial import distance_matrix

from darwin.Log import log
from darwin.options import options
from darwin.utils import get_n_best_index, get_n_worst_index
from darwin.ExecutionManager import keep_going

from darwin.Template import Template
from darwin.ModelRun import ModelRun
from darwin.Population import Population, get_best_run
from darwin.ModelCode import ModelCode


def _get_distances(x, y) -> list:
    return distance_matrix(x, y)[0]


class _Niche:
    def __init__(self, best_run: ModelRun, start: int = None, finish: int = None):
        self.best_run = best_run
        self.runs_start = start
        self.runs_finish = finish
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


def _get_downhill_population(template: Template, niches: list, generation, step_num: int,
                             unique_only: bool = False) -> Population:
    test_models = []
    niches_this_loop = 0

    for niche in niches:
        if niche.done:
            continue

        niche.runs_start = len(test_models)
        # need to adjust runs_start for models deleted due > effect_limit

        niches_this_loop += 1

        # only need to identify niches, so we can do downhill on the best in each niche
        best_run = niche.best_run
        best_code = best_run.model.model_code.MinBinCode
        best_fit = best_run.result.fitness

        fitness_text = '' if best_fit == options.crash_value else f" fitness = {best_fit:.3f},"

        log.message(f"code for niche (minimal binary) {niches_this_loop} = {best_code},"
                    f"{fitness_text} model #  {best_run.file_stem}")

        # will always be minimal binary at this point
        for this_bit in range(len(best_code)):
            # change this_bit
            test_ind = copy(best_code)  # deep copy, not reference
            test_ind[this_bit] = 1 - test_ind[this_bit]
            test_models.append(test_ind)

        niche.runs_finish = len(test_models)

    population = Population.from_codes(template, str(generation) + "D" + f"{step_num:02d}",
                                       test_models, ModelCode.from_min_binary, niches=niches)

    if unique_only:
        population.runs = [run for run in population.runs if run.is_unique()]

    return population


def _get_n_params(run: ModelRun) -> int:
    res = run.result

    return res.estimated_omega_num + res.estimated_theta_num + res.estimated_sigma_num


def _get_better_runs(runs: list, best_run: ModelRun) -> list:
    u_runs = _unique_runs(runs)

    if options.isMOGA:
        if options.isMOGA3:
            best_f = best_run.result.f
            better_runs = []

            for i in range(len(best_f)):
                better = sorted([r for r in u_runs if r.result.f[i] < best_f[i]], key=lambda r: r.result.f[i])
                better_runs.extend(better[:options.max_local_grid_search_bits])
        else:
            best_ofv = best_run.result.ofv
            best_nep = _get_n_params(best_run)

            better_ofv = sorted([r for r in u_runs if r.result.ofv < best_ofv], key=lambda r: r.result.ofv)
            better_nep = sorted([r for r in u_runs if _get_n_params(r) < best_nep], key=lambda r: _get_n_params(r))

            better_runs = better_ofv[:options.max_local_grid_search_bits] \
                + better_nep[:options.max_local_grid_search_bits]
    else:
        better_runs = [r for r in u_runs if r.result.fitness < best_run.result.fitness]

        better_runs = sorted(better_runs, key=lambda r: r.result.fitness)
        better_runs = better_runs[:options.max_local_grid_search_bits]

    return better_runs


def _run_local_grid_search(runs: list, template: Template, niches: list, generation, step_num: int,
                           unique_only: bool = False) -> list:
    test_models = []

    for niche in niches:
        if niche.done:
            continue

        better_runs = _get_better_runs(runs[niche.runs_start:niche.runs_finish], niche.best_run)

        if not better_runs:
            niche.done = True
            continue

        flip_bits = sorted(list(set(_get_flip_bit(niche.best_run, r) for r in better_runs)))
        perms = [_int_to_bin(c, len(flip_bits)) for c in range(2 ** len(flip_bits))]

        niche.runs_start = len(test_models)

        for p in perms:
            new_run = niche.best_run.model.model_code.MinBinCode.copy()

            for i, b in zip(flip_bits, p):
                new_run[i] = b

            test_models.append(new_run)

        niche.runs_finish = len(test_models)

    if not test_models:
        return runs

    population = Population.from_codes(template, str(generation) + f"D{step_num:02d}G",
                                       test_models, ModelCode.from_min_binary, niches=niches)

    if unique_only:
        population.runs = [run for run in population.runs if run.is_unique()]

    if population.runs:
        niches_left = sum([not n.done for n in niches])

        log.message(f"Starting local grid search, total of {len(population.runs)} in {niches_left} niches to be run.")

        population.run()

    return population.runs


def do_moga_downhill_step(template: Template, niche_runs: list, generation, step_num: int) -> list:
    niches = [_Niche(run) for run in niche_runs]

    pop = _get_downhill_population(template, niches, generation, step_num, True)

    if not pop.runs:
        return []

    log.message(f"Starting downhill step {step_num}, total of {len(pop.runs)} in {len(niches)} niches to be run.")

    pop.run()

    runs = pop.runs

    if options.local_grid_search:
        runs += _run_local_grid_search(runs, template, niches, generation, step_num, True)

    return runs


def _unique_runs(runs: list) -> list:
    return [r for r in runs if not r.is_duplicate()]


def _get_flip_bit(r1: ModelRun, r2: ModelRun) -> int or None:
    c1 = r1.model.model_code.MinBinCode
    c2 = r2.model.model_code.MinBinCode

    for i in range(len(c1)):
        if c1[i] != c2[i]:
            return i

    return None


def _int_to_bin(n, length) -> list:
    return list(map(int, list(bin(n)[2:].rjust(length, "0"))))


def run_downhill(template: Template, pop: Population) -> list:
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
    niches_num = len(niches)

    all_runs = []

    for this_step in range(1, 100):  # up to 99 steps
        niches_left = niches_num - sum([n.done for n in niches])

        if niches_left == 0:
            break

        population = _get_downhill_population(template, niches, generation, this_step)

        log.message(f"Starting downhill step {this_step},"
                    f" total of {len(population.runs)} in {niches_left} niches to be run.")

        for i, niche in enumerate(niches):
            if not niche.done:
                log.message(f"{niche.runs_finish - niche.runs_start} models in niche {i + 1}")

        population.run()

        runs = population.runs

        if not keep_going():
            break

        if options.local_grid_search:
            runs = _run_local_grid_search(runs, template, niches, generation, this_step)

            if not keep_going():
                break

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

        run_for_search, runs = _full_search(template, run_for_search, generation)

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


def _full_search(model_template: Template, initial_best: ModelRun, base_generation):
    """perform 2 bit search (radius should always be 2 bits), will always be called after run_downhill (1 bit search),
    argument is:
    best_pre - base model for search 
    Output:
    single best model """

    overall_best = initial_best

    all_runs = []

    this_step = 1

    while True:
        full_generation = str(base_generation) + f"S{this_step:02d}"

        # start with just one, then call recursively for each radius
        test_models = [overall_best.model.model_code.MinBinCode]

        radius = 1

        log.message(f"Model for local exhaustive search = {overall_best.file_stem}, "
                    f"fitness = {overall_best.result.fitness}")

        while radius <= 2:
            test_models, radius = _change_each_bit(test_models, radius)

        population = Population.from_codes(model_template, full_generation, test_models, ModelCode.from_min_binary)

        population.run()

        if not keep_going():
            break

        runs = population.runs

        if options.local_grid_search:
            niche = _Niche(overall_best, 0, len(population.runs))
            runs = _run_local_grid_search(population.runs, model_template, [niche], full_generation, this_step)

            if not keep_going():
                break

        best = get_best_run(runs)

        best_fitness = best.result.fitness

        if best_fitness < overall_best.result.fitness:
            overall_best = copy(best)
        else:
            break

        this_step += 1

    return overall_best, all_runs
