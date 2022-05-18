import time
import os
import gc
import heapq
import numpy as np

import darwin.GlobalVars as GlobalVars

from darwin.Templater import model
from darwin.model_code import model_code
from darwin.runAllModels import InitModellist, run_all


def run_exhaustive(model_template):
    GlobalVars.StartTime = time.time()
    Num_Groups = []
    for thisKey in model_template.tokens.keys():
        tokenGroup = model_template.tokens.get(thisKey)
        Num_Groups.append(list(range(len(tokenGroup))))
    # need to add another group if searching on omega bands
    if model_template.search_omega_band:
        Num_Groups.append(list(range(model_template.omega_bandwidth)))
    codes = np.array(np.meshgrid(*Num_Groups)).T.reshape(-1, len(Num_Groups))
    # convert to regular list
    codes = codes.tolist()
    NumModels = len(codes)
    maxes = model_template.gene_max
    lengths = model_template.gene_length
    # break into smaller list, for memory management
    MaxModels = model_template.options['max_model_list_size']
    # Models = [None]*MaxModels
    current_start = 0
    current_last = current_start + MaxModels
    if current_last > NumModels:
        MaxModels = NumModels
        current_last = NumModels
    InitModellist(model_template)
    fitnesses = []
    while current_last <= NumModels:
        if current_last > len(codes):
            current_last = len(codes)
        # for thisInts,model_num in zip(codes,range(len(codes))):
        thisModel = 0
        Models = [None] * MaxModels
        for thisInts, model_num in zip(codes[current_start:current_last], range(current_start, current_last)):
            code = model_code(thisInts, "Int", maxes, lengths)
            Models[thisModel] = model(model_template, code, model_num, True, 0)
            thisModel += 1
        run_all(Models)
        for i in range(len(Models)):
            fitnesses.append(Models[i].fitness)
        current_start = current_last
        current_last = current_start + MaxModels
    best = heapq.nsmallest(1, range(len(fitnesses)), fitnesses.__getitem__)
    best_fitness = fitnesses[best[0]]
    best_model = Models[best[0]].makeCopy()
    elapsed = time.time() - GlobalVars.StartTime
    Models[0].template.printMessage(f"Elapse time = {elapsed / 60:.1f} minutes \n")
    Models[0].template.printMessage(f"Best overall fitness = {best_fitness:4f}, model {best_model.modelNum}")
    with open(os.path.join(model_template.homeDir, "finalControlFile.mod"), 'w') as control:
        control.write(best_model.control)
    resultFilePath = os.path.join(model_template.homeDir, "finalresultFile.lst")
    with open(resultFilePath, 'w') as result:
        result.write(GlobalVars.BestModelOutput)
    Models[0].template.printMessage(f"Final outout from best model is in {resultFilePath}")
    model_template.printMessage(f"Unique model list in  {GlobalVars.SavedModelsFile}") 
    Models = None  # free up memory??   stil not working
    gc.collect()
    return best_model
