import time
import numpy as np

import darwin.GlobalVars as GlobalVars

from darwin.Log import log
from darwin.options import options

from darwin.Model import Model
from darwin.ModelCode import ModelCode
from darwin.runAllModels import run_all


def run_exhaustive(model_template):
    num_groups = []

    for thisKey in model_template.tokens.keys():
        token_group = model_template.tokens.get(thisKey)
        num_groups.append(list(range(len(token_group))))

    # need to add another group if searching on omega bands
    if model_template.search_omega_band:
        num_groups.append(list(range(model_template.omega_bandwidth)))

    codes = np.array(np.meshgrid(*num_groups)).T.reshape(-1, len(num_groups))

    # convert to regular list
    codes = codes.tolist()
    num_models = len(codes)
    maxes = model_template.gene_max
    lengths = model_template.gene_length

    log.message(f"Total of {num_models} to be run in exhaustive search")

    # break into smaller list, for memory management
    max_models = options['max_model_list_size']

    current_start = 0
    current_last = current_start + max_models

    if current_last > num_models:
        max_models = num_models
        current_last = num_models

    fitnesses = []
    best_fitness = options.crash_value
    best_model = None

    while current_last <= num_models:
        if current_last > len(codes):
            current_last = len(codes)
        models = []
        for thisInts, model_num in zip(codes[current_start:current_last], range(current_start, current_last)):
            code = ModelCode(thisInts, "Int", maxes, lengths)
            models.append(Model(model_template, code, model_num, 0))

        run_all(models)

        for model in models:
            if model.fitness < best_fitness:
                best_fitness = model.fitness
                best_model = model.make_copy()
            fitnesses.append(model.fitness)

        log.message(f"Current Best fitness = {best_fitness}")
        current_start = current_last
        current_last = current_start + max_models

    elapsed = time.time() - GlobalVars.StartTime

    log.message(f"Elapse time = {elapsed / 60:.1f} minutes \n")

    if best_model:
        log.message(f"Best overall fitness = {best_fitness:4f}, model {best_model.model_num}")

        with open(GlobalVars.FinalControlFile, 'w') as control:
            control.write(best_model.control)

    with open(GlobalVars.FinalResultFile, 'w') as result:
        result.write(GlobalVars.BestModelOutput)

    log.message(f"Final output from best model is in {GlobalVars.FinalResultFile}")
    log.message(f"Unique model list in  {GlobalVars.SavedModelsFile}") 

    return best_model
