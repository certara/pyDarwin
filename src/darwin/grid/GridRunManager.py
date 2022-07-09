from darwin.PipelineRunManager import PipelineRunManager, register_model_run_man

import darwin.utils as utils
from darwin.options import options

from darwin.execution_man import keep_going
from darwin.ModelRun import ModelRun
import darwin.grid.GenericGridManager

from .GridManager import create_grid_manager


class GridRunManager(PipelineRunManager):
    def __init__(self):
        darwin.grid.GenericGridManager.register()

        self.grid_man = create_grid_manager(options.grid_man)

    def _start_remote_run(self, run: ModelRun):
        """
        Starts the model run remotely.

        :param run: Model run to start
        :type run: ModelRun
        """

        if not run.started() and keep_going():
            self.grid_man.add_model_run(run)

        return run

    def _gather_results(self, runs: list):
        if not keep_going():
            self.grid_man.remove_all()

            return [], []

        def is_submittable(run: ModelRun) -> bool:
            return run.source != 'saved' and not run.is_duplicate()

        saved = []
        submitted = []

        for r in runs:
            (saved, submitted)[is_submittable(r)].append(r)

        finished, remaining = self.grid_man.poll_model_runs(submitted)

        return saved + finished, remaining

    def _create_model_pipeline(self, runs: list) -> utils.Pipeline:
        num_parallel = min(len(runs), options.num_parallel)
        p_i = int(options.get('grid_manager', {}).get('poll_interval', 10))

        pipe = utils.Pipeline(utils.PipelineStep(self._start_remote_run, size=num_parallel, name='Start model run')) \
            .link(utils.TankStep(self._gather_results, pump_interval=p_i, pipe_size=1, name='Gather run results')) \
            .link(utils.PipelineStep(self._process_run_results, size=1, name='Process run results'))

        return pipe


def register():
    register_model_run_man('darwin.GridRunManager', GridRunManager)
