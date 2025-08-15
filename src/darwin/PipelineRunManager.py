import os
import time

from copy import copy

from abc import abstractmethod

from darwin.Log import log
from darwin.options import options

from .ModelRun import ModelRun, write_best_model_files, log_run
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
                ref_run = originals[run.reference_model_num]
                run.result = copy(ref_run.result)

        model_cache = get_model_cache()
        model_cache.dump()

        write_best_model_files(self.interim_control_file, self.interim_result_file)

        return runs

    @staticmethod
    def _process_run_results(run: ModelRun):
        this_one_is_better = (GlobalVars.best_run is None or run.result.fitness < GlobalVars.best_run.result.fitness) \
            and run.result.fitness != options.crash_value

        run.better = this_one_is_better

        if run.source == 'new' and run.started() and not run.is_duplicate() and not interrupted():
            run.output_results()

            if this_one_is_better:
                with open(os.path.join(run.run_dir, run.output_file_name)) as file:
                    GlobalVars.best_model_output = file.read()

            if run.rerun:
                run.keep()

            run.finish()

            # don't clean up better runs
            if not this_one_is_better or not options.keep_key_models:
                run.cleanup()

            model_cache = get_model_cache()
            model_cache.store_model_run(run)

        if interrupted() or not run.started():
            return run

        res = run.result
        model = run.model

        if run.cold:
            GlobalVars.unique_models_num += 1

        if this_one_is_better:
            _copy_to_best(run)
            run.cleanup()

        if not run.rerun:
            with open(GlobalVars.results_file, "a") as result_file:
                res_str = res.get_results_str()

                result_file.write(f"{run.generation},{run.wide_model_num},{run.run_dir},{run.ref_run},{run.status},"
                                  f"{model.theta_num},{model.omega_num},{model.sigma_num},"
                                  f"{''.join(map(str, model.model_code.IntCode))},"
                                  f"{res_str}\n")

        log_run(run)

        return run


def _copy_to_best(run: ModelRun):
    GlobalVars.best_run = run

    if run.rerun:
        return

    GlobalVars.TimeToBest = (run.finish_time or time.time()) - GlobalVars.start_time
    GlobalVars.unique_models_to_best = run.global_num
