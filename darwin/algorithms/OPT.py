import numpy as np
import skopt
from copy import copy
import time
import logging
import heapq
import warnings
from skopt import Optimizer

from darwin.Log import log
from darwin.options import options

import darwin.GlobalVars as GlobalVars

from darwin.ModelCode import ModelCode
from darwin.run_downhill import run_downhill
from darwin.Template import Template
from darwin.Model import Model, write_best_model_files
from darwin.runAllModels import run_all

logger = logging.getLogger(__name__)
Models = []  # will put models here to query them and not rerun models, will eventually be a MongoDB

warnings.filterwarnings("ignore", message="The objective has been evaluated ")


# run parallel? https://scikit-optimize.github.io/stable/auto_examples/parallel-optimization.html
def run_skopt(model_template: Template) -> Model:
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
    np.random.seed(options['random_seed'])
    downhill_q = options.downhill_q 
    # just get list of numbers, of len of each token group
    num_groups = []

    for token_group in model_template.tokens.values():
        numerical_group = list(range(len(token_group)))
        this_x = skopt.space.Categorical(categories=numerical_group, transform="onehot")
        num_groups.append(this_x)

    # for parallel, will need and array of N number of optimizer,  n_jobs doesn't seem to do anything
    opt = Optimizer(num_groups, n_jobs=1, base_estimator=options.algorithm)

    log.message(f"Algorithm is {options.algorithm}")

    # https://scikit-optimize.github.io/stable/auto_examples/ask-and-tell.html
    
    niter_no_change = 0
    maxes = model_template.gene_max
    lengths = model_template.gene_length

    models = []

    for this_iter in range(options['num_generations']):
        log.message(f"Starting generation/iteration {this_iter}, {options.algorithm} algorithm at {time.asctime()}")
         
        suggestion_start_time = time.time()
        # will need to ask for 1/10 of the total models if run 10  way parallel 
          
        suggested = opt.ask(n_points=options.population_size) 
        log.message("Elapse time for sampling step # %d =  %.1f seconds"
                    % (this_iter, (time.time() - suggestion_start_time)))

        models = []

        for thisInts, model_num in zip(suggested, range(len(suggested))):
            code = ModelCode(thisInts, "Int", maxes, lengths)
            models.append(Model(model_template, code, model_num, this_iter))

        run_all(models)

        fitnesses = list(map(lambda m: m.fitness, models))

        # run downhill?
        if this_iter % downhill_q == 0 and this_iter > 0: 
            # pop will have the fitnesses without the niche penalty here
            
            log.message(f"Starting downhill, iteration = {this_iter} at {time.asctime()}")

            # can only use all models in GP, not in RF or GA
            if options.algorithm == "GP":
                new_models, worst_individuals, all_models = run_downhill(models, return_all=True)
            else:
                new_models, worst_individuals = run_downhill(models, return_all=False)

            # replace worst_individuals with new_individuals, after hof update
            # can't figure out why sometimes returns a tuple and sometimes a scalar
            # run_downhill returns on the fitness and the integer representation!!, need to make GA model from that
            # which means back calculate GA/full bit string representation
            for i in range(len(new_models)):
                models[worst_individuals[i]] = copy(new_models[i])
                fitnesses[worst_individuals[i]] = new_models[i].fitness
                suggested[worst_individuals[i]] = new_models[i].model_code.IntCode

            if options.algorithm == "GP":
                log.message("add in all models to suggested and fitness for GP")

        tell_start_time = time.time()

        # I think you can tell with all models, but not sure
        opt.tell(suggested, fitnesses) 
        
        log.message("Elapse time for tell step %d =  %.1f seconds ---" % (this_iter, (time.time() - tell_start_time)))

        best_fitness = heapq.nsmallest(1, fitnesses)[0]

        best_model = GlobalVars.BestModel

        if best_fitness < best_model.fitness:
            niter_no_change = 0
        else:
            niter_no_change += 1

        log.message(f"Best fitness this iteration = {best_fitness:4f}  at {time.asctime()}")
        log.message(f"Best overall fitness = {best_model.fitness:4f},"
                    f" iteration {best_model.generation}, model {best_model.model_num}")

    if options["final_fullExhaustiveSearch"]:
        log.message(f"Starting final downhill")
        # can only use all models in GP, not in RF or GA

        for model in models:
            model.generation = "FN"

        run_downhill(models, return_all=(options.algorithm == "GP"))

    if niter_no_change:
        log.message(f'No change in fitness in {niter_no_change} iteration')

    log.message(f"total time = {(time.time() - GlobalVars.StartTime)/60:.2f} minutes")

    write_best_model_files(GlobalVars.FinalControlFile, GlobalVars.FinalResultFile)

    log.message(f"Final output from best model is in {GlobalVars.FinalResultFile}")
    log.message(f'Best overall solution =[{GlobalVars.BestModel.model_code.IntCode}],'
                f' Best overall fitness ={GlobalVars.BestModel.fitness:.6f} ')

    final_model = copy(GlobalVars.BestModel)

    return final_model
