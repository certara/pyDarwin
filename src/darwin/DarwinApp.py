import os
import time
import sys

import darwin.GlobalVars as GlobalVars
import darwin.utils as utils

from darwin.Log import log
from darwin.options import options
from darwin.execution_man import start_execution_manager

import darwin.MemoryModelCache
import darwin.ModelRunManager
import darwin.LocalRunManager
import darwin.grid.GridRunManager
import darwin.nonmem.NMEngineAdapter

from .Template import Template
from .ModelRun import ModelRun, write_best_model_files
from .ModelCache import set_model_cache, create_model_cache

from .algorithms.exhaustive import run_exhaustive
from .algorithms.GA import run_ga
from .algorithms.OPT import run_skopt


def run_template(model_template: Template) -> ModelRun:

    algorithm = options.algorithm

    start_execution_manager(clean=True)

    log.message(f"Search start time = {time.asctime()}")

    if algorithm in ["GBRT", "RF", "GP"]:
        final = run_skopt(model_template)
    elif algorithm == "GA":
        final = run_ga(model_template)
    elif algorithm in ["EX", "EXHAUSTIVE"]:
        final = run_exhaustive(model_template)
    else:
        log.error(f"Algorithm {algorithm} is not available")
        sys.exit()

    final_control_file = os.path.join(options.output_dir, "FinalControlFile.mod")
    final_result_file = os.path.join(options.output_dir, "FinalResultFile.lst")

    if write_best_model_files(final_control_file, final_result_file):
        log.message(f"Final output from best model is in {final_result_file}")

    if final:
        log.message(f"Number of unique models to best model = {GlobalVars.UniqueModelsToBest}")
        log.message(f"Time to best model = {GlobalVars.TimeToBest / 60:0.1f} minutes")

        log.message(f"Best overall fitness = {final.result.fitness:4f},"
                    f" iteration {final.generation}, model {final.model_num}")

    elapsed = time.time() - GlobalVars.StartTime

    log.message(f"Elapsed time = {elapsed / 60:.1f} minutes \n")

    log.message(f"Search end time = {time.asctime()}")

    return final


def _go_to_folder(folder: str):
    if folder:
        if not os.path.isdir(folder):
            os.makedirs(folder)

        log.message("Changing directory to " + folder)
        os.chdir(folder)


def _init_model_results():
    results_file = os.path.join(options.output_dir, "results.csv")

    utils.remove_file(results_file)

    log.message(f"Writing intermediate output to {results_file}")

    with open(results_file, "w") as resultsfile:
        resultsfile.write(f"Run Directory,Fitness,Model,ofv,success,covar,correlation #,"
                          f"ntheta,nomega,nsigm,condition,RPenalty,PythonPenalty,NMTran messages\n")

    GlobalVars.results_file = results_file


def _init_app(options_file: str, folder: str = None):
    # if running in folder, options_file may be a relative path, so need to cd to the folder first
    # but if it's an absolute path, then folder may not even exist, in which case we create it
    _go_to_folder(folder)

    options.initialize(options_file, folder)

    log.message(f"Options file found at {options_file}")

    # if folder is not provided, then it must be set in options
    if not folder:
        _go_to_folder(options.project_dir)

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

    log.message(f"Project dir: {options.project_dir}")
    log.message(f"Data dir: {options.data_dir}")
    log.message(f"Project working dir: {options.working_dir}")
    log.message(f"Project temp dir: {options.temp_dir}")
    log.message(f"Project output dir: {options.output_dir}")

    GlobalVars.StartTime = time.time()

    darwin.nonmem.NMEngineAdapter.register()
    darwin.MemoryModelCache.register()

    _init_model_results()


class DarwinApp:
    def __init__(self, options_file: str, folder: str = None):
        self.initialized = False

        _init_app(options_file, folder)

        self.cache = create_model_cache(options.model_cache_class)

        set_model_cache(self.cache)

        self.initialized = True

    def __del__(self):
        if not self.initialized:
            return

        self.cache.finalize()

        set_model_cache(None)

        darwin.ModelRunManager.get_run_manager().cleanup_folders()
