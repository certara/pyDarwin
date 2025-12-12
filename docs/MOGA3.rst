.. _moga3-label:

MOGA3
======
MOGA3 requires user defined code. The template.txt and tokens.json files are identical to those used for other single 
objective algorithms. 



Partitions and population size
--------------------------------

In theory, with more than two or more continuous objective, there can be an infinite number of non-dominated 
solutions. Keep in mind that to be dominated requires that ALL objective in some other solution are better. 
One can imagine a set of solutions with 2 continuous objectives with a list of objectives with values 
alternating with decriments of 0.000001, such that all are non-dominated. The solution to this problem, as 
well as to improve performance, is to partition the search space such that the direction of the search 
is divided into a finite number of directions. The number of parititions will influence the number of 
non-dominated returned by the algorithm, with the number of non-dominated being (roughly) equal to or 
less than the number of partitions. The non-dominated solutions returned will typically be distributed 
throughout the search space. That is, the you are unlikely to get all 2 compartment models with additive 
residual error, and just varying by covariates. More likely there will be a mix of 1 and 2 compartment models, 
with and without ALAG, different residual errors and a range of covariates.

The number of partitions possible will be limited by the population size. A useful (although very technical) 
guide can be found here:
`Cheng et al <https://journals.sagepub.com/doi/10.3233/ICA-170542>`_.

Practically, the population size will be 50-100 (potentially larger with more complex searchs). The number of 
partitions will then be driven by the number of non-dominated models that the user would like returned for 
further consideration. Perhaps 6-12 partitions might typically be used.

The number of paritions is set in the options.json file (`Options.json <https://certara.github.io/pyDarwin/html/Options.html>`_).
An example is below:
 

.. code-block:: JSON

    {
    "MOGA" : {
        "attribute_mutation_probability" : 0.1,
        "constraints" : 1,
        "crossover" : "single",
        "crossover_rate" : 0.95,
        "mutation_rate" : 0.95,
        "names" : [
            "OFV",
            "Nparms",
            "NFailedRSEs"
        ],
        "objectives" : 3,
        "partitions" : 6
    },
    "algorithm" : "MOGA3",
    "postprocess": {
            "use_r": false,
            "use_python": true,
            "post_run_python_code": "{project_dir}/RSE3penalty.py",
            "r_timeout": 30
        },
    "author" : "Certara", 
    "downhill_period" : 3,
    "engine_adapter" : "nlme",
    "final_downhill_search" : true,
    "gcc_dir" : "C:\\Program Files\\Certara\\mingw64",
    "keep_extensions" : ["csv"],
    "keep_files" : ["res.csv","residuals.csv"],
    "local_2_bit_search" : false,
    "model_run_timeout" : 1200,
    "niche_radius" : 2,
    "nlme_dir" : "C:\\Program Files\\Certara\\NLME_Engine",
    "num_generations" : 6,
    "num_niches" : 2,
    "num_parallel" : 1,
    "population_size" : 30,
    
    "project_name" : "MOGA3",
    "random_seed" : 51424319,
    "rscript_path" : "C:/Program Files/R/R-4.5.1/bin/Rscript.exe",
    "working_dir" : "{project_dir}"
    }




Post Run R code
---------------
It is important to insure that R returns (to standard output) the correct number of value in all cases. 
This requires using the suppres? function for all other output, e.g., to load the xpose package, the 
syntax would be:

.. code-block:: R

    suppressPackageStartupMessages(library(xpose))


and to load the NONMEM output into an xpose data base:

.. code-block:: R

        suppressWarnings(xpdb <- xpose_data(file = lstfile, quiet = TRUE))

NONMEM
---------------

NONMEM Post Run R code
~~~~~~~~~~~~~~~~~~~~~~~~
Below is R code to return 3 objectives (OFV, n parameters and the number of parameter estimates with RSE > 0.5), 
and a constraint if anything goes wrong (0 = feasible solution, 1 = infeasible solution).
Note again that this is a script, not a function.

.. code-block:: R
    
    suppressPackageStartupMessages(library(dplyr))
    suppressPackageStartupMessages(library(xpose))
    suppressPackageStartupMessages(library(stringr))
    suppressWarnings({
        suppressMessages({
            OFV <- nparms  <- nfailedRSEs <- 99999
            tryCatch({
                lstfile <- list.files(path = ".",
                                    pattern = "lst$")
                if(length(lstfile) == 0){
                    print(c(OFV, nparms, nfailedRSEs))
                    print(c(1))
                } else{
                    suppressWarnings({
                        xpdb <- xpose_data(file = lstfile, quiet = TRUE)
                    })
                    res <- get_summary(xpdb)
                    OFVpos <- which(res$descr == 'Objective function value')
                    OFV <- res$value[OFVpos]
                    if(OFV == "na") OFV <- 99999
                    res <- tryCatch(
                        prm <- get_prm(xpdb, quiet = TRUE),
                        error = function(e) e
                    )
                    if (inherits(res, "error")) {
                        print(c(OFV, nparms, nfailedRSEs))
                        print(c(1))
                    } else{
                    nparms <- length(prm$name)
                    values <- prm$value
                    ses <- prm$se
                    if(!is.na(ses[1])){
                        rses <- ses/values
                        nfailedRSEs <- sum(rses > 0.5)
                    }else{
                        nfailedRSEs <- nparms
                    }
                    print(c(OFV, nparms, nfailedRSEs))
                    print(c(0))
                    }
                }
                }, error = function(){
                    print(c(OFV, nparms, nfailedRSEs))
                    print(c(1))
            })
        })
    })



NONMEM Post Run python code - post_process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Note that the pharmpy-core package is required for post run NONMEM code.


.. code-block:: python    

    import math
    import numpy as np
    import os
    import re 
    from pharmpy.tools import *
    import warnings
    import sys
    def read_nmoutput(rundir):
        """
        uses pharmpy function to read nonmem outputd return OFV,  nparms and n failed RSEs.
        Parameters
        ----------
        rundir : pyDarwin model run directory

        Returns
        -------
        OFV, nparms, nfailedRSEs

        """

        try:
            ofv = nparms = nfailedRSEs = 99999
            mod_file = None
            for filename in os.listdir(rundir):
                if filename.endswith(".mod") and filename.startswith("NM_") and os.path.isfile and filename[3].isdigit():
                    os.path.join(rundir, filename)
                    mod_file = os.path.join(rundir, filename)
                    break
            if mod_file is None:
                return [ofv, nparms, nfailedRSEs], [1]
            else:
                warnings.filterwarnings("ignore") #pharmpy function throws warning about parameter name THETA etc duplicated
                res = read_modelfit_results(mod_file)
                warnings.filterwarnings("default")
                ofv = getattr(res, "ofv", 9999999)
                if np.isnan(ofv):
                    ofv = 99999
                parms = getattr(res, "parameter_estimates", 999999)
                nparms = len(parms)
                if getattr(res, 'covstep_successful'):
                    rses = getattr(res,'relative_standard_errors')
                    nfailedRSEs  = sum(1 for item in rses if item > 0.5)
                else:
                    nfailedRSEs = nparms
            return ofv, nparms, nfailedRSEs
        except:
            return ofv, nparms, nfailedRSEs




    def post_process(rundir):
        """post run processing for MOGA3 in python. post_process2 takes the run directory as the argument, return
        ofv, number of parameters and number of parameters with RSE > 0.5. Excepteion return available values
        and constraint = 1

        Parameters
        ----------
        rundir : pyDarwin model run directory

        Returns
        -------
        objectives, constraint [float, float, float],[constraint]


        Examples
        --------
        post_process(rundir)
        [10.2, 8, 1],[0]
        """

        try:
            ofv, nparms, nfailedRSEs = read_nmoutput(rundir)
            return [ofv, nparms, nfailedRSEs], [0]
        except Exception as e:
            return [ofv, nparms, nfailedRSEs], [1]

    if __name__ == '__main__':
        print(post_process(sys.argv[1]))


the 

.. code-block:: python

    if __name__ == '__main__':
        print(post_process(sys.argv[1]))


code is again included so that it can be run from command line for checking. An example of code 
to run from command line is:


.. code-block:: console

    python RSE3penalty.py temp/1/01
    ([np.float64(5668.41945648538), 11, 11], [0])


NONMEM Post Run python code - post_process2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The pharmpy-core package is required for the python code below. while some results are available in the run 
object (OFV, number of parameters), others are not (RSEs in this case). The run directory (run_dir in the results 
object) is then used to identify the NM_*.mod file. The read_modelfit_results function in pharmpy-tools is then 
called with the .mod file to return the requred RSEs. It is not possible to run the post_process2 code from command 
line.


.. code-block:: python

    import math
    import numpy as np
    import os
    import re 
    from pharmpy.tools import *
    import warnings
    def read_nmoutput(rundir):
        """
        uses pharmpy function to read nonmem outputd return OFV,  nparms and n failed RSEs.
        Parameters
        ----------
        rundir : pyDarwin model run directory

        Returns
        -------
        OFV, nparms, nfailedRSEs

        """

        try:
            ofv = nparms = nfailedRSEs = 99999
            mod_file = None
            for filename in os.listdir(rundir):
                if filename.endswith(".mod") and filename.startswith("NM_") and os.path.isfile and filename[3].isdigit():
                    os.path.join(rundir, filename)
                    mod_file = os.path.join(rundir, filename)
                    break
            if mod_file is None:
                return [ofv, nparms, nfailedRSEs], [1]
            else:
                warnings.filterwarnings("ignore") #pharmpy function throws warning about he parameter name THETA is duplicated.
                res = read_modelfit_results(mod_file)
                warnings.filterwarnings("default")
                ofv = getattr(res, "ofv", 9999999)
                if np.isnan(ofv):
                    ofv = 99999
                parms = getattr(res, "parameter_estimates", 999999)
                nparms = len(parms)
                if getattr(res, 'covstep_successful'):
                    rses = getattr(res,'relative_standard_errors')
                    nfailedRSEs  = sum(1 for item in rses if item > 0.5)
                else:
                    nfailedRSEs = nparms
            return ofv, nparms, nfailedRSEs
        except:
            return ofv, nparms, nfailedRSEs




    def post_process2(run):
        """post run processing for MOGA3 in python. post_process2 takes the run object as the argument, return
        ofv, number of parameters and number of parameters with RSE > 0.5. Excepteion return available values
        and constraint = 1

        Parameters
        ----------
        run : pyDarwin model

        Returns
        -------
        objectives, constraint [float, float, float],[constraint]


        Examples
        --------
        post_process(run)
        [10.2, 8, 1],[0]
        """

        try:
            # read ofv from run, just to demonstrate
            results = getattr(run, "result")
            ofv = getattr(results, 'ofv')
            # but rses are not in run, need to use pharmpy to read output
            rundir = getattr(run, "run_dir")
            ofv, nparms, nfailedRSEs = read_nmoutput(rundir)
            return [ofv, nparms, nfailedRSEs], [0]
        except Exception as e:
            return [ofv, nparms, nfailedRSEs], [1]




NLME
---------------


NLME Post Run R code
~~~~~~~~~~~~~~~~~~~~~~~~
For R post processing code in NLME, the key output is the dmp.txt file. This file, when 
sourced in R (e.g., source("dmp.txt")) generates a dmp.txt object that contains most of the 
key output for very easy access.
The code below returns 3 objectives and one constraint. As for the NONMEM examples, the 
first two objectives are OFV and number of parameters. The third objective is a CmaxPenalty 
for the mean absolute percent bias is Cmax, abs(%(Observed - predicted)) * 10.
This script also returns a constraint of 1 (infeasible) if any RSE values are > 0.5.

.. code-block:: R

    suppressPackageStartupMessages(suppressMessages(library(dplyr)))
    suppressPackageStartupMessages(suppressWarnings(library(stringr))) 
    suppressPackageStartupMessages(suppressWarnings(library(readtext))) 
    suppressPackageStartupMessages(suppressWarnings(library(tidyr))) 
    
    GetCmaxPenalty <- function(CrashPenalty){
        tryCatch({
        source("dmp.txt")
        preds <- dmp.txt$residuals %>% 
            select(ID5, IPRED, DV) %>% 
            group_by(ID5) %>% 
            summarise(ObsCmax = max(DV), PredCmax = max(IPRED)) %>% 
            mutate(Diff = 100*(ObsCmax-PredCmax)/ObsCmax) %>% 
            summarise(MeanAbsDiff = mean(Diff))
        return(10*abs(preds$MeanAbsDiff))
        
        }, error = function(){
        return(CrashPenalty)
        })
    }
    
    OFV <- nParms <- CmaxPenalty <-  CrashPenalty  <- 99999
    tryCatch({
        if(!file.exists("dmp.txt")){
            print(c(CrashPenalty,CrashPenalty,CrashPenalty)) 
            print(c(1))
        }else{  
            source("dmp.txt")
            OFV <- dmp.txt$logLik * (-2)
            CmaxPenalty <- GetCmaxPenalty(CrashPenalty)
            nParms <- dmp.txt$nParm 
            if(!file.exists("nlme7engine.log")){
                print(c(OFV, nParms, CmaxPenalty))
                print(c(1))
            }else{
                log <- readLines("nlme7engine.log")
                ScoresuccessLine <- grep("external_coords", log) 
                if (length(ScoresuccessLine) == 0){
                    print(c(OFV, nParms, CmaxPenalty))
                    print(c(1))
                }else{
                    parms <- data.frame(matrix(-99, nrow = nParms, ncol= 5))
                    ScoresuccessLine <- ScoresuccessLine[length(ScoresuccessLine)]
                    line <- str_trim(log[ScoresuccessLine[1]])
                    colnames(parms) <- strsplit(line, "\\s{2,}")[[1]]
                    start <- ScoresuccessLine[1] + 1
                    for(this_parm in 1:nParms){
                        line <- str_trim(log[start + this_parm])
                        parms[this_parm,] <- strsplit(line, "\\s{2,}")[[1]]  
                    }
                    parms <- parms %>% mutate(rel_std_err= as.numeric(rel_std_err))
                    if(any(parms$rel_std_err > 0.5)){
                        print(c(OFV, nParms, CmaxPenalty))  
                        print(c(1))
                    }else{
                        print(c(OFV,nParms, CmaxPenalty))
                        print(c(0))
                    }
                }
            }
        }
    },
    error = function(a){
        print(c(OFV, nParms, CmaxPenalty))
        print(c(1))
    }
    )   


.. _moga3-nlme_post_process:


NLME Post Run python code - post_process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using a post_process function is the most practical way to develop post run python code. The argument 
to the post_process function is the nlme run folder, e.g., ./temp/1/01. 

 
Most of the typically need information is in the err1.txt file. Unfortunately, there isn't an 
equivalent to the dmp.txt file for R in python. The err1.txt must be read and parsed to extract 
the model information. Below is example code to return objectives of OFV, number of estimated 
parameters, and number of failed RSEs and one constraint for exceptions (1).
  
 
.. code-block:: python

    import os
    import time 
    import re
    import pandas as pd
    import sys

    def get_external_coords(rundir):
        """read the err1.txt file in the run directory, find the parameter values and SEs and return the number of
        failed RSE (se/value> 0.5).

        Parameters
        ----------
        rundir : string
            run directory

        Returns
        -------
        int
            number of parameters with RSE > 0.5

        Examples
        --------
        get_external_coords('c:/pyDarwinRun/temp/1/01)
        4
        """
        try:
            ## se and parameter estimates in err1.txt
            ## use sandwich
            ## start read at " Standard errors of estimated parameters"
            logfile = os.path.join(rundir, 'err1.txt')
            with open(logfile) as file:
                lines = file.readlines()
            for index, line in enumerate(lines):
                if " Standard errors of estimated parameters" in line:
                    start = index
                    break
                ## find next " external_coords"
            lines = lines[index:]
            for index, line in enumerate(lines):
                if " external_coords" in line:
                    start = index
                    break
            lines = lines[(index + 2):]
            # get end at " std error time="

            for index, line in enumerate(lines):
                if re.search(" std error time=", line):
                    end = index
                    break
            lines = lines[:end]
            external_coor = []
            nFailedRSEs = 0
            nparms = 0
            # Iterate through each string in the array, test if se/value > 0.5
            for line in lines:
                split_words = line.split()
                external_coor.append(split_words)
                value = float(split_words[1])
                se = float(split_words[3])
                nparms += 1
                if se / value > 0.5:
                    nFailedRSEs += 1

            return nFailedRSEs, nparms

        except Exception as e:
            return 999999

    def get_ofv(rundir):
        """read the err1.txt file in the run directory, find the parameter values and SEs and return the number of
        failed RSE (se/value> 0.5).

        Parameters
        ----------
        rundir : string
            run directory

        Returns
        -------
        float OFV values
        int number of parameters

        Examples
        --------
        >>> get_ofv_nparms('c:/pyDarwinRun/temp/1/01)
        [2345.43, 8]
        """
        try:
            ## se and parameter estimates in err1.txt
            ## use sandwich
            ## start read at " Standard errors of estimated parameters"
            logfile = os.path.join(rundir, 'err1.txt')
            with open(logfile) as file:
                lines = file.readlines()
            for index, line in enumerate(lines):
                if " -2*Loglikelihood=" in line:
                    start = index
                    break
            ofv = float(lines[start + 1])
            return ofv
        except Exception as e:
            return 999999


    def post_process(rundir):
        """post run processing for MOGA3 in python. post_process2 takes the run directory as the argument, return
        ofv, number of parameters and number of parameters with RSE > 0.5. Excepteion return available values
        and constraint = 1

        Parameters
        ----------
        rundir : pyDarwin model run directory

        Returns
        -------
        objectives, constraint [float, float, float],[constraint]


        Examples
        --------
        post_process2(run)
        [10.2, 8, 1],[0]
        """
        ofv = 999999
        nparms = 999999
        nfailedRSEs = 999999
        try:
            ofv = get_ofv(rundir)
            nfailedRSEs, nparms  = get_external_coords(rundir)
            return [ofv, nparms, nfailedRSEs], [0]
        except Exception as e:
            return [ofv, nparms, nfailedRSEs], [1]

    if __name__ == '__main__':
        print(post_process(sys.argv[1]))

The last section of code:

.. code-block:: python

    if __name__ == '__main__':
        print(post_process(sys.argv[1]))


is to permit calling the python code from command line. 
The command line for calling from the project directory and return values, assuming the temp folder is called temp is:


.. code-block:: console

    python RSE3penalty.py .\temp\1\01
    ([8438.103, 7, 3], [0])


.. _moga3-nlme_post_process2:

NLME Post Run python code - post_process2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below is python code for OFV, nparms and nFailedRSE using post_process2. 
Note that is it not possible to run post_process2 code from command line as the argument is the pyDarwin run object.


.. code-block:: python

    import os
    import time
    import re
    import pandas as pd


    def get_external_coords(rundir):
        """read the err1.txt file in the run directory, find the parameter values and SEs and return the number of
        failed RSE (se/value> 0.5).

        Parameters
        ----------
        rundir : string
            run directory

        Returns
        -------
        int
            number of parameters with RSE > 0.5

        Examples
        --------
        >>> get_external_coords('c:/pyDarwinRun/temp/1/01)
        4
        """
        try:
            ## se and parameter estimates in err1.txt
            ## use sandwich
            ## start read at " Standard errors of estimated parameters"
            logfile = os.path.join(rundir, 'err1.txt')
            with open(logfile) as file:
                lines = file.readlines()
            for index, line in enumerate(lines):
                if " Standard errors of estimated parameters" in line:
                    start = index
                    break
                ## find next " external_coords"
            lines = lines[index:]
            for index, line in enumerate(lines):
                if " external_coords" in line:
                    start = index
                    break
            lines = lines[(index + 2):]
            # get end at " std error time="

            for index, line in enumerate(lines):
                if re.search(" std error time=", line):
                    end = index
                    break
            lines = lines[:end]
            external_coor = []
            nFailedRSEs = 0
            # Iterate through each string in the array, test if se/value > 0.5
            for line in lines:
                split_words = line.split()
                external_coor.append(split_words)
                value = float(split_words[1])
                se = float(split_words[3])
                if se / value > 0.5:
                    nFailedRSEs += 1

            return nFailedRSEs

        except Exception as e:
            return 999999


    def post_process2(run):
        """post run processing for MOGA3 in python. post_process2 takes the run as the argument, return
        ofv, number of parameters and number of parameters with RSE > 0.5. Excepteion return available values
        and constraint = 1

        Parameters
        ----------
        run : pyDarwin run

        Returns
        -------
        objectives, constraint [float, float, float],[constraint]


        Examples
        --------
        >>> post_process2(run)
        [10.2, 8, 1],[0]
        """
        ofv = nparms = nfailedRSEs = 999999
        try:
            result = getattr(run, 'result')
            model = getattr(run, 'model')
            ntheta = getattr(model, 'theta_num')
            nomega = getattr(model, 'omega_num')
            nsigma = getattr(model, 'sigma_num')
            nparms = ntheta + nomega + nsigma
            ofv = getattr(result, 'ofv')
            nfailedRSEs = get_external_coords(getattr(run, 'run_dir'))
            return [ofv, nparms, nfailedRSEs], [0]
        except Exception as e:
            return [ofv, nparms, nfailedRSEs], [1]




