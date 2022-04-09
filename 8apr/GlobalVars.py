import gc
import time
BestModel = None
BestModelOutput  = None
TotalModels = 0 # whether run or found in json
UniqueModels = 0 # anything not found in allmodel.json nor already run
UniqueModelsToBest = 0
StartTime = 0
TimeToBest = 0
output = None # file for results.csv, opened and closed in main.RunSearch
allModelsDict = dict()
SlotRobjects = [] 
def Set_up_Objects(): 
    UniqueModelsToBest = 0 # need to reset as each algorithm starts
    BestModel = None
    BestModelOutput  = None
    TotalModels = 0 # whether run or found in json
    UniqueModels = 0 # anything not found in allmodel.json nor already run
    UniqueModelsToBest = 0
    StartTime = 0
    TimeToBest = 0
    output = None # file for results.csv, opened and closed in main.RunSearch
    allModelsDict = dict()
    SlotRobjects = []
    gc.collect()    # garbage collect 
    BestModelOutput = "No output yet" 
    StartTime = time.time()
      