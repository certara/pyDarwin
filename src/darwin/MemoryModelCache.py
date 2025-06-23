import os
from pathlib import Path

import json
from copy import deepcopy
from collections import OrderedDict
import threading

import darwin.utils as utils

from darwin.Log import log
from darwin.options import options

from .ModelCache import ModelCache, register_model_cache
from .ModelRun import ModelRun
from .DarwinError import DarwinError

ALL_MODELS_FILE = "models.json"


class _ModelRunEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ModelRun):
            return obj.to_dict()

        return json.JSONEncoder.default(self, obj)


class MemoryModelCache(ModelCache):
    """
    Simple Model Cache that stores model runs in a dictionary. Default option for ``pyDarwin``.
    """

    def __init__(self):
        self._lock_all_runs = threading.Lock()
        self.all_runs = OrderedDict()
        self.phenotypes = {}

        default_models_file = os.path.join(options.working_dir, ALL_MODELS_FILE)

        self.file = default_models_file

        utils.remove_file(default_models_file)

        self.sort_keys = options.get('MemoryModelCache.sort_keys', True)
        self.indent = options.get('MemoryModelCache.indent', 4)
        if self.indent == 'None':
            self.indent = None

        self.load()

    def store_model_run(self, run: ModelRun):
        with self._lock_all_runs:
            genotype = str(run.model.genotype())

            run.source = 'saved'

            self.all_runs[genotype] = run

            if run.model.phenotype not in self.phenotypes:
                self.phenotypes[run.model.phenotype] = run

    def update_model_run_status(self, run: ModelRun, status: str):
        with self._lock_all_runs:
            genotype = str(run.model.genotype())

            crun = self.all_runs[genotype] or self.phenotypes[run.model.phenotype]

            if crun is not None:
                crun.set_status(status)
                crun.run_dir = run.run_dir
                crun.model = run.model

    def find_model_run(self, **kwargs) -> ModelRun:
        if 'genotype' in kwargs:
            return deepcopy(self.all_runs.get(kwargs['genotype']))

        if 'phenotype' in kwargs:
            return deepcopy(self.phenotypes.get(kwargs['phenotype']))

        raise DarwinError('Expected genotype or phenotype')

    def load(self):
        """
        Load the cache from :mono_ref:`saved_models_file <saved_models_file_options_desc>`.
        """

        if options.use_saved_models and options.saved_models_file:
            models_list = Path(options.saved_models_file)

            log.message("Loading saved models...")

            if models_list.is_file():
                try:
                    with open(models_list, encoding='utf-8') as json_file:
                        loaded_runs = json.load(json_file)

                    all_runs = OrderedDict(
                        (str(r.model.genotype()), r)
                        for r in map(lambda src: ModelRun.from_dict(src), loaded_runs.values())
                    )

                    phenotypes = {}

                    for r in all_runs.values():
                        r.status = 'Restored'

                        if r.model.phenotype in phenotypes:
                            continue

                        phenotypes[r.model.phenotype] = r

                    with self._lock_all_runs:
                        self.all_runs = all_runs
                        self.phenotypes = phenotypes

                    if not all_runs:
                        log.warn(f"'{models_list}' is empty")
                    else:
                        log.message(f"Using saved models from '{models_list}'")

                    self.file = models_list

                except Exception as e:
                    log.error(f"Failed to load '{models_list}': {str(e)}")
            else:
                log.warn(f"'{models_list}' does not exist")

                if not options.saved_models_readonly:
                    try:
                        with open(models_list, 'w', encoding='utf-8'):
                            self.file = models_list
                    except OSError:
                        log.error(f"Cannot create '{models_list}'")

        if options.saved_models_readonly:
            log.message("Not saving any models.")
            return

        log.message(f"Models will be saved in {self.file}")

    def dump(self):
        """
        | Save cached runs to file.
        | Does nothing if :mono_ref:`saved_models_readonly <saved_models_readonly_options_desc>`
          is set to ``true``.
        """
        self._dump_impl()

    def _dump_impl(self):
        if options.saved_models_readonly:
            return

        with self._lock_all_runs:
            runs = {f"{r.file_stem}": r for r in self.all_runs.values()}

        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(runs, f, indent=self.indent, sort_keys=self.sort_keys, ensure_ascii=False, cls=_ModelRunEncoder)


class AsyncMemoryModelCache(MemoryModelCache):
    """
    | Non-blocking MemoryModelCache.
    | Dumps model runs in a separate thread so *dump* call doesn't block the search execution.
    """

    def __init__(self):
        super(AsyncMemoryModelCache, self).__init__()

        self._keep_going = True

        self._something_put = False
        self._ready = threading.Condition()

        self._dumper = threading.Thread(target=self._dump_thread)
        self._dumper.start()

    def finalize(self):
        """
        Finish the working thread and dump any unsaved model runs.
        """
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
        """
        Signal the working thread that a dump was requested.
        """
        with self._ready:
            self._something_put = True
            self._ready.notify()


def register():
    """
    :data:`Register <darwin.ModelCache.register_model_cache>`
    :data:`MemoryModelCache <darwin.MemoryModelCache.MemoryModelCache>`
    and :data:`AsyncMemoryModelCache <darwin.MemoryModelCache.AsyncMemoryModelCache>`.
    """
    register_model_cache('darwin.MemoryModelCache', MemoryModelCache)
    register_model_cache('darwin.AsyncMemoryModelCache', AsyncMemoryModelCache)
