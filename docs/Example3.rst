

Example 3: PK Model, ODE model
=============================== 

Example 3 is quite different from the two previous examples. First, it is an ODE model, using ADVAN13. Second, different models in the search space required 
different data sets. Therefore, there is a token in the $DATA record. Next, urine PK is included in the model. Finally, 
linear vs Michaelis-Menten. The token groups/set are quite complex.


While the search space is small (324 models), we'll search by :ref:`Exhaustive search<EX_desc>`. Because of the complexity of the model and the 
ODE solution,  model run times are long. For faster search, the FO method is used. 

The Template file
~~~~~~~~~~~~~~~~~

::

   $PROBLEM ORAL BOLUS WITH PLASMA AND URINE OBSERVATIONS  
	; 
	; NUMBER OF COMPARTMENTS        : 1 OR 2 OR 3
	; 
	; ABSORPTION                    : ZERO-ORDER OR FIRST-ORDER OR ZERO-ORDER FOLLOWED BY FIRST-ORDER
	; 
	; ELIMINATION                   : FIRST-ORDER OR MICHAELIS-MENTEN
	; 
	; BIOAVAILABLITY                : EITHER 1 OR BETWEEN 0 AND 1 (ASSOCIATED IIV IS ALSO SEARCHED)
	;
	; RESIDUAL ERROR FOR PLASMA OBS : PROPORTIONAL OR COMBINED
	; RESIDUAL ERROR FOR URINE OBS  : ADDITIVE OR PROPORTIONAL OR COMBINED 


   ; ====================================================================================================
   ; DATA
   ; ====================================================================================================          
      
   $INPUT       ID TIME AMT CMT {ODE[1]} DV DVID EVID MDV 
   $DATA      {data_dir}/{ODE[2]} IGNORE=@


   ; ====================================================================================================
   ; SUBROUTINE
   ; ====================================================================================================          
   $SUBROUTINE ADVAN13 TOL = 6

   $MODEL
   NCOMP = {ODE[3]}
   COMP = (URINE)


   ; ===================================================================================================
   ; STRUCTURAL PARAMETERS 
   ; ===================================================================================================
   $PK      
   
   {ODE[4]}
   
   {BIOAVAIL[1]}

   ; ====================================================================================================
   ; INITIAL VALUES FOR FIXED EFFECTS
   ; ====================================================================================================
   $THETA  
   
   {ODE[5]} 
   {BIOAVAIL[2]}  

   
   ; ====================================================================================================
   ; INITIAL VALUES FOR OMEGA
   ; ====================================================================================================
   $OMEGA 

   {ODE[6]}
   {BIOAVAIL[3]}


   ; ====================================================================================================
   ; ODE MODEL 
   ; ====================================================================================================
   $DES

   {ODE[7]}
   

   ; ===================================================================================================
   ; RESIDUAL ERROR MODEL
   ; ===================================================================================================
   $ERROR  
         
   ; IPRED 
   {ODE[8]}
   
   ; RESIDUAL ERROR MODEL 
   IF (DVID == 1) Y = IPREDC {RESERRC[1]}
   IF (DVID == 2) Y = IPREDU {RESERRU[1]}


   $SIGMA  

   {RESERRC[2]}
   {RESERRU[2]}


   ; ==================================================================================================
   ; ESTIMATION METHOD AND SE 
   ; ================================================================================================== 

   $EST METHOD = 0 NOABORT MAX = 9999 SIGL = 6 NSIG = 2 PRINT = 5

   $COV UNCOND PRINT = E

Example 3 template file :download:`text <../examples/user/Example3/template.txt>`

The Tokens file
~~~~~~~~~~~~~~~~

The tokens file is quite complex:


::

   {
      "ODE": [
         ["RATE",
            "OralBolus_PlasmaUrine_ResetCpt2.csv",
            " 2 \n COMP = (CENTRAL)", 
            "R1 = THETA(ODER1F) * EXP(ETA(ODER1R)) \n \n VC = THETA(ODEVCF) * EXP(ETA(ODEVCR)) \n \n {ELIM[1]}",
            "(0, 50) \t ; THETA(ODER1F) TVR1 \n (0, 5) \t ; THETA(ODEVCF) TVVC \n {ELIM[2]}",
            "1 \t ; ETA(ODER1R) ETA ON R1 \n 1 \t ; ETA(ODEVCR) ETA ON VC \n {ELIM[3]}", 
            "C = A(1)/VC \n \n DADT(1) = - {ELIM[4]} \n DADT(2) = {ELIM[4]}",
            "IPREDC = A(1)/VC \n IPREDU = A(2)"
         ],
         ["DROP",
            "OralBolus_PlasmaUrine_ResetCpt3.csv",
            " 3 \n COMP = (DEPOT) \n COMP = (CENTRAL)", 
            "KA = THETA(ODEKAF) * EXP(ETA(ODEKAR)) \n \n VC = THETA(ODEVCF) * EXP(ETA(ODEVCR)) \n \n {ELIM[1]}",
            "(0, 1) \t ; THETA(ODEKAF) TVKA \n (0, 5) \t ; THETA(ODEVCF) TVVC \n {ELIM[2]}",
            "1 \t ; ETA(ODEKAR) ETA ON KA \n 1 \t ; ETA(ODEVCR) ETA ON VC \n {ELIM[3]}", 
            "C = A(2)/VC \n \n DADT(1) = - KA * A(1) \n DADT(2) = KA * A(1) - {ELIM[4]} \n DADT(3) = {ELIM[4]}",
            "IPREDC = A(2)/VC \n IPREDU = A(3)"
         ],
         ["RATE",
            "OralBolus_PlasmaUrine_ResetCpt3.csv",
            " 3 \n COMP = (DEPOT) \n COMP = (CENTRAL)", 
            "R1 = THETA(ODER1F) * EXP(ETA(ODER1R)) \n \n KA = THETA(ODEKAF) * EXP(ETA(ODEKAR)) \n \n VC = THETA(ODEVCF) * EXP(ETA(ODEVCR)) \n \n {ELIM[1]}",
            "(0, 5000) \t ; THETA(ODER1F) TVR1 \n (0, 1) \t ; THETA(ODEKAF) TVKA \n (0, 5) \t ; THETA(ODEVCF) TVVC \n {ELIM[2]}",
            "1 \t ; ETA(ODER1R) ETA ON R1 \n 1 \t ; ETA(ODEKAR) ETA ON KA \n 1 \t ; ETA(ODEVCR) ETA ON VC \n {ELIM[3]}", 
            "C = A(2)/VC \n \n DADT(1) = - KA * A(1) \n DADT(2) = KA * A(1) - {ELIM[4]} \n DADT(3) = {ELIM[4]}",
            "IPREDC = A(2)/VC \n IPREDU = A(3)"
         ],
         ["RATE",
            "OralBolus_PlasmaUrine_ResetCpt3.csv",
            " 3 \n COMP = (CENTRAL) \n COMP = (PERIPH)", 
            "R1 = THETA(ODER1F) * EXP(ETA(ODER1R)) \n \n VC = THETA(ODEVCF) * EXP(ETA(ODEVCR)) \n \n VP = THETA(ODEVPF) * EXP(ETA(ODEVPR)) \n \n CLQ = THETA(ODECLQF) * EXP(ETA(ODECLQR)) \n \n {ELIM[1]}",
            "(0, 50) \t ; THETA(ODER1F) TVR1 \n (0, 5) \t ; THETA(ODEVCF) TVVC \n (0, 5) \t ; THETA(ODEVPF) TVVP \n (0, 1) \t ; THETA(ODECLQF) TVCLQ \n {ELIM[2]}",
            "1 \t ; ETA(ODER1R) ETA ON R1 \n 1 \t ; ETA(ODEVCR) ETA ON VC \n 1 \t ; ETA(ODEVPR) ETA ON VP \n 1 \t ; ETA(ODECLQR) ETA ON CLQ \n {ELIM[3]}", 
            "C = A(1)/VC \n \n DADT(1) = - {ELIM[4]} - CLQ * (A(1)/VC - A(2)/VP) \n DADT(2) = CLQ * (A(1)/VC - A(2)/VP) \n DADT(3) = {ELIM[4]}",
            "IPREDC = A(1)/VC \n IPREDU = A(3)"
         ],
         ["DROP",
            "OralBolus_PlasmaUrine_ResetCpt4.csv",
            " 4 \n COMP = (DEPOT) \n COMP = (CENTRAL) \n COMP = (PERIPH)", 
            "KA = THETA(ODEKAF) * EXP(ETA(ODEKAR)) \n \n VC = THETA(ODEVCF) * EXP(ETA(ODEVCR)) \n \n VP = THETA(ODEVPF) * EXP(ETA(ODEVPR)) \n \n CLQ = THETA(ODECLQF) * EXP(ETA(ODECLQR)) \n \n {ELIM[1]}",
            "(0, 1) \t ; THETA(ODEKAF) TVKA \n (0, 5) \t ; THETA(ODEVCF) TVVC \n (0, 5) \t ; THETA(ODEVPF) TVVP \n (0, 1) \t ; THETA(ODECLQF) TVCLQ \n {ELIM[2]}",
            "1 \t ; ETA(ODEKAR) ETA ON KA \n 1 \t ; ETA(ODEVCR) ETA ON VC \n 1 \t ; ETA(ODEVPR) ETA ON VP \n 1 \t ; ETA(ODECLQR) ETA ON CLQ \n {ELIM[3]}", 
            "C = A(2)/VC \n \n DADT(1) = - KA * A(1) \n DADT(2) = KA * A(1) - {ELIM[4]} - CLQ * (A(2)/VC - A(3)/VP) \n DADT(3) = CLQ * (A(2)/VC - A(3)/VP) \n DADT(4) = {ELIM[4]}",
            "IPREDC = A(2)/VC \n IPREDU = A(4)"
         ],
         ["RATE",
            "OralBolus_PlasmaUrine_ResetCpt4.csv",
            " 4 \n COMP = (DEPOT) \n COMP = (CENTRAL) \n COMP = (PERIPH)", 
            "R1 = THETA(ODER1F) * EXP(ETA(ODER1R)) \n \n KA = THETA(ODEKAF) * EXP(ETA(ODEKAR)) \n \n VC = THETA(ODEVCF) * EXP(ETA(ODEVCR)) \n \n VP = THETA(ODEVPF) * EXP(ETA(ODEVPR)) \n \n CLQ = THETA(ODECLQF) * EXP(ETA(ODECLQR)) \n \n {ELIM[1]}",
            "(0, 5000) \t ; THETA(ODER1F) TVR1 \n (0, 1) \t ; THETA(ODEKAF) TVKA \n (0, 5) \t ; THETA(ODEVCF) TVVC \n (0, 5) \t ; THETA(ODEVPF) TVVP \n (0, 1) \t ; THETA(ODECLQF) TVCLQ \n {ELIM[2]}",
            "1 \t ; ETA(ODER1R) ETA ON R1 \n 1 \t ; ETA(ODEKAR) ETA ON KA \n 1 \t ; ETA(ODEVCR) ETA ON VC \n 1 \t ; ETA(ODEVPR) ETA ON VP \n 1 \t ; ETA(ODECLQR) ETA ON CLQ \n {ELIM[3]}", 
            "C = A(2)/VC \n \n DADT(1) = - KA * A(1) \n DADT(2) = KA * A(1) - {ELIM[4]} - CLQ * (A(2)/VC - A(3)/VP) \n DADT(3) = CLQ * (A(2)/VC - A(3)/VP) \n DADT(4) = {ELIM[4]}",
            "IPREDC = A(2)/VC \n IPREDU = A(4)"
         ],
         ["RATE",
            "OralBolus_PlasmaUrine_ResetCpt4.csv",
            " 4 \n COMP = (CENTRAL) \n COMP = (PERIPH) \n COMP = (PERIPH2)", 
            "R1 = THETA(ODER1F) * EXP(ETA(ODER1R)) \n \n VC = THETA(ODEVCF) * EXP(ETA(ODEVCR)) \n \n VP = THETA(ODEVPF) * EXP(ETA(ODEVPR)) \n \n CLQ = THETA(ODECLQF) * EXP(ETA(ODECLQR)) \n \n VP2 = THETA(ODEVP2F) * EXP(ETA(ODEVP2R)) \n \n CLQ2 = THETA(ODECLQ2F) * EXP(ETA(ODECLQ2R)) \n \n {ELIM[1]}",
            "(0, 50) \t ; THETA(ODER1F) TVR1 \n (0, 5) \t ; THETA(ODEVCF) TVVC  \n (0, 5) \t ; THETA(ODEVPF) TVVP \n (0, 1) \t ; THETA(ODECLQF) TVCLQ \n (0, 0.1) \t ; THETA(ODEVP2F) TVVP2  \n (0, 1) \t ; THETA(ODECLQ2F) TVCLQ2 \n {ELIM[2]}",
            "1 \t ; ETA(ODER1R) ETA ON R1 \n 1 \t ; ETA(ODEVCR) ETA ON VC  \n 1 \t ; ETA(ODEVPR) ETA ON VP \n 1 \t ; ETA(ODECLQR) ETA ON CLQ  \n 1 \t ; ETA(ODEVP2R) ETA ON VP2 \n 1 \t ; ETA(ODECLQ2R) ETA ON CLQ2 \n {ELIM[3]}", 
            "C = A(1)/VC \n \n DADT(1) = - {ELIM[4]} - CLQ * (A(1)/VC - A(2)/VP) - CLQ2 * (A(1)/VC - A(3)/VP2) \n DADT(2) = CLQ * (A(1)/VC - A(2)/VP) \n DADT(3) = CLQ2 * (A(1)/VC - A(3)/VP2) \n DADT(4) = {ELIM[4]}",
            "IPREDC = A(1)/VC \n IPREDU = A(4)"
         ],
         ["DROP",
            "OralBolus_PlasmaUrine_ResetCpt5.csv",
            " 5 \n COMP = (DEPOT) \n COMP = (CENTRAL) \n COMP = (PERIPH) \n COMP = (PERIPH2)", 
            "KA = THETA(ODEKAF) * EXP(ETA(ODEKAR)) \n \n VC = THETA(ODEVCF) * EXP(ETA(ODEVCR)) \n \n VP = THETA(ODEVPF) * EXP(ETA(ODEVPR)) \n \n CLQ = THETA(ODECLQF) * EXP(ETA(ODECLQR))\n \n VP2 = THETA(ODEVP2F) * EXP(ETA(ODEVP2R)) \n \n CLQ2 = THETA(ODECLQ2F) * EXP(ETA(ODECLQ2R)) \n \n {ELIM[1]}",
            "(0, 1) \t ; THETA(ODEKAF) TVKA \n (0, 5) \t ; THETA(ODEVCF) TVVC  \n (0, 5) \t ; THETA(ODEVPF) TVVP \n (0, 1) \t ; THETA(ODECLQF) TVCLQ \n (0, 0.1) \t ; THETA(ODEVP2F) TVVP2 \n (0, 1) \t ; THETA(ODECLQ2F) TVCLQ2 \n {ELIM[2]}",
            "1 \t ; ETA(ODEKAR) ETA ON KA \n 1 \t ; ETA(ODEVCR) ETA ON VC  \n 1 \t ; ETA(ODEVPR) ETA ON VP \n 1 \t ; ETA(ODECLQR) ETA ON CLQ \n 1 \t ; ETA(ODEVP2R) ETA ON VP2 \n 1 \t ; ETA(ODECLQ2R) ETA ON CLQ2 \n {ELIM[3]}", 
            "C = A(2)/VC \n \n DADT(1) = - KA * A(1) \n DADT(2) = KA * A(1) - {ELIM[4]} - CLQ * (A(2)/VC - A(3)/VP) - CLQ2 * (A(2)/VC - A(4)/VP2) \n DADT(3) = CLQ * (A(2)/VC - A(3)/VP) \n DADT(4) = CLQ2 * (A(2)/VC - A(4)/VP2) \n DADT(5) = {ELIM[4]}",
            "IPREDC = A(2)/VC \n IPREDU = A(5)"
         ],
         ["RATE",
            "OralBolus_PlasmaUrine_ResetCpt5.csv",
            " 5 \n COMP = (DEPOT) \n COMP = (CENTRAL) \n COMP = (PERIPH) \n COMP = (PERIPH2)", 
            "R1 = THETA(ODER1F) * EXP(ETA(ODER1R)) \n \n KA = THETA(ODEKAF) * EXP(ETA(ODEKAR)) \n \n VC = THETA(ODEVCF) * EXP(ETA(ODEVCR)) \n \n VP = THETA(ODEVPF) * EXP(ETA(ODEVPR)) \n \n CLQ = THETA(ODECLQF) * EXP(ETA(ODECLQR)) \n \n VP2 = THETA(ODEVP2F) * EXP(ETA(ODEVP2R)) \n \n CLQ2 = THETA(ODECLQ2F) * EXP(ETA(ODECLQ2R)) \n \n {ELIM[1]}",
            "(0, 5000) \t ; THETA(ODER1F) TVR1 \n (0, 1) \t ; THETA(ODEKAF) TVKA \n (0, 5) \t ; THETA(ODEVCF) TVVC \n (0, 5) \t ; THETA(ODEVPF) TVVP \n (0, 1) \t ; THETA(ODECLQF) TVCLQ \n (0, 0.1) \t ; THETA(ODEVP2F) TVVP2 \n (0, 1) \t ; THETA(ODECLQ2F) TVCLQ2 \n {ELIM[2]}",
            "1 \t ; ETA(ODER1R) ETA ON R1 \n 1 \t ; ETA(ODEKAR) ETA ON KA \n 1 \t ; ETA(ODEVCR) ETA ON VC \n 1 \t ; ETA(ODEVPR) ETA ON VP \n 1 \t ; ETA(ODECLQR) ETA ON CLQ \n 1 \t ; ETA(ODEVP2R) ETA ON VP2 \n 1 \t ; ETA(ODECLQ2R) ETA ON CLQ2 \n {ELIM[3]}", 
            "C = A(2)/VC \n \n DADT(1) = - KA * A(1) \n DADT(2) = KA * A(1) -{ELIM[4]} - CLQ * (A(2)/VC - A(3)/VP) - CLQ2 * (A(2)/VC - A(4)/VP2) \n DADT(3) = CLQ * (A(2)/VC - A(3)/VP) \n DADT(4) = CLQ2 * (A(2)/VC - A(4)/VP2) \n DADT(5) = {ELIM[4]}",
            "IPREDC = A(2)/VC \n IPREDU = A(5)"
         ]
      ], 
      
      "ELIM":[
         ["CLC = THETA(ODECLCF) * EXP(ETA(ODECLCR))", 
            "(0, 2) \t ; THETA(ODECLCF) TVCLC", 
            "1 \t ; ETA(ODECLCR) ETA ON CLC", 
            "CLC * C"
         ],
         ["VM = THETA(ODEVMF) * EXP(ETA(ODEVMR)) \n \n KM = THETA(ODEKMF) * EXP(ETA(ODEKMR))", 
            "(0, 20) \t ; THETA(ODEVMF) TVVM \n (0, 10) \t ; THETA(ODEKMF) TVKM",
            "1 \t ; ETA(ODEVMR) ETA ON VM \n 1 \t ; ETA(ODEKMR) ETA ON KM",
            "VM * C/(KM + C)"
         ]
      ],
      

      "BIOAVAIL": [
         ["", 
            "",
            ""
         ], 
         ["F1 = THETA(BIOAVAIL)",
            "(0, 0.9, 1) \t ; THETA(BIOAVAIL) TVF",
            ""
         ], 
         ["TEMP = EXP(THETA(BIOAVAILF) + ETA(BIOAVAILR)) \n F1 = TEMP/(1 + TEMP)",
            "3 \t ; THETA(BIOAVAILF) TVLOGITF",
            "1 \t ; ETA(BIOAVAILR) ETA ON LOGITF"
         ]
      ], 
      
      "RESERRC":[
         ["* (1 + EPS(RESERRCP))",
            "0.01 \t ; EPS(RESERRCP) VARIANCE OF PROPORTIONAL ERROR FOR PLASMA OBSERVATION"
         ],
         ["* (1 + EPS(RESERRCP)) + EPS(RESERRCA)",
            "0.01 \t ; EPS(RESERRCP)) VARIANCE OF PROPORTIONAL ERROR FOR PLASMA OBSERVATIONS \n 0.1 \t ; EPS(RESERRCA) VARIANCE OF ADDITIVE ERROR FOR PLASMA OBSERVATIONS"
         ]
      ], 
      
      "RESERRU":[
         ["+ EPS(RESERRUA)",
            "0.1 \t ; EPS(RESERRUA) VARIANCE OF ADDITIVE ERROR FOR URINE OBSERVATIONS"
         ],
         ["* (1 + EPS(RESERRUP))",
            "0.01 \t ; EPS(RESERRUP) VARIANCE OF PROPORTIONAL ERROR FOR URINE OBSERVATIONS"
         ],
         ["* (1 + EPS(RESERRUP)) + EPS(RESERRUA)",
            "0.01 \t ; EPS(RESERRUP)) VARIANCE OF PROPORTIONAL ERROR FOR URINE OBSERVATIONS \n 0.1 \t ; EPS(RESERRUA) VARIANCE OF ADDITIVE ERROR FOR URINE OBSERVATIONS"
         ]
      ]
      
      }



**NOTE AGAIN!!**
The use of THETA(paremeter identifier), e.g.


::

   (-4,.7,4) \t; THETA(CL~WT)


for **ALL** initial estimate token text (THETA, OMEGA and SIGMA).


Example 3 tokens file :download:`json <../examples/user/Example3/tokens.json>`

The Options file
~~~~~~~~~~~~~~~~

The options file is fairly traditional, :ref:`Exhaustive search<EX_desc>`.  Note that the NONMEM timeout is long (9600 seconds), as the run time for the ODE solution is long. 

The user should provide an appropriate path for :ref:`"nmfe_path"<nmfe_path_options_desc>`. NONMEM version 7.4 and 7.5 are supported. 

Note that to run in the enviroment used for this example, the directories are set to:

::

	
    "working_dir": "u:/pyDarwin/example3/working",
    "temp_dir": "u:/pyDarwin/example3/rundir",
    "output_dir": "u:/pyDarwin/example3/output",

It is recommended that the user set the directories to something appropriate for their enviroment. If directories are not set 
the default is:

::

	{user_dir}\pydarwin\{project_name}

In either case, the folder names are given in the initial and final output to facilitate finding the files and debuggins.

::

   {
    "author": "Certara",

    "algorithm": "EX",
    "exhaustive_batch_size": 100,

    "working_dir": "u:/pyDarwin/example3/working",
    "temp_dir": "u:/pyDarwin/example3/rundir",
    "output_dir": "u:/pyDarwin/example3/output",
    "num_parallel": 4,

    "crash_value": 99999999999,

    "penalty": {
        "theta": 2,
        "omega": 2,
        "sigma": 2,
        "convergence": 100,
        "covariance": 100,
        "correlation": 100,
        "condition_number": 100,
        "non_influential_tokens": 0.00001
    },

    "remove_run_dir": false,

    "nmfe_path": "c:/nm744/util/nmfe74.bat",
    "model_run_timeout": 9600
   }

Example 3 options file :download:`json <../examples/user/Example3/options.json>`

Starting the search and console output:
--------------------------------------------

:ref:`Starting the search is covered here<Execution>`


Initialization output should look similar to this:

::

   [12:30:54] Options file found at ..\examples\user\Example3\options.json
   [12:30:54] Preparing project working folder...
   [12:30:54] Preparing project output folder...
   [12:30:54] Preparing project temp folder...
   [12:30:54] Model run priority is below_normal
   [12:30:54] Using darwin.MemoryModelCache
   [12:30:54] Project dir: c:\fda\pyDarwin\examples\user\Example3
   [12:30:54] Data dir: c:\fda\pyDarwin\examples\user\Example3
   [12:30:54] Project working dir: u:/pyDarwin/example3/working
   [12:30:54] Project temp dir: u:/pyDarwin/example3/rundir
   [12:30:54] Project output dir: u:/pyDarwin/example3/output
   [12:30:54] Writing intermediate output to u:/pyDarwin/example3/output\results.csv
   [12:30:54] Models will be saved in u:/pyDarwin/example3/working\models.json
   [12:30:54] Template file found at ..\examples\user\Example3\template.txt
   [12:30:54] Tokens file found at ..\examples\user\Example3\tokens.json
   [12:30:54] Search start time = Sun Jul 31 12:30:54 2022
   [12:30:54] Total of 324 to be run in exhaustive search
   [12:30:54] NMFE found: c:/nm744/util/nmfe74.bat
   [12:30:54] Not using Post Run R code
   [12:30:54] Not using Post Run Python code
   [12:30:54] Checking files in u:\pyDarwin\example3\rundir\0\001
   [12:30:54] Data set # 1 was found: c:\fda\pyDarwin\examples\user\Example3/OralBolus_PlasmaUrine_ResetCpt2.csv
  

