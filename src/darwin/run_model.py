import sys
import os
import json

from darwin.options import options
from darwin.execution_man import start_execution_manager

import darwin.NMEngineAdapter

from .ModelRun import ModelRun
from .ModelResults import ModelResults


def run_model(run: ModelRun) -> ModelRun:
    run.result = ModelResults()
    run.run_model()

    return run


if __name__ == '__main__':
    run_dir = sys.argv[1]
    json_file = sys.argv[2] if len(sys.argv) > 2 else 'model_run.json'
    options_file = sys.argv[3] if len(sys.argv) > 3 else 'options.json'

    if os.path.isdir(run_dir):
        os.chdir(run_dir)

    options.initialize(run_dir, options_file)

    darwin.NMEngineAdapter.register()

    start_execution_manager()

    with open(json_file) as f:
        m = json.load(f)

    r = run_model(ModelRun.from_dict(m))

    print(r.result.to_dict())
