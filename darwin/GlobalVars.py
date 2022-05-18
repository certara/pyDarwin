import gc 
import time

BestModel = None
BestModelOutput = None
TotalModels = 0  # whether run or found in json
UniqueModels = 0  # anything not found in allmodel.json nor already run
UniqueModelsToBest = 0
output = None  # file for results.csv, opened and closed in main.RunSearch
allModelsDict = dict() 
TimeToBest = 0
StartTime = 0
SavedModelsFile = ''


def init_global_vars():
    global UniqueModelsToBest
    global BestModel
    global StartTime
    global TotalModels
    global UniqueModels
    global output
    global allModelsDict
    global TimeToBest
    global BestModelOutput
    global SavedModelsFile

    UniqueModelsToBest = 0  # need to reset as each algorithm starts
    BestModel = None
    StartTime = time.time()
    TotalModels = 0  # whether run or found in json
    UniqueModels = 0  # anything not found in allmodel.json nor already run
    output = None  # file for results.csv, opened and closed in main.RunSearch
    allModelsDict = dict()  
    TimeToBest = 0
    BestModelOutput = "No output yet"  
    SavedModelsFile = None

    gc.collect()
      