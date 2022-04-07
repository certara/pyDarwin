## deap seems to need python 3.9.5 or less, fails with 3.10
 
import GlobalVars
import Templater 
import logging 
import model_code
import time
from time import localtime
import sys
from os import error
from os.path import exists 
import errno 
import gc
import rpy2.robjects as robjects 
from rpy2.robjects.packages import importr
logger = logging.getLogger(__name__) 
import os  
def Set_up_Objects(model_template): 
    GlobalVars.BestModel = None
    GlobalVars.BestModelOutput  = None
    GlobalVars.TotalModels = 0 # whether run or found in json
    GlobalVars.UniqueModels = 0 # anything not found in allmodel.json nor already run
    GlobalVars.UniqueModelsToBest = 0
    GlobalVars.StartTime = 0
    GlobalVars.TimeToBest = 0
    GlobalVars.output = None # file for results.csv, opened and closed in main.RunSearch
    GlobalVars.allModelsDict = dict()
    GlobalVars.SlotRobjects = []
    gc.collect()    # garbage collect
    if model_template.options['useR']:  # set up R objects only if needed
        if not exists(model_template.options['postRunRCode']):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), model_template.options['postRunRCode'])
        with open(model_template.options['postRunRCode']) as f:
            model_template.RcodeTemplate=f.read()
            f.flush()
        GlobalVars.SlotRobjects = []
        for _ in range(model_template.options['num_parallel']):
            #GlobalVars.SlotRobjects.append(robjects.r(model_template.RcodeTemplate)) 
            robjects.r(model_template.RcodeTemplate)
            try:
               robjects.r['RPenalty']
            except:
                raise Exception("Cannot find RPenalty function in R instance") # no built in exception for this, just a general exception
            else:
                GlobalVars.SlotRobjects.append(robjects.r['RPenalty'])# function in R MUST be called RPenalty (case sensitive), returns the function

    return
def RunSearch(template_file: str,tokens_file: str,options_file: str) -> Templater.model: 
    """run algorithm selected in options_file, based on template_file and tokens_file
    At the end, write best control and output file to homeDir (specified in options_file) 
    options_file path name should, in general, be absolute, other file names can be absolute path or path relative to the homeDir  
    function returns the final model object"""
    
    GlobalVars.UniqueModelsToBest = 0 # need to reset as each algorithm starts
    try:   # path to tokens/template is relative to homeDir, probably need to give full path to template/tokens??
        model_template = Templater.template(template_file,tokens_file,options_file)
    except:   
        logger.error(error)
        raise    
    Set_up_Objects(model_template)
    genome_length = sum(model_template.gene_length)
    GlobalVars.output = open("results.csv","w")
    # initialize a trival model for the global best 
    nullCode = model_code.model_code([0]*genome_length,"None",model_template.gene_max,model_template.gene_length)
    GlobalVars.BestModel = Templater.model(model_template,nullCode,-99,True,-99) # set alreadyInt to True to keep decode from running
    GlobalVars.BestModel.fitness = model_template.options['crash_value'] + 1
    GlobalVars.BestModelOutput = "No output yet" 
    GlobalVars.StartTime = time.time()
    algorithm  =  model_template.options['algorithm'] 
    
    print("Search start time =")
    print(time.asctime(localtime()))
    if not algorithm in ["GBRT","RF","GP","GA","EXHAUSTIVE","PSO"]:
        print(f"Algorithm {algorithm} is not available")
        sys.exit()
    if algorithm in ["GBRT","RF","GP"]:
        import OPT 
        final = OPT.run_skopt(model_template)       
    if algorithm == "GA":
        import GA 
        final = GA.run_GA(model_template)
    if algorithm == "EXHAUSTIVE":
        import exhaustive
        final = exhaustive.exhaustive(model_template)
    if algorithm == "PSO":
        import PSO
        final =  PSO.run_pso(model_template)
    print(f"Number of unique models to best model = {GlobalVars.UniqueModelsToBest}")  
    print(f"Time to best model = {GlobalVars.TimeToBest/60:0.1f} minutes")
    GlobalVars.output.close()
    GlobalVars.SlotRobjects = None
    print("Search end time =")
    print(time.asctime(localtime()))
    gc.collect()    
    return final
if __name__ == '__main__': 
     
    print(f"#\n#\n# Start exhaustive search at {time.asctime()}..............................................")
    best_modelEx = RunSearch("C:/fda/FDA-OGD-ML/example_small_template.txt","C:/fda/FDA-OGD-ML/example_small_tokens.json","C:/fda/FDA-OGD-ML/exhaustiveoptions.json")
    print(f"#\n#\n# Start GA at {time.asctime()}..............................................")
    best_modelGA = RunSearch("C:/fda/FDA-OGD-ML/example_small_template.txt","C:/fda/FDA-OGD-ML/example_small_tokens.json","C:/fda/FDA-OGD-ML/GAoptions.json")  
    print(f"#\n#\n# Start RF at {time.asctime()}..............................................")
    best_modelRF = RunSearch("C:/fda/FDA-OGD-ML/example_small_template.txt","C:/fda/FDA-OGD-ML/example_small_tokens.json","C:/fda/FDA-OGD-ML/RFoptions.json")
    print(f"#\n#\n# Start GBRT at {time.asctime()}............................................")
    best_modelGBRT = RunSearch("C:/fda/FDA-OGD-ML/example_small_template.txt","C:/fda/FDA-OGD-ML/example_small_tokens.json","C:/fda/FDA-OGD-ML/GBRToptions.json")
    print(f"#\n#\n# Start GP at {time.asctime()}..............................................")
    best_modelGP = RunSearch("C:/fda/FDA-OGD-ML/example_small_template.txt","C:/fda/FDA-OGD-ML/example_small_tokens.json","C:/fda/FDA-OGD-ML/GPoptions.json")

    print("done")
