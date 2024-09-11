import random

import numpy as np
from scipy.spatial import distance_matrix

from darwin.Log import log
import deap
from deap import base, creator, tools

from darwin.options import options

from darwin.Template import Template
from darwin.ModelRun import ModelRun
import darwin.utils as utils


class DeapToolbox:
    def __init__(self, template: Template):
        ga_options = options.GA
        self.tokens = template.tokens
        num_bits = int(np.sum(template.gene_length))
        self.gene_max = template.gene_max
        self.gene_length = template.gene_length
        creator.create("FitnessMin", deap.base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)

        toolbox = deap.base.Toolbox()
        # Attribute generator
        #                      define 'attr_bool' to be an attribute ('gene')
        #                      which corresponds to integers sampled uniformly
        #                      from the range [0,1] (i.e. 0 or 1 with equal
        #                      probability)

        if options.random_seed is not None:
            random.seed(options.random_seed)

        toolbox.register("attr_bool", random.randint, 0, 1)

        # Structure initializers
        #                         define 'individual' to be an individual
        #                         consisting of 100 'attr_bool' elements ('genes')

        toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, num_bits)

        # define the population to be a list of individuals
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        # the goal ('fitness') function to be maximized

        # register the crossover operator
        if ga_options['crossover_operator'] == "cxOnePoint":
            toolbox.register("mate", tools.cxOnePoint)

        # other cross over options here
        # register a mutation operator with a probability to
        # flip each attribute/gene of 0.05
        if ga_options['mutate'] == "flipBit":
            toolbox.register("mutate", tools.mutFlipBit, indpb=ga_options['attribute_mutation_probability'])

        # operator for selecting individuals for breeding the next
        # generation: each individual of the current generation
        # is replaced by the 'fittest' (best) of three individuals
        # drawn randomly from the current generation.
        if ga_options['selection'] == "tournament":
            toolbox.register("select", tools.selTournament, tournsize=ga_options['selection_size'])

        self.toolbox = toolbox

    def new_population(self, pop_size):
        return self.toolbox.population(n=pop_size)

    def new_population_limit(self, pop_size):
        """
        :param pop_size: How many models
        """
        # the popuation is a individuals
        # individuall is an array of ints (0|1) + a FitnessMin object
        # with properties valid (boolean), values (int) weights (tuple, -1) and wvalues (tuple, 0)
        # fitness objects consiste of
        #
        return self.toolbox.population(n=pop_size)

    def initRepeat_limit(container, func, n):
        """Call the function *func* *n* times and return the results in a
        container type `container`

        :param container: The type to put in the data from func.
        :param func: The function that will be called n times to fill the
                     container.
        :param n: The number of times to repeat func.
        :returns: An instance of the container filled with data from func.

        This helper function can be used in conjunction with a Toolbox
        to register a generator of filled containers, as individuals or
        population.

        """
        return container(func() for _ in range(n))

    def get_offspring(self, pop_full_bits):
        toolbox = self.toolbox

        ga_options = options.GA

        sharing_alpha = ga_options['sharing_alpha']
        niche_penalty = ga_options['niche_penalty']

        crossover_probability = ga_options['crossover_rate']
        mutation_probability = ga_options['mutation_rate']

        # will change the values in pop, but not in fitnesses, need to run downhill from fitness values, not from pop
        # so fitnesses in pop are only used for selection in GA
        _add_sharing_penalty(pop_full_bits, options.niche_radius, sharing_alpha, niche_penalty)

        # do not copy new fitness to models, models should be just the "real" fitness
        # Select the next generation individuals
        n_pop = 0
        count = 0
        if options.use_effect_limit:
            while n_pop < options.population_size and count < 100:
                # why does offspring return 1 more than len(pop_full_bits??)
                # offspring is list of individuals (fitness and genome)
                temp = toolbox.select(pop_full_bits, len(pop_full_bits))
                # Clone the selected individuals, otherwise will be linked to original, by reference
                temp = [toolbox.clone(x) for x in temp]
                # Apply crossover and mutation on the offspring
                for child1, child2 in zip(temp[::2], temp[1::2]):
                    if random.random() < crossover_probability and len(child1) > 1:
                        toolbox.mate(child1, child2)
                for mutant in temp:
                    # mutate an individual
                    if random.random() < mutation_probability:
                        toolbox.mutate(mutant)
                        del mutant.fitness.values
                # now check if < effect_limit
                # need integers,
                phenotype = utils.convert_full_bin_int(temp, self.gene_max,
                                                       self.gene_length)
                all_tokens = list()
                for this_ind in range(len(temp)):
                    all_tokens.append([tokens[gene] for tokens, gene in zip(self.tokens.values(), phenotype[this_ind])])
                num_effects = utils.get_pop_num_effects(all_tokens)
                good_inds = [element <= options.effect_limit for element in num_effects]
                temp = [element for element, flag in zip(temp, good_inds) if flag]
                if n_pop == 0:
                    offspring = [toolbox.clone(x) for x in temp]
                    n_pop = len(offspring)
                else:
                    temp = [toolbox.clone(x) for x in temp]
                    this_new_ind = 0
                    while n_pop < options.population_size and this_new_ind < len(temp):
                        offspring.append(temp[this_new_ind])
                        this_new_ind += 1
                        n_pop = len(offspring)
                count += 1
        else:
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

                if random.random() < crossover_probability and len(child1) > 1:
                    toolbox.mate(child1, child2)

            for mutant in offspring:
                # mutate an individual
                if random.random() < mutation_probability:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values
        if count >= 99:
            log.error(f"Not able to generate population with < {options.effect_limit} effects")
            log.error(f"effect_limit may be too small or search space (with >0 effects) too large, exiting")
            sys.exit()
            # just to check

        phenotype = utils.convert_full_bin_int(offspring, self.gene_max,
                                               self.gene_length)
        all_tokens = list()
        if options.use_effect_limit:
            for this_ind in range(len(offspring)):
                all_tokens.append([tokens[gene] for tokens, gene in zip(self.tokens.values(), phenotype[this_ind])])
            num_effects = utils.get_pop_num_effects(all_tokens)
        else:
            num_effects = None
        return offspring, num_effects


def _sharing(distance: float, niche_radius: float, sharing_alpha: float) -> float:
    """
    :param distance: Hamming distance (https://en.wikipedia.org/wiki/Hamming_distance) between models
    :type distance: float
    :param niche_radius: how close to models have to be be be considered in the same niche?
    :type niche_radius:  float
    :param sharing_alpha: weighting factor for niche penalty, exponential. 1 is linear
    :type sharing_alpha: float
    :return: the sharing penalty, as a fraction of the niche radius,
     adjusted for the sharing alpha (1 - (distance/niche_radius)**sharing_alpha)
    :rtype: float
    """
    res = 0

    if distance <= niche_radius:
        res += 1 - (distance / niche_radius) ** sharing_alpha

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
        penalty = np.exp((crowding - 1) * niche_penalty) - 1

        if isinstance(ind[0].fitness, tuple):
            ind[0].fitness = (ind[0].fitness.values[0] + penalty),  # weighted values changes with this
        else:
            ind[0].fitness.values = (ind[0].fitness.values[0] + penalty),  # weighted values changes with this


def model_run_to_deap_ind(run: ModelRun):
    res = creator.Individual(run.model.model_code.FullBinCode)
    res.fitness.setValues((run.result.fitness,))

    return res
