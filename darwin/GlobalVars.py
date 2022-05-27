import gc 
import time

output = None  # file for results.csv, opened and closed in main.RunSearch
BestModel = None
TotalModels = 0  # whether run or found in json
UniqueModels = 0  # anything not found in allmodel.json nor already run
UniqueModelsToBest = 0
TimeToBest = 0
BestModelOutput = "No output yet"
StartTime = 0
SavedModelsFile = ''
isFirstMModel = True
#process_ids = []

def init_global_vars(NumParallel):
    global StartTime
    global output
    global TimeToBest
    global BestModelOutput
    global SavedModelsFile
    #global process_ids
    global isFirstMModel
    StartTime = time.time()
    output = None  # file for results.csv, opened and closed in main.RunSearch
    TimeToBest = 0
    BestModelOutput = "No output yet"
    SavedModelsFile = ''

    #process_ids = [None] * NumParallel
    gc.collect()
      