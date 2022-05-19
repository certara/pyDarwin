# https://programtalk.com/python-examples/deap.tools.HallOfFame/
# deap seems to need python 3.7.3
from copy import deepcopy, copy
from datetime import timedelta
import random
from itertools import compress
import deap
from deap import base 
from deap import creator
from deap import tools 
import os
import time
import logging 
import numpy as np 
from scipy.spatial import distance_matrix
import heapq

import darwin.GlobalVars as GlobalVars

from darwin.ModelCode import ModelCode
from darwin.run_downhill import run_downhill
from darwin.runAllModels import InitModellist, run_all
from darwin.Template import Template
from darwin.Model import Model

np.warnings.filterwarnings('error', category=np.VisibleDeprecationWarning)
logger = logging.getLogger(__name__) 
   

def get_best_in_niche(pop:list,temp_fitnesses:list,num_niches:int,niche_radius:int,crash_value:float):
    """finds the best model (by fitness) in each niche (defined by the niche radius), Starts with the best model, then finds all models within
    niche_radius of that model. That becomes the first niche. Then, finds the best model that is not in the first niche, then all models withint
    niche radius of that model, etc. Returns a list of the models and list of their fitnesses"""
    fitnesses = copy(temp_fitnesses) 
    best = []  ## hold the best in each niche
    best_fitnesses = [] 
    not_in_niche = [True]*len(fitnesses) 
    for _ in range(num_niches):
        # below should exclude those already in a niche, as  the fitness should be set to 999999
        this_best =  heapq.nsmallest(1, range(len(fitnesses)), fitnesses.__getitem__) 
        # get the best in the current population
        cur_ind = copy(pop[this_best[0]])
        # add the best in this_niche to the list of best
        best.append(cur_ind)
        best_fitnesses.append((fitnesses[this_best][0],))      # return array of tuples  
        # get the distance of all from the best
        distance = distance_matrix( [cur_ind], pop)[0]
        # get list of all < niche radius
        in_niche = (distance <= niche_radius)  
        # and remove those already a niche 
        in_niche = np.array(list(compress(in_niche,not_in_niche)))
        in_niche = np.array([i for i, x in enumerate(in_niche) if x]) 
         
        # add those in a niche to the list of not already in niche
        not_in_niche[in_niche[0]] = False
        # set the fitness of all in this niche to large value, so they aren't in the next seach for best
        # change fitness of those in this niche to 9999999
        fitnesses[in_niche[0]] = crash_value
        # set the fitness of all in this niche to large value, so they aren't in the next seach for best 
        if all(fitnesses == crash_value): # check if all are already in a niche
            break
    return best, best_fitnesses
    


def sharing(distance:float,niche_radius:int,sharing_alpha:float)-> float:
    res = 0
    if distance<=niche_radius:
        res += 1 - (distance/niche_radius)**sharing_alpha
    return res

def add_sharing_penalty(pop,niche_radius,sharing_alpha,niche_penalty):
    """issue with negative sign, if OFV/fitness is +ive, then sharing improves it
     if OFV/fitness is negative, it makes it worse (larger)
     and penalty should be on additive scale, as OFV may cross 0
     goals are:
     keep the best individual in any niche better than the best individual in the next niche.
     all the other MAY be lower.
     so:
       first identify which individualas are in niches.
       then, find difference between best in this niche and best in next niche.
       line by distance from best ( 0 for best) and worst in this niche
       with max niche penalty
       subtract from fitness"""
   
 
    for ind in zip(pop): 
        dists = distance_matrix(ind, pop)[0]
        tmp = [sharing(d,niche_radius,sharing_alpha) for d in dists]
        crowding = sum(tmp)
        penalty = np.exp((crowding-1)*niche_penalty)-1 # sometimes deap object fitness has values,and sometimes just a tuple?
        if isinstance(ind[0].fitness,tuple):
            ind[0].fitness = (ind[0].fitness.values[0] + penalty), # weighted values (wvalues) changes with this
        else: 
            ind[0].fitness.values = (ind[0].fitness.values[0] + penalty), # weighted values (wvalues) changes with this
    return 
 
def run_GA(model_template: Template)-> Model:
    """ Runs GA, 
    Argument is model_template, which has all the needed information """
    GlobalVars.StartTime = time.time()    
    InitModellist(model_template)
    pop_size = model_template.options['popSize'] 
    best_fitness = crash_value = model_template.options['crash_value'] 
    #num_niches = model_template.options['num_niches']
    niche_radius = model_template.options['niche_radius']  
    downhill_q = model_template.options['downhill_q'] 
    elitist_num = model_template.options['elitist_num'] 
    sharing_alpha = model_template.options['sharing_alpha']
    niche_penalty = model_template.options['niche_penalty']   
    numBits = int(np.sum(model_template.gene_length))
    
    print("\n\n\n\nNew Model")
    creator.create("FitnessMin", deap.base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)

    toolbox = deap.base.Toolbox()
    # Attribute generator 
    #                      define 'attr_bool' to be an attribute ('gene')
    #                      which corresponds to integers sampled uniformly
    #                      from the range [0,1] (i.e. 0 or 1 with equal
    #                      probability) 
    random.seed(model_template.options['random_seed'])
    toolbox.register("attr_bool", random.randint, 0, 1)

    # Structure initializers
    #                         define 'individual' to be an individual
    #                         consisting of 100 'attr_bool' elements ('genes')
    
    
    toolbox.register("individual", tools.initRepeat, creator.Individual, 
        toolbox.attr_bool, numBits)

    # define the population to be a list of individuals
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # the goal ('fitness') function to be maximized  
    #models = json.loads(open('e:\\msale\\fda\\ga_niche_downhill\\models.json','r').read()) 
    # register the crossover operator
    if model_template.options['xover'] == "cxOnePoint":
        toolbox.register("mate", tools.cxOnePoint)
    ## other cross over options here
    # register a mutation operator with a probability to
    # flip each attribute/gene of 0.05
    if model_template.options['mutate'] == "flipBit":
        toolbox.register("mutate", tools.mutFlipBit, indpb=model_template.options['indpb'])

    # operator for selecting individuals for breeding the next
    # generation: each individual of the current generation
    # is replaced by the 'fittest' (best) of three individuals
    # drawn randomly from the current generation.
    if model_template.options['selection'] == "tournament":
        toolbox.register("select", tools.selTournament, tournsize=model_template.options['selection_size'])
 
    # create an initial population of pop_size individuals (where
    # each individual is a list of bits [0|1])
    popFullBits = toolbox.population(n=pop_size)   
    best_for_elitism = toolbox.population(n=elitist_num)   
    # CXPB  is the probability with which two individuals
    #       are crossed
    #
    # MUTPB is the probability for mutating an individual
    CXPB = model_template.options['crossOver'] 
    MUTPB =model_template.options['mutationRate']      
    ## argumen tot run_all is integer codes!!!!!
    Models = []
    maxes = model_template.gene_max
    lengths = model_template.gene_length
    for thisFullBits,model_num in zip(popFullBits,range(len(popFullBits))):
        code = ModelCode(thisFullBits, "FullBinary", maxes, lengths)
        Models.append(Model(model_template, code, model_num, True, 0))
    run_all(Models) #popFullBits,model_template,0)  # argument 1 is a full GA/DEAP individual
    print(f"Best overall fitness = {GlobalVars.BestModel.fitness:4f}, iteration {GlobalVars.BestModel.generation}, model {GlobalVars.BestModel.modelNum}" )
     
    fitnesses = [None]*len(Models)
    for ind,pop,fit in zip(Models,popFullBits,range(len(Models))):    
        pop.fitness.values = (ind.fitness,)  
        fitnesses[fit] = (ind.fitness,)
    best_index = heapq.nsmallest(elitist_num, range(len(fitnesses)), fitnesses.__getitem__)
     
    for i in range(elitist_num): #best_index:  
            best_for_elitism[i] = deepcopy(popFullBits[best_index[i]]) 
     
    allbest =  copy(popFullBits[heapq.nsmallest(1, range(len(fitnesses)), fitnesses.__getitem__)[0]].fitness.values[0])
    # Variable keeping track of the number of generations
    generation = 0
    # Begin evolution 

    generations_no_change = 0
    current_overall_best_fitness = crash_value
    model_template.printMessage(f"generation 0 fitness = {allbest:.4f}")
    num_generations  = model_template.options['num_generations']
    while generation < num_generations:
        # A new generation
        generation += 1 
        model_template.printMessage("-- Starting Generation %i --" % generation)
        
        add_sharing_penalty(popFullBits,niche_radius,sharing_alpha,niche_penalty) # will change the values in pop, but not in fitnesses, need to run downhill from fitness values, not from pop
                             # so fitnesses in pop are only used for selection in GA
        # do not copy new fitness to models, models should be just the "real" fitness
        # Select the next generation individuals
        offspring = toolbox.select(popFullBits, len(popFullBits))
        # Clone the selected individuals, otherwise will linked to orginal, by reference    
        offspring = list(map(toolbox.clone, offspring))
    
        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            # cross two individuals with probability CXPB
             # dont need to copy child1, child2 back to offspring, done internally by DEAP
            # from https://deap.readthedocs.io/en/master/examples/ga_onemax.html
            #  "In addition they modify those individuals within the toolbox container and we do not need to reassign their results.""
  
            if random.random() < CXPB:
                toolbox.mate(child1, child2)
  
        for mutant in offspring:

            # mutate an individual with probability MUTPB
            if random.random() < MUTPB:
                toolbox.mutate(mutant)
                del mutant.fitness.values
    
        # Evaluate the individuals with an invalid fitness 
        # will run entire population, but, at some point, check a database to see if already run
        popFullBits = offspring
        # add hof back in at first  positions, maybe should be random???
        # looks like we need to do this manually when we add in niches, can't use hof., replace worst, based on original fitness (without niche penalty)
        worst_inds = heapq.nlargest(elitist_num, range(len(fitnesses)), fitnesses.__getitem__)
        # put elitist back in in place of worst
        for i in range(elitist_num):
            popFullBits[worst_inds[i]] = copy(best_for_elitism[i]) # hof.items need the fitness as well?
        
        cur_gen_best_ind = -1 
        
        Models = []  
        for thisFullBits,model_num in zip(popFullBits,range(len(popFullBits))):
            code = ModelCode(thisFullBits, "FullBinary", maxes, lengths)
            Models.append(Model(model_template, code, model_num, True, generation))
        run_all(Models) #popFullBits,model_template,0)  # argument 1 is a full GA/DEAP individual
        model_template.printMessage(f"Best overall fitness = {GlobalVars.BestModel.fitness:4f}, iteration {GlobalVars.BestModel.generation}, model {GlobalVars.BestModel.modelNum}" )
        
        fitnesses = [None]*len(Models)
        for ind,pop,fit in zip(Models,popFullBits,range(len(Models))):    
            pop.fitness.values = (ind.fitness,)  
            fitnesses[fit] = (ind.fitness,)
        best_index = heapq.nsmallest(elitist_num, range(len(fitnesses)), fitnesses.__getitem__)
     
        for i in range(elitist_num): #best_index:  
            best_for_elitism[i] = deepcopy(popFullBits[best_index[i]]) 
        
        best_index = heapq.nsmallest(1, range(len(fitnesses)), fitnesses.__getitem__)[0]
        single_best_model = copy(Models[best_index])
        if generation % downhill_q == 0 and generation > 0: 
            # pop will have the fitnesses without the niche penalty here
            # add local exhausitve search here??
            # temp_fitnessses = copy(fitnesses)
            # downhill with NumNiches best models
            model_template.printMessage(f"Starting downhill generation = {generation}  at {time.asctime()}")
            best_index = heapq.nsmallest(Models[0].template.options['num_niches'], range(len(fitnesses)), fitnesses.__getitem__)
            best_inds = []
            for i in best_index:  
                best_inds.append(copy(Models[i]))
           
            new_models, worst_inds = run_downhill(Models)
            model_template.printMessage(f"Best overall fitness = {GlobalVars.BestModel.fitness:4f}, iteration {GlobalVars.BestModel.generation}, model {GlobalVars.BestModel.modelNum}" )
            # replace worst_inds with new_inds, after hof update
            # can't figure out why sometimes returns a tuple and sometimes a scalar
            # run_downhill return on the fitness and the integer representation!!, need to make GA model from that
            # which means back calculate GA/full bit string reprentation 
            for i in range(len(new_models)): 
                Models[worst_inds[i]] = copy(new_models[i])
                # sometimes fitness is float, sometimes tuple
                if isinstance(new_models[i].fitness, tuple): 
                    fitnesses[worst_inds[i]] = new_models[i].fitness[0]
                else:
                    fitnesses[worst_inds[i]] = (new_models[i].fitness,)
            best_index = heapq.nsmallest(1, range(len(fitnesses)), fitnesses.__getitem__)[0]
            model_template.printMessage(f"Done with downhill step, {generation}. best fitness = {fitnesses[best_index]}")      
            
            single_best_model = copy(Models[best_index])
            ## redo best_for_elitism, after downhill
    
            best_index = heapq.nsmallest(elitist_num, range(len(fitnesses)), fitnesses.__getitem__)
            num_bits = len(Models[best_index[i]].model_code.FullBinCode)
            for i in range(elitist_num): #best_index:  
                best_for_elitism[i][0:num_bits] = Models[best_index[i]].model_code.FullBinCode # this is GA , so need fullbinary code
                best_for_elitism[i].fitness.values =  (Models[best_index[i]].fitness,)

        cur_gen_best_ind =  heapq.nsmallest(1, range(len(fitnesses)), fitnesses.__getitem__) 
        best_fitness = fitnesses[cur_gen_best_ind[0]]
        # here expects fitnesses to be tuple, but isn't after downhill
        if not type(best_fitness) is tuple:
            best_fitness = (best_fitness,) 
        model_template.printMessage(f"Current generation best genome = {Models[cur_gen_best_ind[0]].model_code.FullBinCode}, best fit = {best_fitness[0]:.4f}")
        
        if best_fitness[0] < current_overall_best_fitness:
            model_template.printMessage(f"Better fitness found, generation = {generation}, new best fitness = {best_fitness[0]:.4f}")
            current_overall_best_fitness = best_fitness[0] # 
            generations_no_change = 0
        else:
            generations_no_change += 1 
            model_template.printMessage(f"No change in fitness for {generations_no_change} generations, best fitness = {current_overall_best_fitness:.4f}")
    print(f"-- End of GA component at {time.asctime()} --") 
    # get current best individual
    cur_best_ind =  heapq.nsmallest(1, range(len(fitnesses)), fitnesses.__getitem__)[0]
    final_model = copy(Models[cur_best_ind])
   
    if  model_template.options["final_fullExhaustiveSearch"]:
        # start with standard downhill 
        # change generation of models to final
        for i in range(len(Models)):
            Models[i].generation = "final"
        best_index = heapq.nsmallest(Models[0].template.options['num_niches'], range(len(fitnesses)), fitnesses.__getitem__)
        best_inds = []
        for i in best_index: # need deepcopy?
            best_inds.append(copy(Models[i]))
         
        new_models, worst_inds = run_downhill(Models)
        for i in range(len(new_models)): 
            fitnesses[worst_inds[i]] = new_models[i].fitness
      
        best_index = heapq.nsmallest(Models[0].template.options['num_niches'], range(len(fitnesses)), fitnesses.__getitem__)[0]
        model_template.printMessage(f"Done with final downhill step, {generation}. best fitness = {fitnesses[best_index]}")      
         
        single_best_model = copy(Models[best_index])
        if single_best_model.fitness < final_model.fitness:
            final_model = copy(single_best_model)
       
    with open(os.path.join(model_template.homeDir,"InterimControlFile.mod"),'w') as control:
        control.write(GlobalVars.BestModel.control)
    resultFilePath = os.path.join(GlobalVars.BestModel.template.homeDir,"InterimresultFile.lst")
    with open(resultFilePath,'w') as result:
        result.write(GlobalVars.BestModelOutput)     
    model_template.printMessage(f"-- End of Optimization at {time.asctime()}--")  
    elapsed = time.time() - GlobalVars.StartTime 
    model_template.printMessage(f"Elapse time = " + str(timedelta(seconds=elapsed)) + "\n") 
    model_template.printMessage(f'Best individual GA is {str(final_model.model_code.FullBinCode)} with fitness of {final_model.fitness:4f}') 
    model_template.printMessage(f"Best overall fitness = {GlobalVars.BestModel.fitness:4f}, iteration {GlobalVars.BestModel.generation}, model {GlobalVars.BestModel.modelNum}" )
    with open(os.path.join(model_template.homeDir,"finalControlFile.mod"),'w') as control:
        control.write(final_model.control)
    resultFilePath = os.path.join(model_template.homeDir,"finalresultFile.lst")
    with open(resultFilePath,'w') as result:
         result.write(GlobalVars.BestModelOutput)
    model_template.printMessage(f"Final outout from best model is in {resultFilePath}")
    return final_model 
 