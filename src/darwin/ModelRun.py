import sys
import os
from os.path import exists

from abc import ABC

import shlex
import shutil

import subprocess
from subprocess import DEVNULL, STDOUT, TimeoutExpired, Popen
import traceback

from darwin.Log import log
from darwin.options import options
from darwin.execution_man import interrupted

import darwin.utils as utils
import darwin.GlobalVars as GlobalVars

from .Model import Model
from .ModelResults import ModelResults
from .ModelEngineAdapter import ModelEngineAdapter, get_engine_adapter

files_checked = utils.AtomicFlag(False)

JSON_ATTRIBUTES = [
    'model_num', 'generation',
    'file_stem', 'run_dir', 'control_file_name', 'output_file_name',
    'run_dir', 'control_file_name', 'output_file_name', 'executable_file_name',
    'status', 'source'
]


class ModelRun(ABC):
    """
    generation : int
        The current generation/iteration.

        Generation + model_num creates a unique "file_stem"

    model_num: int
        Model number, within the generation.

        Generation + model_num creates a unique "file_stem"

    file_stem: string
        Prefix string used to create unique names for control files, executable and run directory.
        Defined as stem_prefix + generation + model_num.

    control_file_name: string
        name of the control file, will be  file_stem + ".mod"

    executable_file_name: string
        name of the executable, will be file_stem + ".exe"

    run_dir: string
        relative path from the home_dir to the directory in which NONMEM is run.

        * For all but downhill search, the values (generation and model_num) will be integer

        * For downhill the run_dir will be generation + D + step

        * For local exhaustive search the run_dir will be generation + S + base_step + search_step, where base_step\
        is the final step in the downhill search

        run_dir names will be based on the file_stem, which will be unique for each model in the search
    """

    def __init__(self, model: Model, model_num: int, generation, adapter: ModelEngineAdapter):
        """

        :param model_num:  Model number, within the generation, Generation + model_num creates a unique "file_stem" that
            is used to name the control file, the executable and the relative path from the home directory (home_dir)
            to the run directory
        :type model_num: int

        :param generation: The current generation/iteration. This value is used to construct both the control
            and executable name (NM_generation_modelNum.exe) and the run directory (./generation/model_num)
        """

        self.model = model
        self.adapter = adapter
        self.result = ModelResults()

        self.model_num = model_num
        self.generation = str(generation)

        self.file_stem = adapter.get_stem(generation, model_num)

        self.run_dir = os.path.join(options.home_dir, self.generation, str(self.model_num))

        self.status = "Not Started"

        # "new" if new run, "saved" if from saved model
        # will be no results and no output file - consider saving output file?
        self.source = "new"

        self.control_file_name, self.output_file_name, self.executable_file_name \
            = adapter.get_file_names(self.file_stem)

    def to_dict(self):
        """
        Assembles what goes into the JSON file of saved models.
        """

        res = {attr: self.__getattribute__(attr) for attr in JSON_ATTRIBUTES}

        res['model'] = self.model.to_dict()
        res['result'] = self.result.to_dict()
        res['engine_adapter'] = self.adapter.get_engine_name()

        return res

    @classmethod
    def from_dict(cls, src):
        model = Model.from_dict(src['model'])

        adapter = get_engine_adapter(src['engine_adapter'])

        run = cls(model, src['model_num'], src['generation'], adapter)

        run.result = ModelResults.from_dict(src['result'])

        for attr in JSON_ATTRIBUTES:
            run.__setattr__(attr, src[attr])

        return run

    def _cleanup_run_dir(self):
        try:
            gen_path = os.path.join(options.home_dir, self.generation)

            utils.remove_file(gen_path)

            utils.remove_file(self.run_dir)
            utils.remove_dir(self.run_dir)

            if not os.path.isdir(self.run_dir):
                os.makedirs(self.run_dir)

            return
        except:
            log.error(f"Unable to prepare run directory: {self.run_dir}")

        # if we cannot create run_dir, there's no point to continue
        sys.exit()

    def _make_control_file(self):
        """
        Constructs the control file from the template and the model code.
        """

        self._cleanup_run_dir()

        utils.remove_file(self.control_file_name)
        utils.remove_file(self.output_file_name)

        with open(os.path.join(self.run_dir, self.control_file_name), 'w+') as f:
            f.write(self.model.control)
            f.flush()

    def check_files_present(self):
        """
        Checks if required files are present.
        """

        global files_checked

        if files_checked.set(True):
            return

        cwd = os.getcwd()

        self._make_control_file()

        os.chdir(self.run_dir)

        log.message("Checking files in " + os.getcwd())

        if not exists(self.control_file_name):
            log.error("Cannot find " + self.control_file_name + " to check for data file")
            sys.exit()

        try:
            data_files_path = self.adapter.read_data_file_name(self.control_file_name)
            this_data_set = 1

            for this_file in data_files_path:
                if not exists(this_file):
                    log.error(f"Data set # {this_data_set} seems to be missing: {this_file}")
                    sys.exit()
                else:
                    log.message(f"Data set # {this_data_set} was found: {this_file}")
                    this_data_set += 1
        except:
            log.error(f"Unable to check if data set is present with current version of NONMEM")
            sys.exit()

        os.chdir(cwd)

    def run_model(self):
        """
        Runs the model. Will terminate model if the timeout option (timeout_sec) is exceeded.
        After model is run, the post run R code and post run Python code (if used) is run, and
        the calc_fitness function is called to calculate the fitness/reward.
        """
        self._make_control_file()

        command = self.adapter.get_model_run_command(self)

        GlobalVars.UniqueModels += 1

        run_process = None

        try:
            self.status = "Running model"

            os.chdir(self.run_dir)

            run_process = Popen(command, stdout=DEVNULL, stderr=STDOUT, cwd=self.run_dir,
                                creationflags=options.model_run_priority)

            run_process.communicate(timeout=options.model_run_timeout)

            self.status = "Finished model run"
        except TimeoutExpired:
            utils.terminate_process(run_process.pid)
            log.error(f'run {self.model_num} has timed out')
            self.status = "Model run timed out"
        except Exception as e:
            log.error(str(e))

        if run_process is None or run_process.returncode != 0:
            if interrupted():
                log.error(f'Model run {self.model_num} was interrupted')
                self.status = "Model run interrupted"
            else:
                log.error(f'Model run {self.model_num} has failed')
            self.status = "Model run failed"

            return

        self._post_run_r()
        self._post_run_python()

        self._calc_fitness()

        self._output_results()

        self.status = "Done"

        return

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
            return

        command = [options.rscript_path, options.postRunRCode]

        r_process = None

        try:
            self.status = "Running post process R code"

            r_process = subprocess.run(command, capture_output=True, cwd=self.run_dir,
                                       creationflags=options.model_run_priority, timeout=options.r_timeout)

            self.status = "Done post process R code"

        except TimeoutExpired:
            log.error(f'Post run R code for run {self.model_num} has timed out')
            self.status = "Post process R timed out"
        except:
            log.error("Post run R code crashed in " + self.run_dir)
            self.status = "Post process R failed"

        res = self.result

        if r_process is None or r_process.returncode != 0:
            res.post_run_r_penalty = options.crash_value

            with open(os.path.join(self.run_dir, self.output_file_name), "a") as f:
                f.write("Post run R code failed\n")
        else:
            self._decode_r_stdout(r_process.stdout)

            with open(os.path.join(self.run_dir, self.output_file_name), "a") as f:
                f.write(f"Post run R code Penalty = {str(res.post_run_r_penalty)}\n")
                f.write(f"Post run R code text = {str(res.post_run_r_text)}\n")

    def _post_run_python(self):
        if not options.use_python:
            return

        res = self.result

        try:
            res.post_run_python_penalty, res.post_run_python_text = options.python_post_process()

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

    def copy_model(self):
        """
        Copies the folder contents from a saved model to the new model destination, used so a model that has already
        been run (and saved in the all_models dict) is copied into the new run directory and the control file name
        and output file name in the new model is updated.
        """
        pass

    def _calc_fitness(self):
        """
        Calculates the fitness, based on the model output, and the penalties (from the options file).
        Need to look in output file for parameter at boundary and parameter non-positive.
        """

        try:
            engine = self.adapter

            engine.read_model(self)
            engine.read_results(self)

            res = self.result

            res.prd_err, res.nm_translation_message = engine.get_error_messages(self)

            res.calc_fitness(self.model)

        except:
            traceback.print_exc()

    def _output_results(self):
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

    def cleanup(self):
        self.adapter.cleanup(self.run_dir, self.file_stem)


class StoredRun(ModelRun):
    def copy_model(self):
        """
        Copies the folder contents from a saved model to the new model destination, used so a model that has already
        been run (and saved in the all_models dict) is copied into the new run directory and the control file name
        and output file name in the new model is updated.
        """

        old_dir = self.run_dir
        new_dir = self.run_dir = os.path.join(options.home_dir, self.generation, str(self.model_num))

        old_control_file = self.control_file_name
        old_output_file = self.output_file_name
        self.control_file_name = self.file_stem + ".mod"
        self.output_file_name = self.file_stem + ".lst"

        self._cleanup_run_dir()

        utils.remove_file(os.path.join(new_dir, self.control_file_name))
        utils.remove_file(os.path.join(new_dir, self.output_file_name))
        utils.remove_file(os.path.join(new_dir, "FMSG"))
        utils.remove_file(os.path.join(new_dir, "PRDERR"))

        # and copy
        try:
            shutil.copyfile(os.path.join(old_dir, old_output_file),
                            os.path.join(new_dir, self.output_file_name))
            shutil.copyfile(os.path.join(old_dir, old_control_file),
                            os.path.join(new_dir, self.control_file_name))
            shutil.copyfile(os.path.join(old_dir, "FMSG"), os.path.join(new_dir, "FMSG"))

            if os.path.exists(os.path.join(old_dir, "PRDERR")):
                shutil.copyfile(os.path.join(old_dir, "PRDERR"), os.path.join(new_dir, "PRDERR"))

            with open(os.path.join(new_dir, self.output_file_name), 'a') as outfile:
                outfile.write(f"!!! Saved model, originally run as {old_control_file} in {old_dir}")
        except:
            pass


def write_best_model_files(control_path: str, result_path: str):
    """
    Copies the current model control file and output file to the home_directory.

    :param control_path: path to current best model control file
    :type control_path: str

    :param result_path: path to current best model result file
    :type result_path: str
    """

    with open(control_path, 'w') as control:
        control.write(GlobalVars.BestRun.model.control)

    with open(result_path, 'w') as result:
        result.write(GlobalVars.BestModelOutput)