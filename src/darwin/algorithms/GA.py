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
from darwin.execution_man import keep_going
from darwin.ModelCode import ModelCode
from darwin.run_downhill import run_downhill
from darwin.Population import Population
from darwin.Template import Template
from darwin.Model import Model, write_best_model_files
from darwin.ModelRun import ModelRun
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


def _create_toolbox(num_bits) -> deap.base.Toolbox:
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

    return toolbox


class DeapToolbox:
    def __init__(self, template: Template):
        self.toolbox = _create_toolbox(int(np.sum(template.gene_length)))

    def new_population(self, pop_size):
        return self.toolbox.population(n=pop_size)

    def get_offspring(self, pop_full_bits):
        toolbox = self.toolbox

        sharing_alpha = options['sharing_alpha']
        niche_penalty = options['niche_penalty']

        crossover_probability = options['crossoverRate']
        mutation_probability = options['mutationRate']

        # will change the values in pop, but not in fitnesses, need to run downhill from fitness values, not from pop
        # so fitnesses in pop are only used for selection in GA
        _add_sharing_penalty(pop_full_bits, options.niche_radius, sharing_alpha, niche_penalty)

        # do not copy new fitness to models, models should be just the "real" fitness
        # Select the next generation individuals
        offspring = toolbox.select(pop_full_bits, len(pop_full_bits))
        # Clone the selected individuals, otherwise will be linked to original, by reference
        offspring = [toolbox.clone(x) for x in offspring]

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

        return offspring


def _model_run_to_deap_ind(run: ModelRun):
    res = creator.Individual(run.model.model_code.FullBinCode)
    res.fitness.setValues((run.result.fitness,))

    return res


class _GenerationRunner:
    def __init__(self, template: Template, elitist_num):
        self.generation = -1
        self.fitnesses = []
        self.template = template
        self.elitist_num = elitist_num

    def run_generation(self, pop_full_bits, best_for_elitism):
        self.generation += 1

        log.message("-- Starting Generation %i --" % self.generation)

        elitist_num = self.elitist_num

        if self.fitnesses:
            # add hof back in at first  positions, maybe should be random???
            # looks like we need to do this manually when we add in niches, can't use hof.,
            # replace worst, based on original fitness (without niche penalty)
            worst_run_indices = get_n_worst_index(elitist_num, self.fitnesses)

            # put elitist back in place of worst
            for i in range(elitist_num):
                pop_full_bits[worst_run_indices[i]] = copy(best_for_elitism[i])  # hof.items need the fitness as well?

        population = Population.from_codes(self.template, self.generation, pop_full_bits, ModelCode.from_full_binary)

        population.run_all()

        if not keep_going():
            return population, False

        runs = population.runs

        for run, pop in zip(runs, pop_full_bits):
            pop.fitness.values = (run.result.fitness,)

        self.fitnesses = [r.result.fitness for r in runs]

        best_index = get_n_best_index(elitist_num, self.fitnesses)

        for i in range(elitist_num):
            best_for_elitism[i] = deepcopy(pop_full_bits[best_index[i]])

        return population, True


def run_ga(model_template: Template) -> ModelRun:
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
    downhill_q = options.downhill_q
    elitist_num = options['elitist_num']

    pop_size = options.population_size

    toolbox = DeapToolbox(model_template)

    # create an initial population of pop_size individuals (where
    # each individual is a list of bits [0|1])
    pop_full_bits = toolbox.new_population(pop_size)
    best_for_elitism = toolbox.new_population(elitist_num)

    runner = _GenerationRunner(model_template, elitist_num)

    population, cont = runner.run_generation(pop_full_bits, best_for_elitism)

    if not cont:
        return GlobalVars.BestRun

    # Begin evolution

    generations_no_change = 0
    overall_best_fitness = options.crash_value
    num_generations = options['num_generations']

    while runner.generation < num_generations:
        pop_full_bits = toolbox.get_offspring(pop_full_bits)

        population, cont = runner.run_generation(pop_full_bits, best_for_elitism)

        if not cont:
            break

        if runner.generation % downhill_q == 0:
            # pop will have the fitnesses without the niche penalty here
            # add local exhaustive search here??
            # temp_fitnesses = copy(fitnesses)
            # downhill with NumNiches best models
            log.message(f"Starting downhill generation = {runner.generation}  at {time.asctime()}")

            best_runs = population.get_best_runs(options.num_niches)

            log.message(f"current best model(s) =")

            for run in best_runs:
                log.message(f"generation {runner.generation}, ind {run.model_num}, fitness = {run.result.fitness}")

            run_downhill(model_template, population)

            best_runs = population.get_best_runs(elitist_num)

            log.message(f"Done with downhill step, {runner.generation}. best fitness = {best_runs[0].result.fitness}")

            # redo best_for_elitism, after downhill
            best_for_elitism = [_model_run_to_deap_ind(run) for run in best_runs]

        best_run = population.get_best_run()

        best_fitness = best_run.result.fitness

        log.message(f"Current generation best genome = {best_run.model.model_code.FullBinCode},"
                    f" best fitness = {best_fitness:.4f}")

        best_run_overall = GlobalVars.BestRun

        log.message(f"Best overall fitness = {best_run_overall.result.fitness:4f},"
                    f" iteration {best_run_overall.generation}, model {best_run_overall.model_num}")

        if best_fitness < overall_best_fitness:
            log.message(f"Better fitness found, generation = {runner.generation}, new best fitness = {best_fitness:.4f}")
            overall_best_fitness = best_fitness
            generations_no_change = 0
        else:
            generations_no_change += 1
            log.message(f"No change in fitness for {generations_no_change} generations,"
                        f" best fitness = {overall_best_fitness:.4f}")

    log.message(f"-- End of GA component at {time.asctime()} --")

    final_ga_run = population.get_best_run()

    if options["final_fullExhaustiveSearch"] and keep_going():
        population.name = 'FN'

        run_downhill(model_template, population)

        best = population.get_best_run()

        log.message(f"Done with final downhill step. best fitness = {best.result.fitness}")

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

    return best_run
