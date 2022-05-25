import sys
import os
from os.path import exists
import re
import shutil
import shlex
import xmltodict
from typing import OrderedDict
from subprocess import DEVNULL, STDOUT, TimeoutExpired, run
import time
import glob
from copy import copy

from pharmpy.modeling import read_model   # v 0.66.0 works

import darwin.utils as utils
import darwin.GlobalVars as GlobalVars

from .Template import Template
from .ModelCode import ModelCode
from .Omega_utils import set_omega_bands, insert_omega_block

files_checked = False


class Model:
    """The full model, used for GA, GP, RF, GBRF and exhaustive
    inheirates the Template object"""

    def __init__(self, template: Template, code: ModelCode, model_num: int, generation=None):  # for ga, code is full GA/DEAP individual, with fitness
        """code is a model_code object, type defines whether it is full binary (for GA), minimal binary (for downhill)
        or integer.
        makecontrol always used intcode"""
        self.ofv = self.crash = None
        self.dataset_path = None
        self.template = template
        self.source = "new"  # new if new run, "saved" if from saved model, will be no results and no output file - consider saving output file?
        self.generation = generation
        # get model number and phenotype
        self.modelNum = model_num
        self.errMsgs = []
        self.model_code = copy(code)
        self.RProcess = None
        self.RSTDOUT = self.RSTDERR = self.NMSTDOUT = self.NMSTDERR = None  # standard output and standard error from NONMEM run
        # all required representations of model are done here
        # GA -> integer,
        # integer is just copied
        # minimal binary is generated, just in case this is a downhill step
        self.success = self.covariance = self.correlation = False
        self.OMEGA = self.SIGMA = None
        self.post_run_Rtext = self.post_run_Pythontext = self.NMtranMSG = self.PRDERR = ""
        # self.Rfuture = None # hold future for running R code
        self.fitness = self.template.options['crash_value']
        self.post_run_Pythonpenalty = self.post_run_Rpenalty = self.Condition_num_test = self.condition_num = 0
        self.num_THETAs = self.num_non_fixed_THETAs = self.num_OMEGAs = self.num_non_fixed_OMEGAs = self.num_SIGMAs = self.num_non_fixed_SIGMAs = self.ofv = 0
        self.jsonListRecord = None  # this is a list of key values to be saved to json file, for subsequent runs and to avoid running the same mdoel
        self.Num_noninfluential_tokens = 0  # home many tokens, due to nesting have a parameter that doesn't end up in the control file?
        self.token_Non_influential = [True] * len(
            self.template.tokens)  # does each token result in a change? does it containt a parameter, if token has a parameter, but doesn't
        # default is true, will change to false if: 1. doesn't contain parameters (in check_contains_parms) is put into control file (in utils.replaceTokens)
        self.startTime = time.time()
        self.elapseTime = None
        self.phenotype = None
        self.control = None
        self.datafile_name = None
        self.status = "Not Started"

        self.file_stem = 'NMModel_' + str(self.generation) + "_" + str(self.modelNum)
        self.runDir = os.path.join(self.template.homeDir, str(self.generation), str(self.modelNum))
        self.controlFileName = self.file_stem + ".mod"
        self.outputFileName = self.file_stem + ".lst"
        self.cltFileName = os.path.join(self.runDir, self.file_stem + ".clt")
        self.xml_file = os.path.join(self.runDir, self.file_stem + ".xml")
        self.executableFileName = self.file_stem + ".exe"  # os.path.join(self.runDir,self.filestem +".exe")

    def make_copy(self):
        newmodel = Model(self.template, self.model_code, self.modelNum, self.generation)
        newmodel.fitness = self.fitness
        newmodel.ofv = self.ofv
        newmodel.condition_num = self.condition_num
        newmodel.control = copy(self.control)
        newmodel.controlFileName = copy(self.controlFileName)
        newmodel.Condition_num_test = copy(self.Condition_num_test)
        newmodel.correlation = copy(self.correlation)
        newmodel.covariance = copy(self.covariance)
        newmodel.datafile_name = copy(self.datafile_name)
        newmodel.elapseTime = copy(self.elapseTime)
        newmodel.errMsgs = copy(self.errMsgs)
        newmodel.executableFileName = copy(self.executableFileName)
        newmodel.generation = self.generation
        newmodel.modelNum = self.modelNum
        newmodel.jsonListRecord = copy(self.jsonListRecord)
        newmodel.NMtranMSG = copy(self.NMtranMSG)
        newmodel.errMsgs = copy(self.errMsgs)
        newmodel.file_stem = copy(self.file_stem)
        newmodel.outputFileName = self.outputFileName
        newmodel.num_non_fixed_THETAs = self.num_non_fixed_THETAs
        newmodel.num_THETAs = self.num_THETAs
        newmodel.num_OMEGAs = self.num_OMEGAs
        newmodel.num_SIGMAs = self.num_SIGMAs
        newmodel.phenotype = copy(self.phenotype)
        newmodel.post_run_Rpenalty = copy(self.post_run_Rpenalty)
        newmodel.post_run_Rtext = copy(self.post_run_Rtext)
        newmodel.post_run_Pythonpenalty = copy(self.post_run_Pythonpenalty)
        newmodel.post_run_Pythonpenalty = copy(self.post_run_Pythonpenalty)
        newmodel.token_Non_influential = copy(self.token_Non_influential)
        newmodel.runDir = copy(self.runDir)
        newmodel.status = "Done"
        newmodel.success = copy(self.success)
        newmodel.xml_file = copy(self.xml_file)
        return newmodel

    def copy_results(self, prevResults):
        try:
            self.fitness = prevResults['fitness']
            self.ofv = prevResults['ofv']
            self.control = prevResults['control']
            self.success = prevResults['success']
            self.covariance = prevResults['covariance']
            self.correlation = prevResults['correlation']
            self.num_THETAs = prevResults['num_THETAs']
            self.num_OMEGAs = prevResults['num_OMEGAs']
            self.num_SIGMAs = prevResults['num_SIGMAs']
            self.condition_num = prevResults['condition_num']
            self.post_run_Rtext = prevResults['post_run_Rtext']
            self.post_run_Rpenalty = prevResults['post_run_Rpenalty']
            self.post_run_Pythontext = prevResults['post_run_Pythontext']
            self.post_run_Pythonpenalty = prevResults['post_run_Pythontext']
            self.NMtranMSG = prevResults['NMtranMSG']
            self.NMtranMSG = "From saved model " + self.NMtranMSG  # ["","","","output from previous model"]
            self.status = "Done"
        except:
            return False

        return True

    def make_control_file(self):
        self._make_control()

        self.source = "new"

        # in case the new folder name is a file
        try:
            if os.path.isfile(os.path.join(self.template.homeDir, str(self.generation))) or os.path.islink(
                    os.path.join(self.template.homeDir, str(self.generation))):
                os.unlink(os.path.join(self.template.homeDir, str(self.generation)))

            if os.path.isfile(self.runDir) or os.path.islink(self.runDir):
                os.unlink(self.runDir)

            if not os.path.isdir(self.runDir):
                os.makedirs(self.runDir)
        except:
            self.template.printMessage(f"Error removing run files/folders for {self.runDir}, is that file/folder open?")

        for filename in os.listdir(self.runDir):
            file_path = os.path.join(self.runDir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                self.template.printMessage('Failed to delete %s. Reason: %s' % (self.runDir, e))
        # check key file, just to make sure

        if os.path.exists(self.controlFileName):
            os.remove(self.controlFileName)

        if os.path.exists(self.outputFileName):
            os.remove(self.outputFileName)

        with open(f"{self.runDir}/{self.controlFileName}", 'w+') as f:
            f.write(self.control)
            f.flush()

    def run_model(self):
        self.make_control_file()

        command = [self.template.options['nmfePath'], self.controlFileName, self.outputFileName,
                   "-nmexec=" + self.executableFileName, f'-rundir={self.runDir}']

        GlobalVars.UniqueModels += 1

        flags = 0x4000 if sys.platform == "win32" else 0

        try:
            self.status = "Running_NM"

            os.chdir(self.runDir)

            run(command, stdout=DEVNULL, stderr=STDOUT, cwd=self.runDir, creationflags=flags,
                timeout=int(self.template.options['timeout_sec']))

            self.status = "Done_running_NM"
        except TimeoutExpired:
            self.template.printMessage(f'run {self.modelNum} has timed out')
            self.status = "NM_timed_out"

        return

    def _decode_r_stdout(self):
        newval = self.RSTDOUT.decode("utf-8").replace("[1]", "").strip()

        # comes back a single string, need to parse by ""
        val = shlex.split(newval)

        self.post_run_Rpenalty = float(val[0])

        # penalty is always first, but may be addition /r/n in array? get the last?
        Num_vals = len(val)

        self.post_run_Rtext = val[Num_vals - 1]

    def _post_run_r(self):
        """Run R code specified in the file options['postRunCode'], return penalty from R code
        R is called by subprocess call to Rscript.exe. User must supply path to Rscript.exe
        Presence of Rscript.exe is check in the files_present"""

        command = [self.template.options['RScriptPath'], self.template.postRunRCode]

        try:
            os.chdir(self.runDir)  # just to make sure it is reading the right data

            self.status = "Running_post_Rcode"

            flags = 0x4000 if sys.platform == "win32" else 0

            self.RProcess = run(command, capture_output=True, cwd=self.runDir, creationflags=flags, timeout=10)

        except TimeoutExpired:
            self.template.printMessage(f'!!! Post run R code for run {self.modelNum} has timed out')
            self.status = "post_run_r_timed_out"
        except:
            self.template.printMessage("!!! Post run R code crashed in " + self.runDir)
            self.status = "post_run_r_failed"

        if self.RProcess is None or self.RProcess.returncode != 0:
            self.post_run_Rpenalty = self.template.options['crash_value']

            with open(os.path.join(self.runDir, self.outputFileName), "a") as f:
                f.write("Post run R code failed\n")
        else:
            self.RSTDOUT = self.RProcess.stdout
            self._decode_r_stdout()
            self.RProcess = None

            with open(os.path.join(self.runDir, self.outputFileName), "a") as f:
                f.write(f"Post run R code Penalty = {str(self.post_run_Rpenalty)}\n")
                f.write(f"Post run R code text = {str(self.post_run_Rtext)}\n")

    def _post_run_python(self):
        try:
            self.post_run_Pythonpenalty, self.post_run_Pythontext = self.template.python_postprocess()

            with open(os.path.join(self.runDir, self.outputFileName), "a") as f:
                f.write(f"Post run Python code Penalty = {str(self.post_run_Pythonpenalty)}\n")
                f.write(f"Post run Python code text = {str(self.post_run_Pythontext)}\n")

        except:
            self.post_run_Pythonpenalty = self.template.options['crash_value']

            self.status = "post_run_python_failed"

            with open(os.path.join(self.runDir, self.outputFileName), "a") as f:
                print("!!! Post run Python code crashed in " + self.runDir)
                f.write("Post run Python code crashed\n")

        self.status = "Done"

    def check_all_done(self):
        """Check is the model is done running, uses the Process of the object. Process.poll() return of 107 or 110
        seems to mean failed to start. Process.poll() of 0 is finished
        if done, reads xml file to collect results, then either calls run_post_Code (if applicable)
        or calls calcFitness."""

        self.template.printMessage(f'model {self.modelNum} status: {self.status}, source: {self.source}')

        if self.status == "Done":  # if done here, then already has post run code results
            return True

        elif self.status == "Done_running_NM":
            if self.template.options['useR']:
                self._post_run_r()

            if self.template.options['usePython']:
                self._post_run_python()

            self.calc_fitness()

            return True

        return False

    def read_xml(self):
        if not exists(self.xml_file):
            self.ofv = self.template.options['crash_value']
            self.success = False
            self.covariance = False
            self.correlation = False
            self.condition_num = self.template.options['crash_value']
            self.Condition_num_test = False
            self.num_THETAs = self.num_non_fixed_THETAs = self.num_OMEGAs = self.num_non_fixed_OMEGAs = self.num_SIGMAs = self.num_non_fixed_SIGMAs = 99
            return ()
        else:
            try:
                with open(self.xml_file) as xml_file:
                    # ofv, success, covariance
                    data_dict = xmltodict.parse(xml_file.read())
                    if self.template.version is None:
                        self.template.version = data_dict['nm:output']['nm:nonmem']['@nm:version']  # string
                        print("NONMEM version = " + self.template.version)
                        # keep first two digits
                        dots = [_.start() for _ in re.finditer("\.", self.template.version)]
                        # and get the first two
                        majorversion = float(self.template.version[:dots[1]])  # float
                        if majorversion < 7.4 or majorversion > 7.5:
                            print("NONMEM is version "
                                  + self.template.version + ", NONMEM 7.4 and 7.5 are supported, exiting")
                            sys.exit()

                            # if 0 in problem_dict: # more than one problem, e.g. with simulation
                # it seems that if there is only one problem, this is orderedDict
                # is multiple problems, is just a plain list, if > 0, assume the FIRST IS THE $EST

                problem_dict = data_dict['nm:output']['nm:nonmem']['nm:problem']
                problem_options = dict()
                if "nm:problem_options" in problem_dict[0]:
                    problem_options = problem_dict[0]['nm:problem_options']
                else:
                    if "nm:problem_options" in problem_dict:
                        problem_options = problem_dict['nm:problem_options']
                    else:  # unable to read
                        self.ofv = self.template.options['crash_value']
                        self.success = False
                        self.covariance = False
                        self.correlation = False
                        self.Condition_num_test = False
                        self.condition_num = self.template.options['crash_value']
                        self.PRDERR += " .xml file not present, perhaps crash in estimation step"
                        self.num_non_fixed_THETAs = self.num_non_fixed_OMEGAs = self.num_SIGMAs = 99
                        self.num_THETAs = self.num_OMEGAs = self.num_SIGMAs = 99
                ## read omegas from clt file, any non zero diagonals are estimated
                parms_file = open(self.cltFileName, "r")
                lines = parms_file.readlines()
                parms_file.close()
                # fixed format, parse on space
                parm_names = lines[1].split()
                num_parms = len(parm_names)
                for this_row in range(2, num_parms + 2):
                    currow = lines[this_row].split()
                    if "THETA" in parm_names[this_row - 2]:
                        self.num_THETAs += 1
                        if float(currow[-1]) != 0.000000:
                            self.num_non_fixed_THETAs += 1
                        continue
                    if "OMEGA" in parm_names[this_row - 2]:
                        self.num_OMEGAs += 1  # total size of OMEGA
                        if float(currow[-1]) != 0.000000:
                            self.num_non_fixed_OMEGAs += 1
                        continue
                    if "SIGMA" in parm_names[this_row - 2]:
                        self.num_SIGMAs += 1
                        if float(currow[-1]) != 0.000000:
                            self.num_non_fixed_SIGMAs += 1
                        continue
                self.num_THETAs = int(problem_options['@nm:nthetat'])
                self.num_SIGMAs = int(problem_options['@nm:sigma_diagdim'])
                if isinstance(problem_dict, list):
                    problem_dict = problem_dict[0]
                estimations = problem_dict['nm:estimation']

                # similar, may be more than one estimation, if > 1, we want the final one
                if isinstance(estimations, list):  # > 1 one $EST
                    n_estimation = len(estimations)
                    last_estimation = estimations[n_estimation - 1]
                else:
                    last_estimation = estimations
                # ofv, success, covariance
                self.ofv = float(last_estimation['nm:final_objective_function'])
                if last_estimation['nm:termination_status'] == '0':
                    self.success = True
                else:
                    self.success = False
                if last_estimation['nm:covariance_status']['@nm:error'] == '0':
                    self.covariance = True
                else:
                    self.covariance = False
                corr_data = last_estimation['nm:correlation']["nm:row"]
                num_rows = len(corr_data)
                self.correlation = True
                for this_row in range(1, num_rows):
                    thisrow = corr_data[this_row]['nm:col'][:-1]
                    # get abs
                    absfunction = lambda t: abs(t) > self.template.options['correlationLimit']
                    thisrow = [absfunction(float(x['#text'])) for x in thisrow]
                    if any(thisrow):
                        self.correlation = False
                        break
                if 'nm:eigenvalues' in last_estimation:
                    # if last_estimation['nm:eigenvalues'] is None:
                    Eigens = last_estimation['nm:eigenvalues']['nm:val']
                    max = -9999999
                    min = 9999999
                    for i in Eigens:
                        val = float(i['#text'])
                        if val < min: min = val
                        if val > max: max = val
                    self.condition_num = max / min
                    if self.condition_num > 1000:  # should 1000 be an option??
                        self.Condition_num_test = False
                    else:
                        self.Condition_num_test = True
                else:
                    self.condition_num = self.template.options['crash_value']
                    self.Condition_num_test = False
            except:
                self.ofv = self.template.options['crash_value']
                self.success = False
                self.covariance = False
                self.correlation = False
                self.Condition_num_test = False
                self.condition_num = self.template.options['crash_value']
                self.PRDERR += " .xml file not present, likely crash in estimation step"

        return ()

    def get_nmtran_msgs(self):
        self.NMtranMSG = ""
        try:
            if (os.path.exists(os.path.join(self.runDir, "FMSG"))):
                with open(os.path.join(self.runDir, "FMSG"), 'r') as file:
                    # to do remove all empty (\n) lines
                    msg = file.readlines()
                warnings = [' (WARNING  31) $OMEGA INCLUDES A NON-FIXED INITIAL ESTIMATE CORRESPONDING TO\n',
                            ' (WARNING  41) NON-FIXED PARAMETER ESTIMATES CORRESPONDING TO UNUSED\n',
                            ' (WARNING  40) $THETA INCLUDES A NON-FIXED INITIAL ESTIMATE CORRESPONDING TO\n']
                shortwarnings = ['NON-FIXED OMEGA ', 'NON-FIXED PARAMETER ', 'NON-FIXED THETA']
                for thiswarning, thisshortwarning in zip(warnings, shortwarnings):
                    if thiswarning in msg:
                        self.NMtranMSG += thisshortwarning
            if (os.path.exists(os.path.join(self.runDir, "PRDERR"))):
                with open(os.path.join(self.runDir, "PRDERR"), 'r') as file:
                    msg = file.readlines()
                warnings = ['PK PARAMETER FOR',
                            'IS TOO CLOSE TO AN EIGENVALUE',
                            'F OR DERIVATIVE RETURNED BY PRED IS INFINITE (INF) OR NOT A NUMBER (NAN)']
                for thiswarning in warnings:
                    for thisline in msg:
                        if thiswarning in thisline and not (thisline.strip() + " ") in self.PRDERR:
                            self.PRDERR += thisline.strip() + " "
            errors = [' AN ERROR WAS FOUND IN THE CONTROL STATEMENTS.']
            # if an error is found, print out the rest of the text immediately, and add to errors
            for thiserror in errors:
                if thiserror in msg:
                    startline = 0
                    for thisline in msg:
                        if thiserror in thisline:  # printout rest of text
                            error_text = ""
                            full_error_text = msg[startline:]
                            for error_line in full_error_text:
                                error_text = error_text + ", " + error_line
                            self.template.printMessage(
                                "!!!ERROR in Model " + str(self.modelNum) + ", " + error_text + "!!!")
                            self.NMtranMSG += error_text
                            break
                        else:
                            startline += 1
            if self.NMtranMSG == "":
                self.NMtranMSG = "No important warnings"
        except:
            self.NMtranMSG = "FMSG file not found"

            return
            ## try to sort relevant message?
            # key are (WARNING  31) - non fixed OMEGA and (WARNING  41) non fixed parameter and (WARNING  40) non fixed theta

    def get_prderr(self):
        try:
            if (os.path.exists(os.path.join(self.runDir, "PRDERR"))):
                with open(os.path.join(self.runDir, "PRDERR"), 'r') as file:
                    msg = file.readlines()
                warnings = ['PK PARAMETER FOR',
                            'IS TOO CLOSE TO AN EIGENVALUE',
                            'F OR DERIVATIVE RETURNED BY PRED IS INFINITE (INF) OR NOT A NUMBER (NAN)']
                for thiswarning in warnings:
                    for thisline in msg:
                        if thiswarning in thisline and not (thisline.strip() + " ") in self.PRDERR:
                            self.PRDERR += thisline.strip() + " "
        except:
            pass
        return

    def calc_fitness(self):
        """calculates the fitness, based on the model output, and the penalties (from the options file)
        need to look in output file for parameter at boundary and parameter non positive """

        try:
            self.get_nmtran_msgs()  # read from FMSG, in case run fails, will still have NMTRAN messages
            # self.get_PRDERR()
            self.read_xml()
            # self.get_results_pharmpy() # only for num fixed theta, omega etc, get the rest directly from the xml file

            if (self.ofv is None):
                self.fitness = self.template.options['crash_value']
                return
            else:
                self.fitness = self.ofv
                # non influential tokens penalties
                self.fitness += self.Num_noninfluential_tokens * self.template.options['non_influential_tokens_penalty']
                self.ofv = min(self.ofv, self.template.options['crash_value'])
        except:
            self.fitness = self.template.options['crash_value']
            return

        try:
            if not self.success:
                self.fitness += self.template.options['covergencePenalty']

            if not self.covariance:  # covariance_step['completed'] != True:
                self.fitness += self.template.options['covariancePenalty']
                self.fitness += self.template.options['correlationPenalty']
                self.fitness += self.template.options['conditionNumberPenalty']
            else:
                if not self.correlation:
                    self.fitness += self.template.options['correlationPenalty']
                if not self.Condition_num_test:  #
                    self.fitness += self.template.options['conditionNumberPenalty']
                    # parsimony penalties

            self.fitness += self.num_non_fixed_THETAs * self.template.options['THETAPenalty']
            self.fitness += self.num_OMEGAs * self.template.options['OMEGAPenalty']
            self.fitness += self.num_SIGMAs * self.template.options['SIGMAPenalty']
        except:
            self.fitness = self.template.options['crash_value']

        if self.template.options['useR']:
            try:
                self.fitness += self.post_run_Rpenalty
            except:
                self.fitness = self.template.options['crash_value']

        if self.template.options['usePython']:
            try:
                self.fitness += self.post_run_Pythonpenalty
            except:
                self.fitness = self.template.options['crash_value']

        if self.fitness > self.template.options['crash_value']:
            self.fitness = self.template.options['crash_value']
            # save results
            # write to output
        output = open(self.outputFileName, "a")
        output.write(f"OFV = {self.ofv}\n")
        output.write(f"success = {self.success}\n")
        output.write(f"covariance = {self.covariance}\n")
        output.write(f"correlation = {self.correlation}\n")
        output.write(f"Condition # = {self.condition_num}\n")
        output.write(f"Num Non fixed THETAs = {self.num_non_fixed_THETAs}\n")
        output.write(f"Num Non fixed OMEGAs = {self.num_non_fixed_OMEGAs}\n")
        output.write(f"Num Non fixed SIGMAs = {self.num_non_fixed_SIGMAs}\n")
        output.flush()
        output.close()

        self.make_json_list()

        return

    def make_json_list(self):
        """assembles what goes into the JSON file of saved models"""
        self.jsonListRecord = {"control": self.control, "fitness": self.fitness, "ofv": self.ofv,
                               "success": self.success, "covariance": self.covariance,
                               "post_run_Rtext": self.post_run_Rtext, "post_run_Rpenalty": self.post_run_Rpenalty,
                               "post_run_Pythontext": self.post_run_Pythontext,
                               "post_run_Pythonpenalty": self.post_run_Pythonpenalty,
                               "correlation": self.correlation, "num_THETAs": self.num_THETAs,
                               "num_non_fixed_THETAs": self.num_non_fixed_THETAs,
                               "num_non_fixed_OMEGAs": self.num_non_fixed_OMEGAs,
                               "num_non_fixed_SIGMAs": self.num_non_fixed_SIGMAs,
                               "num_OMEGAs": self.num_OMEGAs, "num_SIGMAs": self.num_SIGMAs,
                               "condition_num": self.condition_num,
                               "NMtranMSG": self.NMtranMSG}
        return

    def cleanup(self):
        """deletes all unneeded files after run
        no argument, no return value """
        if self.source == "saved":
            self.template.printMessage(f"called clean up for saveed model, # {self.modelNum}")
            return  # ideally shouldn't be called for saved models, but just in case

        try:
            os.chdir(self.template.homeDir)
        except OSError as e:
            self.template.printMessage(f"OS Error {e} in call to cleanup")

        try:
            if self.template.options['remove_run_dir'] == "True":
                try:
                    if os.path.isdir(self.runDir):
                        shutil.rmtree(self.runDir)
                except OSError:
                    self.template.printMessage("Cannot remove folder {self.runDir} in call to cleanup")
            else:
                file_to_delete = [self.file_stem + ".ext",
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
                                  self.executableFileName,
                                  "PRSIZES.F90",
                                  "ifort.txt",
                                  "nmpathlist.txt",
                                  "nmprd4p.mod",
                                  "INTER"]
                file_to_delete = file_to_delete + glob.glob('F*') + glob.glob('W*.*') + glob.glob('*.lnk')
                for f in file_to_delete:
                    try:
                        os.remove(os.path.join(self.runDir, f))
                    except OSError:
                        pass
            if os.path.isdir(os.path.join(self.runDir, "temp_dir")):
                shutil.rmtree(os.path.join(self.runDir, "temp_dir"))
        except OSError as e:
            self.template.printMessage(f"OS Error {e}")

        return

    def check_contains_parms(self):
        """ looks at a token set to see if it contains and OMEGA/SIGMA/THETA/ETA/EPS or ERR, if so it is influential. If not (
            e.g., the token is empty) it is non-influential"""
        tokensetNum = 0
        for thisKey in self.template.tokens.keys():
            tokenSet = self.template.tokens.get(thisKey)[self.phenotype[thisKey]]
            isinfluential = False
            for thistoken in tokenSet:

                trimmedtoken = utils.removeComments(thistoken)
                if "THETA" in trimmedtoken or "OMEGA" in trimmedtoken or "SIGMA" in trimmedtoken or "ETA(" in trimmedtoken or "EPS(" in trimmedtoken or "ERR(" in trimmedtoken:
                    isinfluential = True
                    break
            self.token_Non_influential[
                tokensetNum] = isinfluential  # doesn't containt parm, so can't contribute to non-influential count

            tokensetNum += 1
        return

    def _make_control(self):
        """constructs control file from intcode
        ignore last value if self_search_omega_bands """
        # this appears to be OK with search_omega_bands
        self.phenotype = OrderedDict(zip(self.template.tokens.keys(), self.model_code.IntCode))
        self.check_contains_parms()  # fill in whether any token in each token set contains THETA,OMEGA SIGMA

        anyFound = True  # keep looping, looking for nested tokens
        self.control = self.template.TemplateText
        token_found = False  # error check to see if any tokens are present
        for _ in range(3):  # always need 2, and won't do more than 2, only support 1 level of nested loops
            anyFound, self.control = utils.replaceTokens(self.template.tokens, self.control, self.phenotype,
                                                         self.token_Non_influential)
            self.Num_noninfluential_tokens = sum(self.token_Non_influential)
            token_found = token_found or anyFound

        if anyFound:
            self.template.printMessage(
                "It appears that there is more than one level of nested tokens, only one level is supported, exiting")
            raise RuntimeError("Is there more than 1 level of nested tokens??")

        self.control = utils.matchTHETAs(self.control, self.template.tokens, self.template.varTHETABlock,
                                         self.phenotype, self.template.lastFixedTHETA)
        self.control = utils.matchRands(self.control, self.template.tokens, self.template.varOMEGABlock, self.phenotype,
                                        self.template.lastFixedETA, "ETA")
        self.control = utils.matchRands(self.control, self.template.tokens, self.template.varSIGMABlock, self.phenotype,
                                        self.template.lastFixedEPS, "EPS")
        if self.template.isGA or self.template.isPSO:
            self.control += "\n ;; Phenotype \n ;; " + str(self.phenotype) + "\n;; Genotype \n ;; " + str(
                self.model_code.FullBinCode) + \
                            "\n;; Num influential tokens = " + str(self.token_Non_influential)
        else:
            self.control += "\n ;; Phenotype \n ;; " + str(self.phenotype) + "\n;; code \n ;; " + str(
                self.model_code.IntCode) + \
                            "\n;; Num Non influential tokens = " + str(self.token_Non_influential)

        # add band OMEGA
        if self.template.search_omega_band:
            # bandwidth must be last gene
            bandwidth = self.model_code.IntCode[-1]
            omega_block, self.template.search_omega_band = set_omega_bands(self.control, bandwidth)
            if self.template.search_omega_band:
                self.control = insert_omega_block(self.control, omega_block)

        if not token_found:
            self.template.printMessage("No tokens found, exiting")
            self.errMsgs.append("No tokens found")

        return


def check_files_present(model):
    global files_checked

    if files_checked:
        return

    template = model.template

    model.make_control_file()

    cwd = os.getcwd()

    os.chdir(model.runDir)

    template.printMessage("Checking files in " + os.getcwd())

    if not exists(model.controlFileName):
        template.printMessage("Cannot find " + model.controlFileName + " to check for data file")
        sys.exit()

    try:
        result = read_model(model.controlFileName)

        model.dataset_path = result.datainfo.path

        if not exists(model.dataset_path):
            template.printMessage(f"!!! Data set for FIRST MODEL {model.dataset_path} seems to be missing, exiting")
            sys.exit()
        else:
            template.printMessage(f"Data set for FIRST MODEL ONLY {model.dataset_path} was found")
    except:
        template.printMessage(f"Unable to check if data set is present with current version of NONMEM")
        sys.exit()

    os.chdir(cwd)

    nmfe_path = model.template.options['nmfePath']

    if not exists(nmfe_path):
        template.printMessage(f"NMFE path {nmfe_path} seems to be missing, exiting")
        sys.exit()

    template.printMessage(f"NMFE found at {nmfe_path}")

    if model.template.options['useR']:
        rscript_path = model.template.options['RScriptPath']

        if not exists(rscript_path):
            template.printMessage(f"RScript.exe path {rscript_path} seems to be missing, exiting")
            sys.exit()

        template.printMessage(f"RScript.exe found at {rscript_path}")

        if not exists(model.template.postRunRCode):
            template.printMessage(f"Post Run R code path {model.template.postRunRCode} seems to be missing, exiting")
            sys.exit()

        template.printMessage(f"postRunRCode file found at {model.template.postRunRCode}")
    else:
        template.printMessage("Not using PostRun R code")

    files_checked = True


def start_new_model(model, all_models):
    current_code = str(model.model_code.IntCode)

    if current_code in all_models and model.copy_results(all_models[current_code]):
        model.source = "saved"
    else:
        model.run_model()  # current model is the general model type (not GA/DEAP model)

    if model.check_all_done():  # model finished, collect results, start new on, IF not yet done
        nmtran_msgs = model.NMtranMSG

        if GlobalVars.BestModel is None or model.fitness < GlobalVars.BestModel.fitness:
            _copy_to_best(model)

        if model.source == "new":
            model.cleanup()  # changes back to home_dir
            # Integer code is common denominator for all, entered into dictionary with this
            all_models[str(model.model_code.IntCode)] = model.jsonListRecord

        if model.template.isGA:
            step_name = "Generation"
        else:
            step_name = "Iteration"

        if len(model.PRDERR) > 0:
            prderr_text = " PRDERR = " + model.PRDERR
        else:
            prderr_text = ""

        fitness_crashed = model.fitness == model.template.options['crash_value']
        fitness_text = f"{model.fitness:.0f}" if fitness_crashed else f"{model.fitness:.3f}"

        model.template.printMessage(
            f"{step_name} = {model.generation}, Model {model.modelNum:5},"
            f"\t fitness = {fitness_text}, \t NMTRANMSG = {nmtran_msgs.strip()},{prderr_text}"
        )


def _copy_to_best(current_model: Model):
    """copies current model to the global best model"""

    GlobalVars.TimeToBest = time.time() - GlobalVars.StartTime
    GlobalVars.UniqueModelsToBest = GlobalVars.UniqueModels
    GlobalVars.BestModel.fitness = current_model.fitness
    GlobalVars.BestModel.control = current_model.control
    GlobalVars.BestModel.generation = current_model.generation
    GlobalVars.BestModel.modelNum = current_model.modelNum
    GlobalVars.BestModel.model_code = copy(current_model.model_code)
    GlobalVars.BestModel.ofv = current_model.ofv
    GlobalVars.BestModel.success = current_model.success
    GlobalVars.BestModel.covariance = current_model.covariance
    GlobalVars.BestModel.num_THETAs = current_model.num_THETAs
    GlobalVars.BestModel.OMEGA = current_model.OMEGA
    GlobalVars.BestModel.SIGMA = current_model.SIGMA
    GlobalVars.BestModel.num_OMEGAs = current_model.num_OMEGAs
    GlobalVars.BestModel.num_SIGMAs = current_model.num_SIGMAs
    GlobalVars.BestModel.correlation = current_model.correlation
    GlobalVars.BestModel.condition_num = current_model.condition_num
    GlobalVars.BestModel.Condition_num_test = current_model.Condition_num_test

    if current_model.source == "new":
        with open(os.path.join(current_model.runDir, current_model.outputFileName)) as file:
            GlobalVars.BestModelOutput = file.read()  # only save best model, other models can be reproduced if needed

    return
