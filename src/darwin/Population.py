from copy import copy

import darwin.utils as utils

from darwin.options import options

from .Template import Template
from .ModelRun import ModelRun
from .ModelCode import ModelCode
from .ModelCache import get_model_cache
from .ModelEngineAdapter import get_engine_adapter
from .ModelRunManager import get_run_manager


class Population:

    def __init__(self, template: Template, name, start_number=0):
        self.name = str(name)
        self.runs = []
        self.model_number = start_number
        self.template = template
        self.adapter = get_engine_adapter(options.engine_adapter)

        self.model_cache = get_model_cache()

    @classmethod
    def from_codes(cls, template: Template, name, codes, code_converter, start_number=0):
        pop = cls(template, name, start_number)

        maxes = template.gene_max
        lengths = template.gene_length

        for code in codes:
            pop.add_model_run(code_converter(code, maxes, lengths))

        return pop

    def add_model_run(self, code: ModelCode):
        model = self.adapter.create_new_model(self.template, code)

        genotype = str(model.genotype())

        self.model_number += 1

        run = self.model_cache.find_model_run(genotype)
        existing_runs = list(filter(lambda r: str(r.model.genotype()) == genotype, self.runs))

        if existing_runs:
            run = copy(existing_runs[0])
            run.status = 'Duplicate'
        elif run:
            run.model_num = self.model_number
            run.generation = self.name
            run.result.nm_translation_message = f"From saved model {run.control_file_name}: " \
                                                + run.result.nm_translation_message
        else:
            run = ModelRun(model, self.model_number, self.name, self.adapter)

        self.runs.append(run)

    def get_best_run(self) -> ModelRun:
        fitnesses = [r.result.fitness for r in self.runs]

        best = utils.get_n_best_index(1, fitnesses)[0]

        return self.runs[best]

    def get_best_runs(self, n: int) -> list:
        fitnesses = [r.result.fitness for r in self.runs]

        best = utils.get_n_best_index(n, fitnesses)

        res = [self.runs[i] for i in best]

        return res

    def run(self):
        """
        Runs the models. Always runs from integer representation, so for GA will need to convert to integer,
        for downhill, will need to convert to minimal binary, then to integer.

        No return value, just updates models.
        """
        self.runs = get_run_manager().run_all(self.runs)
