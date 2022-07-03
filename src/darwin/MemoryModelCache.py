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

from .ModelCache import ModelCache, register_model_cache
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
        default_models_file = os.path.join(options.output_dir, ALL_MODELS_FILE)

        GlobalVars.SavedModelsFile = default_models_file

        utils.remove_file(default_models_file)

        prev_list = options.prev_model_list

        if options.use_prev_models and prev_list:
            try:
                models_list = Path(prev_list)

                if models_list.is_file():
                    log.message("Loading saved models...")

                    with open(models_list) as json_file:
                        loaded_runs = json.load(json_file)

                    all_runs = OrderedDict(
                        (str(r.model.genotype()), r)
                        for r in map(lambda src: ModelRun.from_dict(src), loaded_runs.values())
                    )

                    with self._lock_all_runs:
                        self.all_runs = all_runs

                    log.message(f"Using saved models from {models_list}")

                    GlobalVars.SavedModelsFile = models_list
                else:
                    log.error(f"Cannot find {models_list}")
            except:
                traceback.print_exc()
                log.error(f"Failed to load {prev_list}")

        log.message(f"Models will be saved as JSON {GlobalVars.SavedModelsFile}")

    def dump(self):
        self._dump_impl()

    def _dump_impl(self):
        with self._lock_all_runs:
            runs = {f"{r.generation}-{r.model_num}": r for r in self.all_runs.values()}

        with open(GlobalVars.SavedModelsFile, 'w', encoding='utf-8') as f:
            json.dump(runs, f, indent=4, sort_keys=True, ensure_ascii=False, cls=_ModelRunEncoder)


class AsyncMemoryModelCache(MemoryModelCache):
    def __init__(self):
        super(AsyncMemoryModelCache, self).__init__()

        self._keep_going = True

        self._something_put = False
        self._ready = threading.Condition()

        self._dumper = threading.Thread(target=self._dump_thread)
        self._dumper.start()

    def finalize(self):
        self._keep_going = False

        with self._ready:
            self._ready.notify()

        self._dumper.join()

    def _have_something(self, wait: bool) -> bool:
        with self._ready:
            if wait:
                self._ready.wait()

            if not self._something_put:
                return False

            self._something_put = False

            return True

    def _dump_thread(self):
        while self._keep_going:
            if not self._have_something(wait=True):
                break

            self._dump_impl()

        if self._have_something(wait=False):
            self._dump_impl()

    def dump(self):
        with self._ready:
            self._something_put = True
            self._ready.notify()


def register():
    register_model_cache('darwin.MemoryModelCache', MemoryModelCache)
    register_model_cache('darwin.AsyncMemoryModelCache', AsyncMemoryModelCache)
