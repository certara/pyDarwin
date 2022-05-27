import gc 
import time

output = None  # file for results.csv, opened and closed in main.RunSearch
BestModel = None
TotalModels = 0  # whether run or found in json
UniqueModels = 0  # anything not found in allmodels.json nor already run
UniqueModelsToBest = 0
TimeToBest = 0
BestModelOutput = "No output yet"
StartTime = 0
SavedModelsFile = ''
isFirstMModel = True


def init_global_vars():
    global StartTime
    global output
    global TimeToBest
    global BestModelOutput
    global SavedModelsFile
    global isFirstMModel
    StartTime = time.time()
    output = None  # file for results.csv, opened and closed in main.RunSearch
    TimeToBest = 0
    BestModelOutput = "No output yet"
    SavedModelsFile = ''

    gc.collect()
      