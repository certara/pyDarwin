import time
import os

output = None
BestModel = None
TotalModels = 0  # whether run or found in json
UniqueModels = 0  # anything not found in models.json nor already run
UniqueModelsToBest = 0
TimeToBest = 0
BestModelOutput = "No output yet"
StartTime = 0
SavedModelsFile = ''


def init_global_vars(home_dir: str):
    global StartTime
    global TimeToBest
    global output
    global BestModelOutput
    StartTime = time.time()
    TimeToBest = 0
    output = os.path.join(home_dir, "results.csv")
    BestModelOutput = "No output yet"
