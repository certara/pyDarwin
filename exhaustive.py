import numpy as np  
import sys
from sympy import collect
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
import rpy2   
import gc 
from os.path import exists
import rpy2.robjects as robjects 
def exhaustive(model_template):
    start = time.time()    
    Num_Groups = [] 
    for thisKey in model_template.tokens.keys():   
        tokenGroup = model_template.tokens.get(thisKey) 
        Num_Groups.append(list(range(len(tokenGroup))))   
    codes = np.array(np.meshgrid(*Num_Groups)).T.reshape(-1,len(Num_Groups))
    # convert to regular list
    codes = codes.tolist() 
    Models = []
    maxes = model_template.gene_max
    lengths = model_template.gene_length
    for thisInts,model_num in zip(codes,range(len(codes))):
        code = model_code.model_code(thisInts,"Int",maxes,lengths)
        Models.append(Templater.model(model_template,code,model_num,True,1 )) # slot argument will always be the same, model num will change
    runAllModels.InitModellist(model_template)
    runAllModels.run_all(Models)  
    fitnesses = []
    for i in range(len(Models)):
        fitnesses.append(Models[i].fitness) 
        Models[i] = None
    best = heapq.nsmallest(1, range(len(fitnesses)), fitnesses.__getitem__) 
    best_fitness = fitnesses[best[0]]
    best_model = deepcopy(Models[best[0]]) 
    elapsed = time.time() - start
    print(f"Elapse time = {elapsed/60:.1f} minutes \n")  
    print(f"Best overall fitness = {best_fitness:4f}, model {best_model.modelNum}" )
    with open(os.path.join(model_template.homeDir,"finalControlFile.mod"),'w') as control:
        control.write(best_model.control)
    resultFilePath = os.path.join(model_template.homeDir,"finalresultFile.lst")
    with open(resultFilePath,'w') as result:
         result.write(GlobalVars.BestModelOutput)
    print(f"Final outout from best model is in {resultFilePath}")
    print("Number of references to Models before = " + str(sys.getrefcount(Models)))
    Models = None # free up memory??  
    print("Number of references to Models after = " + str(sys.getrefcount(Models)))
    gc.collect()
    return best_model
 
 
