import time
import os

output = None
FinalControlFile = None
FinalResultFile = None
InterimControlFile = None
InterimResultFile = None
SavedModelsFile = None

BestRun = None
UniqueModels = 0  # anything not found in models.json nor already run
UniqueModelsToBest = 0
StartTime = TimeToBest = 0
BestModelOutput = "No output yet"


def init_global_vars(output_dir: str):
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
    output = os.path.join(output_dir, "results.csv")
    FinalControlFile = os.path.join(output_dir, "FinalControlFile.mod")
    FinalResultFile = os.path.join(output_dir, "FinalResultFile.lst")
    InterimControlFile = os.path.join(output_dir, "InterimControlFile.mod")
    InterimResultFile = os.path.join(output_dir, "InterimResultFile.lst")
    BestModelOutput = "No output yet"
