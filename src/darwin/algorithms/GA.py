import sys
from copy import copy
import time
import logging
import numpy as np
import warnings
import darwin.GlobalVars as GlobalVars
import darwin.utils as utils
from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import keep_going
from darwin.algorithms.run_downhill import run_downhill
from darwin.Population import Population
from darwin.Template import Template
from darwin.Model import Model
from darwin.Model import ModelCode
from darwin.ModelRun import ModelRun
from .DeapToolbox import DeapToolbox, model_run_to_deap_ind

from scipy.stats import binom
from scipy.optimize import bisect

warnings.filterwarnings('error', category=DeprecationWarning)
logger = logging.getLogger(__name__)


def _binom_to_zero(x, max_effects):
    """
    param x: value to be tested (x in binomial)
    param max_effects: p in binomial
    """
    # target fraction of samples with < effect_limit hard coded as 0.8
    p = binom.cdf(options.effect_limit, max_effects, x)

    return p - 0.8


def _get_probabilities(num_effects, max_effects):
    """
    param num_effects: list of number of effects in each set for each group
    param total_effects: total # of effects in all groups
    """
    # goal is probabilities such that 80% of samples have total effects <= effect_limit
    # get p_per_effect for 80% good samples
    p_per_effect = bisect(_binom_to_zero, 0, 1, args=max_effects)

    # need total effects or fewer of all groups
    # divide the probability of effects across all groups, non-zero effect set
    # divided proportional to # of effects, (e.g., if 2 effect, p(that set) = p_per_effect/2
    # dividing remaining probability among zero effect sets
    probs = dict()

    for this_group in num_effects:
        cur_group_probs = np.zeros(len(num_effects[this_group]))

        zero_sets = [i for i, value in enumerate(num_effects[this_group]) if value == 0]
        non_zero_sets = [i for i, value in enumerate(num_effects[this_group]) if value > 0]

        n_zero_sets = len(zero_sets)  # (x == 0 for x in zero_sets)
        n_non_zero_sets = len(non_zero_sets)

        # non_zero_slice = tuple(slice(x) for x in non_zero_sets)
        # for each non_zero set, p(1 effect) will equal p_per_effect
        # so, if 2 effects p_per_effect/2
        for this_set in non_zero_sets:
            cur_group_probs[this_set] = p_per_effect / (n_non_zero_sets * num_effects[this_group][this_set])

        sum_non_zero_prob = sum(cur_group_probs[non_zero_sets])

        if n_zero_sets > 0:
            zero_prob = (1 - sum_non_zero_prob) / n_zero_sets
            cur_group_probs[zero_sets] = zero_prob

        # but if all set are non_zero, you're going to get one of them, so scale to sum = 1,
        # may as well scale, regardless
        cur_group_probs = cur_group_probs / sum(cur_group_probs)

        # will be integer, need to convert to bits
        probs[this_group] = cur_group_probs

    return probs


def _get_num_effects(tokens: dict):
    """
    calculate the number of effects in each token set in each token group
    Note that the num_effect count will include all token sets, including non-influential tokens
    """
    num_effects = dict()
    max_effects = 0

    for group in tokens:
        group_effects = list()

        for token_set in tokens[group]:
            value = utils.get_effects_val(token_set)

            if value < 0:
                log.error(f"The final string in token set {group} should be 'effects = n', where n >= 0. n set to 0.")
                value = 0

            group_effects.append(value)

        num_effects[group] = group_effects
        max_effects += max(group_effects)

    return num_effects, max_effects


def _weight_pop_full_bits(population, template: Template):
    # recalculate bits with weighted probability to constraint to total effects < effects_limit
    # it appears that the pop_full_bits.fitness can be just tuple, not the
    # full objects

    num_effects, max_effects = _get_num_effects(template.tokens)

    if options.effect_limit >= max_effects:
        log.error(f"Effect limit ({options.effect_limit}) is greater than the maximum possible effects ({max_effects})")
        log.error("exiting")
        sys.exit(0)

    probabilities = _get_probabilities(num_effects, max_effects)

    all_int_codes = {}

    for this_ind in range(len(population)):
        ind_codes_as_int = [0] * len(template.tokens)
        count = 0
        cur_ind_num_effects = 9999999

        while cur_ind_num_effects > options.effect_limit and count < 100:
            cur_ind_num_effects = 0
            cur_group = 0

            for this_group in template.tokens:
                p = probabilities[this_group]
                cur_string = np.random.choice(len(p), 1, p=p)[0]
                all_int_codes[this_group] = cur_string
                ind_codes_as_int[cur_group] = cur_string
                cur_ind_num_effects += num_effects[this_group][cur_string]

                cur_group += 1

            count += 1

        if count > 99:
            log.warn(f"unable to find genome with <= {options.effect_limit}")

        # once done count number with <= effect_limit effects
        # convert to bits
        # convert dict to simple array
        bits = ModelCode.from_int(ind_codes_as_int, template.gene_max, template.gene_length).FullBinCode

        # probably can be done with zip and list comprehension?
        for this_bit, pos in zip(bits, range(len(bits))):
            population[this_ind][pos] = this_bit  # [[x, pos] for x, pos in zip(bits, range(len(bits)))]

    return population


class _GARunner:
    def __init__(self, template: Template, pop_size, elitist_num, num_generations):
        self.generation = 0
        self.template = template
        self.elitist_num = elitist_num
        self.population = None
        self.num_generations = num_generations
        self.toolbox = DeapToolbox(template)
        # create an initial population of pop_size individuals (where
        # each individual is a list of bits [0|1])
        self.pop_full_bits = self.toolbox.new_population(pop_size)

        if options.use_effect_limit:
            self.pop_full_bits = _weight_pop_full_bits(self.pop_full_bits, self.template)

        self.best_for_elitism = self.toolbox.new_population(elitist_num)

    def run_generation(self):
        self.generation += 1
        if self.generation > self.num_generations or not keep_going():
            return False

        log.message(f"Starting generation {self.generation}")

        if self.generation > 1:
            self.pop_full_bits = self.toolbox.get_offspring(self.pop_full_bits)

            # replace first elitist_num individuals
            for i in range(self.elitist_num):
                self.pop_full_bits[i] = copy(self.best_for_elitism[i])

        self.population = Population.from_codes(self.template, self.generation, self.pop_full_bits,
                                                ModelCode.from_full_binary, max_iteration=self.num_generations)
        self.population.run()

        if not keep_going():
            return False

        for ind, run in zip(self.pop_full_bits, self.population.runs):
            ind.fitness.values = (run.result.fitness,)

        best_runs = self.population.get_best_runs(self.elitist_num)

        self.best_for_elitism = [model_run_to_deap_ind(run) for run in best_runs]

        return True

    def run_downhill(self, population: Population):
        """
        pop will have the fitnesses without the niche penalty here
        add local exhaustive search here??
        param: Population
        """

        log.message(f"Starting downhill generation = {self.generation}  at {time.asctime()}")

        best_runs = population.get_best_runs(options.num_niches)

        log.message(f"current best model(s) =")

        for run in best_runs:
            log.message(f"generation {self.generation}, ind {run.model_num}, fitness = {run.result.fitness}")

        run_downhill(self.template, population)

        best_runs = population.get_best_runs(self.elitist_num)

        log.message(f"Done with downhill step, {self.generation}. best fitness = {best_runs[0].result.fitness}")

        # redo best_for_elitism, after downhill
        self.best_for_elitism = [model_run_to_deap_ind(run) for run in best_runs]


def run_ga(model_template: Template) -> ModelRun:
    """
    Run the Genetic Algorithm (GA) search, using the DEAP (https://github.com/deap/deap) packages.
    The template object includes the control file template and all the token groups.

    :param model_template: Template object for the search
    :type model_template: Template
    :return: The single best model from the search
    :rtype: Model
    """
    pop_size = options.population_size
    elitist_num = options.GA['elitist_num']
    downhill_period = options.downhill_period

    runner = _GARunner(model_template, pop_size, elitist_num, options.num_generations)

    generations_no_change = 0

    # Begin evolution
    while runner.run_generation():
        population = runner.population

        if downhill_period > 0 and runner.generation % downhill_period == 0:
            runner.run_downhill(population)

        best_run = population.get_best_run()
        best_fitness = best_run.result.fitness

        log.message(f"Current generation best genome = {best_run.model.model_code.FullBinCode},"
                    f" best fitness = {best_fitness:.4f}")

        best_run_overall = GlobalVars.best_run or best_run
        overall_best_fitness = best_run_overall.result.fitness

        log.message(f"Best overall fitness = {best_run_overall.result.fitness:4f},"
                    f" iteration {best_run_overall.generation}, model {best_run_overall.model_num}")

        if best_fitness < overall_best_fitness:
            generations_no_change = 0
            log.message(f"Better fitness found, generation = {runner.generation},"
                        f" new best fitness = {best_fitness:.4f}")
        else:
            generations_no_change += 1
            log.message(f"No change in fitness for {generations_no_change} generations,"
                        f" best fitness = {overall_best_fitness:.4f}")

    log.message(f"-- End of GA component at {time.asctime()} --")

    population = runner.population

    final_ga_run = population.get_best_run()

    log.message(f'Best individual GA is {str(final_ga_run.model.model_code.FullBinCode)}'
                f' with fitness of {final_ga_run.result.fitness:4f}')

    if options.final_downhill_search and keep_going():
        population.name = 'FN'

        run_downhill(model_template, population)

        best = population.get_best_run()

        log.message(f"Done with final downhill step. best fitness = {best.result.fitness}")

    return GlobalVars.best_run
