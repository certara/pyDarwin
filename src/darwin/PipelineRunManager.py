import os
import time

from copy import copy

from abc import abstractmethod

import traceback

import darwin.utils as utils

from darwin.execution_man import interrupted

from darwin.Log import log
from darwin.options import options
import darwin.GenericGridManager

from .Model import write_best_model_files
from .ModelRun import ModelRun
from .ModelCache import get_model_cache
from .ModelRunManager import ModelRunManager, register_model_run_man
from .GridManager import create_grid_manager

import darwin.GlobalVars as GlobalVars
from darwin.utils import Pipeline
from darwin.execution_man import keep_going, wait_for_subprocesses


class PipelineRunManager(ModelRunManager):
    def _preprocess_runs(self, runs: list) -> list:
        return runs

    def _process_runs(self, runs: list) -> list:
        pipe = self._create_model_pipeline(runs)

        pipe.put(runs)

        return sorted(pipe.results(), key=lambda r: r.model_num)

    def _postprocess_runs(self, runs: list) -> list:
        if not keep_going():
            log.warn('Execution has stopped')

        duplicates = list(filter(lambda r: r.is_duplicate(), runs))

        if duplicates:
            originals = {r.model_num: r for r in filter(lambda r: not r.is_duplicate(), runs)}

            for run in duplicates:
                run.result = copy(originals[run.reference_model_num].result)

        model_cache = get_model_cache()
        model_cache.dump()

        # write best model to output
        try:
            write_best_model_files(GlobalVars.InterimControlFile, GlobalVars.InterimResultFile)
        except:
            traceback.print_exc()

        return runs

    @abstractmethod
    def _create_model_pipeline(self, runs: list) -> Pipeline:
        pass

    @staticmethod
    def _process_run_results(run: ModelRun):
        if run.source == 'new' and not run.is_duplicate():
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

        if len(res.errors) > 0:
            prd_err_text = ", error = " + res.errors

        with open(GlobalVars.output, "a") as result_file:
            result_file.write(f"{run.run_dir},{res.fitness:.6f},{''.join(map(str, model.model_code.IntCode))},"
                              f"{res.ofv},{res.success},{res.covariance},{res.correlation},{model.theta_num},"
                              f"{model.omega_num},{model.sigma_num},{res.condition_num},{res.post_run_r_penalty},"
                              f"{res.post_run_python_penalty},{res.messages}\n")

        fitness_crashed = res.fitness == options.crash_value
        fitness_text = f"{res.fitness:.0f}" if fitness_crashed else f"{res.fitness:.3f}"

        status = run.status.rjust(14)
        log.message(
            f"{step_name} = {run.generation}, Model {run.model_num:5}, {status},"
            f"    fitness = {fitness_text},    message = {res.messages.strip()}{prd_err_text}"
        )

        return run


class LocalRunManager(PipelineRunManager):
    def _create_model_pipeline(self, runs: list) -> utils.Pipeline:
        num_parallel = min(len(runs), options.num_parallel)

        pipe = utils.Pipeline(utils.PipelineStep(self._start_local_run, size=num_parallel, name='Start model run')) \
            .link(utils.PipelineStep(self._process_run_results, size=1, name='Process run results'))

        return pipe

    @staticmethod
    def _start_local_run(run: ModelRun):
        """
        Starts the model run in the run_dir.

        :param run: Model run to start
        :type run: ModelRun
        """

        if run.status == 'Not Started':
            run.run_model()  # current model is the general model type (not GA/DEAP model)

        return run

    @staticmethod
    def init_folders():
        ModelRunManager.init_folders()

        log.message('Preparing project temp folder...')

        if os.path.isdir(options.temp_dir) and _conflict_project_dirs():
            log.warn("Won't delete project temp folder")
            return

        utils.remove_dir(options.temp_dir)
        os.makedirs(options.temp_dir)

        log.message('Done')

    @staticmethod
    def cleanup_folders():
        if options.remove_temp_dir:
            if _conflict_project_dirs():
                log.warn("Won't delete project temp folder")
                return

            log.message('Removing project temp folder...')

            if not wait_for_subprocesses(5):
                log.warn('Not all subprocesses have been terminated yet, cannot proceed.')
                return

            try:
                utils.remove_dir(options.temp_dir)
                log.message('Done')
            except OSError:
                log.error(f"Cannot remove folder {options.temp_dir}")


class RemoteRunManager(PipelineRunManager):
    def __init__(self):
        darwin.GenericGridManager.register()

        self.grid_man = create_grid_manager(options.grid_man)

    def _start_remote_run(self, run: ModelRun):
        """
        Starts the model run remotely.

        :param run: Model run to start
        :type run: ModelRun
        """

        if run.status == 'Not Started':
            self.grid_man.add_model_run(run)

        return run

    def _gather_results(self, runs: list):
        if not keep_going():
            self.grid_man.remove_all()

            return [], []

        saved = list(filter(lambda r: r.source == 'saved', runs))
        submitted = list(filter(lambda r: r.source != 'saved', runs))

        finished, remaining = self.grid_man.poll_model_runs(submitted)

        return saved + finished, remaining

    def _create_model_pipeline(self, runs: list) -> utils.Pipeline:
        num_parallel = min(len(runs), options.num_parallel)
        p_i = int(options.get('grid_manager', {}).get('poll_interval', 10))

        pipe = utils.Pipeline(utils.PipelineStep(self._start_remote_run, size=num_parallel, name='Start model run')) \
            .link(utils.TankStep(self._gather_results, pump_interval=p_i, pipe_size=1, name='Gather run results')) \
            .link(utils.PipelineStep(self._process_run_results, size=1, name='Process run results'))

        return pipe


def _copy_to_best(run: ModelRun):
    """
    Copies current model to the global best model.

    :param run: Run to be saved as the current best
    :type run: ModelRun
    """

    GlobalVars.BestRun = run
    GlobalVars.TimeToBest = time.time() - GlobalVars.StartTime
    GlobalVars.UniqueModelsToBest = GlobalVars.UniqueModels

    if run.source == "new" and not run.is_duplicate():
        with open(os.path.join(run.run_dir, run.output_file_name)) as file:
            GlobalVars.BestModelOutput = file.read()  # only save best model, other models can be reproduced if needed


def _conflict_project_dirs() -> bool:
    if any(os.path.samefile(options.temp_dir, path)
           for path in [options.project_dir, options.data_dir, options.output_dir]):
        return True

    return False


def register():
    register_model_run_man('darwin.LocalRunManager', LocalRunManager)
    register_model_run_man('darwin.RemoteRunManager', RemoteRunManager)
