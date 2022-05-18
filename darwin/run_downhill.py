import numpy as np
from copy import copy
import heapq
from scipy.spatial import distance_matrix

from .Templater import model
from .runAllModels import run_all
from .model_code import model_code


def get_best_in_niche(pop: list):
    """find the best in each of num_niches, return the full model
    argument is pop - list of full models
    return value is list of models, of length num_niches"""
    num_niches = pop[0].template.options['num_niches']
    niche_radius = pop[0].template.options['num_niches']
    crash_value = pop[0].template.options['crash_value']
    fitnesses = [None]*len(pop)
    for i in range(len(pop)):
        fitnesses[i] = pop[i].fitness
    best = []  ## hold the best in each niche
    best_fitnesses = [] 
    best_models = []
    not_in_niche = [True]*len(fitnesses) 
    AllCodes = [None]*len(pop)
    for i in range(len(pop)):
        AllCodes[i] = pop[i].model_code.MinBinCode
    for _ in range(num_niches):
        # below should exclude those already in a niche, as  the fitness should be set to 999999
        this_best =  heapq.nsmallest(1, range(len(fitnesses)), fitnesses.__getitem__)[0]
        # get the best in the current population
        cur_ind = copy(pop[this_best].model_code.MinBinCode)
        cur_fitness = pop[this_best].fitness
        # add the best in this_niche to the list of best
        best.append(cur_ind)
        best_fitnesses.append(cur_fitness) 
        best_models.append(pop[this_best])
        # get the distance of all from the best
        distance = distance_matrix( [cur_ind], AllCodes)[0]
        # get list of all < niche radius
        in_niche = (distance <= niche_radius)  
        for i in range(len(in_niche)):
            if in_niche[i]:
                not_in_niche[i] = False
                fitnesses[i] = crash_value
 
        # set the fitness of all in this niche to large value, so they aren't in the next seach for best 
        if all(x == crash_value for x in fitnesses): # check if all are already in a niche
            break
    return best, best_fitnesses,best_models
    

def run_downhill(pop: list,return_all = False): # only return new models - best _in_niches
    """Run the downhill step, with full (2 bit) search if requested,
    arguments a population of full models
    return value is list of length num_niches full models after search 
    if return_all is true, will also return a list of ALL models
    to be used in GP only, to update the distribution, not helpful in other algorithms
    arguments are the current population of models and whether to return all models (not implemented, maybe can be used for GP??)
    return is the single best model, the worst models (length num_niches) +/- the entire list of models"""
    generation = pop[0].generation
    this_step = 0
    fitnesses = [None]*len(pop)
    for i in range(len(pop)):
        fitnesses[i] = pop[i].fitness
    num_niches = pop[0].template.options['num_niches']
    done = [False]*num_niches  
    best_MinBinary ,best_fitnesses, best_Models_in_niches = get_best_in_niche(pop)  
    # may be less than num_nicnes 
    current_num_niches = len(best_MinBinary)
    # while we're here, get the worst in the population, to replace them later 
    worst =  heapq.nlargest(num_niches, range(len(fitnesses)), fitnesses.__getitem__)  
    while not all(done) and this_step < 100:     # up to 99 steps 
        test_models = [] 
        which_niche =  []
        for this_niche in range(current_num_niches):
            if not done[this_niche]: 
                # only need to identify niches so we can do downhill on the best in each niche
                cur_ind = copy(best_MinBinary[this_niche]) #just code, no fitness
                # will always be minimal binary at this point
                for this_bit in range(len(cur_ind)):
                    which_niche.append(this_niche)
                    # change this_bit
                    test_ind = copy(cur_ind) # deep copy, not reference 
                    test_ind[this_bit] = 1-test_ind[this_bit]
                    test_models.append(test_ind)
                    # and run test_ind
                # and run all of them
        #global model_num
        model_num = 0 # global, incremented in eval, should be a better way to do this? 
 
        ## need to create models
        Models = []  
        maxes  = pop[0].template.gene_max
        lengths  = pop[0].template.gene_length
        for thisMinBits,model_num in zip(test_models,range(len(test_models))):
            code = model_code(thisMinBits,"MinBinary",maxes,lengths)
            Models.append(model(pop[0].template,code,model_num,False,generation=str(pop[0].generation)+"_downhill_"+ str(this_step)))
        if len(Models)> 0:
            print(f"Starting downhill step {this_step}")
            run_all(Models)
            # check, for each niche, if any in the fitnesses is better, if so, that become the source for the next round
            # repeat until no more better (all(done))      
            for this_niche in range(current_num_niches):
                    ## check if any niches are done
                    if not done[this_niche]:
                        # pull out fitness from just this niche 
                        this_niche_indices = np.array([i for i, x in enumerate(which_niche) if x == this_niche]) 
                        #cur_niche_test_models = [test_models[i] for i in this_niche_indices] # shallow copy, still linked
                        cur_niche_fitnesses = [Models[i].fitness for i in this_niche_indices] 
                        new_best_in_niche =  heapq.nsmallest(1, range(len(cur_niche_fitnesses)), cur_niche_fitnesses.__getitem__)[0]
                        New_best_Model_num = this_niche_indices[new_best_in_niche]
                        # new_best_fitness = cur_niche_fitnesses[new_best_in_niche[0]]
                        # # create grid of all better than previous best for local search     
                        if Models[New_best_Model_num].fitness < best_fitnesses[this_niche]: 
                            best_MinBinary[this_niche] = copy(Models[New_best_Model_num].model_code.MinBinCode)
                            best_Models_in_niches[this_niche] = copy(Models[New_best_Model_num]) # don't seem to need deepcopy, copy entire model
                            best_fitnesses[this_niche] = Models[New_best_Model_num].fitness
                            done[this_niche] = False
                        else:
                            done[this_niche] = True 
        else:
            done = [True]*len(done)
        this_step += 1
            ## best_in_niches is just minimal binary at this point
    if pop[0].template.options["fullExhaustiveSearch_qdownhill"]:
        step = 0
        best_model_index = heapq.nsmallest(1, range(len(best_fitnesses)), best_fitnesses.__getitem__)[0]
        model_for_search = copy(best_Models_in_niches[best_model_index])  
        Last_Best_fitness = model_for_search.fitness
        print(f"Begin exhaustive search, search radius = {pop[0].template.options['niche_radius']}, generation = {generation},step = {step}")
 
        model_for_search = FullSearch(model_for_search)
        ## fitness should already be added to allresults here, gets added by fullsearch after call to runallGA
        # and only use the fullbest  
        # replace the niche this one came from, to preseve diversity 
        if model_for_search.fitness < Last_Best_fitness:
            best_MinBinary[this_niche] = copy(model_for_search.model_code.MinBinCode)
            best_Models_in_niches[this_niche] = copy(model_for_search) # don't seem to need deepcopy, copy entire model
            best_fitnesses[this_niche] = model_for_search.fitness 
        step += 1
    if return_all:
        return best_Models_in_niches, worst, -999 # returning all models not  yet implemented
    else:
        return  best_Models_in_niches, worst
 
def ChangeEachBit(sourcemodels:list,radius: int): ## only need upper triangle, add start row here
    """loop over either 1 or 2 radius 
    raised exception if radius is not 1 or 2
    if, e.g, numbits is 16, and radius is 2, the number of modesl is 136 (16+15+14 + ...)
    if 50 bits, then 1275 models (probably not doable??)
    arguments are:
    base_models - list o MinBinCode (not full models)
    radius - integer of both wide to search, should always be 2?
    model_template - template
    returns:
    list of all MinBinCode and radius"""
    ## get MinBinCode list 
    # may be just 1 or a list 
    if type(sourcemodels[0]) == int:
        base_models = sourcemodels 
        num_base_models = 1
    else: 
        base_models = []
        num_base_models = len(sourcemodels[0])
        for i in range(len(sourcemodels)):
            base_models.append(sourcemodels[i]) 
              
        
    if radius > 2 or radius < 1 or not isinstance(radius,int):
        raise Exception('radius for full local search must be 1 or 2')
    radius += 1
    models = []
       
    for base_model_num in range(num_base_models): # only upper triangle
        if num_base_models == 1:
            this_base_model = copy(base_models)
            #this_base_model.fitness.values = model_template.options['crash_value'],
        else:
            this_base_model = copy(base_models[base_model_num]) 
            #this_base_model.fitness.values = model_template.options['crash_value'],
        for this_bit in range(base_model_num,len(this_base_model)): ## only need upper triangle
            new_model = copy(this_base_model) 
            new_model[this_bit] = 1 - new_model[this_bit]
            #new_model.fitness.values = model_template.options['crash_value'], # don't really need this
            models.append(copy(new_model))
    print(f"{len(models)} models in local exhaustive search, {radius -1} bits")
    return models, radius


def FullSearch(best_pre: model) -> model:
    """perform 2 bit search (radius should always be 2 bits), will always be called after rundownhill (1 bit search),  
    argument is:
    best_pre - base model for search 
    Output:
    single best model """
    this_step = 0 
    Best_Pre_fitness = best_pre.fitness
    generation = best_pre.generation
    model_template = best_pre.template
    Last_Best_fitness = Best_Pre_fitness
    Current_Best_fitness = Best_Pre_fitness
    #Overall_Best_Model = best_pre
    OverallBestModel = best_pre
    Current_Best_Model = best_pre.model_code.MinBinCode
    radius = model_template.options['niche_radius'] 
    while Current_Best_fitness < Last_Best_fitness or this_step == 0: # run at least once  
        Last_Best_fitness = Current_Best_fitness
        curradius = 1  
        test_models = Current_Best_Model # start with just one, then call recurivaly for each radius
        while curradius <= radius: 
            test_models,curradius = ChangeEachBit(test_models,curradius)  
        Models = []  
        maxes  = model_template.gene_max
        lengths  = model_template.gene_length
        for thisMinBits,model_num in zip(test_models,range(len(test_models))):
            code = model_code(thisMinBits,"MinBinary",maxes,lengths)
            Models.append(model(model_template,code,model_num,False,generation= str(generation) +"_Search_"+ str(this_step)))
        run_all(Models) #,model_template,round(generation+(0.01*this_step)+0.01,2),isAlreadyInt= True) # not sure isMinimalBinary is ever used? run_all is always called with int
        fitnesses = []
        for i in range(len(Models)):
            fitnesses.append(Models[i].fitness) 
        best = heapq.nsmallest(1, range(len(fitnesses)), fitnesses.__getitem__) 
        Current_Best_fitness = fitnesses[best[0]]
        if Current_Best_fitness < Last_Best_fitness: 
             
            Current_Best_Model = Models[best[0]].model_code.MinBinCode #copy(Overall_Best_Model)
            Current_Best_fitness = Models[best[0]].fitness
        if Current_Best_fitness < OverallBestModel.fitness:
            OverallBestModel = copy(Models[best[0]])
        this_step += 1       
          
    return OverallBestModel