# https://programtalk.com/python-examples/deap.tools.HallOfFame/
# deap seems to need python 3.7.3
from copy import deepcopy, copy
from datetime import timedelta
import random
import deap
from deap import base, creator, tools
import time
import logging 
import numpy as np 
from scipy.spatial import distance_matrix
import darwin.GlobalVars as GlobalVars
from darwin.Log import log
from darwin.options import options
from darwin.ModelCode import ModelCode
from darwin.run_downhill import run_downhill
from darwin.Population import Population
from darwin.Template import Template
from darwin.Model import Model, write_best_model_files
from darwin.utils import get_n_best_index, get_n_worst_index

np.warnings.filterwarnings('error', category=np.VisibleDeprecationWarning)
logger = logging.getLogger(__name__) 
   

def _sharing(distance: float, niche_radius: int, sharing_alpha: float) -> float: 
    """
    :param distance: Hamming distance (https://en.wikipedia.org/wiki/Hamming_distance) between models    
    :type distance: float
    :param niche_radius: how close to models have to be be be considered in the same niche?
    :type niche_radius:  int
    :param sharing_alpha: weighting factor for niche penalty, exponential. 1 is linear
    :type sharing_alpha: float
    :return: the sharing penalty, as a fraction of the niche radius,
     adjusted for the sharing alpha (1 - (distance/niche_radius)**sharing_alpha)
    :rtype: float
    """    
    res = 0

    if distance <= niche_radius:
        res += 1 - (distance/niche_radius)**sharing_alpha

    return res


def _add_sharing_penalty(pop, niche_radius, sharing_alpha, niche_penalty):
    """issue with negative sign, if OFV/fitness is +ive, then sharing improves it
    if OFV/fitness is negative, it makes it worse (larger)
    and penalty should be on additive scale, as OFV may cross 0
    goals are:
    keep the best individual in any niche better than the best individual in the next niche.
    all the other MAY be lower.
    so:
    - first identify which individuals are in niches.
    - then, find difference between best in this niche and best in next niche.
    - line by distance from best ( 0 for best) and worst in this niche with max niche penalty
    subtract from fitness"""
   
    for ind in zip(pop):
        dists = distance_matrix(ind, pop)[0]
        tmp = [_sharing(d, niche_radius, sharing_alpha) for d in dists]
        crowding = sum(tmp)

        # sometimes deap object fitness has values, and sometimes just a tuple?
        penalty = np.exp((crowding-1)*niche_penalty)-1

        if isinstance(ind[0].fitness, tuple):
            ind[0].fitness = (ind[0].fitness.values[0] + penalty),  # weighted values changes with this
        else: 
            ind[0].fitness.values = (ind[0].fitness.values[0] + penalty),  # weighted values changes with this

    return


def run_ga(model_template: Template) -> Model:
    """
    Run the Genetic Algorithm (GA) search, using the DEAP (https://github.com/deap/deap) packages.
    All the required information is contained in the Template objects, plus the options module
    The template objects includes the control file template, and all the token groups.

    Called from Darwin.run_search, _run_template

    :param model_template: Template object for the search

    :type model_template: Template

    :return: The single best model from the search

    :rtype: Model
    """    
    pop_size = options.population_size
    downhill_q = options.downhill_q
    elitist_num = options['elitist_num'] 
    sharing_alpha = options['sharing_alpha']
    niche_penalty = options['niche_penalty']   
    num_bits = int(np.sum(model_template.gene_length))
    
    log.message("\n\n\n\nNew Model")

    creator.create("FitnessMin", deap.base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)

    toolbox = deap.base.Toolbox()
    # Attribute generator 
    #                      define 'attr_bool' to be an attribute ('gene')
    #                      which corresponds to integers sampled uniformly
    #                      from the range [0,1] (i.e. 0 or 1 with equal
    #                      probability) 
    random.seed(options['random_seed'])
    toolbox.register("attr_bool", random.randint, 0, 1)

    # Structure initializers
    #                         define 'individual' to be an individual
    #                         consisting of 100 'attr_bool' elements ('genes')

    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, num_bits)

    # define the population to be a list of individuals
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # the goal ('fitness') function to be maximized  

    # register the crossover operator
    if options['crossoverOperator'] == "cxOnePoint":
        toolbox.register("mate", tools.cxOnePoint)

    # other cross over options here
    # register a mutation operator with a probability to
    # flip each attribute/gene of 0.05
    if options['mutate'] == "flipBit":
        toolbox.register("mutate", tools.mutFlipBit, indpb=options['attribute_mutation_probability'])

    # operator for selecting individuals for breeding the next
    # generation: each individual of the current generation
    # is replaced by the 'fittest' (best) of three individuals
    # drawn randomly from the current generation.
    if options['selection'] == "tournament":
        toolbox.register("select", tools.selTournament, tournsize=options['selection_size'])
 
    # create an initial population of pop_size individuals (where
    # each individual is a list of bits [0|1])
    pop_full_bits = toolbox.population(n=pop_size)
    best_for_elitism = toolbox.population(n=elitist_num)   
    crossover_probability = options['crossoverRate']
    mutation_probability = options['mutationRate']

    # argument to run_all is integer codes!!!!!
    maxes = model_template.gene_max
    lengths = model_template.gene_length

    first_gen = Population(model_template, 0)

    for thisFullBits, model_num in zip(pop_full_bits, range(len(pop_full_bits))):
        code = ModelCode(thisFullBits, "FullBinary", maxes, lengths)
        first_gen.add_model(code)

    first_gen.run_all()

    log.message(f"Best overall fitness = {GlobalVars.BestRun.result.fitness:4f},"
                f" iteration 0, model {GlobalVars.BestRun.model_num}")

    fitnesses = [None]*len(first_gen.runs)

    for ind, pop, fit in zip(first_gen.runs, pop_full_bits, range(len(first_gen.runs))):
        pop.fitness.values = (ind.result.fitness,)
        fitnesses[fit] = ind.result.fitness

    best_index = get_n_best_index(elitist_num, fitnesses)

    for i in range(elitist_num):  # best_index:
        best_for_elitism[i] = deepcopy(pop_full_bits[best_index[i]])

    all_best = copy(pop_full_bits[best_index[0]].fitness.values[0])

    # Variable keeping track of the number of generations
    generation = 0

    # Begin evolution

    generations_no_change = 0
    current_overall_best_fitness = options.crash_value
    log.message(f"generation 0 fitness = {all_best:.4f}")
    num_generations = options['num_generations']

    population = Population(model_template, generation)
    runs = []

    while generation < num_generations:
        # A new generation
        generation += 1
        log.message("-- Starting Generation %i --" % generation)

        # will change the values in pop, but not in fitnesses, need to run downhill from fitness values, not from pop
        # so fitnesses in pop are only used for selection in GA
        _add_sharing_penalty(pop_full_bits, options.niche_radius, sharing_alpha, niche_penalty)

        # do not copy new fitness to models, models should be just the "real" fitness
        # Select the next generation individuals
        offspring = toolbox.select(pop_full_bits, len(pop_full_bits))
        # Clone the selected individuals, otherwise will be linked to original, by reference
        offspring = list(map(toolbox.clone, offspring))

        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            # cross two individuals
            # don't need to copy child1, child2 back to offspring, done internally by DEAP
            # from https://deap.readthedocs.io/en/master/examples/ga_onemax.html
            # "In addition they modify those individuals within the toolbox container,
            # and we do not need to reassign their results.""

            if random.random() < crossover_probability:
                toolbox.mate(child1, child2)

        for mutant in offspring:
            # mutate an individual
            if random.random() < mutation_probability:
                toolbox.mutate(mutant)
                del mutant.fitness.values

        # Evaluate the individuals with an invalid fitness
        # will run entire population, but, at some point, check a database to see if already run
        pop_full_bits = offspring

        # add hof back in at first  positions, maybe should be random???
        # looks like we need to do this manually when we add in niches, can't use hof.,
        # replace worst, based on original fitness (without niche penalty)
        worst_run_indices = get_n_worst_index(elitist_num, fitnesses)

        # put elitist back in place of worst
        for i in range(elitist_num):
            pop_full_bits[worst_run_indices[i]] = copy(best_for_elitism[i])  # hof.items need the fitness as well?

        population = Population(model_template, generation)

        for thisFullBits, model_num in zip(pop_full_bits, range(len(pop_full_bits))):
            code = ModelCode(thisFullBits, "FullBinary", maxes, lengths)
            population.add_model(code)

        population.run_all()

        runs = population.runs

        log.message(f"Best overall fitness = {GlobalVars.BestRun.result.fitness:4f},"
                    f" iteration {GlobalVars.BestRun.generation}, model {GlobalVars.BestRun.model_num}")

        fitnesses = [None]*len(runs)

        for ind, pop, fit in zip(runs, pop_full_bits, range(len(runs))):
            pop.fitness.values = (ind.result.fitness,)
            fitnesses[fit] = ind.result.fitness

        best_index = get_n_best_index(elitist_num, fitnesses)

        for i in range(elitist_num):  # best_index:
            best_for_elitism[i] = deepcopy(pop_full_bits[best_index[i]])

        if generation % downhill_q == 0 and generation > 0:
            # pop will have the fitnesses without the niche penalty here
            # add local exhaustive search here??
            # temp_fitnesses = copy(fitnesses)
            # downhill with NumNiches best models
            log.message(f"Starting downhill generation = {generation}  at {time.asctime()}")

            best_index = get_n_best_index(options.num_niches, fitnesses)

            log.message(f"current best model(s) =")

            for run in map(lambda idx: runs[idx], best_index):
                log.message(f"generation {generation}, ind {run.model_num}, fitness = {run.result.fitness}")

            new_runs, worst_run_indices = run_downhill(model_template, population)

            log.message(f"Best overall fitness = {GlobalVars.BestRun.result.fitness:4f},"
                        f" iteration {GlobalVars.BestRun.generation}, model {GlobalVars.BestRun.model_num}")

            # replace worst_individuals with new_models, after hof update
            # can't figure out why sometimes returns a tuple and sometimes a scalar
            # run_downhill return on the fitness and the integer representation!!, need to make GA model from that
            # which means back calculate GA/full bit string representation
            for i in range(len(new_runs)):
                runs[worst_run_indices[i]] = copy(new_runs[i])
                fitnesses[worst_run_indices[i]] = new_runs[i].result.fitness

            best_index = get_n_best_index(elitist_num, fitnesses)

            log.message(f"Done with downhill step, {generation}. best fitness = {fitnesses[best_index[0]]}")

            # redo best_for_elitism, after downhill

            num_bits = len(runs[best_index[-1]].model.model_code.FullBinCode)

            for i in range(elitist_num):  # best_index:
                # this is GA, so need full binary code
                best_for_elitism[i][0:num_bits] = runs[best_index[i]].model.model_code.FullBinCode
                best_for_elitism[i].fitness.values = (runs[best_index[i]].result.fitness,)

        cur_gen_best_ind = get_n_best_index(1, fitnesses)[0]

        best_fitness = fitnesses[cur_gen_best_ind]

        # here expects fitnesses to be tuple, but isn't after downhill
        if not type(best_fitness) is tuple:
            best_fitness = (best_fitness,)

        log.message(f"Current generation best genome = {runs[cur_gen_best_ind].model.model_code.FullBinCode},"
                    f" best fitness = {best_fitness[0]:.4f}")

        if best_fitness[0] < current_overall_best_fitness:
            log.message(f"Better fitness found, generation = {generation}, new best fitness = {best_fitness[0]:.4f}")
            current_overall_best_fitness = best_fitness[0]
            generations_no_change = 0
        else:
            generations_no_change += 1
            log.message(f"No change in fitness for {generations_no_change} generations,"
                        f" best fitness = {current_overall_best_fitness:.4f}")

    log.message(f"-- End of GA component at {time.asctime()} --")

    # get current best individual
    cur_best_ind = get_n_best_index(1, fitnesses)[0]

    final_ga_run = runs[cur_best_ind]

    if options["final_fullExhaustiveSearch"]:
        # start with standard downhill

        population.name = 'FN'

        new_runs, worst_run_indices = run_downhill(model_template, population)

        for i in range(len(new_runs)):
            runs[worst_run_indices[i]] = copy(new_runs[i])

        best = population.get_best_run()

        log.message(f"Done with final downhill step, {generation}. best fitness = {best.result.fitness}")

    log.message(f"-- End of Optimization at {time.asctime()} --")

    best_run = GlobalVars.BestRun

    elapsed = time.time() - GlobalVars.StartTime

    log.message(f"Elapse time = " + str(timedelta(seconds=elapsed)) + "\n")
    log.message(f'Best individual GA is {str(final_ga_run.model.model_code.FullBinCode)}'
                f' with fitness of {final_ga_run.result.fitness:4f}')
    log.message(f"Best overall fitness = {best_run.result.fitness:4f},"
                f" iteration {best_run.generation}, model {best_run.model_num}")

    write_best_model_files(GlobalVars.FinalControlFile, GlobalVars.FinalResultFile)

    log.message(f"Final out from best model is in {GlobalVars.FinalResultFile}")

    return best_run.model
