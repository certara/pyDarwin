import numpy as np   
from sympy import Max, collect
import Templater  
import time
from datetime import timedelta
import GlobalVars
import model_code
import runAllModels  
import errno
import heapq
from copy import deepcopy, copy  
import os 
import gc 
from os.path import exists 
def exhaustive(model_template):
    start = time.time()    
    Num_Groups = [] 
    for thisKey in model_template.tokens.keys():   
        tokenGroup = model_template.tokens.get(thisKey) 
        Num_Groups.append(list(range(len(tokenGroup))))   
    codes = np.array(np.meshgrid(*Num_Groups)).T.reshape(-1,len(Num_Groups))
    # convert to regular list
    codes = codes.tolist() 
    NumModels = len(codes) 
    maxes = model_template.gene_max
    lengths = model_template.gene_length
    # break into smaller list, for memory management
    MaxModels = model_template.options['max_model_list_size']  
    #Models = [None]*MaxModels
    current_start = 0
    current_last = current_start + MaxModels
    if current_last > NumModels:
        MaxModels = NumModels
        current_last = NumModels
    runAllModels.InitModellist(model_template)
    fitnesses = []
    while current_last <= NumModels: 
        if current_last > len(codes):
            current_last = len(codes)
        #for thisInts,model_num in zip(codes,range(len(codes))):
        thisModel = 0
        Models = [None]*MaxModels
        for thisInts,model_num in zip(codes[current_start:current_last],range(current_start,current_last)):
            code = model_code.model_code(thisInts,"Int",maxes,lengths)
            Models[thisModel] = Templater.model(model_template,code,model_num,True,0 ) 
            thisModel += 1
        runAllModels.run_all(Models)   
        for i in range(len(Models)):
            fitnesses.append(Models[i].fitness)  
        current_start = current_last 
        current_last = current_start + MaxModels
    best = heapq.nsmallest(1, range(len(fitnesses)), fitnesses.__getitem__) 
    best_fitness = fitnesses[best[0]]
    best_model = Models[best[0]].makeCopy()
    elapsed = time.time() - start
    print(f"Elapse time = {elapsed/60:.1f} minutes \n")  
    print(f"Best overall fitness = {best_fitness:4f}, model {best_model.modelNum}" )
    with open(os.path.join(model_template.homeDir,"finalControlFile.mod"),'w') as control:
        control.write(best_model.control)
    resultFilePath = os.path.join(model_template.homeDir,"finalresultFile.lst")
    with open(resultFilePath,'w') as result:
         result.write(GlobalVars.BestModelOutput)
    print(f"Final outout from best model is in {resultFilePath}") 
    Models = None # free up memory??   stil not working
    gc.collect()
    return best_model
 
 
