import gc 
import json
import os
from copy import copy
import numpy as np
from pathlib import Path
import threading
from time import sleep, time
import darwin.GlobalVars as GlobalVars

from .Template import Template
from .Model import Model

np.warnings.filterwarnings('error', category=np.VisibleDeprecationWarning)
allModelsDict = dict()


def init_model_list(model_template: Template):
    """Initializes model from template. Need Options first"""
    # write header to results file
    results_file = os.path.join(model_template.homeDir, "results.csv")
    if os.path.exists(results_file):
        try:
            os.remove(results_file)
        except OSError:
            pass
    with open(results_file  ,"w") as resultsfile:
        resultsfile.write(f"Run Directory,Fitness,Model,ofv,success,covar,correlation #,ntheta,nomega,nsigm,condition,RPenalty,PythonPenalty,NMTran messages\n")
        model_template.printMessage(f"Writing intermediate output to {results_file}")
        resultsfile.flush()
        resultsfile.close()
    global allModelsDict

    if "usePreviousModelsList" in model_template.options.keys():
        if model_template.options['usePreviousModelsList']:
            try:
                models_list = Path(model_template.options['PreviousModelsList'])
                if models_list.name.lower() == "none":
                    # remove default file name if no model specified and set name to default
                    if os.path.exists(os.path.join(model_template.homeDir,"allmodel.json")):
                        os.remove(os.path.join(model_template.homeDir,"allmodel.json"))
                    GlobalVars.SavedModelsFile = os.path.join(model_template.homeDir,"allmodel.json")
                else:
                    if models_list.is_file() and not models_list.name.lower() == "none":
                        with open(models_list) as json_file:
                            allModelsDict = json.load(json_file)
                            GlobalVars.SavedModelsFile = model_template.options['PreviousModelsList']
                            model_template.printMessage(f"Using Saved model list from  {GlobalVars.SavedModelsFile}")
                    else:
                        model_template.printMessage(f"Cannot find {models_list}, setting models list to empty")
                        GlobalVars.SavedModelsFile = model_template.options['PreviousModelsList']
                        allModelsDict = dict()
            except:
                model_template.printMessage(f"Cannot read {model_template.options['input_model_json']}, setting models list to empty")
                model_template.printMessage(f"Models will be saved as JSON {GlobalVars.SavedModelsFile}")
                GlobalVars.SavedModelsFile = os.path.join(model_template.homeDir,"allmodels.json")
                allModelsDict = dict()
           
            return
        else:
            allModelsDict = dict()
            if  "PreviousModelsList" in model_template.options:
                if not model_template.options['PreviousModelsList'].lower() == "none":
                    GlobalVars.SavedModelsFile = model_template.options['PreviousModelsList']

                else:
                    GlobalVars.SavedModelsFile = os.path.join(model_template.homeDir,"allmodels.json")
            else:
                GlobalVars.SavedModelsFile = os.path.join(model_template.homeDir,"allmodels.json")
                # delete the model if it is there
            if os.path.exists(GlobalVars.SavedModelsFile ):
                    os.remove(GlobalVars.SavedModelsFile )
        model_template.printMessage(f"Models will be saved as JSON {GlobalVars.SavedModelsFile}")
    else:
        GlobalVars.SavedModelsFile = os.path.join(model_template.homeDir,"allmodels.json")
                # delete the model if it is there
        if os.path.exists(GlobalVars.SavedModelsFile ):
            os.remove(GlobalVars.SavedModelsFile )


def Copy_to_Best(current_model: Model):
    """copies current model to the global best model"""

    GlobalVars.TimeToBest = time() -GlobalVars.StartTime
    GlobalVars.UniqueModelsToBest = GlobalVars.UniqueModels
    GlobalVars.BestModel.fitness = current_model.fitness
    GlobalVars.BestModel.control = current_model.control
    GlobalVars.BestModel.generation = current_model.generation
    GlobalVars.BestModel.modelNum = current_model.modelNum
    GlobalVars.BestModel.model_code = copy(current_model.model_code)
    GlobalVars.BestModel.ofv = current_model.ofv
    GlobalVars.BestModel.success = current_model.success
    GlobalVars.BestModel.covariance = current_model.covariance
    GlobalVars.BestModel.num_THETAs = current_model.num_THETAs
    GlobalVars.BestModel.OMEGA = current_model.OMEGA
    GlobalVars.BestModel.SIGMA = current_model.SIGMA
    GlobalVars.BestModel.num_OMEGAs = current_model.num_OMEGAs
    GlobalVars.BestModel.num_SIGMAs = current_model.num_SIGMAs
    GlobalVars.BestModel.correlation = current_model.correlation
    GlobalVars.BestModel.condition_num = current_model.condition_num
    GlobalVars.BestModel.Condition_num_test = current_model.Condition_num_test

    if current_model.source == "new":
        with open(os.path.join(current_model.runDir, current_model.outputFileName)) as file:
            GlobalVars.BestModelOutput = file.read()  # only save best model, other models can be reproduced if needed
    return

def run_all(models):
    """runs the models, always runs from integer representation, so for GA will need to convert to integer,
    for downhill, will need to convert to minimal binary, then to integer
    all_results maybe full binary (GA) or integer (not GA) or minimal binary (downhill)
    no return value, just updates Models"""
    start_model_num = models[0].modelNum  # will be 0 unless this is exhaustive and the model list is broken up into smaller lists
    fitnesses = [None]*len(models)   # all_results is full GA/DEAP individual, with fitness.values as tuple (currently empty)
    # will keep results in all_results, note that fitness MUST be assigned after call to this
    num_parallel = min(len(models), models[0].template.options['num_parallel'])
    slots = []
    num_models = len(models)
    started = [False]*num_models
    cur_model_num = 0
    models_list = []
    start_times = [] 
    #num_models = 0
    for cur_model_num in range(num_parallel) :
        # current_model = all_results_int[cur_model_num] # shallow copy, still linked but just bit string for GA
        # or downhill, integer string for others returns a model object = to be consistent with GP, RF, GBRF etc,
        # not the same as the model in all_results
        # will need to copy fitness, ntheta, OFV, success etc back to all_results when done, by model_num,
        # current model has only fitness  (scalar), not fitness.values (tuple)
        # all_results has fitness.values (a tuple)
        # check if already done here
        current_model = models[cur_model_num]
        models_list.append(models[cur_model_num])
        current_model.slot = cur_model_num # defines which slot, which R object to use
        current_code = str(current_model.model_code.IntCode)
         
        if current_code in allModelsDict:
            # make sure that the save model is complete
            if isinstance(allModelsDict[current_code], dict) and isinstance(allModelsDict[current_code]['fitness'],float):
                if current_model.copy_results(allModelsDict[current_code]): # returns True if copy is successful
                    current_model.copy_model()
                    current_model.source = "saved"
                    slots.append(threading.Thread(target=current_model.start_model, daemon=True))
                    start_times.append(time()) 
                    ## but don't run, just here as placeholder, is_alive will be False as it is never started
                    if GlobalVars.BestModel is None or current_model.fitness < GlobalVars.BestModel.fitness:
                        Copy_to_Best(current_model)
                else:
                    slots.append(threading.Thread(target=current_model.start_model, daemon=True))
                    slots[cur_model_num].start()  
                    start_times.append(time())  
                    current_model.source = "new"
                    GlobalVars.UniqueModels += 1
            else:
                
                slots.append(threading.Thread(target=current_model.start_model, daemon=True))
                slots[cur_model_num].start()  
                start_times.append(time())  
                current_model.source = "new"
                GlobalVars.UniqueModels += 1
        else:
              
            sleep(0.5) # not sure why this is needed, but seem to take a little while to create the thread??
            #current_model.slot = cur_model_num
            slots.append(threading.Thread(target=current_model.start_model, daemon=True))
            slots[cur_model_num].start()  
            start_times.append(time())   
            #num_models += 1  
            current_model.source = "new"
            GlobalVars.UniqueModels += 1
        started[cur_model_num] = True
        #slots.append(current_model)  # slots are the local/general model type, will need to copy fitness to all_results

    while not all(started):
        for slot_being_checked in range(num_parallel):
            current_slot = slots[slot_being_checked] # shallow copy, still linked to all_results
            current_model = models_list[slot_being_checked]
            # note that at this point, w are using local models, not GA/DEAP models, addressed in the object initialization
            if not current_slot.is_alive(): # model finished, collect results, start new on, IF not yet done
           # if current_model.check_all_done() == True: # model finished, collect results, start new on, IF not yet done

                nmtranMsgs = current_model.NMtranMSG
                fitnesses[current_model.modelNum-start_model_num] = current_model.fitness  # all we do with this fitness is print out the best, this fitness is not returned separately
                if GlobalVars.BestModel == None or current_model.fitness < GlobalVars.BestModel.fitness:
                    Copy_to_Best(current_model)
                if current_model.source == "new":
                    current_model.cleanup() # changes back to home_dir
                    # Integer code is common denominator for all, entered into dictionary with this 
                    if isinstance(current_model.jsonListRecord, dict):
                        allModelsDict[str(current_model.model_code.IntCode)] = current_model.jsonListRecord
                 

                with open(os.path.join(current_model.template.homeDir, "results.csv"),"a") as resultfile: # unfortunately, below needs to be all on one line, otherwise writes a new line
                    resultfile.write(f"{current_model.runDir},{current_model.fitness:.6f},{''.join(map(str, current_model.model_code.IntCode))},{current_model.ofv},{current_model.success},{current_model.covariance},{current_model.correlation},{current_model.num_THETAs},{current_model.num_OMEGAs},{current_model.num_SIGMAs},{current_model.condition_num},{current_model.post_run_Rpenalty},{current_model.post_run_Pythonpenalty},{current_model.NMtranMSG}\n")
                    resultfile.flush()
                    
                if current_model.template.isGA:
                    step_name = "Generation"
                else:
                    step_name = "Iteration"
                if current_model.generation == None: # will be None if this is a saved model, need to update
                    current_model.generation = current_model.generation
                if len(current_model.PRDERR) > 0:
                    PRDERR_text = " PRDERR = " + current_model.PRDERR
                else:
                    PRDERR_text = ""
                if current_model.fitness == current_model.template.options['crash_value']:
                    current_model.template.printMessage(f"{step_name} = {current_model.generation}, Model {current_model.modelNum:5},\t fitness = {current_model.fitness:.0f}, \t NMTRANMSG = {nmtranMsgs.strip()},{PRDERR_text}")
                else:
                    current_model.template.printMessage(f"{step_name} = {current_model.generation}, Model {current_model.modelNum:5},\t fitness = {current_model.fitness:.3f}, \t NMTRANMSG = {nmtranMsgs.strip()},{PRDERR_text}")

                current_slot = current_model.slot # keep slot number of next model

                #current_model.__del__()
                #gc.collect()
                # start new model  
                if not all(started): #cur_model_num < (num_models-1):
                    cur_model_num += 1
                    
                    models_list[current_slot] = models[cur_model_num]
                    #current_model = models[cur_model_num] # by reference
  
                    current_code = str(models_list[current_slot].model_code.IntCode)
    
                    models_list[current_slot].slot = current_slot # dont' think we need this anymore
                    if current_code in allModelsDict:
                         

                        if isinstance(allModelsDict[current_code], dict) and isinstance(allModelsDict[current_code]['fitness'],float):
                            if current_model.copy_results(allModelsDict[current_code]): # returns True if copy is successful
                                current_model.copy_model()
                                current_model.source = "saved"
                                slots.append(threading.Thread(target=current_model.start_model, daemon=True))
                                start_times.append(time()) 
                                ## but don't run, just here as placeholder, is_alive will be False
                                if GlobalVars.BestModel is None or current_model.fitness < GlobalVars.BestModel.fitness:
                                    Copy_to_Best(current_model)
                            else:
                                slots.append(threading.Thread(target=current_model.start_model, daemon=True))
                                slots[cur_model_num].start()  
                                start_times.append(time())  
                                current_model.source = "new"
                                GlobalVars.UniqueModels += 1                                                                                                
 
                        else: 
                            slots[current_slot] = threading.Thread(target=models_list[current_slot].start_model, daemon=True)
                            slots[current_slot].start()  
                            start_times.append(time())  
                            current_model.source = "new"
                            GlobalVars.UniqueModels += 1
                    else:
                        
                        sleep(0.5) # not sure why this is needed, but seem to take a little while to create the thread??
                        #current_model.slot = cur_model_num
                        slots[current_slot] = threading.Thread(target=models_list[current_slot].start_model, daemon=True)
                        slots[current_slot].start()  
                        start_times[current_slot] = time()
                        #num_models += 1  
                        current_model.source = "new"
                        GlobalVars.UniqueModels += 1
 
                    started[cur_model_num] = True
 
        # wait for all to finish
    done = [False] * num_parallel
    while not all(done):
        for slot_being_checked in range(num_parallel):
            
            if not done[slot_being_checked]: 
                #current model is the model object, not the same as in all_results
                if not slots[slot_being_checked].is_alive(): # current_model.check_all_done() == True: # model finished, collect results, start new on, IF not yet done
                    
                    current_model = models_list[slot_being_checked] ## still linked to all_results
                    if current_model.source == "new":
                        current_model.cleanup() # changes back to home_dir
                        
                        if isinstance(current_model.jsonListRecord, dict):
                            allModelsDict[str(current_model.model_code.IntCode)] = current_model.jsonListRecord

                    with open(os.path.join(current_model.template.homeDir, "results.csv"), "a") as resultfile: # unfortunately, below needs to be all on one line
                        resultfile.write(f"{current_model.runDir},{current_model.fitness:.6f},{''.join(map(str, current_model.model_code.IntCode))},{current_model.ofv},{current_model.success},{current_model.covariance},{current_model.correlation},{current_model.num_THETAs},{current_model.num_OMEGAs},{current_model.num_SIGMAs},{current_model.condition_num},{current_model.post_run_Rpenalty},{current_model.post_run_Pythonpenalty},{current_model.NMtranMSG}\n")
                        resultfile.flush()
                    nmtranMsgs = current_model.NMtranMSG
                    fitnesses[current_model.modelNum-start_model_num] = current_model.fitness
                    if GlobalVars.BestModel == None or current_model.fitness < GlobalVars.BestModel.fitness:
                        Copy_to_Best(current_model)
                    with open(os.path.join(current_model.template.homeDir, "results.csv")   ,"a") as resultfile:
                        resultfile.write(f"{current_model.runDir},{current_model.fitness:.6f},{''.join(map(str, current_model.model_code.IntCode))},{current_model.ofv},{current_model.success},{current_model.covariance},{current_model.correlation},{current_model.num_THETAs},{current_model.num_OMEGAs},{current_model.num_SIGMAs},{current_model.condition_num},{current_model.post_run_Rpenalty},{current_model.post_run_Pythonpenalty},{current_model.NMtranMSG}\n")
                        resultfile.flush()
                    if current_model.template.isGA:
                        step_name = "Generation"
                    else:
                        step_name = "Iteration"
                    if current_model.generation == None: # will be None if this is a saved model, need to update
                        current_model.generation = current_model.generation

                    if len(current_model.PRDERR) > 0:
                        PRDERR_text = " PRDERR = " + current_model.PRDERR
                    else:
                        PRDERR_text = ""
                    if current_model.fitness == current_model.template.options['crash_value']:
                        current_model.template.printMessage(f"{step_name} = {current_model.generation}, Model {current_model.modelNum:5},\t fitness = {current_model.fitness:.0f}, \t NMTRANMSG = {nmtranMsgs.strip()},{PRDERR_text}")
                    else:
                        current_model.template.printMessage(f"{step_name} = {current_model.generation}, Model {current_model.modelNum:5},\t fitness = {current_model.fitness:.3f}, \t NMTRANMSG = {nmtranMsgs.strip()},{PRDERR_text}")

                    current_model = slots[slot_being_checked] = None
                    gc.collect()
                    done[slot_being_checked] = True

    with open(os.path.join(models[0].template.homeDir, "allModels.json"), 'w', encoding ='utf-8') as f:
        json.dump(allModelsDict,f,indent=4, sort_keys=True, ensure_ascii=False)
    # write best model to output
    try:
        with open(os.path.join(models[0].template.homeDir, "InterimBestControl.mod"), 'w') as f:
            f.write(GlobalVars.BestModel.control)
        with open(os.path.join(models[0].template.homeDir, "InterimBestOutput.mod"), 'w') as f:
            f.write(GlobalVars.BestModelOutput)
    except:
        pass

    return

