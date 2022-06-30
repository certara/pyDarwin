import sys
import os

from darwin.options import options
from darwin.execution_man import start_execution_manager

import darwin.NMEngineAdapter

from .ModelRun import ModelRun, run_to_json, json_to_run
from .ModelResults import ModelResults


def run_model(run: ModelRun) -> ModelRun:
    run.result = ModelResults()
    run.run_model()

    return run


if __name__ == '__main__':
    json_file = sys.argv[1]
    options_file = sys.argv[2] if len(sys.argv) > 2 else 'options.json'

    options.initialize(options_file)

    darwin.NMEngineAdapter.register()

    start_execution_manager()

    r = run_model(json_to_run(json_file))

    run_to_json(r, os.path.join(options.home_dir, 'results', r.file_stem + '.json'))
