from copy import copy, deepcopy
from collections import OrderedDict
import time
import numpy as np
from darwin.Log import log

import darwin.utils as utils
import darwin.GlobalVars as GlobalVars

from darwin.options import options

from .Template import Template
from .ModelRun import ModelRun
from .ModelCode import ModelCode
from .ModelCache import get_model_cache
from .ModelEngineAdapter import get_engine_adapter
from .ModelRunManager import get_run_manager
from .DarwinError import DarwinError


class Population:
    """
    Population of individuals (model runs).
    """

    def __init__(self, template: Template, name, start_number=0, max_number=0, max_iteration=0):
        """
        Create an empty population.

        :param name: Population name. Will be used as generation for every ModelRun added to this population.
            If an integer is specified, the name is formatted respectively to max_iteration (filled with leading
            zeroes, if needed). Otherwise, it’s just converted to a string.
        :param start_number: Starting model number of this population.
        :param max_number: Maximum model number of entire **iteration**. Used for formatting model number. Note that
            iteration may contain multiple populations (see exhaustive search).
        :param max_iteration: Maximum iteration number. Used for formatting population name.
        """
        try:
            iter_format = '{:0' + str(len(str(max_iteration))) + 'd}'
            name = iter_format.format(name)
        except ValueError:
            pass

        self.name = str(name)
        self.runs = []
        self.runs_g = {}
        self.runs_ph = {}
        self.model_number = start_number
        self.num_format = '{:0' + str(len(str(max_number))) + 'd}'
        self.template = template
        self.adapter = get_engine_adapter(options.engine_adapter)

        self.model_cache = get_model_cache()

    @classmethod
    def from_codes(cls, template: Template, name, codes, code_converter,
                   start_number=0, max_number=0, max_iteration=0, all_starts=None, num_effects=None):
        """
        Create a new population from a set of codes.
        if not downhill, have already generated good codes
        params: template - model template
        params: name - generation name
        params: codes - codes for models
        params: code_converter - bin, minimal bin or integer
        params: start_number
        params: maximum value for each gene
        params: max_iterations
        params: all_starts, array of starting positions for each niche, when doing downhill, None if not downhill
        params: num_effects, array of number of effects in each model, can be -99 if not use_effect_limit
        """

        pop = cls(template, name, start_number, max_number or len(codes), max_iteration)
        maxes = template.gene_max
        lengths = template.gene_length

        if "D" in str(name) or "F" in str(name) or "G" in str(name):  # G for local grid search
            has_niches = True
        else:
            has_niches = False

        # need to generate population of "good" models (i.e., models with < effects_limit) only if
        # this is downhill AND use_effect_limit otherwise, just return the population
        if options.use_effect_limit and has_niches and all_starts is not None:  # search will not have niches, only downhill
            num_niches = len(all_starts)  # may not be the same as i options?? when niches have been eliminated
            new_starts = np.zeros(num_niches + 1, dtype=int)  # but need one more for new_starts, as there may not be
                                                              # the full set
            cum_start = 0
            pop_int_codes = list()

            for code in codes:
                temp = code_converter(code, maxes, lengths)
                pop_int_codes.append(temp.IntCode)

            n_initial_models = len(codes)
            tokens = list()

            for this_ind in pop_int_codes:
                tokens.append([this_set[gene] for this_set, gene in zip(list(template.tokens.values()), this_ind)])

            num_effects = utils.get_pop_num_effects(tokens)
            good_inds = [element <= options.effect_limit for element in num_effects]

            # adjust new_start, subtract # of eliminated models from all_starts
            all_starts.append(len(good_inds))  # need the last value here

            for this_start in range(num_niches):
                this_niche_good_inds = good_inds[all_starts[this_start]:all_starts[this_start+1]]
                num_kept = sum(this_niche_good_inds)
                cum_start = cum_start + num_kept
                new_starts[this_start + 1] = cum_start  # first is zero

            codes = [element for element, flag in zip(codes, good_inds) if flag]

            for code, ind_num_effects in zip(codes, num_effects):
                pop.add_model_run(code_converter(code, maxes, lengths), ind_num_effects)

            log.message(f"{-(len(codes) - n_initial_models)} of {n_initial_models} "
                        f"models removed in downhill due to number of effects > {options.effect_limit}")

            return [pop, new_starts]
        else:
            # filtering for num_effects is not needed for ML step,
            # but will be for 2 bit search, not done any other place
            if options.use_effect_limit:
                pop_int_codes = list()

                for code in codes:
                    temp = code_converter(code, maxes, lengths)
                    pop_int_codes.append(temp.IntCode)

                n_initial_models = len(codes)
                tokens = list()

                for this_ind in pop_int_codes:
                    tokens.append([this_set[gene] for this_set, gene in zip(list(template.tokens.values()), this_ind)])

                num_effects = utils.get_pop_num_effects(tokens)
                good_inds = [element <= options.effect_limit for element in num_effects]
                codes = [element for element, flag in zip(codes, good_inds) if flag]

                for code, ind_num_effects in zip(codes, num_effects):
                    pop.add_model_run(code_converter(code, maxes, lengths), ind_num_effects)

                if n_initial_models - len(codes) > 0:
                    log.message(f"{n_initial_models - len(codes)} of {n_initial_models} "
                                f"models removed due to number of effects > {options.effect_limit}")
            else:
                if num_effects is None:
                    num_effects = np.ones(len(codes)) * -99

                for code, n_effects in zip(codes, num_effects):
                    pop.add_model_run(code_converter(code, maxes, lengths), n_effects)

            return pop

    def add_model_run(self, code: ModelCode, num_effects):
        """
        Create a new ModelRun and append it to *self.runs*.
        If a ModelRun with such code already exists in *self.runs*, the new one will be marked as a duplicate and
        will not be run. If the code is found in the cache, ModelRun will be restored from there and will not be run.
        """
        model = self.adapter.create_new_model(self.template, code, num_effects)

        genotype = str(model.genotype())
        phenotype = model.phenotype

        self.model_number += 1

        run = self.model_cache.find_model_run(genotype=genotype) \
              or self.model_cache.find_model_run(phenotype=phenotype)

        existing_run = self.runs_g.get(genotype, None) or self.runs_ph.get(phenotype, None)

        wide_model_num = self.num_format.format(self.model_number)

        if existing_run:
            run = copy(existing_run)
            run.model_num = self.model_number
            run.file_stem += f'_{run.model_num}'
            run.reference_model_num = existing_run.model_num
            clone = 'Clone' if str(existing_run.model.genotype()) == genotype else 'Twin'
            run.status = f'{clone}({run.reference_model_num})'
        elif run:
            if run.generation != self.name or run.model_num != self.model_number:
                run.result.messages = str(run.result.messages)
                run.result.ref_run = run.file_stem

            if run.status != 'Restored':
                run.set_status(f"Cache({run.generation}-{run.model_num})")

            run.orig_run_dir = run.run_dir
            run.init_stem(wide_model_num, self.name)

            if not run.status.startswith('Cache('):
                run1 = deepcopy(run)
                run1.set_status('not restored')
                self.model_cache.store_model_run(run1)
        else:
            run = ModelRun(model, wide_model_num, self.name, self.adapter)

        run.wide_model_num = wide_model_num

        GlobalVars.all_models_num += 1

        self.runs.append(run)

        if genotype not in self.runs_g:
            self.runs_g[genotype] = run
        if phenotype not in self.runs_ph:
            self.runs_ph[phenotype] = run

    def get_best_run(self) -> ModelRun:
        """
        Get the best run (the run with the least fitness among entire population).
        """
        fitnesses = [r.result.fitness for r in self.runs]

        best = utils.get_n_best_index(1, fitnesses)[0]

        return self.runs[best]

    def get_best_runs(self, n: int) -> list:
        """
        Get n best runs of entire population.
        """
        fitnesses = [r.result.fitness for r in self.runs]

        best = utils.get_n_best_index(n, fitnesses)

        res = [self.runs[i] for i in best]

        return res

    def run(self, remaining_models=None):
        """
        Run the population - pass all runs to current run manager.
        There is no return value, the runs are just updated.
        """

        if not self.runs:
            raise DarwinError('Nothing to run')

        if remaining_models is not None:
            remaining = remaining_models
        else:
            # at least remove current population from the list
            remaining = get_remaining_model_num(self)

        if GlobalVars.unique_models_num:
            elapsed = (time.time() - GlobalVars.start_time) / 60
            left = elapsed / GlobalVars.unique_models_num * remaining
            fuzzy = options.fuzzy_eta

            log.message(f"Time elapsed: {utils.format_time(elapsed, fuzzy)}")
            log.message(f"Estimated time remaining: {utils.format_time(left, fuzzy)}")

        self.runs = get_run_manager().run_all(self.runs)

        if not options.keep_key_models:
            return

        best_run = self.get_best_run()

        if options.keep_best_models and not best_run.better:
            return

        if best_run.status == 'Restored' or best_run.status.startswith('Cache('):
            best_run.make_control_file()
            best_run.output_results()

        GlobalVars.key_models.append(best_run)

        if GlobalVars.best_run is not None and best_run.result.fitness > GlobalVars.best_run.result.fitness:
            best_run.rerun = True

        best_run.keep()
        best_run.cleanup()


def init_pop_nums(template: Template):
    global pop_nums

    res = OrderedDict()

    if options.algorithm in ['EX', 'EXHAUSTIVE']:
        pop_nums = res
        return

    pop_size = options.population_size
    downhill_period = options.downhill_period
    x = sum(template.gene_length)

    iter_format = '{:0' + str(len(str(options.num_generations))) + 'd}'

    dn = options.get('ESTIMATED_DOWNHILL_STEPS', 5)
    sn = options.get('ESTIMATED_2BIT_STEPS', 2)

    def downhill(n: str):
        for d in range(1, dn + 1):
            res[f"{n}D{d:02d}"] = x * options.num_niches
        if options.local_2_bit_search:
            for d in range(1, sn + 1):
                res[f"{n}S{d:02d}"] = int(x * (x + 1) / 2)

    for i in range(1, options.num_generations + 1):
        name = iter_format.format(i)
        res[name] = pop_size

        if downhill_period > 0 and i % downhill_period == 0 and i > 0:
            downhill(name)

    if options.final_downhill_search:
        downhill('FN')

    log.message(f"Estimated number of models to run: {sum(res.values())}")

    pop_nums = res


pop_nums = {}


def get_remaining_model_num(pop: Population):
    global pop_nums

    if pop.name in pop_nums:
        names = list(pop_nums.keys())

        for name in names[:names.index(pop.name) + 1]:
            pop_nums.pop(name)

    return sum(pop_nums.values()) + len(pop.runs)
