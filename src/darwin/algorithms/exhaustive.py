import numpy as np

import darwin.GlobalVars as GlobalVars

from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import keep_going

from darwin.Template import Template
from darwin.ModelRun import ModelRun
from darwin.ModelCode import ModelCode
from darwin.Population import Population


def run_exhaustive(model_template: Template) -> ModelRun:
    """
    Run full exhaustive search on the Template, all possible combinations.
    All models will be run in iteration number 0.

    :param model_template: Model Template
    :type model_template: Template

    :return: Returns final/best model run
    :rtype: ModelRun
    """    
    num_groups = []

    for thisKey in model_template.tokens.keys():
        token_group = model_template.tokens.get(thisKey)
        num_groups.append(list(range(len(token_group))))

    # need to add another group if searching on omega bands
    if options.search_omega_bands:
        num_groups.append(list(range(options.max_omega_band_width + 1)))

    # need to add another group if searching on omega submatrices
    if options.search_omega_sub_matrix:
        for i in range(options.max_omega_sub_matrix):
            num_groups.append([0, 1])
    if not(num_groups):
        log.message("Nothing to search in exhaustive search - exiting")
        exit("Nothing to search in exhaustive search")
    codes = np.array(np.meshgrid(*num_groups)).T.reshape(-1, len(num_groups))

    # convert to regular list
    codes = codes.tolist()
    num_models = len(codes)

    log.message(f"Total of {num_models} to be run in exhaustive search")

    # break into smaller list, for memory management
    batch_size = options.get('exhaustive_batch_size', 100)

    for start in range(0, num_models, batch_size):
        pop = Population.from_codes(model_template, '0', codes[start:start + batch_size], ModelCode.from_int,
                                    start_number=start, max_number=num_models)

        pop.run()

        if not keep_going():
            break

        log.message(f"Current Best fitness = {GlobalVars.BestRun.result.fitness}")

    return GlobalVars.BestRun
