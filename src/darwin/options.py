import os
import sys
import json
import subprocess
import pathlib
import tempfile

from os.path import exists

from darwin.Log import log


def _get_mandatory_option(opts: dict, name, for_what=None):
    res = opts.get(name)

    if res is None:
        err = f'{name} is mandatory'

        if for_what:
            err += f' for {for_what}'

        raise RuntimeError(err)

    return res


def _calc_option(option, aliases: dict):
    if not option:
        return option

    res = str(option)

    for alias, text in aliases.items():
        res = res.replace('{' + alias + '}', text)

    return res


def _import_postprocessing(path: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location("postprocessing.module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.post_process


def _get_priority_class(opts: dict):
    if sys.platform != "win32":
        return 0

    priorities = {
        'idle': subprocess.IDLE_PRIORITY_CLASS,
        'below_normal': subprocess.BELOW_NORMAL_PRIORITY_CLASS,
        'normal': subprocess.NORMAL_PRIORITY_CLASS,
        'above_normal': subprocess.ABOVE_NORMAL_PRIORITY_CLASS,
        'high': subprocess.HIGH_PRIORITY_CLASS
    }

    priority = str(opts.get('NM_priority_class', 'normal')).lower()

    if priority not in priorities:
        priority = 'normal'

    log.message(f'NM priority is {priority}')

    return priorities[priority]


class Options:
    def __init__(self):
        self._options = {}

    def __getitem__(self, key):
        return self._options[key]

    def get(self, key, default):
        return self._options.get(key, default)

    def apply_aliases(self, text: str) -> str:
        return _calc_option(text, self.aliases)

    def _init_options(self, folder, options_file: str):
        opts = json.loads(open(options_file, 'r').read())

        self._options = opts

        self.engine_adapter = opts.get('engine_adapter', 'nonmem')
        self.model_cache_class = opts.get('model_cache', 'darwin.MemoryModelCache')
        self.model_run_man = opts.get('model_run_man', 'darwin.LocalRunManager')
        self.grid_man = opts.get('grid_man', 'darwin.GenericGridManager')

        log.message(f"Using {self.model_cache_class}")

        self.num_parallel = opts.get('num_parallel', 4)

        options_file_parent = pathlib.Path(os.path.abspath(options_file)).parent

        self.project_name = opts.get('project_name') or options_file_parent.name

        self.project_dir = str(folder or opts.get('project_dir') or options_file_parent)

        project_dir_alias = {'project_dir': self.project_dir}

        self.data_dir = _calc_option(opts.get('data_dir'), project_dir_alias) or self.project_dir
        self.output_dir = _calc_option(opts.get('output_dir'), project_dir_alias) \
            or os.path.join(self.project_dir, 'output')
        self.temp_dir = _calc_option(opts.get('temp_dir'), project_dir_alias) \
            or os.path.join(tempfile.gettempdir(), 'pydarwin', self.project_name)

        self.aliases = {
            'project_dir': self.project_dir,
            'data_dir': self.data_dir,
            'output_dir': self.output_dir,
            'temp_dir': self.temp_dir,
        }

        self.prev_model_list = _calc_option(opts.get('prev_model_list'), self.aliases)
        self.use_prev_models = opts.get('use_prev_models', False)

        self.remove_temp_dir = opts.get('remove_temp_dir', False)
        self.remove_run_dir = opts.get('remove_run_dir', False)

        self.crash_value = opts.get('crash_value', 99999999)

        self.algorithm = _get_mandatory_option(opts, 'algorithm')

        self.isGA = self.algorithm == "GA"
        self.isPSO = self.algorithm == "PSO"

        if self.algorithm in ["GA", "PSO", "GBRT", "RF", "GP"]:
            self.population_size = _get_mandatory_option(opts, 'population_size', self.algorithm)
        if self.algorithm in ["GBRT", "RF", "GP"]:
            self.num_opt_chains = _get_mandatory_option(opts, 'num_opt_chains', self.algorithm)
        if self.algorithm in ["GA", "GBRT", "RF", "GP"]:
            self.downhill_q = _get_mandatory_option(opts, 'downhill_q', self.algorithm)
            self.num_niches = _get_mandatory_option(opts, 'num_niches', self.algorithm)
            self.niche_radius = _get_mandatory_option(opts, 'niche_radius', self.algorithm)

            if self.downhill_q <= 0:
                raise RuntimeError("downhill_q value must be > 0")

        self.use_r = opts.get('useR', False)
        self.use_python = opts.get('usePython', False)

        self.nmfe_path = _get_mandatory_option(opts, 'nmfePath')

        if not exists(self.nmfe_path):
            raise RuntimeError(f"NMFE path {self.nmfe_path} seems to be missing")

        log.message(f"NMFE found at {self.nmfe_path}")

        self.model_run_priority = _get_priority_class(opts)
        self.model_run_timeout = int(opts.get('NM_timeout_sec', 1200))
        self.r_timeout = int(opts.get('R_timeout_sec', 90))

        self.search_omega_bands = opts.get('search_omega_bands', False)
        self.max_omega_band_width = opts.get('max_omega_band_width', 0)

        if self.search_omega_bands and self.max_omega_band_width < 1:
            log.warn("max_omega_band_width must be at least 1, omitting omega band width search")
            self.search_omega_bands = False

        if self.use_r:
            self.rscript_path = rscript_path = _get_mandatory_option(opts, 'RScriptPath')

            if not (os.path.isfile(self.rscript_path) or os.path.islink(self.rscript_path)):
                raise RuntimeError(f"RScriptPath doesn't exist: {self.rscript_path}")

            if not exists(rscript_path):
                raise RuntimeError(f"RScript.exe path {rscript_path} seems to be missing")

            log.message(f"RScript.exe found at {rscript_path}")

            rr = _calc_option(_get_mandatory_option(opts, 'postRunRCode'), project_dir_alias)

            self.postRunRCode = os.path.abspath(rr)

            if not exists(self.postRunRCode):
                raise RuntimeError(f"Post Run R code path {self.postRunRCode} seems to be missing")

            log.message(f"Post Run R code found at {self.postRunRCode}")
        else:
            log.message("Not using Post Run R code")

        if self.use_python:
            rp = _calc_option(_get_mandatory_option(opts, 'postRunPythonCode'), project_dir_alias)

            python_post_process_path = os.path.abspath(rp)

            if not os.path.isfile(python_post_process_path):
                raise RuntimeError(f"Post Run Python code path {python_post_process_path} seems to be missing")
            else:
                log.message(f"Post Run Python code found at {python_post_process_path}")
                self.python_post_process = _import_postprocessing(python_post_process_path)
        else:
            log.message("Not using Post Run Python code")

    def initialize(self, options_file, folder=None):
        if not os.path.exists(options_file):
            log.error(f"Couldn't find options file '{options_file}', exiting")
            sys.exit()

        try:
            self._init_options(folder, options_file)
        except Exception as error:
            log.error(str(error))
            log.error(f"Failed to parse JSON options in '{options_file}', exiting")
            sys.exit()


options = Options()
