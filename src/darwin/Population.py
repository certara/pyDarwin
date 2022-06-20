import json
import os
import time
from pathlib import Path
from copy import deepcopy

import threading
from multiprocessing.dummy import Pool as ThreadPool
import traceback

import darwin.GlobalVars as GlobalVars
import darwin.utils as utils

from darwin.Log import log
from darwin.options import options

from .Template import Template
from .Model import Model, write_best_model_files
from .ModelRun import ModelRun
from .ModelCode import ModelCode
from .NMEngineAdapter import NMEngineAdapter

adapter = NMEngineAdapter()

ALL_MODELS_FILE = "models.json"

all_models = dict()


def init_model_list():
    """Initializes model from template. Need Options first"""

    global all_models

    all_models = dict()

    default_models_file = os.path.join(options.home_dir, ALL_MODELS_FILE)

    GlobalVars.SavedModelsFile = default_models_file

    results_file = GlobalVars.output

    utils.remove_file(results_file)
    utils.remove_file(default_models_file)

    with open(results_file, "w") as resultsfile:
        resultsfile.write(f"Run Directory,Fitness,Model,ofv,success,covar,correlation #,"
                          f"ntheta,nomega,nsigm,condition,RPenalty,PythonPenalty,NMTran messages\n")
        log.message(f"Writing intermediate output to {results_file}")

    prev_list = options.get('PreviousModelsList', 'none')

    if options.get("usePreviousModelsList", False) and prev_list.lower() != 'none':
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


class Population:
    all_runs = {}
    _lock_all_runs = threading.Lock()

    def __init__(self, template: Template, name):
        self.name = name
        self.models = []
        self.runs = []
        self.model_number = 0
        self.template = template

    def add_model(self, code: ModelCode):
        model = adapter.create_new_model(self.template, code)
        self.models.append(model)

    def get_best_run(self) -> ModelRun:
        fitnesses = list(map(lambda m: m.result.fitness, self.runs))

        best = utils.get_n_best_index(1, fitnesses)[0]

        return self.runs[best]

    def run_all(self):
        """
        Runs the models. Always runs from integer representation, so for GA will need to convert to integer,
        for downhill, will need to convert to minimal binary, then to integer.

        ???
        all_results maybe full binary (GA) or integer (not GA) or minimal binary (downhill)

        No return value, just updates models.
        """

        self._process_models()

        with open(GlobalVars.SavedModelsFile, 'w', encoding='utf-8') as f:
            json.dump(all_models, f, indent=4, sort_keys=True, ensure_ascii=False)

        # write best model to output
        try:
            write_best_model_files(GlobalVars.InterimControlFile, GlobalVars.InterimResultFile)
        except:
            traceback.print_exc()

    def _register_model_run(self, model: Model) -> ModelRun:
        with self._lock_all_runs:
            genotype = str(model.genotype())

            self.model_number += 1

            run = deepcopy(self.all_runs.get(genotype))

            if run:
                run.model_num = self.model_number
                run.result.nm_translation_message = f"From saved model {run.control_file_name}: "\
                                                    + run.result.nm_translation_message
            else:
                run = ModelRun(model, self.model_number, self.name, 'NM', adapter)

            self.runs.append(run)

            return run

    def _save_model_run(self, run: ModelRun):
        with self._lock_all_runs:
            genotype = str(run.model.genotype())

            run.source = 'saved'

            self.all_runs[genotype] = run

    def start_new_model(self, model: Model):
        """
        Starts the model run in the run_dir.

        :param model: Model Object
        :type model: Model
        """

        run = self._register_model_run(model)

        if run.status != 'Not Started':
            run.copy_model()
        else:
            run.run_model()  # current model is the general model type (not GA/DEAP model)

            run.cleanup()

            self._save_model_run(run)

        res = run.result

        if GlobalVars.BestRun is None or res.fitness < GlobalVars.BestRun.result.fitness:
            _copy_to_best(run)

        step_name = "Iteration"
        prd_err_text = ""

        if options.isGA:
            step_name = "Generation"

        if len(res.prd_err) > 0:
            prd_err_text = ", PRDERR = " + res.prd_err

        with open(GlobalVars.output, "a") as result_file:
            result_file.write(f"{run.run_dir},{res.fitness:.6f},{''.join(map(str, model.model_code.IntCode))},"
                              f"{res.ofv},{res.success},{res.covariance},{res.correlation},{model.theta_num},"
                              f"{model.omega_num},{model.sigma_num},{res.condition_num},{res.post_run_r_penalty},"
                              f"{res.post_run_python_penalty},{res.nm_translation_message}\n")

        fitness_crashed = res.fitness == options.crash_value
        fitness_text = f"{res.fitness:.0f}" if fitness_crashed else f"{res.fitness:.3f}"

        log.message(
            f"{step_name} = {self.name}, Model {run.model_num:5},"
            f"\t fitness = {fitness_text}, \t NMTRANMSG = {res.nm_translation_message.strip()}{prd_err_text}"
        )

    def _start_model_wrapper(self, model: Model):
        try:
            self.start_new_model(model)
        # if we don't catch it, pool will do it silently
        except:
            traceback.print_exc()

    def _process_models(self):
        num_parallel = min(len(self.models), options.num_parallel)

        pool = ThreadPool(num_parallel)

        pool.imap(self._start_model_wrapper, self.models)

        pool.close()
        pool.join()


def _copy_to_best(run: ModelRun):
    """
    Copies current model to the global best model.

    :param run: Run to be saved as the current best
    :type run: ModelRun
    """

    GlobalVars.BestRun = run
    GlobalVars.TimeToBest = time.time() - GlobalVars.StartTime
    GlobalVars.UniqueModelsToBest = GlobalVars.UniqueModels

    if run.source == "new":
        with open(os.path.join(run.run_dir, run.output_file_name)) as file:
            GlobalVars.BestModelOutput = file.read()  # only save best model, other models can be reproduced if needed
