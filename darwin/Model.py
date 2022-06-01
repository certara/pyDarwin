import re
import os
import shutil
import shlex
import xmltodict 
from collections import OrderedDict
from os.path import exists
import subprocess
from subprocess import DEVNULL, STDOUT, TimeoutExpired
import time
import glob
from copy import copy
import sys

import traceback

import darwin.utils as utils
import darwin.GlobalVars as GlobalVars

from darwin.Log import log
from darwin.options import options

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
        self.oldoutputfile = None
        self.oldcontrolfile = None  # where did a saved model come from
        self.ofv = None
        self.dataset_path = None
        self.template = template
        self.source = "new"  # new if new run, "saved" if from saved model, will be no results and no output file - consider saving output file?
        self.generation = generation
        # get model number and phenotype
        self.modelNum = model_num
        self.errMsgs = []
        self.model_code = copy(code)
        # all required representations of model are done here
        # GA -> integer,
        # integer is just copied
        # minimal binary is generated, just in case this is a downhill step
        self.success = self.covariance = self.correlation = False
        self.OMEGA = self.SIGMA = None
        self.post_run_Rtext = self.post_run_Pythontext = self.NMtranMSG = self.PRDERR = ""
        self.fitness = options.crash_value
        self.post_run_Pythonpenalty = self.post_run_Rpenalty = self.Condition_num_test = self.condition_num = 0
        self.num_THETAs = self.num_non_fixed_THETAs = self.num_OMEGAs = self.num_non_fixed_OMEGAs = self.num_SIGMAs = self.num_non_fixed_SIGMAs = self.ofv = 0
        self.jsonListRecord = None  # this is a list of key values to be saved to json file, for subsequent runs and to avoid running the same mdoel
        self.Num_noninfluential_tokens = 0  # home many tokens, due to nesting have a parameter that doesn't end up in the control file?
        self.token_Non_influential = [True] * len(
            self.template.tokens)  # does each token result in a change? does it containt a parameter, if token has a parameter, but doesn't
        # default is true, will change to false if: 1. doesn't contain parameters (in check_contains_parms) is put into control file (in utils.replaceTokens)
        self.elapseTime = None
        self.phenotype = None
        self.control = None
        self.datafile_name = None
        self.status = "Not Started"

        self.file_stem = f'NM_{self.generation}_{self.modelNum}'
        self.runDir = os.path.join(options.homeDir, str(self.generation), str(self.modelNum))
        self.controlFileName = self.file_stem + ".mod"
        self.outputFileName = self.file_stem + ".lst"
        self.cltFileName = os.path.join(self.runDir, self.file_stem + ".clt")
        self.xml_file = os.path.join(self.runDir, self.file_stem + ".xml")
        self.executableFileName = self.file_stem + ".exe"

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

    def copy_results(self, src):
        try:
            self.fitness = src['fitness']
            self.ofv = src['ofv']
            self.control = src['control']
            self.success = src['success']
            self.covariance = src['covariance']
            self.correlation = src['correlation']
            self.num_THETAs = src['num_THETAs']
            self.num_OMEGAs = src['num_OMEGAs']
            self.num_SIGMAs = src['num_SIGMAs']
            self.condition_num = src['condition_num']
            self.post_run_Rtext = src['post_run_Rtext']
            self.post_run_Rpenalty = src['post_run_Rpenalty']
            self.post_run_Pythontext = src['post_run_Pythontext']
            self.post_run_Pythonpenalty = src['post_run_Pythontext']
            self.NMtranMSG = src['NMtranMSG']
            self.runDir = src['runDir']
            self.controlFileName = src['control_file_name']
            self.outputFileName = src['output_file_name']
            self.NMtranMSG = "From saved model " + self.runDir + " " + self.controlFileName + ": " + src['NMtranMSG']  # ["","","","output from previous model"]

            return True
        except:
            traceback.print_exc()

        return False

    def copy_model(self):
        new_dir = os.path.join(options.homeDir, str(self.generation), str(self.modelNum))

        self.oldcontrolfile = self.controlFileName
        self.oldoutputfile = self.outputFileName
        self.controlFileName = self.file_stem + ".mod"
        self.outputFileName = self.file_stem + ".lst"
        try:
            gen_path = os.path.join(options.homeDir, str(self.generation))

            if os.path.isfile(gen_path) or os.path.islink(gen_path):
                os.unlink(gen_path)

            if os.path.isfile(new_dir) or os.path.islink(new_dir):
                os.unlink(new_dir)

            if not os.path.isdir(new_dir):
                os.makedirs(new_dir)
        except:
            log.error(f"Error removing run files/folders for {new_dir}, is that file/folder open?")

        if os.path.exists(os.path.join(new_dir,self.controlFileName)):
            os.remove(os.path.join(new_dir,self.controlFileName))
        if os.path.exists(os.path.join(new_dir,self.outputFileName)):
            os.remove(os.path.join(new_dir,self.outputFileName))
        if os.path.exists(os.path.join(new_dir,"FMSG")):
            os.remove(os.path.join(new_dir,"FMSG"))
        if os.path.exists(os.path.join(new_dir,"PRDERR")):
            os.remove(os.path.join(new_dir,"PRDERR"))

        # and copy
        try:
            shutil.copyfile(os.path.join(self.runDir,self.oldoutputfile), os.path.join(new_dir, self.file_stem + ".lst"))
            shutil.copyfile(os.path.join(self.runDir,self.oldcontrolfile), os.path.join(new_dir, self.file_stem + ".mod"))
            shutil.copyfile(os.path.join(self.runDir,"FMSG"), os.path.join(new_dir, "FMSG"))
            if os.path.exists(os.path.join(self.runDir,"PRDERR")):
                shutil.copyfile(os.path.join(self.runDir,"PRDERR"), os.path.join(new_dir, "PRDERR"))
            with open(os.path.join(new_dir, self.file_stem + ".lst"), 'a') as outfile:
                outfile.write(f"!!! Saved model, Orginally run as {self.oldcontrolfile} in {self.runDir}")
        except:
            pass

    def make_control_file(self):
        self._make_control()

        self.source = "new"

        # in case the new folder name is a file
        try:
            if os.path.isfile(os.path.join(options.homeDir, str(self.generation))) or os.path.islink(
                    os.path.join(options.homeDir, str(self.generation))):
                os.unlink(os.path.join(options.homeDir, str(self.generation)))

            if os.path.isfile(self.runDir) or os.path.islink(self.runDir):
                os.unlink(self.runDir)

            if not os.path.isdir(self.runDir):
                os.makedirs(self.runDir)
        except:
            log.error(f"Error removing run files/folders for {self.runDir}, is that file/folder open?")

        for filename in os.listdir(self.runDir):
            file_path = os.path.join(self.runDir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                log.error('Failed to delete %s. Reason: %s' % (self.runDir, e))

        if os.path.exists(self.controlFileName):
            os.remove(self.controlFileName)

        if os.path.exists(self.outputFileName):
            os.remove(self.outputFileName)

        with open(f"{self.runDir}/{self.controlFileName}", 'w+') as f:
            f.write(self.control)
            f.flush()

    def run_model(self):
        self.make_control_file()

        command = [options.nmfe_path, os.path.join(self.runDir, self.controlFileName),
                   os.path.join(self.runDir, self.outputFileName),
                   " -nmexec=" + self.executableFileName, f'-rundir={self.runDir}']

        GlobalVars.UniqueModels += 1

        nm = None

        try:
            self.status = "Running_NM"

            os.chdir(self.runDir)

            nm = subprocess.run(command, stdout=DEVNULL, stderr=STDOUT, cwd=self.runDir,
                                creationflags=options.nm_priority, timeout=options.nm_timeout)

            self.status = "Done_running_NM"
        except TimeoutExpired:
            log.error(f'run {self.modelNum} has timed out')
            self.status = "NM_timed_out"
        except:
            pass

        if nm is None or nm.returncode != 0:
            log.error(f'run {self.modelNum} has failed')
            return

        self._post_run_r()
        self._post_run_python()

        self._calc_fitness()

        self.status = "Done"

        return

    def _decode_r_stdout(self, r_stdout):
        newval = r_stdout.decode("utf-8").replace("[1]", "").strip()
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

        if not options.use_r:
            return

        command = [options.rscript_path, options.postRunRCode]

        r_process = None

        try:
            self.status = "Running_post_Rcode"

            r_process = subprocess.run(command, capture_output=True, cwd=self.runDir,
                                       creationflags=options.nm_priority, timeout=options.r_timeout)

            self.status = "Done_post_Rcode"

        except TimeoutExpired:
            log.error(f'Post run R code for run {self.modelNum} has timed out')
            self.status = "post_run_r_timed_out"
        except:
            log.error("Post run R code crashed in " + self.runDir)
            self.status = "post_run_r_failed"

        if r_process is None or r_process.returncode != 0:
            self.post_run_Rpenalty = options.crash_value

            with open(os.path.join(self.runDir, self.outputFileName), "a") as f:
                f.write("Post run R code failed\n")
        else:
            self._decode_r_stdout(r_process.stdout)

            with open(os.path.join(self.runDir, self.outputFileName), "a") as f:
                f.write(f"Post run R code Penalty = {str(self.post_run_Rpenalty)}\n")
                f.write(f"Post run R code text = {str(self.post_run_Rtext)}\n")

    def _post_run_python(self):
        if not options.use_python:
            return

        try:
            self.post_run_Pythonpenalty, self.post_run_Pythontext = options.python_post_process()

            with open(os.path.join(self.runDir, self.outputFileName), "a") as f:
                f.write(f"Post run Python code Penalty = {str(self.post_run_Pythonpenalty)}\n")
                f.write(f"Post run Python code text = {str(self.post_run_Pythontext)}\n")

            self.status = "Done_post_Python"

        except:
            self.post_run_Pythonpenalty = options.crash_value

            self.status = "post_run_python_failed"

            with open(os.path.join(self.runDir, self.outputFileName), "a") as f:
                log.error("Post run Python code crashed in " + self.runDir)
                f.write("Post run Python code crashed\n")

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
                            log.error("ERROR in Model " + str(self.modelNum) + ": " + error_text)
                            self.NMtranMSG += error_text
                            break
                        else:
                            startline += 1
            if self.NMtranMSG == "" or self.NMtranMSG.strip() == ",":
                self.NMtranMSG = "No important warnings"
        except:
            self.NMtranMSG = "FMSG file not found"

            return
            ## try to sort relevant message?
            # key are (WARNING  31) - non fixed OMEGA and (WARNING  41) non fixed parameter and (WARNING  40) non fixed theta

    def get_PRDERR(self):
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
            self.PRDERR += f"Unable to read PDERR in {self.runDir}"
        return
                         
    def read_xml(self):
        xml_file = self.xml_file
        if not os.path.exists (xml_file):
            self.ofv = self.condition_num = options.crash_value 
            self.success = self.covariance  = self.correlation = False  
             
        else:
            try:
                with open(xml_file) as xml_file: 
                    data_dict = xmltodict.parse(xml_file.read())
                    #if template.version is None:
                    version = data_dict['nm:output']['nm:nonmem']['@nm:version']  # string
                    #print("NONMEM version = " +version)
                    # keep first two digits
                    dots = [_.start() for _ in re.finditer("\.", version)]
                    # and get the first two
                    majorversion = float(version[:dots[1]])  # float
                    if majorversion < 7.4 or majorversion > 7.5:
                        print("NONMEM is version "
                                + version + ", NONMEM 7.4 and 7.5 are supported, exiting")
                problem =  data_dict['nm:output']['nm:nonmem']['nm:problem']
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
                    self.ofv = float(last_estimation['nm:final_objective_function'])
                    if last_estimation['nm:termination_status'] == '0':
                        self.success = True
                    else:
                        self.success = False
                else:
                    self.ofv = options.crash_value
                    self.success = False 
                    self.covariance = False
                    self.correlation = False 
                    self.condition_num =  options.crash_value     
                    
                     
                # IS COVARIANCE REQUESTED:
                if 'nm:covariance_status' in last_estimation:
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
                        absfunction = lambda t: abs(t) >  99999 #['correlationLimit']
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
                    else:
                        self.condition_num =  options.crash_value  
                else:
                    self.covariance = False 
                    self.correlation = False
                    self.condition_num =  options.crash_value 
            except:
                self.ofv = options.crash_value
                self.success = False
                self.covariance = False
                self.correlation = False 
                self.condition_num = options.crash_value
              

    def get_block(self,start,fcon,fixed = False):
        # how many lines? find next RNBL 
        rnbl_block = fcon[start:]
        rest_of_block = fcon[(1+start):]
        next_start = [bool(re.search("^RNBL", n)) for n in rest_of_block]
        if any(next_start):
            rnbl_start_lines = [i for i, x in enumerate(next_start) if x][0] # RNBL lines
            this_block = rnbl_block[:(rnbl_start_lines + 1)] 
        else:  
            next_start = [bool(re.search("^\S+", n)) for n in rest_of_block]   
            next_start = [i for i, x in enumerate(next_start) if x][0] # RNBL lines 
            this_block = rnbl_block[:(next_start + 1)]  
        # if next_start:
        this_block = " ".join(this_block)
        if fixed:
            # remvoe 1 i posiiton 7
            this_block = list(this_block) 
            this_block[7] = ' ' 
            this_block = "".join(this_block)
        this_block = this_block[4:].strip().replace("\n","," ) 
        this_block = this_block.split(",")
        # convert to float
        this_block = [float(a) for a in this_block]
        # have to remove any 0's they will be 0's for band OMEGA
        this_block =[i for i in this_block if i != 0]
        nvals = len(this_block) 
        return nvals

    def read_model(self): 
        if not os.path.exists(os.path.join(self.runDir,"FCON")):
            self.ofv = self.condition_num = options.crash_value
            self.success = self.covariance  = self.correlation = False 
            self.num_THETA=self.num_OMEGA=self.num_SIGMA=self.n_estimated_theta=self.n_estimated_omega=self.n_estimated_sigma = 999
        
        else:
            try:
                with open(os.path.join(self.runDir,"FCON"),"r") as fcon:
                    fconlines = fcon.readlines()  
                #IF MORE THAN ONE PROB only use first, the number of parameters will be the same, although
                # the values in subsequen THTA etc willbe different
                PROBS = [bool(re.search("^PROB", i)) for i in fconlines] 
                PROBs_lines = [i for i, x in enumerate(PROBS) if x]
                # assume only first problem is estiamtion, subsequent are simulation?
                if len(PROBs_lines)>1:  
                    fconlines = fconlines[:PROBs_lines[1]]
                # replace all BLST or DIAG with RNBL (randomd block) - they will be treated the same 
                strclines = [idx for idx in fconlines if idx[0:4] == "STRC"]  
                self.num_THETA = int(strclines[0][9:12]) 
                THTA_start = [bool(re.search("^THTA", i)) for i in fconlines] 
                THTA_start_line = [i for i, x in enumerate(THTA_start) if x][0]
                # HOW MAY LINES IN THTA BLOCK:
                LOWR_start = [bool(re.search("^LOWR", i)) for i in fconlines] 
                LOWR_start_line = [i for i, x in enumerate(LOWR_start) if x][0] 
                lines_in_block = LOWR_start_line -THTA_start_line
                THTAl = fconlines[THTA_start_line:LOWR_start_line]
                THTA = " ".join(THTAl).replace("THTA","").strip().replace("\n","," ) # initial values, don't actually use these
                # remove "," at end
                THTA = THTA.split(",")
                # convert to float
                THTA = [float(a) for a in THTA]
                UPPR_START = [bool(re.search("^UPPR", i)) for i in fconlines]
                UPPR_start_line = [i for i, x in enumerate(UPPR_START) if x][0]
                LOWRL = fconlines[LOWR_start_line:UPPR_start_line]
                LOWR = " ".join(LOWRL).replace("LOWR","").strip().replace("\n","," )
                # remove "," at end
                LOWR = LOWR.split(",")
                # convert to float
                LOWR = [float(a) for a in LOWR]
                # find end of UPPR, next will be anything with char in 0-4
                rest_after_UPPR_start = fconlines[(UPPR_start_line+1):] 
                end_of_UPPR_bool = [bool(re.search("^\S{4}", i)) for i in rest_after_UPPR_start]  # does line start with non blank?
                end_of_UPPR_line = [i for i, x in enumerate(end_of_UPPR_bool) if x]  
                end_of_UPPR = end_of_UPPR_line[0]
                UPPRL = fconlines[UPPR_start_line:(UPPR_start_line + end_of_UPPR + 1 )]
                UPPR = " ".join(UPPRL).replace("UPPR","").strip().replace("\n","," )
                # remove "," at end
                UPPR = UPPR.split(",")
                # convert to float
                UPPR = [float(a) for a in UPPR]
                self.n_estimated_theta = self.num_THETA
                for i in range(self.num_THETA):
                    self.n_estimated_theta -= (LOWR[i]==UPPR[i]) # if upper == lower than this is fixed, not estimated
                    
                fconlines =   [w.replace('BLST', 'RNBL') for w in fconlines]
                fconlines =   [w.replace('DIAG', 'RNBL') for w in fconlines]
            # and all rangdom blocks 
                
                rnbl_start = [bool(re.search("^RNBL", n)) for n in fconlines] 
                rnbl_start_lines = [i for i, x in enumerate(rnbl_start) if x]
                
                nomegablocks = int(strclines [0][32:36]) # field 7, 0 or blank if diagonal, otherwise # of blocks for omega
                if nomegablocks ==0:
                    nomegablocks = 1
                nsigmablocks = int(strclines [0][40:44]) # field 9, 0 or 1 if diagonal, otherwise # of blocks for sigma
                
                if nsigmablocks == 0:
                    nsigmablocks = 1
                self.n_estimated_sigma = n_estimated_omega = 0
                self.num_OMEGA = num_SIGMA = 0

                for thisomega in range(nomegablocks):
                    #if postion 8 == 1,   this block is fixed, need to remove that value to parse
                    
                    if fconlines[rnbl_start_lines[thisomega]][7] == '1':  
                        vals_this_block = self.get_block(rnbl_start_lines[thisomega],fconlines, True)  
                    else:  
                        vals_this_block = self.get_block(rnbl_start_lines[thisomega],fconlines, False)
                        n_estimated_omega += vals_this_block  
                    self.num_OMEGA += vals_this_block 
                
                for thissigma in range(nomegablocks,(nomegablocks+nsigmablocks)): 
                    if fconlines[rnbl_start_lines[thissigma]][7] == '1':  
                        vals_this_block = self.get_block(rnbl_start_lines[thissigma],fconlines, True)
                    else:
                        vals_this_block = self.get_block(rnbl_start_lines[thissigma],fconlines, False)
                        self.n_estimated_sigma += vals_this_block  
                    num_SIGMA += vals_this_block 
            
                self.read_xml()

                
            except:
                self.ofv = self.condition_num = options.crash_value
                self.success = self.covariance  = self.correlation = False 
                self.num_THETA=self.num_OMEGA=self.num_SIGMA=self.n_estimated_theta=self.n_estimated_omega=self.n_estimated_sigma = 999
                 
            return

    def _calc_fitness(self):
        """calculates the fitness, based on the model output, and the penalties (from the options file)
        need to look in output file for parameter at boundary and parameter non-positive """

        try:
            self.read_model()
            #self.get_results_pharmpy()
            self.get_nmtran_msgs()  # read from FMSG, in case run fails, will still have NMTRAN messages
            self.get_PRDERR()

            if self.ofv is None:
                self.fitness = options.crash_value
                return
            else:
                self.fitness = self.ofv
                # non influential tokens penalties
                self.fitness += self.Num_noninfluential_tokens * options['non_influential_tokens_penalty']
                self.ofv = min(self.ofv, options.crash_value)
        except:
            self.fitness = options.crash_value
            return

        try:
            if not self.success:
                self.fitness += options['covergencePenalty']

            if not self.covariance:  # covariance_step['completed'] != True:
                self.fitness += options['covariancePenalty']
                self.fitness += options['correlationPenalty']
                self.fitness += options['conditionNumberPenalty']
            else:
                if not self.correlation:
                    self.fitness += options['correlationPenalty']
                if not self.Condition_num_test:  #
                    self.fitness += options['conditionNumberPenalty']
                    # parsimony penalties

            self.fitness += self.num_non_fixed_THETAs * options['THETAPenalty']
            self.fitness += self.num_OMEGAs * options['OMEGAPenalty']
            self.fitness += self.num_SIGMAs * options['SIGMAPenalty']
        except:
            self.fitness = options.crash_value

        self.fitness += self.post_run_Rpenalty
        self.fitness += self.post_run_Pythonpenalty

        if self.fitness > options.crash_value:
            self.fitness = options.crash_value
            # save results
            # write to output 

        with open(os.path.join(self.runDir,self.outputFileName)  ,"a") as ouputfile:
            ouputfile.write(f"OFV = {self.ofv}\n")
            ouputfile.write(f"success = {self.success}\n")
            ouputfile.write(f"covariance = {self.covariance}\n")
            ouputfile.write(f"correlation = {self.correlation}\n")
            ouputfile.write(f"Condition # = {self.condition_num}\n")
            ouputfile.write(f"Num Non fixed THETAs = {self.num_non_fixed_THETAs}\n")
            ouputfile.write(f"Num Non fixed OMEGAs = {self.num_non_fixed_OMEGAs}\n")
            ouputfile.write(f"Num Non fixed SIGMAs = {self.num_non_fixed_SIGMAs}\n")
            ouputfile.write(f"Original run directory = {self.runDir}\n")
            ouputfile.flush()

        self._make_json_list()

        return

    def _make_json_list(self):
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
                               "NMtranMSG": self.NMtranMSG, 
                               "runDir": self.runDir, # original run directory
                               "control_file_name": self.controlFileName, # this is just file, not path
                               "output_file_name": self.outputFileName 
                               } # original run directory
        return

    def cleanup(self):
        """deletes all unneeded files after run
        no argument, no return value """
         
        if self.source == "saved":
            log.message(f"called clean up for saved model, # {self.modelNum}")
            return  # ideally shouldn't be called for saved models, but just in case

        try:
            if options.remove_run_dir:
                try:
                    if os.path.isdir(self.runDir):
                        shutil.rmtree(self.runDir)
                except OSError:
                    log.error(f"Cannot remove folder {self.runDir} in call to cleanup")
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
                    self.executableFileName
                ]

                file_to_delete = file_to_delete + glob.glob('FILE*') + glob.glob('WK*.*') + glob.glob('*.lnk') + glob.glob("FSUB*.*")

                for f in file_to_delete:
                    try:
                        os.remove(os.path.join(self.runDir, f))
                    except OSError:
                        pass
            if self.runDir is not None:
                if os.path.isdir(os.path.join(self.runDir, "temp_dir")):
                    shutil.rmtree(os.path.join(self.runDir, "temp_dir"))
        except OSError as e:
            log.error(f"OS Error {e}")

        return

    def _check_contains_parms(self):
        """ looks at a token set to see if it contains and OMEGA/SIGMA/THETA/ETA/EPS or ERR, if so it is influential.
         If not (e.g., the token is empty) it is non-influential"""

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
        self._check_contains_parms()  # fill in whether any token in each token set contains THETA,OMEGA SIGMA

        anyFound = True  # keep looping, looking for nested tokens
        self.control = self.template.TemplateText
        token_found = False  # error check to see if any tokens are present
        for _ in range(3):  # always need 2, and won't do more than 2, only support 1 level of nested loops
            anyFound, self.control = utils.replaceTokens(self.template.tokens, self.control, self.phenotype,
                                                         self.token_Non_influential)
            self.Num_noninfluential_tokens = sum(self.token_Non_influential)
            token_found = token_found or anyFound

        if anyFound:
            log.error("It appears that there is more than one level of nested tokens."
                      " Only one level is supported, exiting")
            raise RuntimeError("Is there more than 1 level of nested tokens?")

        self.control = utils.matchTHETAs(self.control, self.template.tokens, self.template.varTHETABlock,
                                         self.phenotype, self.template.lastFixedTHETA)
        self.control = utils.matchRands(self.control, self.template.tokens, self.template.varOMEGABlock, self.phenotype,
                                        self.template.lastFixedETA, "ETA")
        self.control = utils.matchRands(self.control, self.template.tokens, self.template.varSIGMABlock, self.phenotype,
                                        self.template.lastFixedEPS, "EPS")
        self.control = utils.matchRands(self.control, self.template.tokens, self.template.varSIGMABlock, self.phenotype,
                                        self.template.lastFixedEPS, "ERR")  # check for ERRo as well

        if options.isGA or options.isPSO:
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
            log.error("No tokens found, exiting")
            self.errMsgs.append("No tokens found")
            raise RuntimeError("No tokens found")

        return 

def read_data_file_name(model):
    with open(model.controlFileName, "r") as f: 
        datalines = []
        
        for ln in f:
            if ln.strip().startswith("$DATA"):
                line = ln.strip()
                line = line.replace("$DATA ","").strip()
                # remove comments
                if ";" in line:
                    pos = line.index(";")
                    line = line[:pos]
                # look for quotes, single or double. if no quotes, find first white space
                if "\"" in line:
                    l = line.split('"')[1::2]
                    datalines.append(l[0].strip())
                elif "\'" in line:
                    l = line.split("'")[1::2]
                    datalines.append(l[0].strip())
                else: 
                    # find first while space
                    result = re.search('\s', line)
                    if result is None:
                        datalines.append(line.strip())
                    else:
                        datalines.append(line[:result.regs[0][0]].strip())

    return datalines


def check_files_present(model):
    global files_checked

    if files_checked:
        return

    model.make_control_file()

    cwd = os.getcwd()

    os.chdir(model.runDir)

    log.message("Checking files in " + os.getcwd())

    if not exists(model.controlFileName):
        log.error("Cannot find " + model.controlFileName + " to check for data file")
        sys.exit()

    try:
        data_files_path = read_data_file_name(model)
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

    files_checked = True


def start_new_model(model: Model, all_models):
    current_code = str(model.model_code.IntCode)

    if current_code in all_models and model.copy_results(all_models[current_code]):
        model.source = "saved"
        model.copy_model()
        model.status = "Done"
    else:
        model.run_model()  # current model is the general model type (not GA/DEAP model)

    if model.status == "Done":
        nm_tran_msgs = model.NMtranMSG

        if GlobalVars.BestModel is None or model.fitness < GlobalVars.BestModel.fitness:
            _copy_to_best(model)

        if model.source == "new":
            model.cleanup()  # changes back to home_dir
            # Integer code is common denominator for all, entered into dictionary with this
            if isinstance(model.jsonListRecord, dict):
                all_models[str(model.model_code.IntCode)] = model.jsonListRecord

        step_name = "Iteration"
        prderr_text = ""

        if options.isGA:
            step_name = "Generation"

        if len(model.PRDERR) > 0:
            prderr_text = " PRDERR = " + model.PRDERR

        with open(GlobalVars.output, "a") as result_file:
            result_file.write(f"{model.runDir},{model.fitness:.6f},{''.join(map(str, model.model_code.IntCode))},"
                              f"{model.ofv},{model.success},{model.covariance},{model.correlation},{model.num_THETAs},"
                              f"{model.num_OMEGAs},{model.num_SIGMAs},{model.condition_num},{model.post_run_Rpenalty},"
                              f"{model.post_run_Pythonpenalty},{model.NMtranMSG}\n")
            result_file.flush()

        fitness_crashed = model.fitness == options.crash_value
        fitness_text = f"{model.fitness:.0f}" if fitness_crashed else f"{model.fitness:.3f}"

        log.message(
            f"{step_name} = {model.generation}, Model {model.modelNum:5},"
            f"\t fitness = {fitness_text}, \t NMTRANMSG = {nm_tran_msgs.strip()},{prderr_text}"
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


def write_best_model_files(control_path, result_path):
    with open(control_path, 'w') as control:
        control.write(GlobalVars.BestModel.control)

    with open(result_path, 'w') as result:
        result.write(GlobalVars.BestModelOutput)
