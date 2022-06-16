import re
import os
import shutil
import shlex
import xmltodict
from collections import OrderedDict
from os.path import exists
import subprocess
from subprocess import DEVNULL, STDOUT, TimeoutExpired, Popen
import time
import glob
from copy import copy
import sys
import psutil

import traceback

import darwin.utils as utils
import darwin.GlobalVars as GlobalVars

from darwin.Log import log
from darwin.options import options

from .Template import Template
from .ModelCode import ModelCode
from .omega_utils import set_omega_bands

files_checked = utils.AtomicFlag(False)

JSON_ATTRIBUTES = [
    'fitness', 'ofv', 'control', 'success', 'covariance', 'correlation', 'theta_num', 'omega_num', 'sigma_num',
    'estimated_theta_num', 'estimated_omega_num', 'estimated_sigma_num', 'condition_num',
    'post_run_r_text', 'post_run_r_penalty', 'post_run_python_text', 'post_run_python_penalty',
    'run_dir', 'control_file_name', 'output_file_name', 'nm_translation_message'
]


class Model:
    """
    The full model, used for GA, GP, RF, GBRF and exhaustive search.

    Model instantiation takes a template as an argument, along with the model code, model number and generation
    function include constructing the control file, executing the control file, calculating the fitness/reward.

    template : model template
        constructed from the template class

    model_code : a ModelCode object
        contains the bit string/integer string representation of the model. Includes the Fullbinary
        string, integer string and minimal binary representation of the model
        (for GA, GP/RF/GBRT and downhill respectively)

    generation : int
        The current generation/iteration.

        Generation + model_num creates a unique "file_stem"

    model_num: int
        Model number, within the generation.

        Generation + model_num creates a unique "file_stem"

    file_stem: string
        Prefix string used to create unique names for control files, executable and run directory.
        Defined as NM + generation + model_num.

    control_file_name: string
        name of the control file, will be  file_stem + ".mod"

    executable_file_name: string
        name of NONMEM executable, will be file_stem + ".exe"

    run_dir: string
        relative path from the home_dir to the directory in which NONMEM is run.

        * For all but downhill search, the values (generation and model_num) will be integer

        * For downhill the run_dir will be generation + D + step

        * For local exhaustive search the run_dir will be generation + S + base_step + search_step, where base_step\
        is the final step in the downhill search

        run_dir names will be based on the file_stem, which will be unique for each model in the search
    """

    def __init__(self, template: Template, code: ModelCode, model_num: int, generation):
        """
        Create model object from Template.

        :param template: Template object, constructed from the template class
        :type template: Template

        :param code: ModelCode Object, contains the bit string/integer string representation of the model.
            Includes the Fullbinary string, integer string and minimal binary representation of the model
            (for GA, GP/RF/GBRT and downhill respectively)
        :type code: ModelCode

        :param model_num:  Model number, within the generation, Generation + model_num creates a unique "file_stem" that
            is used to name the control file, the executable and the relative path from the home directory (home_dir)
            to the run directory
        :type model_num: int

        :param generation: The current generation/iteration. This value is used to construct both the control
            and executable name (NM_generation_modelNum.exe) and the run directory (./generation/model_num)
        """

        self.template = template
        self.model_code = copy(code)
        self.model_num = model_num
        self.generation = str(generation)

        self.ofv = options.crash_value
        self.fitness = options.crash_value
        self.condition_num = options.crash_value

        # "new" if new run, "saved" if from saved model
        # will be no results and no output file - consider saving output file?
        self.source = "new"

        self.old_output_file = None
        self.old_control_file = None  # where did a saved model come from

        # get model number and phenotype
        # all required representations of model are done here
        # GA -> integer,
        # integer is just copied
        # minimal binary is generated, just in case this is a downhill step

        self.success = self.covariance = self.correlation = False

        self.post_run_r_text = self.post_run_python_text = ""
        self.post_run_python_penalty = self.post_run_r_penalty = 0
        self.nm_translation_message = self.prd_err = ""
        self.theta_num = self.estimated_theta_num = 0
        self.omega_num = self.estimated_omega_num = 0
        self.sigma_num = self.estimated_sigma_num = 0

        # home many tokens, due to nesting have a parameter that doesn't end up in the control file?
        self.non_influential_token_num = 0
        self.non_influential_tokens = [False] * len(self.template.tokens)

        self.phenotype = None
        self.control = None
        self.status = "Not Started"

        self.file_stem = f'NM_{self.generation}_{self.model_num}'
        self.run_dir = os.path.join(options.home_dir, self.generation, str(self.model_num))
        self.control_file_name = self.file_stem + ".mod"
        self.output_file_name = self.file_stem + ".lst"
        self.clt_file_name = os.path.join(self.run_dir, self.file_stem + ".clt")
        self.xml_file = os.path.join(self.run_dir, self.file_stem + ".xml")
        self.executable_file_name = self.file_stem + ".exe"

    def from_dict(self, src):
        try:
            for attr in JSON_ATTRIBUTES:
                self.__setattr__(attr, src[attr])

            self.nm_translation_message = f"From saved model {self.run_dir} {self.control_file_name}:" \
                                          f" {src['nm_translation_message']}"

            return True

        except:
            traceback.print_exc()

        return False

    def _cleanup_run_dir(self):
        try:
            gen_path = os.path.join(options.home_dir, self.generation)

            utils.remove_file(gen_path)

            utils.remove_file(self.run_dir)
            utils.remove_dir(self.run_dir)

            if not os.path.isdir(self.run_dir):
                os.makedirs(self.run_dir)
        except:
            log.error(f"Error removing run files/folders for {self.run_dir}")

    def copy_model(self):
        """
        Copies the folder contents from a saved model to the new model destination, used so a model that has already
        been run (and saved in the all_models dict) is copied into the new run directory and the control file name
        and output file name in the new model is updated.
        """

        new_dir = self.run_dir = os.path.join(options.home_dir, self.generation, str(self.model_num))

        self.old_control_file = self.control_file_name
        self.old_output_file = self.output_file_name
        self.control_file_name = self.file_stem + ".mod"
        self.output_file_name = self.file_stem + ".lst"

        self._cleanup_run_dir()

        utils.remove_file(os.path.join(new_dir, self.control_file_name))
        utils.remove_file(os.path.join(new_dir, self.output_file_name))
        utils.remove_file(os.path.join(new_dir, "FMSG"))
        utils.remove_file(os.path.join(new_dir, "PRDERR"))

        # and copy
        try:
            shutil.copyfile(os.path.join(self.run_dir, self.old_output_file),
                            os.path.join(new_dir, self.file_stem + ".lst"))
            shutil.copyfile(os.path.join(self.run_dir, self.old_control_file),
                            os.path.join(new_dir, self.file_stem + ".mod"))
            shutil.copyfile(os.path.join(self.run_dir, "FMSG"), os.path.join(new_dir, "FMSG"))

            if os.path.exists(os.path.join(self.run_dir, "PRDERR")):
                shutil.copyfile(os.path.join(self.run_dir, "PRDERR"), os.path.join(new_dir, "PRDERR"))

            with open(os.path.join(new_dir, self.file_stem + ".lst"), 'a') as outfile:
                outfile.write(f"!!! Saved model, originally run as {self.old_control_file} in {self.run_dir}")
        except:
            pass

    def _make_control_file(self):
        """
        Constructs the control file from the template and the model code.
        """
        
        self._make_control()

        self.source = "new"

        self._cleanup_run_dir()

        utils.remove_file(self.control_file_name)
        utils.remove_file(self.output_file_name)

        with open(os.path.join(self.run_dir, self.control_file_name), 'w+') as f:
            f.write(self.control)

        _check_files_present(self)

    def run_model(self):
        """
        Runs the model. Will terminate model if the timeout option (timeout_sec) is exceeded.
        After model is run, the post run R code and post run Python code (if used) is run, and
        the calc_fitness function is called to calculate the fitness/reward.
        """
        self._make_control_file()

        command = [options.nmfe_path, self.control_file_name, self.output_file_name,
                   " -nmexec=" + self.executable_file_name, f'-rundir={self.run_dir}']

        GlobalVars.UniqueModels += 1

        nm = None

        try:
            self.status = "Running_NM"

            os.chdir(self.run_dir)

            nm = Popen(command, stdout=DEVNULL, stderr=STDOUT, cwd=self.run_dir, creationflags=options.nm_priority)

            nm.communicate(timeout=options.nm_timeout)

            self.status = "Done_running_NM"
        except TimeoutExpired:
            _terminate_process(nm.pid)
            log.error(f'run {self.model_num} has timed out')
            self.status = "NM_timed_out"
        except Exception as e:
            log.error(str(e))

        if nm is None or nm.returncode != 0:
            log.error(f'run {self.model_num} has failed')
            return

        self._post_run_r()
        self._post_run_python()

        self._calc_fitness()

        self.status = "Done"

        return

    def _decode_r_stdout(self, r_stdout):
        new_val = r_stdout.decode("utf-8").replace("[1]", "").strip()
        # comes back a single string, need to parse by ""
        val = shlex.split(new_val)
        self.post_run_r_penalty = float(val[0])
        # penalty is always first, but may be addition /r/n in array? get the last?
        num_vals = len(val)
        self.post_run_r_text = val[num_vals - 1]

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
            self.status = "Running_post_Rcode"

            r_process = subprocess.run(command, capture_output=True, cwd=self.run_dir,
                                       creationflags=options.nm_priority, timeout=options.r_timeout)

            self.status = "Done_post_Rcode"

        except TimeoutExpired:
            log.error(f'Post run R code for run {self.model_num} has timed out')
            self.status = "post_run_r_timed_out"
        except:
            log.error("Post run R code crashed in " + self.run_dir)
            self.status = "post_run_r_failed"

        if r_process is None or r_process.returncode != 0:
            self.post_run_r_penalty = options.crash_value

            with open(os.path.join(self.run_dir, self.output_file_name), "a") as f:
                f.write("Post run R code failed\n")
        else:
            self._decode_r_stdout(r_process.stdout)

            with open(os.path.join(self.run_dir, self.output_file_name), "a") as f:
                f.write(f"Post run R code Penalty = {str(self.post_run_r_penalty)}\n")
                f.write(f"Post run R code text = {str(self.post_run_r_text)}\n")

    def _post_run_python(self):
        if not options.use_python:
            return

        try:
            self.post_run_python_penalty, self.post_run_python_text = options.python_post_process()

            with open(os.path.join(self.run_dir, self.output_file_name), "a") as f:
                f.write(f"Post run Python code Penalty = {str(self.post_run_python_penalty)}\n")
                f.write(f"Post run Python code text = {str(self.post_run_python_text)}\n")

            self.status = "Done_post_Python"

        except:
            self.post_run_python_penalty = options.crash_value

            self.status = "post_run_python_failed"

            with open(os.path.join(self.run_dir, self.output_file_name), "a") as f:
                log.error("Post run Python code crashed in " + self.run_dir)
                f.write("Post run Python code crashed\n")

    def _get_nmtran_msgs(self):
        """
        Reads NMTRAN messages from the FMSG file and error messages from the PRDERR file.
        """
        self.nm_translation_message = ""

        errors = ['PK PARAMETER FOR',
                  'IS TOO CLOSE TO AN EIGENVALUE',
                  'F OR DERIVATIVE RETURNED BY PRED IS INFINITE (INF) OR NOT A NUMBER (NAN)']

        for error in errors:
            for line in _file_to_lines(os.path.join(self.run_dir, "PRDERR")):
                if error in line and not (line.strip() + " ") in self.prd_err:
                    self.prd_err += line.strip() + " "

        warnings = [' (WARNING  31) $OMEGA INCLUDES A NON-FIXED INITIAL ESTIMATE CORRESPONDING TO\n',
                    ' (WARNING  41) NON-FIXED PARAMETER ESTIMATES CORRESPONDING TO UNUSED\n',
                    ' (WARNING  40) $THETA INCLUDES A NON-FIXED INITIAL ESTIMATE CORRESPONDING TO\n']
        short_warnings = ['NON-FIXED OMEGA ', 'NON-FIXED PARAMETER ', 'NON-FIXED THETA']

        f_msg = _file_to_lines(os.path.join(self.run_dir, "FMSG"))

        for warning, short_warning in zip(warnings, short_warnings):
            if warning in f_msg:
                self.nm_translation_message += short_warning

        errors = [' AN ERROR WAS FOUND IN THE CONTROL STATEMENTS.']

        # if an error is found, print out the rest of the text immediately, and add to errors
        for error in errors:
            if error in f_msg:
                start = f_msg.index(error)

                error_text = ", ".join(f_msg[start:])

                log.error("ERROR in Model " + str(self.model_num) + ": " + error_text)

                self.nm_translation_message += error_text

                break

        if self.nm_translation_message == "" or self.nm_translation_message.strip() == ",":
            self.nm_translation_message = "No important warnings"

        # try to sort relevant message?
        # key are
        # (WARNING  31) - non-fixed OMEGA
        # (WARNING  41) - non-fixed parameter
        # (WARNING  40) - non-fixed theta

    def _read_xml(self):
        success = covariance = correlation = False
        ofv = condition_num = options.crash_value

        if not os.path.exists(self.xml_file):
            return

        try:
            with open(self.xml_file) as xml_file:
                data_dict = xmltodict.parse(xml_file.read())
                version = data_dict['nm:output']['nm:nonmem']['@nm:version']  # string
                # keep first two digits
                dots = [_.start() for _ in re.finditer(r"\.", version)]
                # and get the first two
                major_version = float(version[:dots[1]])  # float

                if major_version < 7.4 or major_version > 7.5:
                    log.error(f"NONMEM is version {version}, NONMEM 7.4 and 7.5 are supported, exiting")
                    sys.exit()

            problem = data_dict['nm:output']['nm:nonmem']['nm:problem']

            # if more than one problem, use the first, assume that is the estimation, assume final is simulation
            # really not sure what to do if there is more than one estimation problem
            if isinstance(problem, list):  # > 1 one $PROB
                problem = problem[0]       # use the first

            estimations = problem['nm:estimation']

            # similar, may be more than one estimation, if > 1, we want the final one
            if isinstance(estimations, list):  # > 1 one $EST
                last_estimation = estimations[-1]
            else:
                last_estimation = estimations

            if 'nm:final_objective_function' in last_estimation:
                ofv = float(last_estimation['nm:final_objective_function'])

                if last_estimation['nm:termination_status'] == '0':
                    success = True

            # IS COVARIANCE REQUESTED:
            if 'nm:covariance_status' in last_estimation:
                if last_estimation['nm:covariance_status']['@nm:error'] == '0':
                    covariance = True

                corr_data = last_estimation.get('nm:correlation', {}).get('nm:row', [])
                num_rows = len(corr_data)

                correlation = num_rows > 0

                for this_row in range(1, num_rows):
                    row_data = corr_data[this_row]['nm:col'][:-1]

                    def abs_function(t):
                        return abs(t) > 99999

                    row_data = [abs_function(float(x['#text'])) for x in row_data]

                    if any(row_data):
                        correlation = False
                        break

                if 'nm:eigenvalues' in last_estimation:
                    # if last_estimation['nm:eigenvalues'] is None:
                    eigenvalues = last_estimation['nm:eigenvalues']['nm:val']
                    max_val = -9999999
                    min_val = 9999999

                    for i in eigenvalues:
                        val = float(i['#text'])
                        if val < min_val:
                            min_val = val
                        if val > max_val:
                            max_val = val

                    condition_num = max_val / min_val

            self.success = success
            self.covariance = covariance
            self.correlation = correlation
            self.ofv = ofv
            self.condition_num = condition_num
        except:
            pass

    def _read_model(self):
        if not os.path.exists(os.path.join(self.run_dir, "FCON")):
            return

        try:
            with open(os.path.join(self.run_dir, "FCON"), "r") as fcon:
                fcon_lines = fcon.readlines()

            # IF MORE THAN ONE PROB only use first, the number of parameters will be the same, although
            # the values in subsequent THTA etc. will be different
            prob = [bool(re.search("^PROB", i)) for i in fcon_lines]
            prob_lines = [i for i, x in enumerate(prob) if x]
            # assume only first problem is estimation, subsequent are simulation?
            if len(prob_lines) > 1:
                fcon_lines = fcon_lines[:prob_lines[1]]

            # replace all BLST or DIAG with RNBL (random block) - they will be treated the same
            strc_lines = [idx for idx in fcon_lines if idx[0:4] == "STRC"]

            theta_num = int(strc_lines[0][9:12])

            # HOW MAY LINES IN THETA BLOCK:
            lowr_start = [bool(re.search("^LOWR", i)) for i in fcon_lines]
            lowr_start_line = [i for i, x in enumerate(lowr_start) if x][0]
            uppr_start = [bool(re.search("^UPPR", i)) for i in fcon_lines]
            uppr_start_line = [i for i, x in enumerate(uppr_start) if x][0]

            lowr_lines = fcon_lines[lowr_start_line:uppr_start_line]
            lowr = " ".join(lowr_lines).replace("LOWR", "").strip().replace("\n", ",")
            # remove "," at end
            lowr = lowr.split(",")
            # convert to float
            lowr = [float(a) for a in lowr]

            # find end of UPPR, next will be anything with char in 0-4
            rest_after_uppr_start = fcon_lines[(uppr_start_line+1):]
            # does line start with non-blank?
            end_of_uppr_bool = [bool(re.search(r"^\S{4}", i)) for i in rest_after_uppr_start]
            end_of_uppr_line = [i for i, x in enumerate(end_of_uppr_bool) if x]
            end_of_uppr = end_of_uppr_line[0]

            uppr_lines = fcon_lines[uppr_start_line:(uppr_start_line + end_of_uppr + 1)]
            uppr = " ".join(uppr_lines).replace("UPPR", "").strip().replace("\n", ",")
            # remove "," at end
            uppr = uppr.split(",")
            # convert to float
            uppr = [float(a) for a in uppr]

            estimated_theta = theta_num

            for i in range(theta_num):
                estimated_theta -= (lowr[i] == uppr[i])  # if upper == lower than this is fixed, not estimated

            fcon_lines = [w.replace('BLST', 'RNBL') for w in fcon_lines]
            fcon_lines = [w.replace('DIAG', 'RNBL') for w in fcon_lines]
            # and all random blocks

            rnbl_start = [bool(re.search("^RNBL", n)) for n in fcon_lines]
            rnbl_start_lines = [i for i, x in enumerate(rnbl_start) if x]

            nomegablocks = int(strc_lines[0][32:36])  # field 7, 0 or blank if diagonal, otherwise # of blocks for omega

            if nomegablocks == 0:
                nomegablocks = 1

            nsigmablocks = int(strc_lines[0][40:44])  # field 9, 0 or 1 if diagonal, otherwise # of blocks for sigma

            if nsigmablocks == 0:
                nsigmablocks = 1

            estimated_sigma = estimated_omega = 0
            omega_num = sigma_num = 0

            for this_omega in range(nomegablocks):
                # if position 8 == 1,this block is fixed, need to remove that value to parse

                if fcon_lines[rnbl_start_lines[this_omega]][7] == '1':
                    vals_this_block = _get_block(rnbl_start_lines[this_omega], fcon_lines, True)
                else:
                    vals_this_block = _get_block(rnbl_start_lines[this_omega], fcon_lines, False)
                    estimated_omega += vals_this_block
                omega_num += vals_this_block

            for sigma in range(nomegablocks, (nomegablocks+nsigmablocks)):
                if fcon_lines[rnbl_start_lines[sigma]][7] == '1':
                    vals_this_block = _get_block(rnbl_start_lines[sigma], fcon_lines, True)
                else:
                    vals_this_block = _get_block(rnbl_start_lines[sigma], fcon_lines, False)
                    estimated_sigma += vals_this_block

                sigma_num += vals_this_block

            self._read_xml()

            self.theta_num = theta_num
            self.omega_num = omega_num
            self.sigma_num = sigma_num

            self.estimated_theta_num = estimated_theta
            self.estimated_omega_num = estimated_omega
            self.estimated_sigma_num = estimated_sigma

        except:
            pass

    def _calc_fitness(self):
        """
        Calculates the fitness, based on the model output, and the penalties (from the options file).
        Need to look in output file for parameter at boundary and parameter non-positive.
        """

        self.fitness = options.crash_value

        try:
            self._read_model()
            self._get_nmtran_msgs()  # read from FMSG, in case run fails, will still have NMTRAN messages

            fitness = self.ofv
            # non influential tokens penalties
            fitness += self.non_influential_token_num * options['non_influential_tokens_penalty']

            if not self.success:
                fitness += options['covergencePenalty']

            if not self.covariance:
                fitness += options['covariancePenalty']
                fitness += options['correlationPenalty']
                fitness += options['conditionNumberPenalty']
            else:
                if not self.correlation:
                    fitness += options['correlationPenalty']

            fitness += self.estimated_theta_num * options['THETAPenalty']
            fitness += self.omega_num * options['OMEGAPenalty']
            fitness += self.sigma_num * options['SIGMAPenalty']

            fitness += self.post_run_r_penalty
            fitness += self.post_run_python_penalty

            if fitness > options.crash_value:
                fitness = options.crash_value

            self.fitness = fitness
        except:
            return

        with open(os.path.join(self.run_dir, self.output_file_name), "a") as output:
            output.write(f"OFV = {self.ofv}\n")
            output.write(f"success = {self.success}\n")
            output.write(f"covariance = {self.covariance}\n")
            output.write(f"correlation = {self.correlation}\n")
            output.write(f"Condition # = {self.condition_num}\n")
            output.write(f"Num Non fixed THETAs = {self.estimated_theta_num}\n")
            output.write(f"Num Non fixed OMEGAs = {self.estimated_omega_num}\n")
            output.write(f"Num Non fixed SIGMAs = {self.estimated_sigma_num}\n")
            output.write(f"Original run directory = {self.run_dir}\n")

    def to_dict(self):
        """
        Assembles what goes into the JSON file of saved models.
        """

        res = {}

        for attr in JSON_ATTRIBUTES:
            res[attr] = self.__getattribute__(attr)

        return res

    def cleanup(self):
        """
        Deletes all unneeded files after run.
        Note that an option "remove_run_dir" in the options file to remove the entire run_dir.
        By default, key files (.lst, .xml, mod and any $TABLE files are retained).

        Note however that any files that starts 'FILE' or 'WK' will be removed even if remove_run_dir is set to false.
        """

        if self.source == "saved":
            log.message(f"called clean up for saved model, # {self.model_num}")
            return  # ideally shouldn't be called for saved models, but just in case

        try:
            if options.remove_run_dir:
                try:
                    utils.remove_dir(self.run_dir)
                except OSError:
                    log.error(f"Cannot remove folder {self.run_dir} in call to cleanup")
            else:
                file_to_delete = [
                    "PRSIZES.F90",
                    "GFCOMPILE.BAT",
                    "FSTREAM",
                    "fsubs.90",
                    "compile.lnk",
                    "FDATA",
                    "FCON",
                    "FREPORT",
                    "LINK.LNK",
                    "FSIZES"
                    "ifort.txt",
                    "nmpathlist.txt",
                    "nmprd4p.mod",
                    "PRSIZES.f90",
                    "INTER",
                    self.file_stem + ".ext",
                    self.file_stem + ".clt",
                    self.file_stem + ".coi",
                    self.file_stem + ".cor",
                    self.file_stem + ".cov",
                    self.file_stem + ".cpu",
                    self.file_stem + ".grd",
                    self.file_stem + ".phi",
                    self.file_stem + ".shm",
                    self.file_stem + ".smt",
                    self.file_stem + ".shk",
                    self.file_stem + ".rmt",
                    self.executable_file_name
                ]

                file_to_delete += glob.glob('FILE*') + glob.glob('WK*.*') + glob.glob('*.lnk') + glob.glob("FSUB*.*")

                for f in file_to_delete:
                    try:
                        os.remove(os.path.join(self.run_dir, f))
                    except OSError:
                        pass

                utils.remove_dir(os.path.join(self.run_dir, "temp_dir"))
        except OSError as e:
            log.error(f"OS Error {e}")

        return

    def _check_contains_params(self):
        """
        Looks at the token set to see if it contains OMEGA/SIGMA/THETA/ETA/EPS or ERR, if so it is influential.
        If not (e.g., the token is empty) it is non-influential.
        """

        token_set_num = 0

        for thisKey in self.template.tokens.keys():
            token_set = self.template.tokens.get(thisKey)[self.phenotype[thisKey]]

            for token in token_set:
                trimmed_token = utils.remove_comments(token)

                if "THETA" in trimmed_token or "OMEGA" in trimmed_token or "SIGMA" in trimmed_token\
                        or "ETA(" in trimmed_token or "EPS(" in trimmed_token or "ERR(" in trimmed_token:
                    # doesn't contain parm, so can't contribute to non-influential count
                    self.non_influential_tokens[token_set_num] = True
                    break

            token_set_num += 1

    def _make_control(self):
        """
        Constructs control file from intcode.
        Ignore last value if self_search_omega_bands.
        """
        # this appears to be OK with search_omega_bands
        self.phenotype = OrderedDict(zip(self.template.tokens.keys(), self.model_code.IntCode))
        self._check_contains_params()  # fill in whether any token in each token set contains THETA,OMEGA SIGMA

        template = self.template

        self.control = template.template_text

        any_found = True  # keep looping, looking for nested tokens
        token_found = False  # error check to see if any tokens are present

        for _ in range(5):  # up to 4 levels of nesting?
            
            any_found, self.control = utils.replace_tokens(template.tokens, self.control, self.phenotype,
                                                           self.non_influential_tokens)
            self.non_influential_token_num = sum(self.non_influential_tokens)
            token_found = token_found or any_found
            if not any_found:
                break
        if any_found:
            log.error("It appears that there is more than four level of nested tokens."
                      " Only four levels are supported, exiting")
            raise RuntimeError("Are there more than 4 levels of nested tokens?")

        self.control = utils.match_thetas(self.control, template.tokens, template.var_theta_block, self.phenotype,
                                          template.last_fixed_theta)
        self.control = utils.match_rands(self.control, template.tokens, template.var_omega_block, self.phenotype,
                                         template.last_fixed_eta, "ETA")
        self.control = utils.match_rands(self.control, template.tokens, template.var_sigma_block, self.phenotype,
                                         template.last_fixed_eps, "EPS")
        self.control = utils.match_rands(self.control, template.tokens, template.var_sigma_block, self.phenotype,
                                         template.last_fixed_eps, "ERR")  # check for ERRo as well

        model_code = str(self.model_code.FullBinCode if (options.isGA or options.isPSO) else self.model_code.IntCode)

        self.control += "\n ;; Phenotype \n ;; " + str(self.phenotype) + "\n;; Genotype \n ;; " + model_code\
                        + "\n;; Num non-influential tokens = " + str(self.non_influential_tokens)

        # add band OMEGA
        if options.search_omega_bands:
            # bandwidth must be last gene
            bandwidth = self.model_code.IntCode[-1]

            self.control = set_omega_bands(self.control, bandwidth)

        if not token_found:
            log.error("No tokens found, exiting")
            raise RuntimeError("No tokens found")

        return


def _read_data_file_name(model: Model) -> list:
    """
    Parses the control file to read the data file name

    :param model: Model object
    :type model: Model

    :return: data file path string
    :rtype: list
    """
  
    with open(model.control_file_name, "r") as f:
        datalines = []

        for ln in f:
            if ln.strip().startswith("$DATA"):
                line = ln.strip()
                line = line.replace("$DATA ", "").strip()

                # remove comments
                if ";" in line:
                    pos = line.index(";")
                    line = line[:pos]

                # look for quotes, single or double. if no quotes, find first white space
                if "\"" in line:
                    ll = line.split('"')[1::2]
                    datalines.append(ll[0].strip())
                elif "\'" in line:
                    ll = line.split("'")[1::2]
                    datalines.append(ll[0].strip())
                else:
                    # find first while space
                    result = re.search(r'\s', line)
                    if result is None:
                        datalines.append(line.strip())
                    else:
                        datalines.append(line[:result.regs[0][0]].strip())

    return datalines


def _check_files_present(model: Model):
    """
    Checks if required files are present.

    :param model: Model object
    :type model: Model
    """    

    global files_checked

    if files_checked.set(True):
        return

    cwd = os.getcwd()

    os.chdir(model.run_dir)

    log.message("Checking files in " + os.getcwd())

    if not exists(model.control_file_name):
        log.error("Cannot find " + model.control_file_name + " to check for data file")
        sys.exit()

    try:
        data_files_path = _read_data_file_name(model)
        this_data_set = 1

        for this_file in data_files_path:
            if not exists(this_file):
                log.error(f"Data set # {this_data_set} for FIRST MODEL {this_file} seems to be missing, exiting")
                sys.exit()
            else:
                log.message(f"Data set # {this_data_set} for FIRST MODEL ONLY {this_file} was found")
                this_data_set += 1
    except:
        log.error(f"Unable to check if data set is present with current version of NONMEM")
        sys.exit()

    os.chdir(cwd)


def start_new_model(model: Model, all_models: dict):
    """
    Starts the model run in the run_dir.

    :param model: Model Object
    :type model: Model

    :param all_models: dict of all models that have completed, used to check if this model has already been run
    :type all_models: dict
    """
    
    current_code = str(model.model_code.IntCode)

    if current_code in all_models and model.from_dict(all_models[current_code]):
        model.source = "saved"
        model.copy_model()
        model.status = "Done"
    else:
        model.run_model()  # current model is the general model type (not GA/DEAP model)

    if model.status == "Done":
        if GlobalVars.BestModel is None or model.fitness < GlobalVars.BestModel.fitness:
            _copy_to_best(model)

        if model.source == "new":
            model.cleanup()  # changes back to home_dir
            # Integer code is common denominator for all, entered into dictionary with this
            all_models[str(model.model_code.IntCode)] = model.to_dict()

        step_name = "Iteration"
        prd_err_text = ""

        if options.isGA:
            step_name = "Generation"

        if len(model.prd_err) > 0:
            prd_err_text = ", PRDERR = " + model.prd_err

        with open(GlobalVars.output, "a") as result_file:
            result_file.write(f"{model.run_dir},{model.fitness:.6f},{''.join(map(str, model.model_code.IntCode))},"
                              f"{model.ofv},{model.success},{model.covariance},{model.correlation},{model.theta_num},"
                              f"{model.omega_num},{model.sigma_num},{model.condition_num},{model.post_run_r_penalty},"
                              f"{model.post_run_python_penalty},{model.nm_translation_message}\n")

        fitness_crashed = model.fitness == options.crash_value
        fitness_text = f"{model.fitness:.0f}" if fitness_crashed else f"{model.fitness:.3f}"

        log.message(
            f"{step_name} = {model.generation}, Model {model.model_num:5},"
            f"\t fitness = {fitness_text}, \t NMTRANMSG = {model.nm_translation_message.strip()}{prd_err_text}"
        )


def _copy_to_best(current_model: Model):
    """
    Copies current model to the global best model.

    :param current_model: Model to be saved as the current best
    :type current_model: Model
    """

    GlobalVars.TimeToBest = time.time() - GlobalVars.StartTime
    GlobalVars.UniqueModelsToBest = GlobalVars.UniqueModels
    GlobalVars.BestModel = current_model

    if current_model.source == "new":
        with open(os.path.join(current_model.run_dir, current_model.output_file_name)) as file:
            GlobalVars.BestModelOutput = file.read()  # only save best model, other models can be reproduced if needed

    return


def write_best_model_files(control_path: str, result_path: str):
    """
    Copies the current model control file and output file to the home_directory.

    :param control_path: path to current best model control file
    :type control_path: str

    :param result_path: path to current best model result file
    :type result_path: str
    """
  
    with open(control_path, 'w') as control:
        control.write(GlobalVars.BestModel.control)

    with open(result_path, 'w') as result:
        result.write(GlobalVars.BestModelOutput)


def _terminate_process(pid: int):
    """
    Kills the specified process and its subprocesses.

    :param pid: PID
    :type pid: int
    """    
    proc = psutil.Process(pid)

    for p in proc.children(True):
        p.terminate()

    proc.terminate()


def _file_to_lines(file_name: str):
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            return file.readlines()

    return []


def _get_block(start, fcon, fixed=False):
    # how many lines? find next RNBL
    rnbl_block = fcon[start:]
    rest_of_block = fcon[(1+start):]
    next_start = [bool(re.search("^RNBL", n)) for n in rest_of_block]

    if any(next_start):
        rnbl_start_lines = [i for i, x in enumerate(next_start) if x][0]  # RNBL lines
        this_block = rnbl_block[:(rnbl_start_lines + 1)]
    else:
        next_start = [bool(re.search(r"^\S+", n)) for n in rest_of_block]
        next_start = [i for i, x in enumerate(next_start) if x][0]  # RNBL lines
        this_block = rnbl_block[:(next_start + 1)]

    # if next_start:
    this_block = " ".join(this_block)

    if fixed:
        # remove 1 i position 7
        this_block = list(this_block)
        this_block[7] = ' '
        this_block = "".join(this_block)

    this_block = this_block[4:].strip().replace("\n", ",")
    this_block = this_block.split(",")

    # convert to float
    this_block = [float(a) for a in this_block]

    # have to remove any 0's they will be 0's for band OMEGA
    this_block = [i for i in this_block if i != 0]

    return len(this_block)
