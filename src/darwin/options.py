import os
import sys
import re
import json
import subprocess
import pathlib
import random

import darwin.utils as utils

from .DarwinError import DarwinError

from darwin.Log import log

_default_penalty = {
    'theta': 10,
    'omega': 10,
    'sigma': 10,
    'convergence': 100,
    'covariance': 100,
    'correlation': 100,
    'condition_number': 100,
    'non_influential_tokens': 0.00001
}

_default_GA = {
    'crossover_rate': 0.95,
    'elitist_num': 4,
    'mutation_rate': 0.95,
    'attribute_mutation_probability': 0.1,
    'mutate': 'flipBit',
    'niche_penalty': 20,
    'selection': 'tournament',
    'selection_size': 2,
    'sharing_alpha': 0.1,
    'crossover_operator': 'cxOnePoint'
}

_default_MOGA = {
    'objectives': 3,
    'names': [],
    'constraints': 0,
    'partitions': 12,
    'crossover': 'single',
    'crossover_rate': 0.95,
    'mutation_rate': 0.95,
    'attribute_mutation_probability': 0.1
}

_default_PSO = {
    'elitist_num': 4,
    'cognitive': 0.5,
    'social': 0.5,
    'inertia': 0.4,
    'neighbor_num': 20,  # must check if < pop_size
    'p_norm': 2,
    'break_on_no_change': 5
}


def _get_mandatory_option(opts: dict, name, for_what=None):
    res = opts.get(name)

    if res is None:
        err = f'{name} is mandatory'

        if for_what:
            err += f' for {for_what}'

        raise DarwinError(err)

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


def _load_system_options(opts: dict) -> dict:
    global_opts_file = os.environ.get('PYDARWIN_OPTIONS')

    if global_opts_file:
        if not os.path.exists(global_opts_file):
            log.warn(f'System options file not found: {global_opts_file}')
            return opts

        log.message(f'Loading system options: {global_opts_file}')

        global_opts = json.loads(open(global_opts_file, 'r', encoding='utf-8').read())

        for x, y in global_opts.items():
            if type(y) == dict:
                opts[x] = opts.get(x, {}) | y
            else:
                opts[x] = y

    return opts


class Options:
    def __init__(self):
        self._options = {}

    def __getitem__(self, key):
        return self._options[key]

    def get(self, key, default):
        return self._options.get(key, default)

    def apply_aliases(self, text: str) -> str:
        return utils.apply_aliases(text, self.aliases)

    def _init_options(self, options_file: str, folder):
        opts = json.loads(open(options_file, 'r', encoding='utf-8').read())

        if opts.get('use_system_options', True):
            opts = _load_system_options(opts)

        self._options = opts

        self.algorithm = _get_mandatory_option(opts, 'algorithm')

        self.engine_adapter = opts.get('engine_adapter', 'nonmem')
        self.model_cache_class = opts.get('model_cache', 'darwin.MemoryModelCache')
        self.model_run_man = opts.get('model_run_man', 'darwin.LocalRunManager')
        self.grid_adapter = opts.get('grid_adapter', 'darwin.GenericGridAdapter')

        self.LOCAL_RUN = self.model_run_man == 'darwin.LocalRunManager'

        self.MAX_RAND_SEED = int(opts.get('MAX_RAND_SEED', 31415926))

        try:
            self.random_seed = int(opts.get('random_seed', random.randint(0, self.MAX_RAND_SEED)))
        except ValueError:
            self.random_seed = None

        try:
            self.num_parallel = int(opts.get('num_parallel', 4))
        except ValueError:
            self.num_parallel = 0

        if self.num_parallel < 1:
            raise DarwinError('num_parallel must be a positive integer')

        self.options_file = os.path.abspath(options_file)

        options_file_parent = pathlib.Path(self.options_file).parent

        self.project_name = opts.get('project_name') or options_file_parent.name
        self.project_stem = re.sub(r'\W', '_', self.project_name)

        darwin_home = os.environ.get('PYDARWIN_HOME') or os.path.join(pathlib.Path.home(), 'pydarwin')

        self.project_dir = str(folder or options_file_parent)
        self.working_dir = utils.apply_aliases(opts.get('working_dir'), {'project_dir': self.project_dir})\
            or os.path.join(darwin_home, self.project_stem)

        if not os.path.isabs(self.working_dir):
            raise DarwinError('working_dir must be an absolute path')

        project_dir_alias = {'project_dir': self.project_dir, 'working_dir': self.working_dir}

        self.isMOGA = self.algorithm == 'MOGA' or self.algorithm == 'MOGA3'
        self.isMOGA3 = self.algorithm == 'MOGA3'
        self.isGA = self.algorithm == 'GA'
        self.isPSO = self.algorithm == 'PSO'

        self.data_dir = utils.apply_aliases(opts.get('data_dir'), project_dir_alias) or self.project_dir
        self.output_dir = utils.apply_aliases(opts.get('output_dir'), project_dir_alias) \
            or os.path.join(self.working_dir, 'output')
        self.temp_dir = utils.apply_aliases(opts.get('temp_dir'), project_dir_alias) \
            or os.path.join(self.working_dir, 'temp')
        self.key_models_dir = utils.apply_aliases(opts.get('key_models_dir'), project_dir_alias) \
            or os.path.join(options.working_dir, 'key_models')

        if self.isMOGA:
            self.non_dominated_models_dir = \
                utils.apply_aliases(opts.get('non_dominated_models_dir'), project_dir_alias) \
                or os.path.join(options.working_dir, 'non_dominated_models')

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
        moga = opts.get('MOGA', {})
        pso = opts.get('PSO', {})

        self.penalty = _default_penalty | penalty
        self.GA = _default_GA | ga
        self.MOGA = _default_MOGA | moga
        self.PSO = _default_PSO | pso
        self.use_saved_models = opts.get('use_saved_models', False)
        self.saved_models_file = utils.apply_aliases(opts.get('saved_models_file'), self.aliases)
        self.saved_models_readonly = opts.get('saved_models_readonly', False) and self.use_saved_models

        self.effect_limit = opts.get('effect_limit', -1)
        self.use_effect_limit = self.effect_limit > 0

        if (options.engine_adapter != 'nonmem' or options.algorithm not in ['GA', 'MOGA', 'MOGA3']) and self.use_effect_limit:
            log.warn('Can only use effect_limit with GA/MOGA/MOGA3 and NONMEM, turned off')
            self.use_effect_limit = False

        self.remove_temp_dir = opts.get('remove_temp_dir', False)
        self.remove_run_dir = opts.get('remove_run_dir', False)
        self.no_cleanup = opts.get('no_cleanup', False)

        self.crash_value = opts.get('crash_value', 99999999)

        if self.algorithm in ["GA", "PSO", "GBRT", "RF", "GP", "MOGA", "MOGA3"]:
            self.population_size = _get_mandatory_option(opts, 'population_size', self.algorithm)
            self.num_generations = _get_mandatory_option(opts, 'num_generations', self.algorithm)

        if self.algorithm in ["GBRT", "RF", "GP"]:
            self.num_opt_chains = _get_mandatory_option(opts, 'num_opt_chains', self.algorithm)

        if self.algorithm in ["GA", "PSO", "GBRT", "RF", "GP", "MOGA", "MOGA3"]:
            self.downhill_period = opts.get('downhill_period', -1)
            self.final_downhill_search = opts.get('final_downhill_search', False)
            self.local_2_bit_search = opts.get('local_2_bit_search', False)

            self.local_grid_search = opts.get('local_grid_search', False)
            self.max_local_grid_search_bits = opts.get('max_local_grid_search_bits', 5)

            if self.local_2_bit_search and self.isMOGA:
                log.warn('2-bit search is requested but ignored for MOGA algorithms')

            if self.downhill_period > 0 or self.final_downhill_search:
                self.num_niches = opts.get('num_niches', 2)
                self.niche_radius = float(opts.get('niche_radius', 2.0))
            elif self.algorithm == 'GA':
                self.niche_radius = float(opts.get('niche_radius', 2.0))

        self.model_run_priority = _get_priority_class(opts)
        self.model_run_timeout = int(opts.get('model_run_timeout', 1200))

        if self.engine_adapter == 'nlme':
            self.rscript_path = _get_mandatory_option(opts, 'rscript_path')
        else:
            self.rscript_path = opts.get('rscript_path', None)

        pp_opts = opts.get('postprocess', {})

        self.use_r = pp_opts.get('use_r', False)
        self.use_python = pp_opts.get('use_python', False)

        self.r_timeout = int(pp_opts.get('r_timeout', 90))

        if self.use_r:
            if self.rscript_path is None:
                self.rscript_path = _get_mandatory_option(pp_opts, 'rscript_path')

            rr = utils.apply_aliases(_get_mandatory_option(pp_opts, 'post_run_r_code'), project_dir_alias)

            self.post_run_r_code = os.path.abspath(rr)

        if self.use_python:
            rp = utils.apply_aliases(_get_mandatory_option(pp_opts, 'post_run_python_code'), project_dir_alias)

            self.python_post_process_path = os.path.abspath(rp)

        self.keep_best_models = opts.get('keep_best_models', True)
        self.keep_key_models = opts.get('keep_key_models', False) or self.keep_best_models

        if self.algorithm in ['EX', 'EXHAUSTIVE']:
            if opts.get('keep_best_models', False) or opts.get('keep_key_models', False):
                log.warn('Not keeping key models for Exhaustive search')

            self.keep_best_models = False
            self.keep_key_models = False

        # don't rerun if key models are not kept
        self.rerun_key_models = opts.get('rerun_key_models', False) and self.keep_key_models

        self.rerun_front_models = opts.get('rerun_front_models', True)

        self.TOKEN_NESTING_LIMIT = opts.get('TOKEN_NESTING_LIMIT', 4)

        self.CORRELATION_THRESHOLD = opts.get('CORRELATION_THRESHOLD', 0.95)

        self.fuzzy_eta = opts.get('fuzzy_eta', True)

        self.keep_extensions = opts.get('keep_extensions', [])
        self.keep_files = opts.get('keep_files', [])

        self.skip_running = opts.get('skip_running', False)

    def initialize(self, options_file, folder=None):
        if not os.path.exists(options_file):
            log.error(f"Couldn't find options file '{options_file}', exiting")
            sys.exit()

        log.message(f"Options file found at {options_file}")

        try:
            self._init_options(options_file, folder)
        except DarwinError as error:
            log.error('Option error: ' + str(error))
            sys.exit()
        except Exception as error:
            log.error(str(error))
            log.error(f"Failed to parse JSON options in '{options_file}', exiting")
            sys.exit()


options = Options()
