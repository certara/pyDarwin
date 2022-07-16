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
from darwin.execution_man import keep_going

import darwin.GlobalVars as GlobalVars

from darwin.ModelCode import ModelCode
from darwin.algorithms.run_downhill import run_downhill
from darwin.Template import Template
from darwin.Model import Model
from darwin.ModelRun import ModelRun
from darwin.Population import Population

logger = logging.getLogger(__name__)
Models = []  # will put models here to query them and not rerun models, will eventually be a MongoDB

warnings.filterwarnings("ignore", message="The objective has been evaluated ")
warnings.filterwarnings("ignore", message="The optimal value found for ", append=True)


def _create_optimizer(model_template: Template, algorithm, chain_num) -> list:
    # just get list of numbers, of len of each token group
    num_groups = []

    for token_group in model_template.tokens.values():
        numerical_group = list(range(len(token_group)))
        this_x = skopt.space.Categorical(categories=numerical_group, transform="onehot")
        num_groups.append(this_x)

    opts = []

    for _ in range(chain_num):
        opts.append(Optimizer(num_groups, n_jobs=1, base_estimator=algorithm, random_state=np.random.randint(0, 1000)))

    return opts


def _opt_ask(opt: Optimizer, n_points: int) -> list:
    if not keep_going():
        return []

    try:
        return opt[0].ask(n_points)
    # if we don't catch it, pool will do it silently
    except:
        traceback.print_exc()

    return []


def _ask_models(opts: list, n_points: int) -> list:
    #n_opts = len(opts)

    #pool = Pool(n_opts)

    #n_ask = int(n_points / n_opts)
    #lens = [n_ask] * n_opts
    #lens[-1] += n_points % n_opts

    #asks = pool.starmap(_opt_ask, zip(opts, lens))
    asks = _opt_ask(opts,n_points)


    #pool.close()
    #pool.join()

    #return [x for xs in asks for x in xs]
    return asks


# run parallel? https://scikit-optimize.github.io/stable/auto_examples/parallel-optimization.html
def run_skopt(model_template: Template) -> ModelRun:
    """
    Run one of the scikit optimize (https://scikit-optimize.github.io/stable/) algorithms, specified in the options file 
    
    Called from Darwin.run_search, _run_template.
    
    Which algorithm is used is defined in the options files, with the code for the algorithms being:

    -"algorithm":"GP"

    -"algorithm":"RF"

    -"algorithm":"GBRT"

    :param model_template: Model template to be run

    :type model_template: Template

    :return: return best model from search

    :rtype: Model
    """
    downhill_period = options.downhill_period

    seed = options.get('random_seed', None)

    if seed is not None:
        np.random.seed(seed)

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

        population = Population.from_codes(model_template, generation, suggested, ModelCode.from_int)

        population.run()

        if not keep_going():
            break

        # run downhill?
        if downhill_period > 0 and generation % downhill_period == 0:
            # pop will have the fitnesses without the niche penalty here

            population.runs.append(GlobalVars.BestRun)

            log.message(f"Starting downhill, iteration = {generation}")

            run_downhill(model_template, population)

            if not keep_going():
                break

            suggested = [r.model.model_code.IntCode for r in population.runs]

        fitnesses = [r.result.fitness for r in population.runs]

        log.message(f"Tell...")

        opt = opts[0]
        opt.tell(suggested, fitnesses)

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
