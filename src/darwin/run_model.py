import sys

from darwin.options import options
from darwin.ExecutionManager import ExecutionManager

import darwin.nonmem.NMEngineAdapter
import darwin.nlme.NLMEEngineAdapter
from darwin.ModelEngineAdapter import get_engine_adapter

from darwin.Log import log

from .ModelRun import ModelRun, run_to_json, json_to_run


def _run_model(run: ModelRun) -> ModelRun:
    run.result = run.model_result_class()

    run.run_model()

    return run


if __name__ == '__main__':
    input_file, output_file, options_file = sys.argv[1:4]

    options.initialize(options_file)

    darwin.nonmem.NMEngineAdapter.register()
    darwin.nlme.NLMEEngineAdapter.register()

    adapter = get_engine_adapter(options.engine_adapter)

    if not adapter.init_engine():
        exit(1)

    with ExecutionManager(options.working_dir):
        run_to_json(_run_model(json_to_run(input_file)), output_file)

        log.message('Done')
