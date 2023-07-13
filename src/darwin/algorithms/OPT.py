import numpy as np
import skopt
import time
import logging
import heapq
import warnings
from skopt import Optimizer

from multiprocessing import Pool
import traceback

from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import keep_going

import darwin.GlobalVars as GlobalVars

from darwin.ModelCode import ModelCode
from darwin.algorithms.run_downhill import run_downhill
from darwin.Template import Template
from darwin.Model import Model
from darwin.ModelRun import ModelRun
from darwin.Population import Population

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", message="The objective has been evaluated ")
warnings.filterwarnings("ignore", message="The optimal value found for ", append=True)


def _create_optimizer(model_template: Template, algorithm, chain_num) -> list:
    # just get list of numbers, of len of each token group
    num_groups = []

    for token_group in model_template.tokens.values():
        numerical_group = list(range(len(token_group)))
        this_x = skopt.space.Categorical(categories=numerical_group, transform="onehot")
        num_groups.append(this_x)

    # and for omega bands
    if options.search_omega_bands:
        numerical_group = list(range(options.max_omega_band_width))

        this_x = skopt.space.Categorical(categories=numerical_group, transform="onehot")
        num_groups.append(this_x)

    # and for omega submatrices
    if options.search_omega_sub_matrix:
        numerical_group = list(range(2))

        for this_m in range(options.max_omega_sub_matrix):
            this_x = skopt.space.Categorical(categories=numerical_group, transform="onehot")
            num_groups.append(this_x)

    opts = []

    for _ in range(chain_num):
        opts.append(Optimizer(num_groups, n_jobs=1, base_estimator=algorithm, random_state=np.random.randint(0, 1000)))

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


# run parallel? https://scikit-optimize.github.io/stable/auto_examples/parallel-optimization.html
def run_skopt(model_template: Template) -> ModelRun:
    """
    Run one of the scikit optimize algorithms (GP, RF, GBRT). See https://scikit-optimize.github.io/stable/.

    :param model_template: Model template to be run
    :type model_template: Template
    :return: The best model from search
    :rtype: Model
    """
    downhill_period = options.downhill_period

    if options.random_seed is not None:
        np.random.seed(options.random_seed)

    opts = _create_optimizer(model_template, options.algorithm, options.num_opt_chains)

    log.message(f"Algorithm is {options.algorithm}")

    # https://scikit-optimize.github.io/stable/auto_examples/ask-and-tell.html

    niter_no_change = 0

    population = Population(model_template, 0)

    for generation in range(1, options.num_generations + 1):
        if not keep_going():
            break

        log.message(f"Starting generation {generation}")

        suggested = _ask_models(opts, options.population_size)

        log.message(f"Done asking")

        if not keep_going():
            break

        population = Population.from_codes(model_template, generation, suggested, ModelCode.from_int,
                                           max_iteration=options.num_generations)

        population.run()

        if not keep_going():
            break

        downhill_runs = []

        # run downhill?
        if downhill_period > 0 and generation % downhill_period == 0:
            # pop will have the fitnesses without the niche penalty here

            population.runs.append(GlobalVars.BestRun)

            log.message(f"Starting downhill, iteration = {generation}")

            downhill_runs = run_downhill(model_template, population, return_all=False)

            if not keep_going():
                break

            suggested = [r.model.model_code.IntCode for r in population.runs]

        fitnesses = [r.result.fitness for r in population.runs]

        log.message(f"Tell...")

        opt = opts[0]
        opt.tell(suggested, fitnesses)

        if downhill_runs:
            opt.tell([r.model.model_code.IntCode for r in downhill_runs], [r.result.fitness for r in downhill_runs])

        opts = [opt.copy(random_state=o.rng) for o in opts]

        log.message(f"Done telling")

        best_fitness = heapq.nsmallest(1, fitnesses)[0]

        best_run = GlobalVars.BestRun

        if best_fitness < best_run.result.fitness:
            niter_no_change = 0
        else:
            niter_no_change += 1

        log.message(f"Best fitness this iteration = {best_fitness:4f}  at {time.asctime()}")
        log.message(f"Best overall fitness = {best_run.result.fitness:4f},"
                    f" iteration {best_run.generation}, model {best_run.model_num}")

    if options.final_downhill_search and keep_going():
        log.message(f"Starting final downhill")

        population.name = 'FN'

        population.runs.append(GlobalVars.BestRun)

        run_downhill(model_template, population)

    if niter_no_change:
        log.message(f'No change in fitness in {niter_no_change} iterations')

    return GlobalVars.BestRun
