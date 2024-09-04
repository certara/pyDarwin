import random
from copy import copy
import time
import logging
from scipy.stats import binom
from scipy.optimize import bisect
import numpy as np
import warnings
import re
import darwin.GlobalVars as GlobalVars
import random
from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import keep_going
from darwin.ModelCode import ModelCode
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
            self.pop_full_bits, all_num_effects = self.weight_pop_full_bits()
            self.num_effects = all_num_effects
        self.best_for_elitism = self.toolbox.new_population(elitist_num)

    def weight_pop_full_bits(self):
        # recalculate bits with weighted probability to constraint to total effects < effects_limit
        # it appears that the pop_full_bits.fitness can be just tuple, not the
        # full objects
        population = self.pop_full_bits
        num_effects, max_effects = self.get_num_effects()
        probabilities = self.get_probabilities(num_effects, max_effects)
        all_int_codes = dict()
        cur_ind_num_effects = 9999999
        all_num_effects = np.zeros(len(population), dtype=int)
        for this_ind in range(len(population)):
            ind_codes_as_int = np.zeros(len(self.template.tokens))
            count = 0
            while cur_ind_num_effects > options['effect_limit'] and count < 100:
                cur_ind_num_effects = 0
                cur_group = 0
                for this_group in self.template.tokens:
                    p = probabilities[this_group]
                    n_strings = len(p)
                    cur_string = np.random.choice(n_strings, 1, p=p)[0]
                    all_int_codes[this_group] = cur_string
                    ind_codes_as_int[cur_group] = cur_string
                    cur_ind_num_effects += num_effects[this_group][cur_string]
                    cur_group += 1
                count += 1
            if count > 99:
                log(f"unable to find genome with less than or equal to {this_group}")
            # once done count number with <=options['effect_limit'] effects
            # convert to bits
            # convert dict to simple array
            all_num_effects[this_ind] = cur_ind_num_effects
            bits = ModelCode.from_int(ind_codes_as_int, self.template.gene_max, self.template.gene_length).FullBinCode
            # probably can be done with zip and list comprehension?
            for this_bit, pos in zip(bits, range(len(bits))):
                population[this_ind][pos] = this_bit  # [[x, pos] for x, pos in zip(bits, range(len(bits)))]
            cur_ind_num_effects = 9999999
        return population, all_num_effects

    def get_probabilities(self, num_effects, max_effects):
        """
        param num_effects: list of number of effects in each set for each group
        param total_effects: total # of effects in all groups
        """
        # goal is probabilities such that 80% of samples have total effects <= options['effect_limit']
        # get p_per_effect for 80% good samples
        p_per_effect = bisect(self.binom_to_zero, 0, 1, args=max_effects)
        # need total effects or fewer of all groups
        # divide the probability of effects across all groups, non-zero effect set
        # divided proportional to # of effects, (e.g., if 2 effect, p(that set) = p_per_effect/2
        # dividing remaining probability among zero effect sets
        probs = dict()
        for this_group in num_effects:
            cur_group_probs = np.zeros(len(num_effects[this_group]))
            zero_sets = [i for i, value in enumerate(num_effects[this_group]) if value == 0]
            n_zero_sets = len(zero_sets)  # (x == 0 for x in zero_sets)
            non_zero_sets = [i for i, value in enumerate(num_effects[this_group]) if value > 0]
            n_non_zero_sets = len(non_zero_sets)
            if n_non_zero_sets > 0:
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

    def binom_to_zero(self, x, max_effects):
        """
        param x: value to be tested (x in binomial)
        param max_effects: p in binomial
        """
        # target fraction of samples with < effect_limit hard coded as  0.8
        p = binom.cdf(options['effect_limit'], max_effects, x)
        return p - 0.8

    def get_num_effects(self):
        """
        calculate the number of effects in each token set in each token group
        """
        num_effects = dict()
        max_effects = 0
        for this_group in self.template.tokens:
            this_max = -999
            cur_group_list = list()
            effect_token = len(self.template.tokens[this_group][0])
            for this_set in self.template.tokens[this_group]:
                value = this_set[effect_token - 1].lower()
                value = value.replace("effects", "")
                value = value.replace("effect", "")
                value = value.replace("=", "")
                try:
                    value = int(value)
                except ValueError:
                    log.error(f"The final string in token set {this_group} should be effects = n where n in a integer")
                    log.error(f"N effects for this set set to 0")
                    value = 0
                cur_group_list.append(value)
                if value > this_max:
                    this_max = value
            num_effects[this_group] = cur_group_list
            max_effects += this_max

        return num_effects, max_effects

    def reweight_bits(self):
        # calculate total effect in tokens
        # sum will be sum of maximum # in any token set across all token groups
        # set up array of how many effects in each tokens set
        # count total of max effect possible
        max_effects, n_effects = self.get_max_effects()
        # get probability per group of 1 effect, to be divided amount all with effects > 0
        all_probs = self.get_all_probs(n_effects, max_effects)
        # and randomly generate integer genome
        # new_genome = np.zeros(shape=(options['population_size'], len(self.template.tokens)),dtype=int)
        n_needed = int(options['population_size'] * 1.5)
        count = 0
        ncols = len(n_effects)
        test_genome = np.empty(shape=(0, ncols), dtype=int)
        while n_needed > 0 and count < 10:
            new_test_genome = self.get_test_genome(n_needed, n_effects, all_probs)
            test_genome = numpy.append(test_genome, new_test_genome, axis=0)
            bad_rows, num_effects = self.count_bad(n_effects, test_genome)
            test_genome = np.delete(test_genome, bad_rows, 0)
            num_effects = np.delete(num_effects, bad_rows, 0)
            n_inds, num_cols = test_genome.shape
            n_needed = int((options['population_size'] - n_inds) * 3)  # * 3 in case you only need 1 or 2 more
            count += 1

        if count >= 9:
            log.message("Cannot find adequate initial sample for size limit")

        new_genome = test_genome[:options['population_size'], ]
        num_effects = num_effects[:options['population_size'], ]
        self.num_effects = num_effects
        return new_genome

    def get_test_genome(self, n_needed, n_effects, all_probs):
        cur_group = 0
        test_genome = np.zeros(shape=(n_needed, len(self.template.tokens)), dtype=int)
        for this_group in self.template.tokens:
            cur_probs = all_probs[this_group]
            test_genome[..., cur_group] = random.choices(
                population=range(len(n_effects[this_group])),
                weights=cur_probs,
                k=n_needed)
            cur_group += 1

        return test_genome

    def count_bad(self, n_effects, new_genome):
        num_effects = np.zeros(len(new_genome), dtype=int)
        bad_rows = []
        for this_ind in range(len(new_genome)):
            ind_effects = 0
            cur_group = 0
            for this_group in n_effects:
                ind_effects += n_effects[this_group][new_genome[this_ind, cur_group]]
                cur_group += 1
            num_effects[this_ind] = int(ind_effects)
            if ind_effects > options['effect_limit']:
                bad_rows.append(this_ind)
        return bad_rows, num_effects

    def get_max_effects(self):
        max_effects = 0
        n_effects = dict()
        for this_group in self.template.tokens:
            cur_max = -999
            cur_set = 0
            n_effects_cur_set = dict()
            for this_set in self.template.tokens[this_group]:
                text = this_set[-1].lower()
                text = re.sub("(?i)effects", "", text)
                text = re.sub("(?i)effect", "", text)
                text = re.sub("(?i)=", "", text)
                val = int(text)
                n_effects_cur_set[cur_set] = val
                cur_set += 1
                if val > cur_max:
                    cur_max = val
            max_effects += cur_max
            n_effects[this_group] = n_effects_cur_set
        return max_effects, n_effects

    def cumulative_prob(self, p, n):
        return binom.cdf(options['effect_limit'], n, p) - self.target_prob

    def get_all_probs(self, n_effects, Max_effects):
        total_p_for_effects = bisect(self.cumulative_prob, 0, 1, args=Max_effects)
        total_p_for_zeros = 1 - total_p_for_effects  # rest of probability to be divided among all tokens set with 0 effects
        # get probability for sets with n_effects > 0
        # total probablility across entire set wll be prob_per_effect, divided
        # inversely proportinally to any non-zero effect, and the remaining evenly divided
        # among the 0's
        all_probs = dict()
        for this_group in self.template.tokens:
            # there is a total of prob_per_effect to disctibute
            # across all sets where effect_size > 0
            # sum of probs * number of effects should be prob_per_effect
            probs = np.zeros(len(n_effects[this_group]))
            # get total possible effect in this group, sum in n_effect
            # then divide prob_per_effect among them, with e.g., if 2 effects, only 1/2 of the value that a token
            # total_effects_this_group = sum(n_effects[this_group])
            non_zeros = [True if x > 0 else False for x in n_effects[this_group].values()]
            zeros = [True if x == 0 else False for x in n_effects[this_group].values()]
            n_non_zero = sum(non_zeros)
            n_zeros = sum(zeros)
            n_effects_per_string = [x for x, y in zip(n_effects[this_group].values(), non_zeros) if y]
            if n_non_zero > 0:
                p_per_non_zero = total_p_for_effects / sum(n_effects_per_string)
            else:
                p_per_non_zero = -999  # there aren't any effect in any sets, so doesn't matter

            probs[non_zeros] = p_per_non_zero / np.array(n_effects_per_string)
            if n_zeros > 0:
                probs[zeros] = total_p_for_zeros / n_zeros
            else:
                probs[zeros] = -999  # redo non-zeros for all prob
                p_per_non_zero = 1 / sum(n_effects_per_string)
                probs[non_zeros] = p_per_non_zero / np.array(n_effects_per_string)
            # normalize all to sum 1
            sum_prob = sum(probs)
            probs = probs / sum_prob
            all_probs[this_group] = probs
        return all_probs

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
                                                ModelCode.from_full_binary, max_iteration=self.num_generations,
                                                num_effects=self.num_effects)

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
