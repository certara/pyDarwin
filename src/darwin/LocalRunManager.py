import os

import darwin.utils as utils

from darwin.Log import log
from darwin.options import options

from .ModelRun import ModelRun

from .ModelRunManager import ModelRunManager, register_model_run_man
from .PipelineRunManager import PipelineRunManager

from darwin.ExecutionManager import keep_going, wait_for_subprocesses


class LocalRunManager(PipelineRunManager):
    def _create_model_pipeline(self, runs: list) -> utils.Pipeline:
        num_parallel = min(len(runs) or 1, options.num_parallel)

        pipe = utils.Pipeline(utils.PipelineStep(self._start_local_run, size=num_parallel, name='Start model run')) \
            .link(utils.PipelineStep(self._process_run_results, size=1, name='Process run results'))

        return pipe

    @staticmethod
    def _start_local_run(run: ModelRun) -> ModelRun:
        """
        Starts the model run in the run_dir.

        :param run: Model run to start
        :type run: ModelRun
        """

        if not run.started() and keep_going():
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

        utils.remove_dir(options.key_models_dir)

        if options.keep_key_models:
            os.makedirs(options.key_models_dir, exist_ok=True)

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


def _conflict_project_dirs() -> bool:
    if any(os.path.samefile(options.temp_dir, path)
           for path in [options.project_dir, options.working_dir, options.data_dir, options.output_dir]):
        return True

    return False


def register():
    register_model_run_man('darwin.LocalRunManager', LocalRunManager)
