import os
from pathlib import Path

import json
from copy import deepcopy
from collections import OrderedDict
import threading
import traceback

import darwin.GlobalVars as GlobalVars
import darwin.utils as utils

from darwin.Log import log
from darwin.options import options

from .ModelCache import ModelCache
from .ModelRun import ModelRun

ALL_MODELS_FILE = "models.json"


class _ModelRunEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ModelRun):
            return obj.to_dict()

        return json.JSONEncoder.default(self, obj)


class MemoryModelCache(ModelCache):
    def __init__(self):
        self._lock_all_runs = threading.Lock()
        self.all_runs = OrderedDict()

        self.load()

    def store_model_run(self, run: ModelRun):
        with self._lock_all_runs:
            genotype = str(run.model.genotype())

            run.source = 'saved'

            self.all_runs[genotype] = run

    def find_model_run(self, genotype: str) -> ModelRun:
        return deepcopy(self.all_runs.get(genotype))

    def load(self):
        default_models_file = os.path.join(options.home_dir, ALL_MODELS_FILE)

        GlobalVars.SavedModelsFile = default_models_file

        utils.remove_file(default_models_file)

        prev_list = options.get('PreviousModelsList', 'none')

        if options.get("usePreviousModelsList", False) and prev_list.lower() != 'none':
            try:
                models_list = Path(prev_list)

                if models_list.is_file():
                    with open(models_list) as json_file:
                        all_runs = json.load(json_file)

                        self.all_runs = OrderedDict(
                            (str(r.model.genotype()), r)
                            for r in map(lambda src: ModelRun.from_dict(src), all_runs.values())
                        )

                        log.message(f"Using Saved model list from {models_list}")

                        GlobalVars.SavedModelsFile = models_list
                else:
                    log.error(f"Cannot find {models_list}, setting models list to empty")
            except:
                traceback.print_exc()
                log.error(f"Cannot read {prev_list}, setting models list to empty")

        log.message(f"Models will be saved as JSON {GlobalVars.SavedModelsFile}")

    def dump(self):
        with open(GlobalVars.SavedModelsFile, 'w', encoding='utf-8') as f:
            runs = {f"{r.generation}-{r.model_num}": r for r in self.all_runs.values()}
            json.dump(runs, f, indent=4, sort_keys=True, ensure_ascii=False, cls=_ModelRunEncoder)
