import sys

from darwin.options import options
from darwin.execution_man import start_execution_manager

import darwin.nonmem.NMEngineAdapter

from darwin.Log import log

from .ModelRun import ModelRun, run_to_json, json_to_run
from .ModelResults import ModelResults


def run_model(run: ModelRun) -> ModelRun:
    run.result = ModelResults()

    run.run_model()

    return run


if __name__ == '__main__':
    input_file, output_file, options_file = sys.argv[1:4]

    options.initialize(options_file)

    darwin.nonmem.NMEngineAdapter.register()

    start_execution_manager()

    run_to_json(run_model(json_to_run(input_file)), output_file)

    log.message('Done')
