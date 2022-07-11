import os
import sys
import re
import json
import subprocess
import pathlib

import darwin.utils as utils

from darwin.Log import log

_default_penalty = {
    'THETA': 10,
    'OMEGA': 10,
    'SIGMA': 10,
    'convergence': 100,
    'covariance': 100,
    'correlation': 100,
    'conditionNumber': 100,
    'non_influential_tokens': 0.00001
}

_default_GA = {
    'crossoverRate': 0.95,
    'elitist_num': 4,
    'mutationRate': 0.95,
    'attribute_mutation_probability': 0.1,
    'mutate': 'flipBit',
    'niche_penalty': 20,
    'selection': 'tournament',
    'selection_size': 2,
    'sharing_alpha': 0.1,
    'crossoverOperator': 'cxOnePoint'
}


def _get_mandatory_option(opts: dict, name, for_what=None):
    res = opts.get(name)

    if res is None:
        err = f'{name} is mandatory'

        if for_what:
            err += f' for {for_what}'

        raise RuntimeError(err)

    return res


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

    priority = str(opts.get('model_run_priority_class', 'below_normal')).lower()
    opts['model_run_priority_class'] = priority

    if priority not in priorities:
        priority = 'below_normal'

    return priorities[priority]


class Options:
    def __init__(self):
        self._options = {}

    def __getitem__(self, key):
        return self._options[key]

    def get(self, key, default):
        return self._options.get(key, default)

    def apply_aliases(self, text: str) -> str:
        return utils.apply_aliases(text, self.aliases)

    def _init_options(self, folder, options_file: str):
        opts = json.loads(open(options_file, 'r').read())

        self._options = opts

        self.algorithm = _get_mandatory_option(opts, 'algorithm')

        self.engine_adapter = opts.get('engine_adapter', 'nonmem')
        self.model_cache_class = opts.get('model_cache', 'darwin.MemoryModelCache')
        self.model_run_man = opts.get('model_run_man', 'darwin.LocalRunManager')
        self.grid_man = opts.get('grid_man', 'darwin.GenericGridManager')

        self.num_parallel = opts.get('num_parallel', 4)

        self.options_file = os.path.abspath(options_file)

        options_file_parent = pathlib.Path(self.options_file).parent

        self.project_name = opts.get('project_name') or options_file_parent.name
        self.project_stem = re.sub(r'[^\w]', '_', self.project_name)

        self.project_dir = str(folder or options_file_parent)
        self.working_dir = str(opts.get('working_dir')
                               or os.path.join(pathlib.Path.home(), 'pydarwin', self.project_stem))

        project_dir_alias = {'project_dir': self.project_dir, 'working_dir': self.working_dir}

        self.data_dir = utils.apply_aliases(opts.get('data_dir'), project_dir_alias) or self.project_dir
        self.output_dir = utils.apply_aliases(opts.get('output_dir'), project_dir_alias) \
            or os.path.join(self.working_dir, 'output')
        self.temp_dir = utils.apply_aliases(opts.get('temp_dir'), project_dir_alias) \
            or os.path.join(self.working_dir, 'temp')

        self.aliases = {
            'project_dir': self.project_dir,
            'working_dir': self.working_dir,
            'data_dir': self.data_dir,
            'output_dir': self.output_dir,
            'temp_dir': self.temp_dir,
            'algorithm': self.algorithm,
            'author': opts.get('author', 'C.R.Darwin'),
            'project_name': self.project_name,
            'project_stem': self.project_stem,
        }

        penalty = opts.get('penalty', {})
        ga = opts.get('GA', {})

        self.penalty = _default_penalty | penalty
        self.GA = _default_GA | ga

        self.saved_models_file = utils.apply_aliases(opts.get('saved_models_file'), self.aliases)
        self.use_saved_models = opts.get('use_saved_models', False)

        self.remove_temp_dir = opts.get('remove_temp_dir', False)
        self.remove_run_dir = opts.get('remove_run_dir', False)

        self.crash_value = opts.get('crash_value', 99999999)

        self.isGA = self.algorithm == "GA"
        self.isPSO = self.algorithm == "PSO"

        if self.algorithm in ["GA", "PSO", "GBRT", "RF", "GP"]:
            self.population_size = _get_mandatory_option(opts, 'population_size', self.algorithm)
            self.num_generations = _get_mandatory_option(opts, 'num_generations', self.algorithm)
        if self.algorithm in ["GBRT", "RF", "GP"]:
            self.num_opt_chains = _get_mandatory_option(opts, 'num_opt_chains', self.algorithm)
        if self.algorithm in ["GA", "GBRT", "RF", "GP"]:
            self.downhill_period = opts.get('downhill_period', -1)
            self.final_downhill_search = opts.get('final_downhill_search', False)
            self.local_2_bit_search = opts.get('local_2_bit_search', False)

            if self.downhill_period > 0 or self.final_downhill_search:
                self.num_niches = _get_mandatory_option(opts, 'num_niches', 'downhill search')
                self.niche_radius = _get_mandatory_option(opts, 'niche_radius', 'downhill search')
            elif self.algorithm == 'GA':
                self.niche_radius = _get_mandatory_option(opts, 'niche_radius', self.algorithm)

        self.model_run_priority = _get_priority_class(opts)
        self.model_run_timeout = int(opts.get('model_run_timeout', 1200))

        pp_opts = opts.get('postprocess', {})

        self.use_r = pp_opts.get('useR', False)
        self.use_python = pp_opts.get('usePython', False)

        self.r_timeout = int(pp_opts.get('R_timeout', 90))

        if self.use_r:
            self.rscript_path = _get_mandatory_option(pp_opts, 'RScriptPath')

            rr = utils.apply_aliases(_get_mandatory_option(pp_opts, 'postRunRCode'), project_dir_alias)

            self.postRunRCode = os.path.abspath(rr)

        if self.use_python:
            rp = utils.apply_aliases(_get_mandatory_option(pp_opts, 'postRunPythonCode'), project_dir_alias)

            self.python_post_process_path = os.path.abspath(rp)

        self.search_omega_bands = opts.get('search_omega_bands', False)
        self.max_omega_band_width = opts.get('max_omega_band_width', 0)

        if self.search_omega_bands and self.max_omega_band_width < 1:
            log.warn("max_omega_band_width must be at least 1, omitting omega band width search")
            self.search_omega_bands = False

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
