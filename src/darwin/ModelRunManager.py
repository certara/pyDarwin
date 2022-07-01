import os
import time

import traceback

from abc import ABC, abstractmethod

import darwin.utils as utils

from darwin.Log import log
from darwin.options import options
from darwin.execution_man import interrupted

from .Model import write_best_model_files
from .ModelRun import ModelRun, run_to_json, json_to_run
from .ModelCache import get_model_cache

import darwin.GlobalVars as GlobalVars
from darwin.utils import Pipeline
from darwin.execution_man import keep_going

_model_run_man = None

_runs_dir = '.'


class ModelRunManager(ABC):

    @abstractmethod
    def _create_model_pipeline(self, runs: list) -> Pipeline:
        pass

    def _preprocess_runs(self, runs: list):
        pass

    def _postprocess_runs(self, runs: list):
        if not keep_going():
            log.warn('Execution has stopped')

        model_cache = get_model_cache()
        model_cache.dump()

        # write best model to output
        try:
            write_best_model_files(GlobalVars.InterimControlFile, GlobalVars.InterimResultFile)
        except:
            traceback.print_exc()

    def _process_runs(self, runs: list):
        pipe = self._create_model_pipeline(runs)

        pipe.put(runs)

        return sorted(pipe.results(), key=lambda r: r.model_num)

    def run_all(self, runs: list):
        """
        Runs the models. Always runs from integer representation, so for GA will need to convert to integer,
        for downhill, will need to convert to minimal binary, then to integer.
        """

        self._preprocess_runs(runs)

        self._process_runs(runs)

        self._postprocess_runs(runs)


class LocalRunManager(ModelRunManager):
    def _create_model_pipeline(self, runs: list) -> utils.Pipeline:
        num_parallel = min(len(runs), options.num_parallel)

        pipe = utils.Pipeline(utils.PipelineStep(_start_new_run, size=num_parallel, name='Start model run')) \
            .link(utils.PipelineStep(_process_run_results, size=1, name='Process run results'))

        return pipe


class RemoteRunManager(ModelRunManager):
    def __init__(self):
        global _runs_dir

        _runs_dir = os.path.join(options.project_dir, 'runs')

        utils.remove_dir(_runs_dir)

        if not os.path.isdir(_runs_dir):
            os.makedirs(_runs_dir)

    def _create_model_pipeline(self, runs: list) -> utils.Pipeline:
        num_parallel = min(len(runs), options.num_parallel)

        pipe = utils.Pipeline(utils.PipelineStep(_start_remote_run, size=num_parallel, name='Start model run')) \
            .link(utils.TankStep(_gather_results, tank_size=1, pipe_size=1, name='Gather run results')) \
            .link(utils.PipelineStep(_process_run_results, size=1, name='Process run results'))

        return pipe


def _start_new_run(run: ModelRun):
    """
    Starts the model run in the run_dir.

    :param run: Model run to start
    :type run: ModelRun
    """

    if run.status == 'Not Started':
        run.run_model()  # current model is the general model type (not GA/DEAP model)

    return run


def _start_remote_run(run: ModelRun):
    """
    Starts the model run remotely.

    :param run: Model run to start
    :type run: ModelRun
    """

    if run.status == 'Not Started':
        run_to_json(run, os.path.join(_runs_dir, run.file_stem + '.json'))

    return run


def _gather_results(runs: list):
    return runs[:4], runs[4:]


def _process_run_results(run: ModelRun):
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


def set_run_manager(man):
    global _model_run_man

    _model_run_man = man


def get_run_manager():
    return _model_run_man


def register():
    set_run_manager(LocalRunManager())
