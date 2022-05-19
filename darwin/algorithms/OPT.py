import numpy as np
import skopt
from copy import copy
import time
import logging
import heapq
import os  # not needed in 3.10

import darwin.GlobalVars as GlobalVars

from darwin.ModelCode import ModelCode
from darwin.run_downhill import run_downhill
from darwin.Template import Template
from darwin.Model import Model
from darwin.runAllModels import InitModellist, run_all

logger = logging.getLogger(__name__)
Models = []  # hold NONMEM models # will put models here to query them and not rerun models, will eventually be a MongoDB


# run parallel? https://scikit-optimize.github.io/stable/auto_examples/parallel-optimization.html
def run_skopt(model_template: Template) -> Model:
    """run any of  the three skopt algorithms. Algorithm is define in Template.options['algorithm'], which is read from the options json file
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
    GlobalVars.StartTime = time.time()    
    # from doc https://scikit-optimize.github.io/dev//_downloads/scikit-optimize-docs.pdf
    # command to install is pip install scikit-optimize
    from skopt import Optimizer
    
    InitModellist(model_template)
    #opt = Optimizer(Num_Groups,n_jobs = 1, base_estimator="GBRT")
    # for parallel, will need and array of N number of optimizaer,  n_jobs doesn't seem to do anything
    opt = Optimizer(Num_Groups,n_jobs = 1, base_estimator=model_template.options['algorithm'])
    model_template.printMessage(f"Algorithm is {model_template.options['algorithm']}")
    # https://scikit-optimize.github.io/stable/auto_examples/ask-and-tell.html 
    
    niter_no_change = 0 
    maxes = model_template.gene_max
    lengths = model_template.gene_length
    for this_iter in range(model_template.options['num_generations']): 
        model_template.printMessage(f"Starting generation/iteration {this_iter}, {model_template.options['algorithm']} algorithm at {time.asctime()}" )
         
        suggestion_start_time = time.time()
        # will need to ask for 1/10 of the total models if run 10  way parallel
        suggested = opt.ask(n_points = model_template.options['popSize'])
        model_template.printMessage("Elapse time for sampling step # %d =  %.1f seconds" % (this_iter, (time.time() - suggestion_start_time)))
        Models = [] # some other method to clear memory??
        for thisInts,model_num in zip(suggested,range(len(suggested))):
            code = ModelCode(thisInts, "Int", maxes, lengths)
            Models.append(Model(model_template, code, model_num, True, this_iter))
        run_all(Models) #popFullBits,model_template,0)  # argument 1 is a full GA/DEAP individual
        # copy fitnesses back
        fitnesses = [None]*len(suggested)
        for i in range(len(suggested)):
            fitnesses[i] = Models[i].fitness
         ### run downhill??
        if this_iter % downhill_q == 0 and this_iter > 0: 
            # pop will have the fitnesses without the niche penalty here
            
            model_template.printMessage(f"Starting downhill, iteration = {this_iter} at {time.asctime()}")
            # can only use all models in GP, not in RF or GA
            if model_template.options['algorithm'] == "GP":
                new_models, worst_inds, all_models = run_downhill(Models, return_all = True)
            else:
                new_models, worst_inds = run_downhill(Models, return_all = False)
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
                model_template.printMessage("add in all models to suggested and fitness for GP")
 
        tell_start_time = time.time() 
        # I think you can tell with all models, but not sure 
        opt.tell(suggested, fitnesses) 
        
        model_template.printMessage("Elapse time for tell step %d =  %.1f seconds ---" % (this_iter, (time.time() - tell_start_time)))
        # copy fitnesses back
         
        best = heapq.nsmallest(1, range(len(fitnesses)), fitnesses.__getitem__)
        model_template.printMessage(f"Best fitness this iteration = {fitnesses[best[0]]:4f}  at {time.asctime()}" )
        model_template.printMessage(f"Best overall fitness = {GlobalVars.BestModel.fitness:4f}, iteration {GlobalVars.BestModel.generation}, model {GlobalVars.BestModel.modelNum}" )
    if  model_template.options["final_fullExhaustiveSearch"]:
        model_template.printMessage(f"Starting final downhill, iteration = {this_iter}")
            # can only use all models in GP, not in RF or GA
        if model_template.options['algorithm'] == "GP":
            new_models, worst_inds, all_models = run_downhill(Models, return_all = True)
        else:
            new_models, worst_inds = run_downhill(Models, return_all = False)
        for i in range(len(new_models)):
            Models[worst_inds[i]] = copy(new_models[i])
            fitnesses[worst_inds[i]] = new_models[i].fitness 
            # need max values to convert int to bits
    with open(os.path.join(model_template.homeDir,"InterimControlFile.mod"),'w') as control:
        control.write(GlobalVars.BestModel.control)
    resultFilePath = os.path.join(GlobalVars.BestModel.template.homeDir,"InterimresultFile.lst")
    with open(resultFilePath,'w') as result:
        result.write(GlobalVars.BestModelOutput)
    #elapsed = time.time() - GlobalVars.StartTime 
    if niter_no_change > GlobalVars.BestModel.fitness:
        last_best_fitness = GlobalVars.BestModel.fitness
        niter_no_change = 0
    else:
        niter_no_change += 1
    model_template.printMessage(f'No change in fitness in {niter_no_change} iteration')
    model_template.printMessage(f"total time = {(time.time() - GlobalVars.StartTime)/60:.2f} minutes")
    with open(os.path.join(model_template.homeDir,"finalControlFile.mod"),'w') as control:
        control.write(GlobalVars.BestModel.control)
    resultFilePath = os.path.join(GlobalVars.BestModel.template.homeDir,"finalresultFile.lst")
    with open(resultFilePath,'w') as result:
        result.write(GlobalVars.BestModelOutput)
    model_template.printMessage(f"Final outout from best model is in {resultFilePath}") 
    model_template.printMessage(f'Best overall solution =[{GlobalVars.BestModel.model_code.IntCode}], Best overall fitness ={GlobalVars.BestModel.fitness:.6f} ') 
    final_model = copy(GlobalVars.BestModel)
    return  final_model 
