import os
import time
import sys
import traceback
import math

import darwin.GlobalVars as GlobalVars
import darwin.utils as utils

from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import ExecutionManager

import darwin.MemoryModelCache
import darwin.ModelRunManager
import darwin.LocalRunManager
import darwin.grid.GridRunManager
import darwin.nonmem.NMEngineAdapter
import darwin.nlme.NLMEEngineAdapter
from darwin.omega_search import get_omega_block_masks

from darwin.ModelEngineAdapter import get_engine_adapter

from .Template import Template
from .ModelRun import ModelRun, write_best_model_files, file_checker
from .ModelCache import set_model_cache, create_model_cache
from .DarwinError import DarwinError

from .algorithms.exhaustive import run_exhaustive, get_search_space_size
from .algorithms.GA import run_ga
from .algorithms.PSO import run_pso
from .algorithms.OPT import run_skopt


def _go_to_folder(folder: str):
    if not os.path.isdir(folder):
        os.makedirs(folder)

    log.message("Changing directory to " + folder)
    os.chdir(folder)


def _init_model_results():
    results_file = os.path.join(options.output_dir, "results.csv")

    utils.remove_file(results_file)

    log.message(f"Writing intermediate output to {results_file}")

    with open(results_file, "w") as resultsfile:
        resultsfile.write(f"Iteration,Model number,Run directory,Ref. run,Status,Fitness,Model,ofv,success,"
                          f"covar,correlation #,ntheta,nomega,nsigm,condition,RPenalty,PythonPenalty,"
                          f"Translation messages,Runtime errors\n")

    GlobalVars.results_file = results_file


def _reset_global_vars():
    GlobalVars.results_file = None
    GlobalVars.best_run = None
    GlobalVars.all_models_num = 0
    GlobalVars.run_models_num = 0
    GlobalVars.unique_models_num = 0
    GlobalVars.unique_models_to_best = 0
    GlobalVars.start_time = GlobalVars.TimeToBest = 0
    GlobalVars.best_model_output = "No output yet"


def _init_app(options_file: str, folder: str = None):
    log.message("Running pyDarwin v1.1.1")
    _reset_global_vars()

    file_checker.reset()

    # if running in folder, options_file may be a relative path, so need to cd to the folder first
    # but if it's an absolute path, then folder may not even exist, in which case we create it
    if folder:
        _go_to_folder(folder)

    options.initialize(options_file, folder)

    log.message(f"Options file found at {options_file}")

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
    log.message(f"Algorithm is {options.algorithm}")

    log.message(f"Project dir: {options.project_dir}")
    log.message(f"Data dir: {options.data_dir}")
    log.message(f"Project working dir: {options.working_dir}")
    log.message(f"Project temp dir: {options.temp_dir}")
    log.message(f"Project output dir: {options.output_dir}")

    GlobalVars.start_time = time.time()

    darwin.nonmem.NMEngineAdapter.register()
    darwin.nlme.NLMEEngineAdapter.register()
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

        algorithm = options.algorithm

        adapter = get_engine_adapter(options.engine_adapter)

        if not adapter.init_engine():
            return GlobalVars.best_run

        adapter.init_template(model_template)

        _init_omega_search(model_template, adapter)

        self.exec_man.start()

        space_size = get_search_space_size(model_template)
        log.message(f"Search space size = {space_size}")

        log.message(f"Search start time = {time.asctime()}")

        if algorithm in ["GBRT", "RF", "GP"]:
            final = run_skopt(model_template)
        elif algorithm == "GA":
            final = run_ga(model_template)
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

        if write_best_model_files(final_control_file, final_result_file):
            log.message(f"Final output from best model is in {final_result_file}")

        if final:
            log.message(f"Number of considered models = {GlobalVars.all_models_num}")
            log.message(f"Number of models that were run during the search = {GlobalVars.run_models_num}")
            log.message(f"Number of unique models to best model = {GlobalVars.unique_models_to_best}")
            log.message(f"Time to best model = {GlobalVars.TimeToBest / 60:0.1f} minutes")

            log.message(f"Best overall fitness = {final.result.fitness:4f},"
                        f" iteration {final.generation}, model {final.model_num}")

        elapsed = time.time() - GlobalVars.start_time

        log.message(f"Elapsed time = {elapsed / 60:.1f} minutes \n")

        log.message(f"Search end time = {time.asctime()}")

        try:
            os.remove(os.path.join(options.working_dir, "InterimControlFile.mod"))
            os.remove(os.path.join(options.working_dir, "InterimResultFile.lst"))
        except OSError:
            pass

        return final


def _init_omega_search(template: darwin.Template, adapter: darwin.ModelEngineAdapter):
    """
    see if Search_OMEGA and omega_band_width are in the token set
    if so, find how many bits needed for band width, and add that gene
    final gene in genome is omega band width, values 0 to max omega size -1
    """

    if not options.search_omega_blocks:
        return

    (can_search, err) = adapter.can_omega_search(template.template_text)

    if not can_search:
        log.warn(f"{err} Turning off OMEGA search.")

        options.search_omega_blocks = False
        options.search_omega_sub_matrix = False

        return

    if options.search_omega_blocks is False and options.search_omega_sub_matrix is True:
        log.warn(
            f"Cannot do omega sub matrix search without omega band search. Turning off omega submatrix search.")

        options.search_omega_sub_matrix = False

        return

    # this is the number of off diagonal bands (diagonal is NOT included)
    template.gene_max.append(options.max_omega_band_width)
    template.gene_length.append(math.ceil(math.log(options.max_omega_band_width + 1, 2)))

    log.message(f"Including search of band OMEGA, with width up to {options.max_omega_band_width}")

    template.omega_band_pos = len(template.gene_max) - 1

    if options.search_omega_sub_matrix:
        log.message(f"Including search for OMEGA submatrices, with size up to {options.max_omega_sub_matrix}")

        size = len(get_omega_block_masks())

        template.gene_max.append(size - 1)
        template.gene_length.append(math.ceil(math.log(size, 2)))
