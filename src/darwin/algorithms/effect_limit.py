import sys

import numpy as np

from scipy.stats import binom
from scipy.optimize import bisect

from darwin.options import options
from darwin.Log import log

from darwin.Template import Template
from darwin.Model import ModelCode


def _get_effects_val(token_set: list) -> int:
    value = token_set[-1].lower()
    value = value.replace("effects", "")
    value = value.replace("effect", "")
    value = value.replace("=", "")

    try:
        value = int(value)
    except ValueError:
        value = -1

    return value


def _get_num_effects(tokens: dict):
    """
    calculate the number of effects in each token set in each token group
    Note that the num_effect count will include all token sets, including non-influential tokens
    """
    num_effects = dict()
    max_effects = 0

    if options.use_effect_limit:
        for group in tokens:
            group_effects = list()

            for token_set in tokens[group]:
                value = _get_effects_val(token_set)

                if value < 0:
                    log.error(f"The final string in token set {group} should be 'effects = n', where n >= 0. n set to 0.")
                    value = 0

                group_effects.append(value)

            num_effects[group] = group_effects
            max_effects += max(group_effects)

        if options.effect_limit >= max_effects:
            log.error(f"Effect limit ({options.effect_limit}) is greater than the maximum possible effects ({max_effects})")
            log.error("exiting")
            sys.exit(0)

    return num_effects, max_effects


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


class WeightedSampler:
    def __init__(self, template: Template):
        self.tokens = template.tokens
        self.gene_max = template.gene_max
        self.gene_length = template.gene_length

        self.zero_ind = [0] * len(self.tokens)

        self.num_effects, max_effect = _get_num_effects(template.tokens)
        self.probabilities = _get_probabilities(self.num_effects, max_effect)

    def create_individual(self) -> list:
        ind_codes_as_int = self.zero_ind.copy()
        count = 0

        while count < 100:
            count += 1

            cur_ind_num_effects = 0
            cur_group = 0

            for this_group in self.tokens:
                p = self.probabilities[this_group]
                cur_string = np.random.choice(len(p), 1, p=p)[0]
                ind_codes_as_int[cur_group] = cur_string
                cur_ind_num_effects += self.num_effects[this_group][cur_string]

                cur_group += 1

            if cur_ind_num_effects <= options.effect_limit:
                break

        if count > 99:
            log.warn(f"unable to find genome with <= {options.effect_limit}")

        bits = ModelCode.from_int(ind_codes_as_int, self.gene_max, self.gene_length).FullBinCode

        return bits


def get_pop_num_effects(phenotype: list, all_tokens: list) -> list:
    num_effects = []

    tokens = list()

    for this_ind in phenotype:
        tokens.append([tok_set[gene] for tok_set, gene in zip(all_tokens, this_ind)])

    for individual in tokens:
        cur_n_effects = 0

        for token_set in individual:
            value = _get_effects_val(token_set)

            if value > 0:
                cur_n_effects += value

        num_effects.append(cur_n_effects)

    return num_effects


def trim_population(population: list, phenotype: list, all_tokens: list, effect_limit: int):
    num_effects = get_pop_num_effects(phenotype, all_tokens)
    good_individuals = [element <= effect_limit for element in num_effects]

    population = [element for element, flag in zip(population, good_individuals) if flag]

    return population, num_effects, good_individuals
