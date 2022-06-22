import time
import os

output = None
FinalControlFile = None
FinalResultFile = None
InterimControlFile = None
InterimResultFile = None
SavedModelsFile = None

BestRun = None
TotalModels = 0  # whether run or found in json
UniqueModels = 0  # anything not found in models.json nor already run
UniqueModelsToBest = 0
TimeToBest = 0
BestModelOutput = "No output yet"
StartTime = 0


def init_global_vars(home_dir: str):
    global StartTime
    global TimeToBest
    global output
    global FinalControlFile
    global FinalResultFile
    global InterimControlFile
    global InterimResultFile
    global BestModelOutput

    StartTime = time.time()
    TimeToBest = 0
    output = os.path.join(home_dir, "results.csv")
    FinalControlFile = os.path.join(home_dir, "FinalControlFile.mod")
    FinalResultFile = os.path.join(home_dir, "FinalResultFile.lst")
    InterimControlFile = os.path.join(home_dir, "InterimControlFile.mod")
    InterimResultFile = os.path.join(home_dir, "InterimResultFile.lst")
    BestModelOutput = "No output yet"
