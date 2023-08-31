from copy import copy, deepcopy

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
    def from_codes(cls, template: Template, name, codes, code_converter, start_number=0, max_number=0, max_iteration=0):
        """
        Create a new population from a set of codes.
        """
        pop = cls(template, name, start_number, max_number or len(codes), max_iteration)

        maxes = template.gene_max
        lengths = template.gene_length

        for code in codes:
            pop.add_model_run(code_converter(code, maxes, lengths))

        return pop

    def add_model_run(self, code: ModelCode):
        """
        Create a new ModelRun and append it to *self.runs*.
        If a ModelRun with such code already exists in *self.runs*, the new one will be marked as a duplicate and
        will not be run. If the code is found in the cache, ModelRun will be restored from there and will not be run.
        """
        model = self.adapter.create_new_model(self.template, code)

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
            clone = 'Clone' if existing_run.model.genotype() == genotype else 'Twin'
            run.status = f'{clone}({run.reference_model_num})'
        elif run:
            if run.generation != self.name or run.model_num != self.model_number:
                run.result.messages = str(run.result.messages)
                run.result.ref_run = run.file_stem

            if run.status != 'Restored':
                run.status = f"Cache({run.generation}-{run.model_num})"

            run.orig_run_dir = run.run_dir
            run.init_stem(wide_model_num, self.name)

            if not run.status.startswith('Cache('):
                run1 = deepcopy(run)
                run1.status = 'not restored'
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

    def run(self):
        """
        Run the population - pass all runs to current run manager.
        There is no return value, the runs are just updated.
        """

        if not self.runs:
            raise DarwinError('Nothing to run')

        self.runs = get_run_manager().run_all(self.runs)

        if not options.keep_key_models or options.algorithm in ["EX", "EXHAUSTIVE"]:
            return

        best_run = self.get_best_run()

        if options.keep_best_models and not best_run.better:
            return

        if best_run.status == 'Restored' or best_run.status.startswith('Cache('):
            best_run.make_control_file()
            best_run.output_results()

        GlobalVars.key_models.append(best_run)

        if best_run.result.fitness > GlobalVars.best_run.result.fitness:
            best_run.rerun = True

        best_run.keep()
        best_run.cleanup()
