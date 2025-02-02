import os
import time
import sys
import re
import traceback
import math
from collections import OrderedDict

import darwin.GlobalVars as GlobalVars
import darwin.utils as utils

from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import ExecutionManager
from darwin.ModelRunManager import get_run_manager

import darwin.MemoryModelCache
import darwin.ModelRunManager
import darwin.LocalRunManager
import darwin.grid.GridRunManager
import darwin.nonmem.NMEngineAdapter
import darwin.nlme.NLMEEngineAdapter
from darwin.omega_search import get_omega_block_masks

from darwin.ModelEngineAdapter import get_engine_adapter, ModelEngineAdapter

from .Template import Template
from .ModelRun import ModelRun, write_best_model_files, file_checker, log_run
from .ModelCache import set_model_cache, create_model_cache
from .DarwinError import DarwinError
from .Population import init_pop_nums

from .algorithms.exhaustive import run_exhaustive, get_search_space_size
from .algorithms.GA import run_ga
from .algorithms.MOGA import run_moga
from .algorithms.PSO import run_pso
from .algorithms.OPT import run_skopt

search_exp = r'\{[^\[\n]+\[\s*\d+\s*]\s*}'

darwin.nonmem.NMEngineAdapter.register()
darwin.nlme.NLMEEngineAdapter.register()


def go_to_folder(folder: str, create: bool = False) -> bool:
    if not os.path.isdir(folder):
        if create:
            os.makedirs(folder)
        else:
            log.error(f"Directory doesn't exist: {folder}")

            return False

    log.message("Changing directory to " + folder)
    os.chdir(folder)

    return True


def _init_model_results():
    results_file = os.path.join(options.output_dir, "results.csv")

    utils.remove_file(results_file)

    log.message(f"Writing intermediate output to {results_file}")

    with open(results_file, "w") as resultsfile:
        resultsfile.write('iteration,model number,run directory,ref run,status,fitness,model,ofv,success,'
                          'covariance,correlation,ntheta,nomega,nsigm,total number of parameters,'
                          'condition num,r penalty,python penalty,'
                          'translation messages,runtime errors\n')

    GlobalVars.results_file = results_file


def _reset_global_vars():
    GlobalVars.results_file = None
    GlobalVars.best_run = None
    GlobalVars.key_models = []
    GlobalVars.all_models_num = 0
    GlobalVars.run_models_num = 0
    GlobalVars.unique_models_num = 0
    GlobalVars.unique_models_to_best = 0
    GlobalVars.start_time = GlobalVars.TimeToBest = 0
    GlobalVars.best_model_output = "No output yet"


def init_search(model_template: Template) -> bool:
    adapter = get_engine_adapter(options.engine_adapter)

    log.message(f"Algorithm: {options.algorithm}")
    log.message(f"Engine: {adapter.get_engine_name().upper()}")

    log.message(f"random_seed: {options.random_seed}")

    log.message(f"Project dir: {options.project_dir}")
    log.message(f"Data dir: {options.data_dir}")
    log.message(f"Project working dir: {options.working_dir}")
    log.message(f"Project temp dir: {options.temp_dir}")
    log.message(f"Project output dir: {options.output_dir}")
    log.message(f"Key models dir: {options.key_models_dir}")

    if not _check_tokens(model_template, adapter):
        return False

    _init_omega_search(model_template, adapter)

    adapter.init_template(model_template)

    space_size = get_search_space_size(model_template)
    log.message(f"Search space size: {space_size}")

    init_pop_nums(model_template)

    return True


def _init_app(options_file: str, folder: str = None):
    log.message("Running pyDarwin v3.0.0")
    _reset_global_vars()

    file_checker.reset()

    # if running in folder, options_file may be a relative path, so need to cd to the folder first
    # but if it's an absolute path, then folder may not even exist, in which case we create it
    if folder:
        go_to_folder(folder, True)

    options.initialize(options_file, folder)

    darwin.LocalRunManager.register()
    darwin.grid.GridRunManager.register()

    run_man = darwin.ModelRunManager.create_model_run_man(options.model_run_man)

    # init folders before log in case if the log is set up in temp or output folder
    run_man.init_folders()

    darwin.ModelRunManager.set_run_manager(run_man)

    log_file = os.path.join(options.working_dir, "messages.txt")

    utils.remove_file(log_file)

    log.initialize(log_file)

    if sys.platform == "win32":
        priority = options.get('model_run_priority_class', None)
        if priority:
            log.message(f'Model run priority is {priority}')

    log.message(f"Using {options.model_cache_class}")

    darwin.MemoryModelCache.register()

    _init_model_results()


class DarwinApp:
    def __init__(self, options_file: str, folder: str = None):
        self.initialized = False

        if folder:
            folder = os.path.abspath(folder)

        _init_app(options_file, folder)

        self.cache = create_model_cache(options.model_cache_class)

        set_model_cache(self.cache)

        self.exec_man = ExecutionManager(options.working_dir, clean=True)

        self.initialized = True

    def __del__(self):
        if not self.initialized:
            return

        self.cache.finalize()

        set_model_cache(None)

        self.exec_man.stop()

        darwin.ModelRunManager.get_run_manager().cleanup_folders()

    def run_template(self, model_template: Template) -> ModelRun:
        try:
            return self._run_template(model_template)
        except DarwinError as e:
            log.error(str(e))
        except:
            traceback.print_exc()

        return GlobalVars.best_run

    def _run_template(self, model_template: Template) -> ModelRun:
        if not init_search(model_template):
            return GlobalVars.best_run

        adapter = get_engine_adapter(options.engine_adapter)

        if options.LOCAL_RUN and not adapter.init_engine():
            return GlobalVars.best_run

        self.exec_man.start()

        GlobalVars.start_time = time.time()
        log.message(f"Search start time: {time.asctime()}")

        algorithm = options.algorithm

        if algorithm in ["GBRT", "RF", "GP"]:
            final = run_skopt(model_template)
        elif algorithm == "GA":
            final = run_ga(model_template)
        elif algorithm == "MOGA":
            run_moga(model_template)
            final = None
        elif algorithm == "PSO":
            final = run_pso(model_template)
        elif algorithm in ["EX", "EXHAUSTIVE"]:
            final = run_exhaustive(model_template)
        else:
            log.error(f"Algorithm {algorithm} is not available")
            sys.exit()

        final_control_file, final_result_file = adapter.get_final_file_names()

        final_control_file = os.path.join(options.output_dir, final_control_file)
        final_result_file = os.path.join(options.output_dir, final_result_file)

        final_output_done = False

        if write_best_model_files(final_control_file, final_result_file) \
                and GlobalVars.best_model_output != 'No output yet':
            final_output_done = True
            log.message(f"Final output from best model is in {final_result_file}")

        log.message(f"Number of considered models: {GlobalVars.all_models_num}")
        log.message(f"Number of models that were run during the search: {GlobalVars.run_models_num}")

        if final:
            log.message(f"Number of unique models to best model: {GlobalVars.unique_models_to_best}")
            log.message(f"Time to best model: {GlobalVars.TimeToBest / 60:0.1f} minutes")

            log.message(f"Best overall fitness: {final.result.fitness:4f},"
                        f" iteration {final.generation}, model {final.model_num}")

        elapsed = time.time() - GlobalVars.start_time

        log.message(f"Elapsed time: {elapsed / 60:.1f} minutes \n")

        log.message(f"Search end time: {time.asctime()}\n")

        if options.keep_key_models:
            log.message('Key models:')
            for r in GlobalVars.key_models:
                log_run(r)

        if options.rerun_key_models:
            _rerun_key_models()

            if not final_output_done and write_best_model_files(final_control_file, final_result_file):
                log.message(f"Final output from best model is in {final_result_file}")

        try:
            os.remove(os.path.join(options.working_dir, "InterimControlFile.mod"))
            os.remove(os.path.join(options.working_dir, "InterimResultFile.lst"))
        except OSError:
            pass

        return final


def _rerun_key_models():
    GlobalVars.best_run = None

    rerun_models = [r for r in GlobalVars.key_models if r.orig_run_dir is not None or r.rerun]

    if not rerun_models:
        return

    for r in rerun_models:
        r.rerun = True
        r.source = 'new'
        r.reference_model_num = -1
        r.status = 'Not Started'
        r.result.ref_run = ''

    log.message("Re-running models")

    get_run_manager().run_all(rerun_models)


def _has_omega_search(tokens: OrderedDict, pattern: str) -> bool:
    for k in tokens.values():
        for i in k:
            for j in i:
                if re.findall(pattern, j, flags=re.MULTILINE):
                    return True

    return False


def _init_omega_search(template: darwin.Template, adapter: darwin.ModelEngineAdapter):
    """
    see if Search_OMEGA and omega_band_width are in the token set
    if so, find how many bits needed for band width, and add that gene
    final gene in genome is omega band width, values 0 to max omega size -1
    """

    if options.engine_adapter == 'nonmem':
        options.search_omega_blocks = options.get('search_omega_bands', False)

        if options.search_omega_blocks and options.random_seed is None:
            raise DarwinError('random_seed is required for omega band search')

        options.max_omega_band_width = options.get('max_omega_band_width', 1)

        if options.search_omega_blocks and options.max_omega_band_width < 1:
            log.warn('max_omega_band_width must be at least 1, omitting omega band width search')
            options.search_omega_blocks = False

    elif options.engine_adapter == 'nlme':
        options.search_omega_blocks = options.get('search_omega_blocks', False)
        options.max_omega_band_width = None

    options.search_omega_sub_matrix = False

    if not options.search_omega_blocks:
        return

    omega_search_limit = options.get('OMEGA_SEARCH_LIMIT', 16)
    options.OMEGA_SEARCH_LIMIT = omega_search_limit

    options.individual_omega_search = options.get('individual_omega_search', True)

    if options.individual_omega_search and _has_omega_search(template.tokens, adapter.get_omega_search_pattern()):
        log.warn('Token file contains omega search blocks, turning individual omega search off')
        options.individual_omega_search = False

    max_len_config = options.get('max_omega_search_len', None)

    if max_len_config is not None and max_len_config < 2:
        log.warn(f"max_omega_search_len must be [2, {omega_search_limit}], disabling omega search")
        options.search_omega_blocks = False

        return

    max_len_config = max_len_config or 0

    if max_len_config > omega_search_limit:
        log.warn(f"max_omega_search_len is too big, resetting to {omega_search_limit}")
        max_len_config = omega_search_limit

    max_len = max_len_config
    max_lens = []

    # calculate it if it wasn't set, or if it was set and individual search was requested
    if not max_len or options.individual_omega_search:
        (max_len, max_lens) = adapter.get_max_search_block(template)

        if max_len > 0 and not max_len_config:
            log.message(f"Calculated max omega search length = {max_len}")

    if max_len > omega_search_limit:
        # if it was calculated for uniform (not individual) search
        if not max_len_config and not options.individual_omega_search:
            log.warn(f"max omega search length is too big, resetting to {omega_search_limit}")
            max_len = omega_search_limit

    # if individual search was requested and the max len was set, make all the lengths equal
    if options.individual_omega_search and max_len_config:
        max_lens = [max_len_config] * len(max_lens)

    if max_len < 2:
        log.warn(f"max omega search length must be [2, {omega_search_limit}], disabling omega search")
        options.search_omega_blocks = False

    # if not individual_omega_search, max_omega_search_lens contains the only value, and omega_idx is always 0
    options.max_omega_search_lens = max_lens or [max_len]
    options.max_omega_search_len = max_len_config if max_len_config else max_len

    if not options.search_omega_blocks:
        return

    options.search_omega_sub_matrix = options.get('search_omega_sub_matrix', False)
    options.max_omega_sub_matrix = options.get('max_omega_sub_matrix', 4)

    if options.search_omega_sub_matrix and options.max_omega_sub_matrix < 2:
        log.warn('max_omega_sub_matrix must be at least 2, omitting search_omega_sub_matrix')
        options.search_omega_sub_matrix = False

    (can_search, err) = adapter.can_omega_search(template.template_text)

    if not can_search:
        log.warn(f"{err} Turning off OMEGA search.")

        options.search_omega_blocks = False
        options.search_omega_sub_matrix = False

        return

    if options.max_omega_band_width is not None:
        log.message(f"Including search of band OMEGA, with width up to {options.max_omega_band_width}")

    if options.search_omega_sub_matrix:
        log.message(f"Including search for OMEGA submatrices, with size up to {options.max_omega_sub_matrix}")

    for i in options.max_omega_search_lens:
        if options.max_omega_band_width is not None:
            # if no submatrices add no-block mask as band_width = 0
            extra_band = 0 if options.search_omega_sub_matrix else 1

            # this is the number of off diagonal bands (diagonal is NOT included)
            template.gene_max.append(options.max_omega_band_width - 1 + extra_band)
            template.gene_length.append(math.ceil(math.log(options.max_omega_band_width + extra_band, 2)))

            if template.omega_band_pos is None:
                template.omega_band_pos = len(template.gene_max) - 1

        size = len(get_omega_block_masks(i))

        template.gene_max.append(size - 1)
        template.gene_length.append(math.ceil(math.log(size, 2)))

        if template.omega_band_pos is None:
            template.omega_band_pos = len(template.gene_max) - 1


def _check_tokens(model_template: Template, adapter: ModelEngineAdapter) -> bool:
    """
    Generates list of "target" tokens from the tokens file and of "source" tokens from
    the template and tokens file. Checks to see if all source tokens are available in the target
    tokens list. Also prints a warning if the number of text string in a token set are not
    consistent.
    """

    template_text, tokens = adapter.remove_comments(model_template.template_text), model_template.tokens

    target_tokens = _get_target_tokens(tokens)
    source_tokens = _get_template_tokens(template_text) + _get_nested_tokens(tokens, adapter)

    source_tokens = [re.sub(r'\s', '', tok, ) for tok in source_tokens]

    missing = [token for token in source_tokens if token not in target_tokens]

    if missing:
        log.error("Text string for following tokens are missing: " + ', '.join(missing))

    return not bool(missing)


def _get_template_tokens(template_text) -> list:
    token_keys = re.findall(search_exp, template_text)

    return token_keys


def _get_nested_tokens(tokens: dict, adapter: ModelEngineAdapter) -> list:
    found_tokens = []

    for group in tokens.values():
        for lines in group:
            for line in lines:
                line = adapter.remove_comments(line)

                pos = re.search(search_exp, line)

                if pos is not None:
                    found_tokens.append(pos.group(0))

    return found_tokens


def _get_target_tokens(tokens: dict) -> set:
    full_tokens = set()

    for key, group in tokens.items():
        n_text = [len(text) for text in group]

        if not all(x == n_text[0] for x in n_text):
            log.error(f"Inconsistent number of text strings for {key} in tokens file")

        for this_text in range(1, min(n_text) + 1):
            # check each token, e.g., ADVAN[1], then ADVAN[3] is OK in template, but warning
            # note that the token text are, by definition sequential in the tokens file, but there need not be
            # a matching one in template - but give a warning for this.
            text_string = "{" + key + "[" + str(this_text) + "]}"
            full_tokens.add(text_string)

    return full_tokens
