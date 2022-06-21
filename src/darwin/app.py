import os
import time
import sys
import gc

import darwin.GlobalVars as GlobalVars
import darwin.utils as utils

from darwin.Log import log
from darwin.options import options

from .ModelEngineAdapter import register_engine_adapter
from .NMEngineAdapter import NMEngineAdapter

from .Template import Template
from .Model import Model
from .Population import init_model_list

from .algorithms.exhaustive import run_exhaustive
from .algorithms.GA import run_ga
from .algorithms.OPT import run_skopt
from .algorithms.PSO import run_pso


def run_template(model_template: Template) -> Model:

    algorithm = options.algorithm

    log.message(f"Search start time = {time.asctime()}")

    if algorithm in ["GBRT", "RF", "GP"]:
        final = run_skopt(model_template)
    elif algorithm == "GA":
        final = run_ga(model_template)
    elif algorithm in ["EX", "EXHAUSTIVE"]:
        final = run_exhaustive(model_template)
    elif algorithm == "PSO":
        final = run_pso(model_template)
    else:
        log.error(f"Algorithm {algorithm} is not available")
        sys.exit()

    log.message(f"Number of unique models to best model = {GlobalVars.UniqueModelsToBest}")
    log.message(f"Time to best model = {GlobalVars.TimeToBest / 60:0.1f} minutes")

    log.message(f"Search end time = {time.asctime()}")

    gc.collect()

    return final


def _go_to_folder(folder: str):
    if folder:
        if not os.path.isdir(folder):
            os.mkdir(folder)

        log.message("Changing directory to " + folder)
        os.chdir(folder)


def init_app(options_file: str, folder: str = None):
    # if running in folder, options_file may be a relative path, so need to cd to the folder first
    _go_to_folder(folder)

    options.initialize(folder, options_file)

    # if folder is not provided, then it must be set in options
    if not folder:
        _go_to_folder(options.home_dir)

    log_file = os.path.join(options.home_dir, "messages.txt")

    utils.remove_file(log_file)

    log.initialize(log_file)

    log.message(f"Options file found at {options_file}")

    GlobalVars.init_global_vars(options.home_dir)

    register_engine_adapter('nonmem', NMEngineAdapter)

    init_model_list()
