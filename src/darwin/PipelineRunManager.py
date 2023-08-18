import os
import time

from copy import copy

from abc import abstractmethod

from darwin.Log import log
from darwin.options import options

from .ModelRun import ModelRun, write_best_model_files
from .ModelCache import get_model_cache
from .ModelRunManager import ModelRunManager

import darwin.GlobalVars as GlobalVars
from darwin.utils import Pipeline
from darwin.ExecutionManager import keep_going, interrupted


class PipelineRunManager(ModelRunManager):
    def __init__(self):
        self.interim_control_file = os.path.join(options.working_dir, "InterimControlFile.mod")
        self.interim_result_file = os.path.join(options.working_dir, "InterimResultFile.lst")

    @abstractmethod
    def _create_model_pipeline(self, runs: list) -> Pipeline:
        pass

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

        write_best_model_files(self.interim_control_file, self.interim_result_file)

        return runs

    @staticmethod
    def _process_run_results(run: ModelRun):
        this_one_is_better = (GlobalVars.best_run is None or run.result.fitness < GlobalVars.best_run.result.fitness) \
                             and run.result.fitness != options.crash_value

        if this_one_is_better and options.keep_key_models and run.status == 'Restored':
            run.make_control_file()
            run.output_results()

            run.keep()

        if run.source == 'new' and run.started() and not run.is_duplicate() and not interrupted():
            run.output_results()

            # cleanup may wipe entire run_dir, so need to save the output before
            if this_one_is_better:
                with open(os.path.join(run.run_dir, run.output_file_name)) as file:
                    GlobalVars.best_model_output = file.read()

                if options.keep_key_models:
                    run.keep()

            run.cleanup()

            model_cache = get_model_cache()
            model_cache.store_model_run(run)

        if interrupted() or not run.started():
            return run

        res = run.result
        model = run.model

        if run.status == 'Restored':
            GlobalVars.unique_models_num += 1

        if this_one_is_better:
            _copy_to_best(run)

        step_name = 'Iteration'
        prd_err_text = ''

        if options.isGA:
            step_name = 'Generation'

        if res.errors:
            prd_err_text = ', error = ' + res.errors

        message = res.get_message_text()

        with open(GlobalVars.results_file, "a") as result_file:
            result_file.write(f"{run.generation},{run.wide_model_num},{run.run_dir},{res.ref_run},"
                              f"{run.status},{res.fitness:.6f},{''.join(map(str, model.model_code.IntCode))},"
                              f"{res.ofv},{res.success},{res.covariance},{res.correlation},{model.theta_num},"
                              f"{model.omega_num},{model.sigma_num},{res.condition_num},{res.post_run_r_penalty},"
                              f"{res.post_run_python_penalty},{res.messages},{res.errors}\n")

        if run.status.startswith('Twin(') or run.status.startswith('Clone(') or run.status.startswith('Cache('):
            fitness_text = ''
        else:
            fitness_crashed = res.fitness == options.crash_value
            fitness_text = f"{res.fitness:.0f}" if fitness_crashed else f"{res.fitness:.3f}"

        status = run.status.rjust(14)

        log.message(
            f"{step_name} = {run.generation}, Model {run.model_num:5}, {status},"
            f"    fitness = {fitness_text:>9},    message = {message}{prd_err_text}"
        )

        return run


def _copy_to_best(run: ModelRun):
    GlobalVars.best_run = run
    GlobalVars.TimeToBest = time.time() - GlobalVars.start_time
    GlobalVars.unique_models_to_best = GlobalVars.unique_models_num
