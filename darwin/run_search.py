""""
Sponsor:FDA OGD 
Program:
Programmer’s Name: Mark Sale
Date:13Apr2022
Purpose:
Brief Description:
Platform: Windows
Environment: 
Input:
Output:
Notes:  
ModifiedBy:
    Date: 23 Apr, 2022
    Details: added omega bands
    Effective
"""
import logging
import time
import sys

import gc

import darwin.GlobalVars as GlobalVars

from .Templater import model, template
from .model_code import model_code

from .algorithms.exhaustive import run_exhaustive
from .algorithms.GA import run_GA
from .algorithms.OPT import run_skopt
from .algorithms.PSO import run_PSO

logger = logging.getLogger(__name__)


def run_search(template_file: str, tokens_file: str, options_file: str) -> model:
    """
    run algorithm selected in options_file, based on template_file and tokens_file
    At the end, write best control and output file to homeDir (specified in options_file) 
    options_file path name should, in general, be absolute, other file names can be absolute path
    or path relative to the homeDir
    function returns the final model object
    """

    try:  # path to tokens/template is relative to homeDir, probably need to give full path to template/tokens??
        model_template = template(template_file, tokens_file, options_file)
    except Exception as e:
        logger.error(e)
        raise

    GlobalVars.init_global_vars()
    genome_length = sum(model_template.gene_length)
    # this many include one (last one) for OMEGA band width

    # initialize a trivial model for the global best
    null_code = model_code([0] * len(model_template.gene_length), "Int", model_template.gene_max, model_template.gene_length)
    GlobalVars.BestModel = model(model_template, null_code, -99, True, -99)
    GlobalVars.BestModel.fitness = model_template.options['crash_value'] + 1
    algorithm = model_template.options['algorithm']

    model_template.printMessage(f"Search start time = {time.asctime()}")

    if algorithm in ["GBRT", "RF", "GP"]:
        final = run_skopt(model_template)
    elif algorithm == "GA":
        final = run_GA(model_template)
    elif algorithm == "EXHAUSTIVE":
        final = run_exhaustive(model_template)
    elif algorithm == "PSO":
        final = run_PSO(model_template)
    else:
        print(f"Algorithm {algorithm} is not available")
        sys.exit()

    model_template.printMessage(f"Number of unique models to best model = {GlobalVars.UniqueModelsToBest}")
    model_template.printMessage(f"Time to best model = {GlobalVars.TimeToBest / 60:0.1f} minutes")

    model_template.printMessage(f"Search end time = {time.asctime()}")
    gc.collect()

    return final
