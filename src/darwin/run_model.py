import sys
import os
import json

from darwin.options import options
import darwin.NMEngineAdapter

from .Model import Model
from .ModelRun import ModelRun
from .ModelEngineAdapter import get_engine_adapter


def run_model(model: Model, engine_name) -> ModelRun:
    adapter = get_engine_adapter(engine_name)
    run = ModelRun(model, 0, 0, adapter)

    run.run_model()

    return run


if __name__ == '__main__':
    run_dir = sys.argv[1]
    json_file = sys.argv[2] if len(sys.argv) > 2 else 'model.json'
    options_file = sys.argv[3] if len(sys.argv) > 3 else 'options.json'

    if os.path.isdir(run_dir):
        os.chdir(run_dir)

    options.initialize(run_dir, options_file)

    with open(json_file) as f:
        m = json.load(f)

    r = run_model(Model.from_dict(m), options.engine_adapter)

    print(r.result.to_dict())
