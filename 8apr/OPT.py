from os import error
import model_code
import GlobalVars
import numpy as np
import skopt
# install packages for specific version of python, e.g c:\users\msale\appdata\local\programs\python\python38\python -m pip install scikit-optimize
from skopt import Optimizer
import run_downhill
from copy import deepcopy, copy 
print("\n\n\n\n\n\nNew Model")
import Templater
import runAllModels
import time
import logging
import heapq
import warnings
import os # not needed in 3.10
from datetime import timedelta 
logger = logging.getLogger(__name__)
Models = [] # hold NONMEM models # will put models here to query them and not rerun models, will eventually be a MongoDB
#def get_max_values(model_template):
# run paralell? https://scikit-optimize.github.io/stable/auto_examples/parallel-optimization.html
def run_skopt(model_template:Templater.template) -> Templater.model: 
    """run any of  the three skopt algorithms. Algorithm is define in template.options['algorithm'], which is read from the options json file
    returns the single best model after the search """
    np.random.seed(model_template.options['random_seed'])
    downhill_q = model_template.options['downhill_q'] 
    # just get list of numbers, of len of each token group
    Num_Groups = []
    #Keys = model_template.tokens.keys() 
    for thisKey in model_template.tokens.keys():   
        tokenGroup = model_template.tokens.get(thisKey) 
        numerical_group = list(range(len(tokenGroup)))
        this_x = skopt.space.Categorical(categories = numerical_group,transform="onehot")
        Num_Groups.append(this_x)       
    model_num = 0
    start = time.time()    
    # from doc https://scikit-optimize.github.io/dev//_downloads/scikit-optimize-docs.pdf
    # command to install is pip install scikit-optimize
    from skopt import Optimizer
    
    runAllModels.InitModellist(model_template)
    #opt = Optimizer(Num_Groups,n_jobs = 1, base_estimator="GBRT")
    opt = Optimizer(Num_Groups,n_jobs = 5, base_estimator=model_template.options['algorithm'])
    print(f"Algorithm is {model_template.options['algorithm']}")
    # https://scikit-optimize.github.io/stable/auto_examples/ask-and-tell.html 
    
    niter_no_change = 0
    for this_iter in range(model_template.options['num_generations']): 
        print(f"Starting generation/iteration {this_iter}, {model_template.options['algorithm']} algorithm at {time.asctime()}" )
         
        suggestion_start_time = time.time()
        suggested = opt.ask(n_points = model_template.options['popSize'])
        print("Elapse time for sampling step # %d =  %.1f seconds" % (this_iter, (time.time() - suggestion_start_time)))
        Models = []
        maxes = model_template.gene_max
        lengths = model_template.gene_length
        for thisInts,model_num in zip(suggested,range(len(suggested))):
            code = model_code.model_code(thisInts,"Int",maxes,lengths)
            Models.append(Templater.model(model_template,code,model_num,True,this_iter))
        runAllModels.run_all(Models) #popFullBits,model_template,0)  # argument 1 is a full GA/DEAP individual
        # copy fitnesses back
        fitnesses = [None]*len(suggested)
        for i in range(len(suggested)):
            fitnesses[i] = Models[i].fitness
         ### run downhill??
        if this_iter % downhill_q == 0 and this_iter > 0: 
            # pop will have the fitnesses without the niche penalty here
            # add local exhausitve search here??
            # temp_fitnessses = copy(fitnesses)
            # downhill with NumNiches best models
            print(f"Starting downhill, iteration = {this_iter} at {time.asctime()}")
            # can only use all models in GP, not in RF or GA
            if model_template.options['algorithm'] == "GP":
                new_models, worst_inds, all_models = run_downhill.run_downhill(Models, return_all = True) 
            else:
                new_models, worst_inds = run_downhill.run_downhill(Models, return_all = False) 
            # replace worst_inds with new_inds, after hof update
            # can't figure out why sometimes returns a tuple and sometimes a scalar
            ## rundownhill returns on the fitness and the integer representation!!, need to make GA model from that
            ## which means back calculate GA/full bit string reprentation
            #full_bit_inds = []
            for i in range(len(new_models)):
                Models[worst_inds[i]] = copy(new_models[i])
                fitnesses[worst_inds[i]] = new_models[i].fitness
                suggested[worst_inds[i]] = new_models[i].model_code.IntCode
            if model_template.options['algorithm'] == "GP":
                print("add in all models to suggested and fitness for GP")
 
        tell_start_time = time.time()  
        opt.tell( suggested, fitnesses) # this returns only one (the best???), just updates the model for the next ask
        
        print("Elapse time for tell step %d =  %.1f seconds ---" % (this_iter, (time.time() - tell_start_time)))
        # copy fitnesses back
         
        best = heapq.nsmallest(1, range(len(fitnesses)), fitnesses.__getitem__)
        print(f"Best fitness this iteration = {fitnesses[best[0]]:4f}  at {time.asctime()}" )
        print(f"Best overall fitness = {GlobalVars.BestModel.fitness:4f}, iteration {GlobalVars.BestModel.generation}, model {GlobalVars.BestModel.modelNum}" )
    if  model_template.options["final_fullExhaustiveSearch"]:
        print(f"Starting final downhill, iteration = {this_iter}")
            # can only use all models in GP, not in RF or GA
        if model_template.options['algorithm'] == "GP":
            new_models, worst_inds, all_models = run_downhill.run_downhill(Models, return_all = True) 
        else:
            new_models, worst_inds = run_downhill.run_downhill(Models, return_all = False) 
        for i in range(len(new_models)):
            Models[worst_inds[i]] = copy(new_models[i])
            fitnesses[worst_inds[i]] = new_models[i].fitness 
            # need max values to convert int to bits
    with open(os.path.join(model_template.homeDir,"InterimControlFile.mod"),'w') as control:
        control.write(GlobalVars.BestModel.control)
    resultFilePath = os.path.join(GlobalVars.BestModel.template.homeDir,"InterimresultFile.lst")
    with open(resultFilePath,'w') as result:
        result.write(GlobalVars.BestModelOutput)
    elapsed = time.time() - start 
    if niter_no_change > GlobalVars.BestModel.fitness:
        last_best_fitness = GlobalVars.BestModel.fitness
        niter_no_change = 0
    else:
        niter_no_change += 1
    print(f'No change in fitness in {niter_no_change} iteration')
    print(f"total time = {(time.time() - start)/60:.2f} minutes")
    with open(os.path.join(model_template.homeDir,"finalControlFile.mod"),'w') as control:
        control.write(GlobalVars.BestModel.control)
    resultFilePath = os.path.join(GlobalVars.BestModel.template.homeDir,"finalresultFile.lst")
    with open(resultFilePath,'w') as result:
        result.write(GlobalVars.BestModelOutput)
    print(f"Final outout from best model is in {resultFilePath}") 
    print(f'Best overall solution =[{GlobalVars.BestModel.model_code.IntCode}], Best overall fitness ={GlobalVars.BestModel.fitness:.6f} ') 
    final_model = copy(GlobalVars.BestModel)
    return  final_model 
