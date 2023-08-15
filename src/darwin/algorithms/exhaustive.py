import numpy as np

import darwin.GlobalVars as GlobalVars

from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import keep_going

from darwin.Template import Template
from darwin.ModelRun import ModelRun
from darwin.ModelCode import ModelCode
from darwin.Population import Population
from darwin.omega_search import get_omega_block_masks


def run_exhaustive(model_template: Template) -> ModelRun:
    """
    Run full exhaustive search on the Template, all possible combinations.
    All models will be run in iteration number 0.

    :param model_template: Model Template
    :type model_template: Template

    :return: Returns final/best model run
    :rtype: ModelRun
    """
    codes = get_search_space(model_template)

    num_models = codes.shape[0]

    # break into smaller list, for memory management
    batch_size = options.get('exhaustive_batch_size', 100)

    for start in range(0, num_models, batch_size):
        pop = Population.from_codes(model_template, '0', codes[start:start + batch_size], ModelCode.from_int,
                                    start_number=start, max_number=num_models)

        pop.run()

        if not keep_going():
            break

        log.message(f"Current Best fitness = {GlobalVars.best_run.result.fitness}")

    return GlobalVars.best_run


def get_search_space(model_template: Template) -> np.ndarray:
    num_groups = []

    for thisKey in model_template.tokens.keys():
        token_group = model_template.tokens.get(thisKey)
        num_groups.append(list(range(len(token_group))))

    if options.search_omega_blocks:
        for i in options.max_omega_search_lens:
            if options.max_omega_band_width is not None:
                # need to add another group if searching on omega bands
                num_groups.append(list(range(1, options.max_omega_band_width + 1)))

            # need to add another group if searching on omega submatrices
            num_groups.append(list(range(len(get_omega_block_masks(i)))))

    if not num_groups:
        log.error('The search space is empty - exiting')
        exit('The search space is empty')

    codes = np.array(np.meshgrid(*num_groups)).T.reshape(-1, len(num_groups))

    return codes


def get_search_space_size(model_template: Template) -> int:
    return get_search_space(model_template).shape[0]
