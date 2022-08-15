import sys
import os
from os.path import exists

import json
import shlex

import subprocess
from subprocess import DEVNULL, STDOUT, TimeoutExpired, Popen
import threading
import traceback

from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import interrupted, keep_going, dont_even_start

import darwin.utils as utils
import darwin.GlobalVars as GlobalVars

from .Model import Model
from .ModelResults import ModelResults
from .ModelEngineAdapter import ModelEngineAdapter, get_engine_adapter

JSON_ATTRIBUTES = [
    'model_num', 'generation', 'file_stem',
    'run_dir', 'control_file_name', 'output_file_name', 'executable_file_name',
    'status', 'source'
]


def _dummy(run_dir: str):
    return 0, ""


class _ModelFileChecker:
    _lock_file_check = threading.Lock()

    def __init__(self):
        self._files_checked = False
        self._files_ok = False

    def reset(self):
        self._files_checked = False
        self._files_ok = False

    def check_files_present(self, run):
        """
        Checks if required files are present.
        """

        if self._files_ok:
            return True

        with self._lock_file_check:
            if self._files_checked and not self._files_ok:
                log.error('files not ok')
                return False

            try:
                if not self._files_checked:
                    self._files_checked = True

                    run.check_files_present_impl()

                self._files_ok = True
            except Exception as e:
                dont_even_start()
                log.error(str(e))

        return self._files_ok


file_checker = _ModelFileChecker()
_python_post_process = _dummy


class ModelRun:
    """
    .. _model_run_generation:

    generation : int
        The current generation/iteration.

        Generation + model_num creates a unique "file_stem"

    .. _model_run_num:

    model_num: int
        Model number within the generation.

        Generation + model_num creates a unique "file_stem"

    .. _model_run_stem:

    file_stem: string
        Prefix string used to create unique names for control files, executable, and run directory.
        Defined as stem_prefix + generation + model_num.

    control_file_name: string
        Name of the control file, will be  file_stem + ".mod"

    executable_file_name: string
        Name of the executable, will be file_stem + ".exe"

    .. _model_run_dir:

    run_dir: string
        Path to the directory where the model is run;
        run_dir name is based on the file_stem, which must be unique for each model in the search.
    """

    # nice try
    model_result_class = ModelResults

    def __init__(self, model: Model, model_num, generation, adapter: ModelEngineAdapter):
        """
        :param model_num: Model number, within the generation, Generation + model_num creates a unique "file_stem" that
            is used to name the control file, the executable and the run directory
        :param generation: The current generation/iteration. This value is used to construct both the control
            and executable name and the run directory
        :param adapter: an instance of ModelEngineAdapter, may be obtained
            with get_engine_adapter(options.engine_adapter)
        """

        self.model = model
        self._adapter = adapter
        self.result = self.model_result_class()

        self.wide_model_num = str(model_num)
        self.model_num = int(model_num)
        self.generation = str(generation)

        self.file_stem = adapter.get_stem(generation, model_num)

        self.run_dir = os.path.join(options.temp_dir, self.generation, str(model_num))

        self.status = "Not Started"

        # "new" if new run, "saved" if from saved model
        # will be no results and no output file - consider saving output file?
        self.source = "new"

        self.control_file_name, self.output_file_name, self.executable_file_name \
            = adapter.get_file_names(self.file_stem)

        self.reference_model_num = -1

    def is_duplicate(self) -> bool:
        """
        Whether the run is a duplicate of another run in the same population.
        """
        return self.reference_model_num > -1

    def started(self) -> bool:
        """
        Whether the run has been started.
        """
        return self.status != 'Not Started'

    def to_dict(self):
        """
        Assembles what goes into the JSON file of saved models.
        """

        res = {attr: self.__getattribute__(attr) for attr in JSON_ATTRIBUTES}

        res['model'] = self.model.to_dict()
        res['result'] = self.result.to_dict()
        res['engine_adapter'] = self._adapter.get_engine_name()

        return res

    @classmethod
    def from_dict(cls, src):
        model = Model.from_dict(src['model'])

        adapter = get_engine_adapter(src['engine_adapter'])

        run = cls(model, src['model_num'], src['generation'], adapter)

        run.result = cls.model_result_class.from_dict(src['result'])

        for attr in JSON_ATTRIBUTES:
            run.__setattr__(attr, src[attr])

        run.generation = str(run.generation)

        return run

    def _prepare_run_dir(self):
        try:
            utils.remove_file(self.run_dir)
            utils.remove_dir(self.run_dir)

            if not os.path.isdir(self.run_dir):
                os.makedirs(self.run_dir)

            return
        except:
            traceback.print_exc()
            log.error(f"Unable to prepare run directory: {self.run_dir}")

        # if we cannot create run_dir, there's no point to continue
        sys.exit()

    def _make_control_file(self):
        """
        Constructs the control file from the template and the model code.
        """

        self._prepare_run_dir()

        utils.remove_file(self.control_file_name)
        utils.remove_file(self.output_file_name)

        with open(os.path.join(self.run_dir, self.control_file_name), 'w+') as f:
            f.write(self.model.control)
            f.flush()

    def check_files_present_impl(self):
        self._adapter.check_settings()

        if options.use_r:
            rscript_path = options.rscript_path

            if not os.path.isfile(rscript_path):
                raise RuntimeError(f"RScript path doesn't exist: {rscript_path}")

            log.message(f"RScript found at {rscript_path}")

            if not exists(options.post_run_r_code):
                raise RuntimeError(f"Post Run R code path '{options.post_run_r_code}' seems to be missing")

            log.message(f"Post Run R code found at {options.post_run_r_code}")
        else:
            log.message("Not using Post Run R code")

        if options.use_python:
            python_post_process_path = options.python_post_process_path

            if not os.path.isfile(python_post_process_path):
                raise RuntimeError(f"Post Run Python code path '{python_post_process_path}' seems to be missing")
            else:
                log.message(f"Post Run Python code found at {python_post_process_path}")

                global _python_post_process
                _python_post_process = _import_python_postprocessing(python_post_process_path)
        else:
            log.message("Not using Post Run Python code")

        cwd = os.getcwd()

        os.chdir(self.run_dir)

        log.message("Checking files in " + os.getcwd())

        try:
            if not exists(self.control_file_name):
                raise RuntimeError("Cannot find " + self.control_file_name + " to check for data file")

            try:
                data_files_path = self._adapter.read_data_file_name(self.control_file_name)
            except:
                raise RuntimeError(f"Unable to check if data set is present")

            this_data_set = 1

            for this_file in data_files_path:
                if not exists(this_file):
                    raise RuntimeError(f"Data set # {this_data_set} seems to be missing: {this_file}")
                else:
                    log.message(f"Data set # {this_data_set} was found: {this_file}")
                    this_data_set += 1

        finally:
            os.chdir(cwd)

    def _get_error_messages(self):
        res = self.result

        res.errors, res.messages = self._adapter.get_error_messages(self)

    def run_model(self):
        """
        Runs the model. Will terminate model if the timeout option (model_run_timeout) is exceeded.
        After model is run, the post run R code and post run Python code (if used) are run, and
        the calc_fitness function is called to calculate the fitness/reward.
        """
        if not keep_going():
            return

        self._make_control_file()

        if not file_checker.check_files_present(self):
            return

        command = self._adapter.get_model_run_command(self)

        GlobalVars.UniqueModels += 1

        run_process = None

        try:
            self.status = "Running model"

            run_process = Popen(command, stdout=DEVNULL, stderr=STDOUT, cwd=self.run_dir,
                                creationflags=options.model_run_priority)

            run_process.communicate(timeout=options.model_run_timeout)

            self.status = "Finished model run"
        except TimeoutExpired:
            log.error(f'run {self.model_num} has timed out')
            utils.terminate_process(run_process.pid)

            self.status = "Model run timed out"
            self._get_error_messages()

            return
        except Exception as e:
            log.error(str(e))

        if run_process is None or run_process.returncode != 0:
            if interrupted():
                self.status = "Model run interrupted"
                log.error(f'Model run {self.model_num} was interrupted')
            else:
                self.status = "Model run failed"
                self._get_error_messages()

            return

        self._get_error_messages()

        if not self.result.messages:
            self.result.messages = 'No important warnings'

        if self._post_run_r() and self._post_run_python() and self._calc_fitness():
            self.status = "Done"

    def cleanup(self):
        """
        Deletes all unneeded files after run.
        """
        self._adapter.cleanup(self.run_dir, self.file_stem)

    def _decode_r_stdout(self, r_stdout):
        res = self.result

        new_val = r_stdout.decode("utf-8").replace("[1]", "").strip()
        # comes back a single string, need to parse by ""
        val = shlex.split(new_val)
        # penalty is always first, but may be addition /r/n in array? get the last?
        num_vals = len(val)

        res.post_run_r_penalty = float(val[0])
        res.post_run_r_text = val[num_vals - 1]

    def _post_run_r(self):
        """
        Runs R code specified in the file options['postRunCode'], return penalty from R code.
        R is called by subprocess call to Rscript.exe. User must supply path to Rscript.exe in options file.
        """

        if not options.use_r:
            return True

        command = [options.rscript_path, options.post_run_r_code]

        try:
            self.status = "Running post process R code"

            r_process = subprocess.run(command, capture_output=True, cwd=self.run_dir,
                                       creationflags=options.model_run_priority, timeout=options.r_timeout)

            self.status = "Done post process R code"

        except TimeoutExpired:
            log.error(f'Post run R code for run {self.model_num} has timed out')
            self.status = "Post process R timed out"

            return False
        except:
            log.error("Post run R code crashed in " + self.run_dir)
            self.status = "Post process R failed"

            return False

        res = self.result

        if r_process is None or r_process.returncode != 0:
            res.post_run_r_penalty = options.crash_value

            with open(os.path.join(self.run_dir, self.output_file_name), "a") as f:
                f.write("Post run R code failed\n")

                if r_process is not None:
                    f.write(r_process.stderr.decode("utf-8") + '\n')

            self.status = "Post process R failed"

            return False
        else:
            self._decode_r_stdout(r_process.stdout)

            with open(os.path.join(self.run_dir, self.output_file_name), "a") as f:
                f.write(f"Post run R code Penalty = {str(res.post_run_r_penalty)}\n")
                f.write(f"Post run R code text = {str(res.post_run_r_text)}\n")

        return True

    def _post_run_python(self):
        if not options.use_python:
            return True

        res = self.result

        try:
            res.post_run_python_penalty, res.post_run_python_text = _python_post_process(self.run_dir)

            with open(os.path.join(self.run_dir, self.output_file_name), "a") as f:
                f.write(f"Post run Python code Penalty = {str(res.post_run_python_penalty)}\n")
                f.write(f"Post run Python code text = {str(res.post_run_python_text)}\n")

            self.status = "Done post process Python"

        except:
            res.post_run_python_penalty = options.crash_value

            self.status = "Post process Python failed"

            with open(os.path.join(self.run_dir, self.output_file_name), "a") as f:
                log.error("Post run Python code crashed in " + self.run_dir)
                f.write("Post run Python code crashed\n")
                f.write(traceback.format_exc())

            return False

        return True

    def _calc_fitness(self):
        """
        Calculates the fitness, based on the model output and the penalties.
        Need to look in output file for parameter at boundary and parameter non-positive.
        """

        try:
            engine = self._adapter

            if engine.read_model(self) and engine.read_results(self):
                self.result.calc_fitness(self.model)

        except:
            traceback.print_exc()

        return True

    def output_results(self):
        """
        Prints results to output (.lst) file.
        """

        with open(os.path.join(self.run_dir, self.output_file_name), "a") as output:
            res = self.result
            model = self.model

            output.write(f"OFV = {res.ofv}\n")
            output.write(f"success = {res.success}\n")
            output.write(f"covariance = {res.covariance}\n")
            output.write(f"correlation = {res.correlation}\n")
            output.write(f"Condition # = {res.condition_num}\n")
            output.write(f"Num Non fixed THETAs = {model.estimated_theta_num}\n")
            output.write(f"Num Non fixed OMEGAs = {model.estimated_omega_num}\n")
            output.write(f"Num Non fixed SIGMAs = {model.estimated_sigma_num}\n")
            output.write(f"Original run directory = {self.run_dir}\n")


def _import_python_postprocessing(path: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location("postprocessing.module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.post_process


def write_best_model_files(control_path: str, result_path: str) -> bool:
    """
    Saves the current best model control and output in control_path and result_path, respectively.

    :param control_path: Path to current best model control file
    :param result_path: Path to current best model result file
    """

    if not GlobalVars.BestRun:
        return False

    try:
        with open(control_path, 'w') as control:
            control.write(GlobalVars.BestRun.model.control)

        with open(result_path, 'w') as result:
            result.write(GlobalVars.BestModelOutput)
    except:
        traceback.print_exc()

        return False

    return True


def run_to_json(run: ModelRun, file: str):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(run.to_dict(), f, indent=4, sort_keys=True, ensure_ascii=False)


def json_to_run(file: str) -> ModelRun:
    with open(file) as f:
        return ModelRun.from_dict(json.load(f))
