import logging
import time
import sys 
import gc

import darwin.GlobalVars as GlobalVars

from darwin.Log import log
from darwin.options import options

from .Template import Template
from .Model import Model
from .ModelCode import ModelCode

from .algorithms.exhaustive import run_exhaustive
from .algorithms.GA import run_ga
from .algorithms.OPT import run_skopt
from .algorithms.PSO import run_PSO

logger = logging.getLogger(__name__)


def _run_template(model_template: Template) -> Model: 

    GlobalVars.init_global_vars(options.homeDir)
    # initialize a trivial model for the global best
    null_code = ModelCode([0] * len(model_template.gene_length), "Int",
                          model_template.gene_max, model_template.gene_length) 
    GlobalVars.BestModel = Model(model_template, null_code, -99, -99)
    GlobalVars.BestModel.fitness = options.crash_value + 1
    algorithm = options.algorithm

    log.message(f"Search start time = {time.asctime()}")

    if algorithm in ["GBRT", "RF", "GP"]:
        final = run_skopt(model_template)
    elif algorithm == "GA":
        final = run_ga(model_template)
    elif algorithm in ["EX", "EXHAUSTIVE"]:
        final = run_exhaustive(model_template)
    elif algorithm == "PSO":
        final = run_PSO(model_template)
    else:
        log.error(f"Algorithm {algorithm} is not available")
        sys.exit()

    log.message(f"Number of unique models to best model = {GlobalVars.UniqueModelsToBest}")
    log.message(f"Time to best model = {GlobalVars.TimeToBest / 60:0.1f} minutes")

    log.message(f"Search end time = {time.asctime()}")
  
    gc.collect()

    return final


def run_search(template_file: str, tokens_file: str, options_file: str) -> Model:
    """
    run algorithm selected in options_file, based on template_file and tokens_file
    At the end, write best control and output file to homeDir (specified in options_file)
    options_file path name should, in general, be absolute, other file names can be absolute path
    or path relative to the homeDir
    function returns the final model object
    """

    try:
        model_template = Template(template_file, tokens_file, options_file)
    except Exception as e:
        logger.error(e)
        raise

    return _run_template(model_template)


def run_search_in_folder(
        folder: str,
        template_file: str = 'template.txt', tokens_file: str = 'tokens.json', options_file: str = 'options.json'
) -> Model:

    try:
        model_template = Template(template_file, tokens_file, options_file, folder)
    except Exception as e:
        logger.error(e)
        raise

    return _run_template(model_template)
