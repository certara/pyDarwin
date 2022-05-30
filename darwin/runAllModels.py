import json
import os
from pathlib import Path

from multiprocessing.dummy import Pool as ThreadPool
import traceback

import darwin.GlobalVars as GlobalVars

from darwin.Log import log

from .Template import Template
from .Model import Model, check_files_present, start_new_model

ALL_MODELS_FILE = "models.json"

all_models = dict()


def init_model_list(template: Template):
    """Initializes model from template. Need Options first"""

    global all_models

    all_models = dict()

    default_models_file = os.path.join(template.homeDir, ALL_MODELS_FILE)

    GlobalVars.SavedModelsFile = default_models_file

    results_file = GlobalVars.output

    if os.path.exists(results_file):
        os.remove(results_file)

    if os.path.exists(default_models_file):
        os.remove(default_models_file)

    with open(results_file, "w") as resultsfile:
        resultsfile.write(f"Run Directory,Fitness,Model,ofv,success,covar,correlation #,"
                          f"ntheta,nomega,nsigm,condition,RPenalty,PythonPenalty,NMTran messages\n")
        log.message(f"Writing intermediate output to {results_file}")

    prev_list = template.options.get('PreviousModelsList', 'none')

    if template.options.get("usePreviousModelsList", False) and prev_list.lower() != 'none':
        try:
            models_list = Path(prev_list)

            if models_list.is_file():
                with open(models_list) as json_file:
                    all_models = json.load(json_file)

                    log.message(f"Using Saved model list from {models_list}")

                    GlobalVars.SavedModelsFile = models_list
            else:
                log.error(f"Cannot find {models_list}, setting models list to empty")
        except:
            log.error(f"Cannot read {prev_list}, setting models list to empty")

    log.message(f"Models will be saved as JSON {GlobalVars.SavedModelsFile}")


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

    with open(GlobalVars.SavedModelsFile, 'w', encoding='utf-8') as f:
        json.dump(all_models, f, indent=4, sort_keys=True, ensure_ascii=False)

    # write best model to output
    try:
        with open(os.path.join(template.homeDir, "InterimBestControl.mod"), 'w') as f:
            f.write(GlobalVars.BestModel.control)
        with open(os.path.join(template.homeDir, "InterimBestOutput.lst"), 'w') as f:
            f.write(GlobalVars.BestModelOutput)
    except:
        traceback.print_exc()

    return
