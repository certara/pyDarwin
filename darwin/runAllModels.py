import json
import os
from pathlib import Path

from multiprocessing.dummy import Pool as ThreadPool
import traceback

import darwin.GlobalVars as GlobalVars

from darwin.Log import log

from .Template import Template
from .Model import Model, check_files_present, start_new_model

all_models = dict()


def init_model_list(model_template: Template):
    """Initializes model from template. Need Options first"""

    global all_models

    results_file = os.path.join(model_template.homeDir, "results.csv")

    if os.path.exists(results_file):
        try:
            os.remove(results_file)
        except OSError:
            pass

    with open(results_file, "w") as resultsfile:
        resultsfile.write(f"Run Directory,Fitness,Model,ofv,success,covar,correlation #,"
                          f"ntheta,nomega,nsigm,condition,RPenalty,PythonPenalty,NMTran messages\n")
        log.message(f"Writing intermediate output to {results_file}")

    if "usePreviousModelsList" in model_template.options.keys():
        if model_template.options['usePreviousModelsList']:
            try:
                models_list = Path(model_template.options['PreviousModelsList'])
                if models_list.name.lower() == "none":
                    # remove default file name if no model specified and set name to default
                    if os.path.exists(os.path.join(model_template.homeDir, "allmodels.json")):
                        os.remove(os.path.join(model_template.homeDir, "allmodels.json"))
                    GlobalVars.SavedModelsFile = os.path.join(model_template.homeDir, "allmodels.json")
                else:
                    if models_list.is_file() and not models_list.name.lower() == "none":
                        with open(models_list) as json_file:
                            all_models = json.load(json_file)
                            GlobalVars.SavedModelsFile = model_template.options['PreviousModelsList']
                            log.message(f"Using Saved model list from  {GlobalVars.SavedModelsFile}")
                    else:
                        log.message(f"Cannot find {models_list}, setting models list to empty")
                        GlobalVars.SavedModelsFile = model_template.options['PreviousModelsList']

                        all_models = dict()
            except:
                log.message(f"Cannot read {model_template.options['input_model_json']}, setting models list to empty")
                log.message(f"Models will be saved as JSON {GlobalVars.SavedModelsFile}")

                GlobalVars.SavedModelsFile = os.path.join(model_template.homeDir, "allmodels.json")

                all_models = dict()
           
            return
        else:
            all_models = dict()

            if "PreviousModelsList" in model_template.options:
                if not model_template.options['PreviousModelsList'].lower() == "none":
                    GlobalVars.SavedModelsFile = model_template.options['PreviousModelsList']

                else:
                    GlobalVars.SavedModelsFile = os.path.join(model_template.homeDir, "allmodels.json")
            else:
                GlobalVars.SavedModelsFile = os.path.join(model_template.homeDir, "allmodels.json")
                # delete the model if it is there

            if os.path.exists(GlobalVars.SavedModelsFile):
                os.remove(GlobalVars.SavedModelsFile)

        log.message(f"Models will be saved as JSON {GlobalVars.SavedModelsFile}")
    else:
        GlobalVars.SavedModelsFile = os.path.join(model_template.homeDir, "allmodels.json")

        # delete the model if it is there
        if os.path.exists(GlobalVars.SavedModelsFile):
            os.remove(GlobalVars.SavedModelsFile)


def _start_model_wrapper(model: Model):
    global all_models

    try:
        start_new_model(model, all_models)
    # if we don't catch it, pool will do it silently
    except:
        traceback.print_exc()


def _process_models(models, num_parallel):
    pool = ThreadPool(num_parallel)

    pool.imap(_start_model_wrapper, models)

    pool.close()
    pool.join()


def run_all(models):
    """runs the models, always runs from integer representation, so for GA will need to convert to integer,
    for downhill, will need to convert to minimal binary, then to integer
    all_results maybe full binary (GA) or integer (not GA) or minimal binary (downhill)
    no return value, just updates Models"""

    template = models[0].template

    check_files_present(models[0])

    num_parallel = min(len(models), template.options['num_parallel'])

    _process_models(models, num_parallel)

    with open(os.path.join(models[0].template.homeDir, "allmodels.json"), 'w', encoding='utf-8') as f:
        json.dump(all_models, f, indent=4, sort_keys=True, ensure_ascii=False)

    # write best model to output
    try:
        with open(os.path.join(models[0].template.homeDir, "InterimBestControl.mod"), 'w') as f:
            f.write(GlobalVars.BestModel.control)
        with open(os.path.join(models[0].template.homeDir, "InterimBestOutput.mod"), 'w') as f:
            f.write(GlobalVars.BestModelOutput)
    except:
        pass

    return

