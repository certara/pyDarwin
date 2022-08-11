
#####################################################
Example 4: PK Model, DMAG by GA with post-run R code
#####################################################
  
.. _startpk4:

Example 4 is the first realistic model search example, with real data (courtesy of `Dr. Rob Bies <https:/pharmacy.buffalo.edu/content/pharmacy/faculty-staff/faculty-profile.html?ubit=robertbi>`_ and the 
`CATIE study <https://www.nimh.nih.gov/funding/clinical-research/practical/catie#:~:text=The%20NIMH%2Dfunded%20Clinical%20Antipsychotic,medications%20used%20to%20treat%20schizophrenia>`_ ).
This search again uses :ref:`nested tokens<Nested Tokens>`, as it searches whether K32 is a function of Weight, and 1 vs 2 vs 3 compartments. 
Another important feature of example 4 is the use of post run R code. In this case, it was of interest to capture the Cmax value. There is no straightforward way to include a penalty for 
missing the Cmax 
in the NONMEM control stream. Therefore, the penalty for missing Cmax is added after the NONMEM run is complete. Any R code can be provided by the user and should return a vector of two values. The 
first is a real values penalty to be added to the fitness/reward. The 2nd is text that will be appended to NONMEM output file to describe the results of the R code execution.

The penalty for missing the Cmax is essentially a `Posterior Predictive Check (PPC) <https://pubmed.ncbi.nlm.nih.gov/11381569/>`_. The template file includes two tasks
that are used to generate a table of the PPC: an estimation, followed by a simulation.

::
        
    $PROB SIMULATION FOR CMAX

    $INPUT       ID TIME AMT {D1LAG[1]} DV MDV EVID WT AGE SEX BUN SCR OCC CRCL COV1 COV2
    $DATA      {data_dir}/dmag_with_period.csv IGNORE=@  REWIND
    $MSFI = MSF1
    $SIMULATION (1) ONLYSIM  
    $TABLE REP ID TIME IOBS EVID  NOAPPEND NOPRINT FILE = SIM.DAT ONEHEADER NOAPPEND

User provided R code is then saved to a file (``.R``):

::

    library(dplyr)
    orgdata <-  read.table("ORG.DAT",skip=1,header=TRUE)
    orgdata <- orgdata[orgdata$EVID==0&orgdata$TIME<=24,] # only first 24 hours
    simdata <-  read.table("SIM.DAT",skip=1,header=TRUE) # only first 24 hours
    simdata <- simdata[orgdata$EVID==0&orgdata$TIME<=24,] 
    observed_maxes <- orgdata %>% group_by(ID) %>% 
    summarise(max = max(DV))
    sim_maxes <- simdata %>% group_by(ID) %>% summarise(max = max(IOBS))
    # penalty of 4 points for each % difference
    obs_geomean = exp(mean(log(observed_maxes$max)))
    sim_geomean = exp(mean(log(sim_maxes$max)))
    penalty <- 4*abs((obs_geomean-sim_geomean)/obs_geomean)*100
    text <- paste0("Observed day 1 Cmax geomean = ", round(obs_geomean,1), " simulated day 1 Cmax geo mean = ", round(sim_geomean,1))
    c(penalty,text)

The R code executes from the run directory of that model, so, for example, if a model runs in ``c:\\pydarwin\\example4\\00\\04``, the ``ORG.DAT`` and ``SIM.DAT``
files will be written to that directory and the R code will be read from the same directory.

This R code returns a character vector of length 2. The first is a string that can be read as numeric (penalty) and the 2nd is a string that is appended to the 
NONMEM output file, as a comment to document the output of the R code. The content of the 2nd element of the vector is entirely up to the user, it has no 
impact on the pyDarwin process, it is just appended to the output file.

The first element of the returned value is added to the fitness/reward value and is then used in the selection of subsequent populations, just as any other penalty. The 
penalty value can be any real value - including negative, but typically would be positive. 

The post processing code options are given in the options file:

::
    
    "postprocess": {
        "use_r": true,
        "post_run_r_code": "{project_dir}/Cmaxppc.r",
        "rscript_path": "c:\\Program Files\\R\\R-4.1.3\\bin\\Rscript.exe",
        "r_timeout": 120,
        "use_python": false


Be sure to include whether to ``"use_r": true`` for post processing (true), the path to the R code, the path to Rscript.exe, and the timeout (``"r_timeout"``), after which the R session will be terminated if not 
complete and the :ref:`crash_value<Crash Value>` added as the penalty.


******************
The Template file
******************

::

    $PROBLEM    2 compartment fitting
    $INPUT       ID TIME AMT {D1LAG[1]} DV MDV EVID WT AGE SEX BUN SCR OCC CRCL COV1 COV2

    $DATA      {data_dir}/dmag_with_period.csv IGNORE=@
            
    $SUBROUTINE {ADVAN[1]} 
    $PK      
    CWTKGONE = WT/81  ;; WEIGHT CENTERED ON ONE
    CWTKGZERO = WT-81 ;; WEIGHT CENTERED ON ZERO
    CAGE = AGE/60     ;; AGE CENTERED ON ONE
    CCRCL = CRCL/85.6 ;; CRCL CENTERD ON ONE
    CCOV1 = COV1-15.4 ;; COVARIATE 1 CENTERED ON ZERO
    {IOVV[1]}  
    TVV2=THETA(1) {V2~WT[1]} {V2~SEX[1]} {V2~AGE[1]} {V2~COV2[1]}  *EXP(IOVV)
    V2=TVV2*EXP(ETA(2))   
    {IOVCL[1]}
    TVCL= {INITCL[1]} {CL~WT[1]} {CL~AGE[1]} {CL~CRCL[1]} {CL~COV1[1]} *EXP(IOVCL)
    CL=TVCL*EXP(ETA(1)) 
    
    K=CL/V2      
    {ADVAN[2]}  
    {D1LAG[2]}    
    TVKA=THETA(2) 
    KA=TVKA  {KAETA[1]}    
    S2 = V2 
    $ERROR     	
    REP = IREP      
    IPRED =F  
    IOBS = F {RESERR[1]}
    Y=IOBS
    $THETA      
    (0.001,100) 	; THETA(1) V  UNITS = L
    (0.001, 10) 	; THETA(2) KA UNITS = 1/HR    
    {INITCL[2]}	; THETA(INITCL) CL UNITS =  L/HR
    {ADVAN[3]}   
    {V2~WT[2]}   
    {V2~SEX[2]}   
    {V2~AGE[2]} 
    {V2~COV2[2]}
    {CL~WT[2]} 
    {CL~AGE[2]} 
    {CL~CRCL[2]}
    {CL~COV1[2]}
    {D1LAG[3]}
    $OMEGA    
    0.1  		; ETA(1) CLEARANCE 
    0.4  		; ETA(2) VOLUME  
    {KAETA[2]}  
    {D1LAG[4]} 
    {IOVCL[2]}
    {IOVV[2]}
    $SIGMA   
    {RESERR[2]}

    $EST METHOD=COND INTER MAX = 9999 MSFO=MSF1 PRINT = 10
    $COV UNCOND PRINT=E  PRECOND=1 PRECONDS=TOS  MATRIX = R

    $TABLE REP ID TIME DV EVID NOPRINT FILE = ORG.DAT ONEHEADER NOAPPEND

    $PROB SIMULATION FOR CMAX

    $INPUT       ID TIME AMT {D1LAG[1]} DV MDV EVID WT AGE SEX BUN SCR OCC CRCL COV1 COV2
    $DATA      {data_dir}/dmag_with_period.csv IGNORE=@  REWIND
    $MSFI = MSF1
    $SIMULATION (1) ONLYSIM  
    $TABLE REP ID TIME IOBS EVID  NOAPPEND NOPRINT FILE = SIM.DAT ONEHEADER NOAPPEND
  

Example 4 template file: :download:`text <../examples/user/Example4/template.txt>`

****************
The Tokens file
****************

Nothing new in the tokens file, we see again an example of nested tokens:

::

    {
	"ADVAN": [
		["ADVAN2 ;; advan2",
			";; PK 1 compartment ",
			";; THETA 1 compartment"
		],
		["ADVAN4 ;; advan4",
			"K23=THETA(ADVANA){K23~WT[1]}\n  K32=THETA(ADVANB){K23~WT[1]}",
			"(0.001,0.02)  \t ; THETA(ADVANA) K23 \n (0.001,0.3) \t ; THETA(ADVANB) K32 \n{K23~WT[2]} \t ; init for K23~WT "
		],
		["ADVAN12 ;; advan12",
			"K23=THETA(ADVANA){K23~WT[1]}\n  K32=THETA(ADVANB){K23~WT[1]}\n  K24=THETA(ADVANC)\n  K42=THETA(ADVAND)",
			"(0.001,0.1) \t; THETA(ADVANA) K23 \n (0.001,0.1)\t; THETA(ADVANB) K32 \n (0.001,0.1) \t; THETA(ADVANC) K24  \n (0.001,0.1) \t; THETA(ADVAND) K42  \n {K23~WT[2]} \t ;; init for K23~WT"
		]
	],
	"K23~WT": [
		["",
		 ""
		],
		["*CWTKGONE**THETA(K23~WT)",
			"(0,0.1) \t; THETA(K23~WT) K23~WT"
		]
	],
	"KAETA": [
		["",
		 ""
		],
		["*EXP(ETA(KAETA)) ",
			"$OMEGA ;; 2nd OMEGA block \n0.1\t\t; ETA(KAETA) ETA ON KA"
		]
	],
	"V2~WT": [
		["",
		 ""
		],
		["*CWTKGONE**THETA(V2~WT)",
			"(-4,0.8) \t; THETA(V2~WT) POWER volume ~WT "
		],
		["*EXP(CWTKGZERO*THETA(V2~WT))",
			"(-1,0.01) \t; THETA(V2~WT) EXPONENTIAL volume ~WT "
		]
	],
	"V2~AGE": [
		["",
		 ""
		],
		["*CAGE**THETA(V2~AGE)",
			"(-4,0.8) \t; THETA(V2~AGE) POWER volume ~AGE "
		] 
	],

	"V2~SEX": [
		["",
			""
		],
		["*EXP(SEX*THETA(V2~SEX))",
			"(-4,0.1) \t; THETA(V2~SEX) EXPONENTIAL volume~SEX "
		]
	],
	"V2~COV2": [
		["",
			""
		],
		["*EXP(COV2*THETA(V2~COV2))",
			"(-4,0.1) \t; THETA(V2~COV2) EXPONENTIAL volume ~COV2 "
		]
	],
	"CL~WT": [
		["",
			""
		],
		["*CWTKGONE**THETA(CL~WT)",
			"(-4,.7) \t; THETA(CL~WT) POWER clearance~WT "
		],
		["*EXP(CWTKGZERO*THETA(CL~WT))",
			"(-1,0.01) \t; THETA(CL~WT) EXPONENTIAL clearance~WT "
		]
	], 
	"CL~AGE": [
		["",
			""
		],
		["*CAGE**THETA(CL~AGE)",
			"(-4,.7) \t; THETA(CL~AGE) POWER clearance~AGE "
		] 
	],
	"CL~CRCL": [
		["",
		""
		],
		["*CCRCL**THETA(CL~CRCL)",
			"(-4,-0.2) \t; THETA(CL~CRCL) POWER clearance~CRCL "
		]
	], 
	"CL~COV1": [
		["",
		""
		],

		["*EXP(CCOV1*THETA(CL~COV1))",
			"(-4,0.1) \t; THETA(CL~COV1) EXPONENTIAL CL~COV1 "
		] 
	],
	"IOVCL": [
		["IF(OCC.EQ.1) IOVCL = ETA(IOVCLA) \n  IF(OCC.EQ.2) IOVCL = ETA(IOVCLB) \n  IF(OCC.EQ.3) IOVCL = ETA(IOVCLC)",
			"$OMEGA BLOCK(1) ; ETA(IOVCLA)\n 0.1 \n $OMEGA BLOCK SAME ; ETA(IOVCLB)\n $OMEGA BLOCK SAME ; ETA(IOVCLC)"
		],
		["IOVCL = 0",
		";; no iov ON CL"
		]
	],
	"IOVV": [
		["IF(OCC.EQ.1) IOVV = ETA(IOVVA) \n  IF(OCC.EQ.2) IOVV = ETA(IOVVB) \n  IF(OCC.EQ.3) IOVV = ETA(IOVVC)",
			"$OMEGA BLOCK(1) ; ETA(IOVVA)\n 0.1 \n$OMEGA BLOCK SAME ; ETA(IOVVB)\n$OMEGA BLOCK SAME ; ETA(IOVVC)"
		],
		["IOVV = 0",
		";; no iov ON V"
		]
	], 
	
	"INITCL": [
		["THETA(INITCL)",
		"(0.001,2)"
	   ], 
		["THETA(INITCL)",
		"(0.001,20)"
    	]
      ],
	 
	"ETAD1LAG": [
		["",
			"",
			""
		],
		["*EXP(ETA(ETALAG))",
			"",
			"$OMEGA ;; 3rd OMEGA block \n 0.1 \t\t;; ETA(ETALAG) ETA ON ALAG1"
			],
			["",
			"*EXP(ETA(ETALAG1))",
			"$OMEGA ;;  \n 0.1 \t\t;; ETA(ETALAG1) ETA ON D1"
		],
		["*EXP(ETA(ETALAG1))",
			"*EXP(ETA(ETALAG2))",
			"$OMEGA  ;; diagonal OMEGA \n 0.1 \t\t;; ETA(ETALAG1) ETA ON ALAG1\n 0.1 \t\t;; ETA(ETALAG2) ETA ON D1"
		],
		["*EXP(ETA(ETALAG1))",
			"*EXP(ETA(ETALAG2))",
			"$OMEGA BLOCK(2) ;; block OMEGA block \n 0.1 \t\t;; ETA(ETALAG1) ETA ON ALAG1\n 0.01 0.1 \t\t;; ETA(ETALAG2) ETA ON D1"
		]
	],
	"D1LAG": [
		["DROP",
			"ALAG1=THETA(ALAG){ETAD1LAG[1]}\n;; No D1",
			"(0.001,0.1) \t; THETA(ALAG) ALAG1   ",
			"{ETAD1LAG[3]}"
		],
		["RATE",
			" D1=THETA(D1) {ETAD1LAG[1]} ; infusion only",
			"(0.01,0.2) \t\t;; THETA(D1) D1  ",
			"{ETAD1LAG[3]}  "
		],
		["RATE",
			" ALAG1=THETA(ALAG){ETAD1LAG[1]}\n  D1=THETA(D1){ETAD1LAG[2]}",
			"(0.001,0.1,1) \t\t;; THETA(ALAG) ALAG1\n (0.001,0.1,1) ;;THETA(D1) D1",
			"{ETAD1LAG[3]} \t\t;; D1 and lag, block"
		]
	],
	"RESERR": [
		["*EXP(EPS(RESERRA))+EPS(RESERRB)",
			" 0.1 \t; EPS(RESERRA) proportional error\n  100 \t; EPS(RESERRB) additive error"
		],
		["+EPS(RESERRA)",
			" 200 \t; EPS(RESERRA) additive error"
		]
	]
    }

Note again, the use of THETA(paremeter identifier), e.g.,


::

   (0.001,0.02)  \t ; THETA(ADVANA) K23


for **ALL** initial estimate token text (THETA, OMEGA, and SIGMA).


Example 4 tokens file: :download:`json <../examples/user/Example4/tokens.json>`

*****************
The Options file
*****************

The algorithim selection in the options file is :ref:`GA<GA_desc>`.  

The user should provide an appropriate path for :ref:`"nmfe_path"<nmfe_path_options_desc>`. NONMEM version 7.4 and 7.5 are supported. 

Note that, to run in the environment used for this example, the directories are set to:

::

	
    "working_dir": "u:/pyDarwin/example4/working",
    "temp_dir": "u:/pyDarwin/example4/rundir",
    "output_dir": "u:/pyDarwin/example4/output",

It is recommended that the user set the directories to something appropriate for their environment. If directories are not set, 
the default is:

::

	{user_dir}\pydarwin\{project_name}

In either case, the folder names are given in the initial and final output to facilitate finding the files and debugging.

::

   {
    "author": "Certara",
    "algorithm": "GA",

    "GA": {
        "crossover_rate": 0.95,
        "elitist_num": 4,
        "mutation_rate": 0.95,
        "attribute_mutation_probability": 0.1,
        "mutate": "flipBit",
        "niche_penalty": 20,
        "selection": "tournament",
        "selection_size": 2,
        "sharing_alpha": 0.1,
        "crossover_operator": "cxOnePoint"
    },

    "random_seed": 11,
    "population_size": 80,
    "num_parallel": 4,
    "num_generations": 12,

    "downhill_period": 5,
    "num_niches": 2,
    "niche_radius": 2,
    "local_2_bit_search": true,
    "final_downhill_search": true,

    "crash_value": 99999999,

    "penalty": {
        "theta": 10,
        "omega": 10,
        "sigma": 10,
        "convergence": 100,
        "covariance": 100,
        "correlation": 100,
        "condition_number": 100,
        "non_influential_tokens": 0.00001
    },

    "remove_run_dir": false,

    "nmfe_path": "c:/nm744/util/nmfe74.bat",
    "model_run_timeout": 1200,

    "postprocess": {
        "use_r": true,
        "post_run_r_code": "{project_dir}/Cmaxppc.r",
        "rscript_path": "c:\\Program Files\\R\\R-4.1.3\\bin\\Rscript.exe",
        "r_timeout": 120,
        "use_python": false
    }
    }


Example 4 options file: :download:`json <../examples/user/Example4/options.json>`

******************************************
Execute Search
******************************************

Usage details for starting a search in ``pyDarwin`` can be found :ref:`here<Execution>`.

See :ref:`examples<examples_target>` for additional details about accessing example files.

The search space contains 1.66 million possible models, and searches for the following:

+----------------------------+--------------------------+----------------------------+
| Description                | Token Stem               | Values                     |
+============================+==========================+============================+
| Number of compartments     | ADVAN                    | 1|2|3                      |
+----------------------------+--------------------------+----------------------------+
| Is K23 related to weight?  | K23~WT                   | Yes|No                     |
+----------------------------+--------------------------+----------------------------+
| Is there ETA on Ka?        | KAETA                    | Yes|No                     |
+----------------------------+--------------------------+----------------------------+
| Is V2 related to weight?   | V2~WT                    | None|Power|exponential     |
+----------------------------+--------------------------+----------------------------+
| Is V2 related to Gender?   | V2~GENDER                | Yes|No                     |
+----------------------------+--------------------------+----------------------------+
| Is CL related to weight?   | CL~WT                    | None|Power|exponential     |
+----------------------------+--------------------------+----------------------------+
| Is CL related to Age?      | CL~AGE                   | Yes|No                     |
+----------------------------+--------------------------+----------------------------+
| | Is there ETA on D1 and/or| | ETAD1LAG               | | None or ETA on D1 or ETA |
| | and/or ALAG1 (nested     | |                        | | ETA on ALAGa or ETA on   | 
| | the D1LAG token group)   | |                        | | both or on both (BLOCK)  |
+----------------------------+--------------------------+----------------------------+

In practice, we will be searching for:

#. 1,2,3 compartments
#. Between occasion variability
#. Multiple covariates (but probably still not as many as a real search)
#. Different absorption models
#. Different residual error models
#. Block OMEGA structures
#. Different initial estimates (also likely not as many as a real search should include).

As the search space is large, we'll plan a large sample (population size of 80, with 12 generations). While :ref:`Gaussian Process<GP_desc>` may be more efficient 
in terms of number of models to convergence, once ~500 samples are defined, the `ask step <https://scikit-optimize.github.io/stable/modules/optimizer.html#>`_ becomes long, 
negating any efficiency of the algorithm. 

Below is a table of the ask and tell step times  (hh:mm:ss), by iteration for GP. The sample size ws 80, with 4 chains on a 4 core computer: 

+-----------+----------+----------+ 
| iteration | ask      | tell     | 
+===========+==========+==========+ 
| 1         |          | 0:00:15  |
+-----------+----------+----------+ 
| 2         | 0:01:18  | 0:00:35  |
+-----------+----------+----------+ 
| 3         | 0:03:12  | 0:01:03  |
+-----------+----------+----------+ 
| 4         | 0:05:56  | 0:01:55  |
+-----------+----------+----------+ 
| 5         | 0:09:33  | 0:03:55  |
+-----------+----------+----------+ 
| 6         | 0:16:22  | 0:04:47  |
+-----------+----------+----------+ 
| 7         | 0:25:25  | 0:08:30  |
+-----------+----------+----------+ 
| 8         | 0:33:43  | 0:09:30  |
+-----------+----------+----------+ 
| 9         | 0:50:11  | 0:10:26  |
+-----------+----------+----------+ 
| 10        | 0:55:32  | 0:13:52  |
+-----------+----------+----------+ 
| 11        | 1:09:00  | 0:17:14  |
+-----------+----------+----------+ 
| 12        | 1:22:18  | 0:21:14  |
+-----------+----------+----------+ 
| 13        | 1:40:25  |          |
+-----------+----------+----------+

In contrast, GA execution time for the next generation sample is short (a few seconds) and independent of the cumulative sample size. 

Initialization output should look like:

::
	
    [05:46:53] Options file found at ..\examples\user\Example4\options.json
	[05:46:53] Preparing project working folder...
	[05:46:53] Preparing project output folder...
	[05:46:53] Preparing project temp folder...
	[05:47:21] Model run priority is below_normal
	[05:47:21] Using darwin.MemoryModelCache
	[05:47:21] Project dir: c:\fda\pyDarwin\examples\user\Example4
	[05:47:21] Data dir: c:\fda\pyDarwin\examples\user\Example4
	[05:47:21] Project working dir: u:/pyDarwin/example4/working
	[05:47:21] Project temp dir: u:/pyDarwin/example4/rundir
	[05:47:21] Project output dir: u:/pyDarwin/example4/output
	[05:47:21] Writing intermediate output to u:/pyDarwin/example4/output\results.csv
	[05:47:21] Models will be saved in u:/pyDarwin/example4/working\models.json
	[05:47:21] Template file found at ..\examples\user\Example4\template.txt
	[05:47:21] Tokens file found at ..\examples\user\Example4\tokens.json
	[05:47:21] Search start time = Mon Aug  1 05:47:21 2022
	[05:47:21] -- Starting Generation 0 --
	[05:47:21] NMFE found: c:/nm744/util/nmfe74.bat
	[05:47:21] RScript found at c:\Program Files\R\R-4.1.3\bin\Rscript.exe
	[05:47:21] Post Run R code found at c:\fda\pyDarwin\examples\user\Example4\Cmaxppc.r
	[05:47:21] Not using Post Run Python code
	[05:47:21] Checking files in u:\pyDarwin\example4\rundir\00\01
	[05:47:21] Data set # 1 was found: c:\fda\pyDarwin\examples\user\Example4/dmag_with_period.csv
	[05:47:21] Data set # 2 was found: c:\fda\pyDarwin\examples\user\Example4/dmag_with_period.csv


After a few seconds, the NONMEM execution should begin, with output like:

::

	[05:59:52] Generation = 00, Model     2, Post process R failed,    fitness = 99999999,    message = No important warnings, error = K32, OR K42 IS TOO CLOSE TO AN EIGENVALUE
	[05:59:54] Generation = 00, Model     3, Post process R failed,    fitness = 99999999,    message = NON-FIXED OMEGA NON-FIXED PARAMETER, error = K32, OR K42 IS TOO CLOSE TO AN EIGENVALUE OCCURS DURING SEARCH FOR ETA AT INITIAL VALUE, ETA=0
	[05:59:56] Generation = 00, Model     1, Post process R failed,    fitness = 99999999,    message = No important warnings, error = K32, OR K42 IS TOO CLOSE TO AN EIGENVALUE
	[06:00:41] Generation = 00, Model     7, Post process R failed,    fitness = 99999999,    message = NON-FIXED OMEGA NON-FIXED PARAMETER


Note that (as in the case of human generated NONMEM code) the first 4 models crash, and the :ref:`crash value<Crash Value>` (99999999) is assigned 
to the fitness. There also may be a message: "NON-FIXED OMEGA NON-FIXED PARAMETER". This is a consequence of the nested tokens. With nested tokens, 
there commonly will be tokens that are not used, e.g., covariates relationships for K23 when a cone compartment model (ADVAN1) is selected. A small 
penalty should be added (the non-influential token penalty) in this case, simply to prefer this model over the same model without the non-influential 
token(s). 

The final output from the search should look like:

::

	[23:04:28] Done with final downhill step. best fitness = 8504.69692879228
	[23:04:28] Final output from best model is in u:/pyDarwin/example4/output\FinalResultFile.lst
	[23:04:28] Number of unique models to best model = 897
	[23:04:28] Time to best model = 474.6 minutes
	[23:04:28] Best overall fitness = 8504.696929, iteration 05S071, model 90
	[23:04:28] Elapsed time = 1015.4 minutes


