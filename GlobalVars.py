import gc 
import time 
output = None # file for results.csv, opened and closed in main.RunSearch
#allModelsDict = dict()  
BestModel = None 
BestModelOutput  = None
TotalModels = 0 # whether run or found in json
UniqueModels = 0 # anything not found in allmodel.json nor already run
UniqueModelsToBest = 0
TimeToBest = 0
BestModelOutput = "No output yet"  
StartTime = 0
def Set_up_Objects():  
    StartTime = time.time() 
    output = None # file for results.csv, opened and closed in main.RunSearch
   # allModelsDict = dict()   
    SavedModelsFile = None
    gc.collect()     
      