import json
#import xmltodict
import xml.etree.ElementTree as ET
import sys
import re 
import math

from sympy import true
#import model_code
import numpy as np
from typing import OrderedDict
import collections
from unittest.mock import seal
import utils  
import psutil 
import os, shutil
from os.path import exists
import errno
import pkg_resources
 
#import pharmpy   
from subprocess import DEVNULL, STDOUT, check_call, Popen
import time   
import glob
import logging
import utils
import GlobalVars
from copy import deepcopy, copy  
import concurrent.futures 
import gc
Rexecutor = concurrent.futures.ThreadPoolExecutor(max_workers=10) # is 10 enough? 
logger = logging.getLogger(__name__)

class Object:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

class template:
    def __init__(self,TemplateTextFile,tokensFile,optionsFile):
        """ """
        self.errMsgs = []
        self.warnings = [] 
        
        #os.chdir(home_dir)
        try:
            self.options = json.loads(open(optionsFile,'r').read())
            self.homeDir = self.options['homeDir'] # just to make it easier
        except Exception as error:
            self.errMsgs.append("Failed to parse JSON tokens in " + optionsFile)  
            logger.error(error)
            raise 
        try:    ## should this be absolute path or path from homeDir??
            self.TemplateText= open(TemplateTextFile,'r').read()  
        except Exception as error:
            self.errMsgs.append( "Failed to open Template file " + TemplateTextFile)    
            logger.error(error)
            raise            
        try:     
             self.tokens = collections.OrderedDict(json.loads(open(tokensFile,'r').read()))
                 
        except Exception as error:
            self.errMsgs.append( "Failed to parse JSON tokens in " + tokensFile)  
            logger.error(error)
            raise         
        
          
        # write out space, to use in test for exhaustive search 
        self.space = []
        if self.options['algorithm'] == "GA":
            self.isGA = True
        else:
            self.isGA = False
        self.gene_max = [] ## zero based
        self.gene_length = [] ## length is 1 based
        self.getGeneLength()
        if self.isGA: # if GA in DEAP, intergers
            for this_group in self.tokens: 
                # build list of names from first token in each set
                # note that first token need not be unique, so have to include token set number
                options = list(range(len(self.tokens[this_group])))
                self.space.append(options)    
        else: # is scikit-optimize or exhaustive
            for this_group in self.tokens: 
                # build list of names from first token in each set
                # note that first token need not be unique, so have to include token set number
                names = []
                set_num = 0
                for this_token in self.tokens[this_group]:
                    names.append(this_group + "[" + str(set_num) + "] =" + this_token[0]  )
                    set_num += 1
               
                self.space.append(names)        
        if not os.path.isfile(self.homeDir):
            os.mkdir(self.homeDir)
        os.chdir(self.homeDir)
        self.control =  self.controlBaseTokens = None
        self.status= "Not initialized" 
        self.lastFixedTHETA = None  ## fixed THETA do not count toward penalty
        self.lastFixedETA =  self.lastFixedEPS =  None  
        self.variableTHETAIndices = [] # for each token set does if have THETA(*) alphanumeric indices in THETA(*)
        self.THETAmatchesSequence = {} # dictionary of source (alpha) theta indices and sequence
                                       # e.g. THETA(ABC) is first in $THETA template, then THETA(DEF)
        self.THETABlock = self.NMtranMSG = None  
        nFixedTHETA,nFixedETA,nFixedEPS, THETABlock, OMEGABlock,SIGMABlock = getFixedParms(self.TemplateText) 
          
        self.varTHETABlock =  getVariableBlock(THETABlock) # list of only the variable tokens in $THETA in template, will population with 
                                                    # tokens below
        self.varOMEGABlock =  getVariableBlock(OMEGABlock) # list of only the variable tokens in $THETA in template, will population with 
                                                    # tokens below
        self.varSIGMABlock =  getVariableBlock(SIGMABlock) # list of only the variable tokens in $THETA in template, will population with 
                                                    # tokens below
     
        self.lastFixedTHETA=nFixedTHETA
        self.lastFixedETA=nFixedETA
        self.lastFixedEPS=nFixedEPS  
        
    def getGeneLength(self):
        ''' argument is the token sets, returns maximum value of token sets and number of bits'''  
        tokenKeys = self.tokens.keys()
        for thisset in tokenKeys:
            val = len(self.tokens[thisset])
            self.gene_max.append(val-1) # max is zero based!!!!, everything is zero based (gacode, intcode, gene_max)
            self.gene_length.append(math.ceil(math.log(val,2))) 

def getFixedParms(Template):
     
    NFixedTHETA,THETABlock = getFixedBlock(Template,"$THETA")
    NFixedOMEGA,OMEGABlock = getFixedBlock(Template,"$OMEGA")
    NFixedSIGMA,SIGMABlock = getFixedBlock(Template,"$SIGMA")
    return  NFixedTHETA, NFixedOMEGA,  NFixedSIGMA ,THETABlock,OMEGABlock,SIGMABlock 
  
def getVariableBlock(Code):
   
    cleanCode = utils.removeComments(Code)
    lines = cleanCode.splitlines() 
    ## remove any blanks
    while("" in lines) :
        lines.remove("")
    varBlock = [] 
    ## how many $ blocks - assume only 1 (for now??)
   
    for thisline in lines:
        if re.search("{.+}",thisline) !=None:
            varBlock.append(thisline)
 
    return varBlock

def getFixedBlock(Code,key): 
    nkeys = Code.count(key)
    # get the block from NONMEM control/temlate
    # e.g., $THETA, even if $THETA is in several sections
    # were key is $THETA,$OMEGA,$SIGMA
    block = ""
    start = 0
    FullBlock = []
    for _ in range(nkeys):  
        start = Code.find(key,start)
        end = Code.find("$",start+1)
        block = block + Code[start: end] + '\n'
        start = end  
        ## remove blank lines, and trim
    lines = block.splitlines()
    FullBlock.append(lines)
    Code = []
    nfixed = 0
    for thisline in lines: 
        ### remove blanks, options and tokens, comments
        thisline = utils.removeComments(thisline).strip()  
        ## count fixed only, n 
        # visual studio code showing warning for "\$" below, but that is just literal $ at beginning of line, eg., $THETA
        if (thisline != "" and (not(re.search("^{.+}",thisline)))) and  not re.search("^\$.+",thisline):
            nfixed +=1
    return nfixed,FullBlock
 

class model:
    """The full model, used for GA, GP, RF, GBRF and exhaustive """
    def __init__(self,template: template,code: list, model_num: int,is_ga:bool, generation = None ): # for ga, code is full GA/DEAP individual, with fitness
        """code is a model_code object, type defines whether it is full binary (for GA), minimal binary (for downhill)
        or integer.
        makecontrol always used intcode"""
        self.ofv = self.crash = None
        self.slot = None # which slot in the queue is this run in? need for running R code, assinged at start_model
        self.template = template
        self.source = "new" # new if new run, "saved" if from saved model, will be no results and no output file - consider saving output file?
        self.generation = generation 
        # get model number and phenotype
        self.modelNum = model_num
        self.errMsgs = [] 
        self.model_code = copy(code)
        # all required representations of model are done here
        # GA -> integer, 
        # integer is just copied
        # minimal binary is generated, just in case this is a downhill step 
        self.success = self.covariance = self.correlation =  False
        self.OMEGA = self.SIGMA = None
        self.post_run_text = ""
        self.NMtranMSG = ""
        self.PRDERR = ""
        self.Rfuture = None # hold future for running R code
        self.fitness = self.template.options['crash_value'] 
        self.post_run_penalty = self.Condition_num_test = self.condition_num  = self.num_THETAs = self.num_non_fixed_THETAs = self.num_OMEGAs = self.num_SIGMAs = self.ofv= None
        self.jsonListRecord = None # this is a list of key values to be saved to json file, for subsequent runs and to avoid running the same mdoel
        self.Num_noninfluential_tokens = 0 # home many tokens, due to nesting have a parameter that doesn't end up in the control file?
        self.token_Non_influential = [True]*len(self.template.tokens) # does each token result in a change? does it containt a parameter, if token has a parameter, but doesn't
                                                    # default is true, will change to false if: 1. doesn't contain parameters (in check_contains_parms) is put into control file (in utils.replaceTokens)     
        self.startTime = time.time()     
        self.ElapseTime = None
         
    def __del__(self):
        gc.collect()

    def data_present(self)-> bool: 
        """is the data file specified in the control file present? """
        text = self.control

        self.datafile_name = "data.csv"
        return  True
    def copyResults(self,prevResults):
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
            self.post_run_text = prevResults['post_run_text']
            self.post_run_penalty = prevResults['post_run_penalty']
            self.NMtranMSG = prevResults['NMtranMSG'] 
            self.NMtranMSG = "From saved model " +  self.NMtranMSG  #["","","","output from previous model"]
            self.status = "Done"
            return True
        except:
            return False
 
    def startModel(self): 
        self.filestem = 'NMModel_' + str(self.generation) + "_" + str(self.modelNum)
        self.runDir = os.path.join(self.template.homeDir,str(self.generation),str(self.modelNum))      
        self.controlFileName = os.path.join(self.runDir, self.filestem +".mod")
        self.outputFileName = os.path.join(self.runDir, self.filestem +".lst")
        self.xml_file = os.path.join(self.runDir, self.filestem +".xml")
        self.executableFileName = os.path.join(self.runDir,self.filestem +".exe") 
        self.MakeControl()
         # check if data file is present, still to do
        if not self.data_present():
            raise SystemExit('data set ' + self.datafile_name + ' not found') 
        # in case the new folder name is a file
        try:
            if os.path.isfile(os.path.join(self.template.homeDir,str(self.generation))) or os.path.islink(os.path.join(self.template.homeDir,str(self.generation))):
                os.unlink(os.path.join(self.template.homeDir,str(self.generation)))
            if os.path.isfile(self.runDir) or os.path.islink(self.runDir):
                os.unlink(self.runDir)
            if not os.path.isdir(self.runDir):
                os.makedirs(self.runDir)
        except:
            print(f"Error removing run files/folders for {self.runDir}, is that file/folder open?")
        for filename in os.listdir(self.runDir):
            file_path = os.path.join(self.runDir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (self.runDir, e))
        ## check key file, just to make sure
        if os.path.exists(self.controlFileName):
            os.remove(self.controlFileName)
        if os.path.exists(self.outputFileName ):
            os.remove(self.outputFileName )
        with open(self.controlFileName, 'w+') as f: 
            f.write(self.control)  
            f.flush()

        os.chdir(self.runDir)
        command = [self.template.options['nmfePath'],self.controlFileName ,self.outputFileName, " -nmexec=" + self.executableFileName]
        GlobalVars.UniqueModels += 1
        self.Process = Popen(command, stdout=DEVNULL, stderr=STDOUT)
        self.start = time.time()
        self.status = "RunningNM"
        return
    def runR(self):
        """Run R code specified in the file options['postRunCode'], return penalty from R code
        https://rpy2.github.io/doc/latest/html/introduction.html#getting-started"""
         
        try:

            Rargs = list(self.template.options['Rargs'].values())
            rval =   GlobalVars.SlotRobjects[self.slot](self.runDir,Rargs)     # folder for NONMEM run is required, and only this argument may be sent
        #                               # all other variables needed must be coded into the R function
        except:
            rval = [self.template.options['crash_value'],f"Error in callin RPenalty object from RunR function with,{self.model_num} in R code MUST be called RPenalty (case sensitive)" ]
                # recommend gc after ach call to R - https://rpy2.github.io/doc/latest/html/performances.html#
        gc.collect()
        return rval
        
    def run_post_Code(self): 
        """Run the post minimization R code in the file specified in the options file filename = postRunCode
        creates a future (self.Rfuture) which is then checked in check_done_postRun
        Post run code MUST be a function that takes self.rundir as the only argument
        and returns an array of two values, the penalty and text to append to the output e.g., c(penalty, text)"""
       
        try:
            ## need to write as a function that take the rundir as the argument, otherwise will
            ## run in the last start model rundir
            
            self.Rfuture = Rexecutor.submit(self.runR)
        except:
            print("unable to access R future object")  
            self.status = "Done"
            self.post_run_penalty = self.template.options['crash_value'] 
            return
         
        return
    def check_done_postRun(self):  
        if self.template.options['useR']:
            if self.Rfuture.done(): #also is _state property, will be "FINISHED" when done, "RUNNING" before done
                try:
                    self.post_run_penalty = float(self.Rfuture._Future__get_result()[0])
                except:
                    self.post_run_penalty = self.template.options['crash_value']
                try:    
                    self.post_run_text = self.Rfuture._Future__get_result()[1]
                except:
                    self.post_run_text = " no R output available"
                
                with open(self.outputFileName,"a") as f:
                    f.write("\nPost Run text output: " + self.post_run_text)
                 
                 
                return(True)
            else:
                return(False) 
    # def get_results(self):
    #     with open(self.xml_file) as xml_file:
    #         data_dict = xmltodict.parse(xml_file.read()) 
        # note that there will be nm:output/nm:nonmem/nm:problem/
        # then a list of 000-??? @subproblems, the first will likely be the estimate, then any for simulation
        # so, get last estimation index with len(data_dict['nm:output']['nm:nonmem']['nm:problem'][000]['nm:estimation'])
        # and ofv is data_dict['nm:output']['nm:nonmem']['nm:problem'][000]['nm:estimation'][len-1]['nm:final_objective_function']
        # similarly nm:termination_status
        # ['nm:theta']['nmval']['nm:omega']['nm:row']['nmval'][n]['nm:col'], ['nm:sigma'] 
        # similarly for nm:thetase etc
        # nm:correlation gives correlation matrix and nm:eigenvalues
        # also has nmtran messages in data_dict['nm:nmtran']
        # does not have prderr
        # then in nm:problem\nm
    def check_done(self):
        """Check is the model is done running, uses the Process of the object. Process.poll() return of 107 or 110 
        seems to mean failed to start. Process.poll() of 0 is finished  
        If done, calls (the excellect package) pharmpy to collect results, then either calls run_post_Code (if applicable) 
        or calls calcFitness."""
        if self.status == "Done": # if done here, then already has post run code results
            return True 
        if self.status == "RunningNM":
            if self.Process.poll() == 107 or self.Process.poll() == 110:
            # check FSMG here
                self.fitness = self.template.options['crash_value'] 
                self.NMtranMSG = ( "", "","","No NONMEM execution, is data file present?") # 3 lines empty so we can get the usual (no error) message
                self.process = None
                gc.collect()
                if self.template.options['useR']:
                    self.run_post_Code()
                    self.status = "Running_post_code"
                    return False
                else:
                    self.calcFitness()
                    self.status = "Done" # done with all 
                    self.elapseTime = time.time() - self.startTime
                    return True
            if self.Process.poll() == 0: # done with NM, create the model here, before any post code run
                self.get_results_from_xml()
                self.process = None
                gc.collect()
                #self.result = pharmpy.Model.create_model(self.controlFileName)  
                if self.template.options['useR']:
                    self.run_post_Code()
                    self.status = "Running_post_code"
                    return False
                else:
                    self.calcFitness()
                    self.status = "Done"
                    self.elapseTime = time.time() - self.startTime
                    return True 
            else: 
                end = time.time()
                if (end-self.start) > int(self.template.options['timeout_sec']):
                    print(f"overtime, model in {self.runDir}")
                    try:
                        p = psutil.Process(self.Process.pid)
                        p.terminate()   
                    except:
                        pass 
                    self.get_results_from_xml()
                    self.process = None
                    gc.collect()
                    if self.template.options['useR']:
                        self.run_post_Code()
                        self.status = "Running_post_code"
                        return False
                    else:
                        self.calcFitness()
                        self.status = "Done"
                        self.elapseTime = time.time() - self.startTime
                        return True  
            time.sleep(0.1)  # not sure this adds anything
            self.status = "RunningNM"
            return False
        if self.status == "Running_post_code":
            if self.check_done_postRun():
                self.calcFitness()
                self.status = "Done"
                return True
    def get_results_from_xml(self):
        if not exists(self.xml_file):
            self.crash = True
            self.success = self.covariance = self.correlation  = False
            self.Condition_num_test = False
            self.condition_num = 9999999
            self.ofv = None
            self.fitness = self.template.options['crash_value']
            return()

        tree = ET.parse(self.xml_file)
        root = tree.getroot()
        orgnamespace = root.tag
        namespaceroot = orgnamespace.replace("output","")
        namespace= namespaceroot.replace("{","").replace("}","") 
        ns = {"NMresult":namespace} 
       ## ##THETALB = root.find('NMresult:theta_lb',ns)#
        nonmem = root.find('NMresult:nonmem',ns)   
        #Lbs = THETALB.find('nm:val nm:name')
        EstimationProblem = nonmem.find('NMresult:problem',ns) 
        Estimations = EstimationProblem.findall('NMresult:estimation',ns   )
        NumEstimations = len(Estimations) #only the final estimation
        FinalEst = Estimations[NumEstimations-1]
        self.crash = False
        if len(FinalEst.findall('NMresult:final_objective_function',ns))==0:
            self.crash = True
            self.success = self.covariance = self.correlation  =  self.Condition_num_test = False
            self.condition_num = 9999999
            self.ofv = None
            self.fitness = self.template.options['crash_value']
            return()
        self.ofv = float(FinalEst.findall('NMresult:final_objective_function',ns)[0].text)
        Convergence = int(FinalEst.findall('NMresult:termination_status',ns)[0].text)
        if Convergence == 0:
            self.success = True
        else:
            self.success = False
        Covariance_results = FinalEst.findall('NMresult:covariance_status',ns)[0] 
        allCov = dict(Covariance_results.attrib)
        self.covariance_error = int(allCov[namespaceroot + "error"]) 
        # covariance matrix
        if self.covariance_error == 0:
            self.covariance = True
            allcorr = FinalEst.findall('NMresult:correlation',ns)[0]
            rows = allcorr.findall('NMresult:row',ns)
            #NumRowsCorr = len(rows)
            numCols = 0
            Correlation_limit = self.template.options['correlationLimit']
            self.correlation  = True
            for thisrow in rows:
                if numCols > 0:
                    thiscol = thisrow.findall('NMresult:col',ns)
                    offdiags = thiscol[:numCols]
                    for thisval in offdiags:
                        val = abs(float(thisval.text))
                        if val> Correlation_limit:
                            self.correlation  = False
                numCols += 1 
             
            maxEigen = -9999999
            minEigen = 99999999 

            allEigens = FinalEst.findall('NMresult:eigenvalues',ns)[0]
            
            
            for this_eigen in allEigens: # are the always sorted assending
                eigen = float(this_eigen.text)
                if eigen> maxEigen: maxEigen = eigen
                if eigen < minEigen: minEigen = eigen
            self.condition_num  = maxEigen/minEigen
            if self.condition_num > 1000:
                self.Condition_num_test = False
            else:
                self.Condition_num_test = True
        else:
            self.Condition_num_test = False
            self.correlation  = False
            self.covariance = False
            self.condition_num = 999999
        # nmtran msgs
        self.nmtran = root.find('NMresult:nmtran',ns).text

           # numthetas
        thetalb = EstimationProblem.findall('NMresult:theta_lb',ns  )[0]
        thetaub = EstimationProblem.findall('NMresult:theta_ub',ns  )[0]
        valslb = thetalb.findall('NMresult:val',ns) 
        #valsub = thetaub.findall('NMresult:val',ns) 
        numtheta = len(valslb)
        num_thetas_fixed = 0
        for this_theta in range(numtheta): 
            
            if thetalb[this_theta] == thetaub[this_theta]:
                num_thetas_fixed += 1 
        self.num_THETAs = numtheta
        self.num_non_fixed_THETAs = numtheta-num_thetas_fixed
        # add in final THETA estimates, may need someday? for plausability score?           
        # omega  will always be a full matrix, value of 0 means fixed
        # found in estimation 
        omegaBlock = FinalEst.findall('NMresult:omega',ns)[0]
        rows = omegaBlock.findall('NMresult:row',ns)
        NumRowsOmega = len(rows)
        OMEGA = []
        for _ in range(NumRowsOmega):
            OMEGA.append([None]*NumRowsOmega) #,[None]*NumRowsOmega]#*NumRowsOmega
        cur_row = 0  
        NumOmega = 0
        for thisrow in rows: 
            cur_col = 0
            thiscol = thisrow.findall('NMresult:col',ns) 
            for thisval in thiscol:
                OMEGA[cur_row][cur_col] = float(thisval.text)  
                if(OMEGA[cur_row][cur_col]) !=0.00:
                    NumOmega += 1
                cur_col += 1
            cur_row += 1
        self.num_OMEGAs = NumOmega
        self.OMEGA = OMEGA # may need someday?
        sigmaBlock = FinalEst.findall('NMresult:sigma',ns)[0]
        rows = sigmaBlock.findall('NMresult:row',ns)
        NumRowsSigma = len(rows)
        SIGMA = []
        for _ in range(NumRowsSigma):
            SIGMA.append([None]*NumRowsSigma) #,[None]*NumRowsOmega]#*NumRowsOmega
        cur_row = 0  
        NumSigma = 0
        for thisrow in rows: 
            cur_col = 0
            thiscol = thisrow.findall('NMresult:col',ns) 
            for thisval in thiscol:
                SIGMA[cur_row][cur_col] = float(thisval.text)  
                if(SIGMA[cur_row][cur_col]) !=0.00:
                    NumSigma += 1
                cur_col += 1
            cur_row += 1
        self.num_SIGMAs = NumSigma
        self.SIGMA = SIGMA
        root.clear()
        if exists(self.xml_file):
            os.remove(self.xml_file)
        gc.collect()
        return()
       
    def calcFitness(self): 
        """calculates the fitness, based on the model output, and the penalties (from the options file)
        need to look in output file for parameter at boundary and parameter non positive """
        self.NMtranMSG = ""
        try:
            if(os.path.exists(os.path.join(self.runDir,"FMSG"))):
                with open(os.path.join(self.runDir,"FMSG"), 'r') as file:  
                    # to do remove all empty (\n) lines 
                    msg = file.readlines()
                warnings =  [' (WARNING  31) $OMEGA INCLUDES A NON-FIXED INITIAL ESTIMATE CORRESPONDING TO\n', \
                ' (WARNING  41) NON-FIXED PARAMETER ESTIMATES CORRESPONDING TO UNUSED\n', \
                ' (WARNING  40) $THETA INCLUDES A NON-FIXED INITIAL ESTIMATE CORRESPONDING TO\n']
                shortwarnings =  ['NON-FIXED OMEGA ','NON-FIXED PARAMETER ','NON-FIXED THETA']  
                for thiswarning, thisshortwarning in zip(warnings,shortwarnings):
                    if thiswarning in msg:
                        self.NMtranMSG += thisshortwarning
            if(os.path.exists(os.path.join(self.runDir,"PRDERR"))):
                with open(os.path.join(self.runDir,"PRDERR"), 'r') as file:   
                    msg = file.readlines()
                warnings =  ['PK PARAMETER FOR', \
                             'IS TOO CLOSE TO AN EIGENVALUE', \
                             'F OR DERIVATIVE RETURNED BY PRED IS INFINITE (INF) OR NOT A NUMBER (NAN)']  
                for thiswarning in warnings:
                    for thisline in msg: 
                        if thiswarning in thisline and not (thisline.strip() + " ") in self.PRDERR:
                            self.PRDERR += thisline.strip() + " "
                     
            if self.NMtranMSG == "":
                self.NMtranMSG = "No important warnings"
                    ## try to sort relevant message?
                    # key are (WARNING  31) - non fixed OMEGA and (WARNING  41) non fixed parameter and (WARNING  40) non fixed theta
        except:
            pass
        try:
            if (self.ofv == None):
                self.fitness = self.template.options['crash_value']
                return  
            else:
                self.fitness = self.ofv
                # non influential tokens penalties                    
                self.fitness += self.Num_noninfluential_tokens * self.template.options['non_influential_tokens_penalty']
                self.ofv = min(self.ofv , self.template.options['crash_value'])
        except:
            self.fitness = self.template.options['crash_value']
            return

        try:        
             
            if not self.success: 
                self.fitness += self.template.options['covergencePenalty']   
     
            if not self.covariance: #covariance_step['completed'] != True:
                self.fitness += self.template.options['covariancePenalty']    
                self.fitness += self.template.options['correlationPenalty']
                self.fitness += self.template.options['conditionNumberPenalty']   
            else:  
                if not self.correlation:
                    self.fitness += self.template.options['correlationPenalty'] 
                 
# for some reason pharmpy0.61 doesnt have eigen values, will need to read from xml file
# could just everything from the xml file
                # with open(self.xml_file) as xml_file:
                #     data_dict = xmltodict.parse(xml_file.read()) 
                # numESTs = len(data_dict['nm:output']['nm:nonmem']['nm:problem'][000]['nm:estimation'])
                # result = data_dict['nm:output']['nm:nonmem']['nm:problem'][000]['nm:estimation'][numESTs-1]
                # #ofv = result['nm:final_objective_function']
                # #NMTRANMsg = data_dict['nm:output']['nm:nmtran'] 
                # Eigens = result['nm:eigenvalues']['nm:val']
                # #EigenValues = []  # don't actually need these  
                # max = -9999999
                # min = 9999999
                # for i in Eigens:
                #     val = float(i['#text'])
                #     #EigenValues.append(val)
                #     if val < min: min = val
                #     if val > max: max = val
                # self.result.modelfit_results.condition_num = max/min

                if not self.Condition_num_test: #  
                    self.fitness += self.template.options['conditionNumberPenalty']    
                ## parsimony penalties
               
            self.fitness += self.num_non_fixed_THETAs * self.template.options['THETAPenalty']    
            self.fitness += self.num_OMEGAs * self.template.options['OMEGAPenalty']    
            self.fitness += self.num_SIGMAs * self.template.options['SIGMAPenalty']  
           
        except:
            self.fitness = self.template.options['crash_value']
        if self.template.options['useR']:
            try:
                self.fitness += self.post_run_penalty 
            except:
                self.fitness = self.template.options['crash_value']
            try:
                with open(self.outputFileName,"a") as f:
                    f.append("\nPost Run text" + self.post_run_text)
                    f.flush()
            except:
                pass
        if self.fitness > self.template.options['crash_value']:
            self.fitness = self.template.options['crash_value'] 
            # save results
        self.MakeJsonList()
        return

    def MakeJsonList(self):
        """assembles what goes into the JSON file of saved models"""
        self.jsonListRecord = {"control": self.control, "fitness": self.fitness,"ofv": self.ofv,"success": self.success,"covariance": self.covariance,"post_run_text": self.post_run_text, "post_run_penalty": self.post_run_penalty, \
             "correlation": self.correlation,"num_THETAs": self.num_THETAs,"num_OMEGAs": self.num_OMEGAs,"num_SIGMAs": self.num_SIGMAs, "condition_num": self.condition_num, \
                 "NMtranMSG":self.NMtranMSG}
        return

    def cleanup(self):  
        """deletes all unneeded files after run
        no argument, no return value """
        if self.source == "saved":
            return # ideally shouldn't be called for saved models, but just in case
        try:
            os.chdir(self.template.homeDir)
        except OSError as e:
            print(f"OS Error {e}")
        try:
            if self.template.options['remove_run_dir'] == "True":
                try:
                    if os.path.isdir(self.runDir):
                        shutil.rmtree(self.runDir)
                except OSError:
                    print("Cannot remove folder {self.runDir}")
            else:
                file_to_delete = [self.filestem +".ext",
                                self.filestem +".clt",
                                self.filestem +".coi",
                                self.filestem +".cor",
                                self.filestem +".cov",
                                self.filestem +".cpu",
                                self.filestem +".grd",
                                self.filestem +".phi",
                                self.filestem +".shm", 
                                self.filestem +".smt",
                                self.filestem +".shk",
                                self.filestem +".rmt",
                                self.executableFileName, 
                                "PRSIZES.F90",
                                "ifort.txt",
                                "nmpathlist.txt",
                                "nmprd4p.mod",
                                "INTER"]
                file_to_delete = file_to_delete + glob.glob('F*') +  glob.glob('W*.*') +  glob.glob('*.lnk')
                for f in file_to_delete:
                    try:
                        os.remove(os.path.join(self.runDir,f))
                    except OSError:
                        pass
            if os.path.isdir(os.path.join(self.runDir,"temp_dir")):
                shutil.rmtree(os.path.join(self.runDir,"temp_dir") )
        except OSError as e:
            print(f"OS Error {e}")
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
            self.token_Non_influential[tokensetNum] = isinfluential # doesn't containt parm, so can't contribute to non-influential count
               
            tokensetNum += 1
        return 

    def MakeControl(self):  
        "constructs control file from intcode"""
        self.phenotype = OrderedDict(zip(self.template.tokens.keys(), self.model_code.IntCode))  
        self.check_contains_parms() # fill in whether any token in each token set contains THETA,OMEGA SIGMA
            
        anyFound = True #keep looping, looking for nested tokens 
        self.control = self.template.TemplateText
        token_found = False # error check to see if any tokens are present
        for _ in range(3): # always need 2, and won't do more than 2, only support 1 level of nested loops          
            anyFound = False 
            anyFound, self.control = utils.replaceTokens(self.template.tokens,self.control,self.phenotype,self.token_Non_influential)
            self.Num_noninfluential_tokens = sum(self.token_Non_influential)               
            token_found = token_found or anyFound 
        if anyFound:
            raise RuntimeError("Is there more than 1 level of nested tokens??")
           
            
        self.control = utils.matchTHETAs(self.control,self.template.tokens,self.template.varTHETABlock,self.phenotype,self.template.lastFixedTHETA)
        self.control = utils.matchRands(self.control,self.template.tokens,self.template.varOMEGABlock,self.phenotype,self.template.lastFixedETA,"ETA")
        self.control = utils.matchRands(self.control,self.template.tokens,self.template.varSIGMABlock,self.phenotype,self.template.lastFixedEPS,"EPS")
        if self.template.isGA: 
            self.control += "\n ;; Phenotype \n ;; " + str(self.phenotype) + "\n;; Genotype \n ;; " + str(self.model_code.FullBinCode) + \
            "\n;; Num influential tokens = " + str(self.token_Non_influential)    
        self.control += "\n ;; Phenotype \n ;; " + str(self.phenotype) + "\n;; code \n ;; " + str(self.model_code.IntCode) + \
            "\n;; Num influential tokens = " + str(self.token_Non_influential)    
        if not(token_found):
            self.errMsgs.append("No tokens found") 
        return  
     
 