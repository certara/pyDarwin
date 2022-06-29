import os
import time
import traceback
from copy import copy

import darwin.GlobalVars as GlobalVars
import darwin.utils as utils

from darwin.Log import log
from darwin.options import options
from darwin.execution_man import keep_going, interrupted

from .Template import Template
from .Model import write_best_model_files
from .ModelRun import ModelRun
from .ModelCode import ModelCode
from .ModelCache import get_model_cache
from .ModelEngineAdapter import get_engine_adapter


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

    def run_all(self):
        """
        Runs the models. Always runs from integer representation, so for GA will need to convert to integer,
        for downhill, will need to convert to minimal binary, then to integer.

        ???
        all_results maybe full binary (GA) or integer (not GA) or minimal binary (downhill)

        No return value, just updates models.
        """

        self.runs[0].check_files_present()

        self._process_models()

        if not keep_going():
            log.warn('Execution has stopped')

        self.model_cache.dump()

        # write best model to output
        try:
            write_best_model_files(GlobalVars.InterimControlFile, GlobalVars.InterimResultFile)
        except:
            traceback.print_exc()

    def _process_models(self):
        pipe = _create_model_pipeline(min(len(self.runs), options.num_parallel))

        pipe.put(self.runs)

        self.runs = sorted(pipe.results(), key=lambda r: r.model_num)


def _copy_to_best(run: ModelRun):
    """
    Copies current model to the global best model.

    :param run: Run to be saved as the current best
    :type run: ModelRun
    """

    GlobalVars.BestRun = run
    GlobalVars.TimeToBest = time.time() - GlobalVars.StartTime
    GlobalVars.UniqueModelsToBest = GlobalVars.UniqueModels

    if run.source == "new":
        with open(os.path.join(run.run_dir, run.output_file_name)) as file:
            GlobalVars.BestModelOutput = file.read()  # only save best model, other models can be reproduced if needed


def _start_new_run(run: ModelRun):
    """
    Starts the model run in the run_dir.

    :param run: Model run to start
    :type run: ModelRun
    """

    if keep_going():
        if run.status == 'Not Started':
            run.run_model()  # current model is the general model type (not GA/DEAP model)

    return run


def _gather_results(runs: list):
    return runs[:4], runs[4:]


def _process_new_run(run: ModelRun):
    if run.source == 'new':
        if not interrupted():
            run.output_results()

            model_cache = get_model_cache()
            model_cache.store_model_run(run)

    res = run.result
    model = run.model

    if GlobalVars.BestRun is None or res.fitness < GlobalVars.BestRun.result.fitness:
        _copy_to_best(run)

    if interrupted():
        return run

    step_name = "Iteration"
    prd_err_text = ""

    if options.isGA:
        step_name = "Generation"

    if len(res.prd_err) > 0:
        prd_err_text = ", PRDERR = " + res.prd_err

    with open(GlobalVars.output, "a") as result_file:
        result_file.write(f"{run.run_dir},{res.fitness:.6f},{''.join(map(str, model.model_code.IntCode))},"
                          f"{res.ofv},{res.success},{res.covariance},{res.correlation},{model.theta_num},"
                          f"{model.omega_num},{model.sigma_num},{res.condition_num},{res.post_run_r_penalty},"
                          f"{res.post_run_python_penalty},{res.nm_translation_message}\n")

    fitness_crashed = res.fitness == options.crash_value
    fitness_text = f"{res.fitness:.0f}" if fitness_crashed else f"{res.fitness:.3f}"

    status = run.status.rjust(14)
    log.message(
        f"{step_name} = {run.generation}, Model {run.model_num:5}, {status},"
        f"    fitness = {fitness_text}, \t NMTRANMSG = {res.nm_translation_message.strip()}{prd_err_text}"
    )

    return run


def _create_model_pipeline(num_parallel: int) -> utils.Pipeline:
    pipe = utils.Pipeline(utils.PipelineStep(_start_new_run, size=num_parallel, name='Start model run'))\
        .link(utils.TankStep(_gather_results, tank_size=1, pipe_size=1, name='Gather run results'))\
        .link(utils.PipelineStep(_process_new_run, size=1, name='Process run results'))

    return pipe
