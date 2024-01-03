:orphan:

.. _startpk1:

##################################################
Example 1: PK Model, Trivial Exhaustive Search
##################################################

This first model is quite simple, the search space consists of 6 dimensions, each with 2 options. Thus, the total number of candidate models is 
2^6 = 64 models. As the search space is very small, we'll perform an exhaustive search. See :ref:`details <The Algorithms>` on algorithm selection.

As is the usual practice in pop-PK model selection, the first step will be exploratory data analysis. This serves at least two purposes: to validate the dataset 
and to generate initial hypotheses. For the purpose of this tutorial, we will skip this step and assume that we have a "correct" dataset and a list of 
hypotheses to be tested. The dataset for this example is ``dataExample1.csv``. See :ref:`"Examples" <examples_target>` for more details.

The next step for machine learning model selection is to get a simple model running. The control file for this simple model is given below:

::

    $PROBLEM    2 compartment fitting
    $INPUT       ID TIME AMT DV WTKG GENDER AGE DROP
    $DATA      dataExample1.csv IGNORE=@
            
    $SUBROUTINE ADVAN2
    $ABBR DERIV2=NO
    $PK      
    CWTKG = WTKG/70  ;; CENTERED ON ONE 
    CAGE = AGE/40 
    TVV2=THETA(2) 
    V2=TVV2*EXP(ETA(2)) 
    TVCL= THETA(1)  
    CL=TVCL*EXP(ETA(1)) 
    K=CL/V2  
    TVKA=THETA(3) 
    KA=TVKA   
    S2 	= V2/1000  
    $ERROR     
    REP = IREP      
    IPRED =F  
    IOBS = F*EXP(EPS(1))+EPS(2)
    Y=IOBS
    $THETA  ;; must be one THETA per line.
    (0.001,100)	; THETA(1) CL UNITS =  L/HR
    (0.001,500) 	; THETA(2) V  UNITS = L
    (0.001,2) 	; THETA(3) KA UNITS = 1/HR  
    
    
    $OMEGA   	; must be one ETA/line
    0.2  		; ETA(1) CLEARANCE 
    0.2  		; ETA(2) VOLUME 
    
    $SIGMA   
    (0.1)
    (1)

    $EST METHOD=COND INTER MAX = 9999 MSFO=MSF1 
    $COV UNCOND PRINT=E
    


This text will serve as the starting point for developing the template file. 
Note that for the template file, the data file can either be specified as a full
path or starting with :ref:`{data_dir}<Data Directory>`).


.. warning::
    In all cases, the resulting path to the data file must be less than or equal to 80 characters, including
    after the path is expanded with {data_dir}.

.. _template file: 

********************
The Template file
********************

The initial simple model can then be edited by adding tokens. This first example will include covariates, residual error, and one structural feature. 
Each token group is identified by a :ref:`token stem <token stem>`, e.g., "V2~WT" for the dimension of the 
relationship between weight and a volume of distribution. Each token group includes 
2 or more :ref:`token sets <token set>`, one for each option in the dimension.

These dimensions and the associated :ref:`token stem<token stem>` are:

1. Effect of Weight on Volume ("V2~WT") - None or a power model.
2. Effect of Sex (Gender) on Volume ("V2~GENDER") - None or a power model
3. Effect of Weight on Clearance ("CL~WT") - None or a power model
4. Presence of between subject variability (BSV) on Ka ("KAETA") - None or exponential model
5. Presence of an absorption lag time - ALAG1 ("ALAG") - Present or not
6. Residual error model ("RESERR") - additive or combined additive and proportional

Covariate effects
====================

For the effect of Weight on Volume, we've chosen the :ref:`token stem<token stem>` of "V2~WT". Two tokens will be required for this :ref:`token set<token set>`. The first will
add the relationship to the definition of TVV2 in the $PK block and the 2nd will provide an initial estimate in the $THETA block for the estimated 
THETA. Note that the index for THETA for this feature cannot be defined until the model is constructed. Only then can the number and sequence of the added THETAs be 
determined. In the token set, THETAs will be indexed with text, e.g., THETA(V2~WT). As there will be two tokens in the token set, the first will have an index of 1
and the 2nd an index of 2:

::

     {V2~WT[1]}
     and
     {V2~WT[2]} 
    

Note the curly braces, these are required for tokens in the template file. The record in the $PK will have the token appended to it, resulting in this text:

::

    TVV2=THETA(2){V2~WT[1]}
    
Two options for the text to be substituted for {V2~WT[1]} will 
be defined:

1. ""
2. "\*CWTKG**THETA(V2~WT)"

The first will have no text in that record, resulting in:

::

    TVV2=THETA(2)


and the 2nd text being substituted will result in:

::

    TVV2=THETA(2)*CWTKG**THETA(V2~WT)


The 2nd token for the initial estimate for THETA(V2~WT) will be similar. The token text options will be:

1. ""
2. "  (-4,0.8,4) \\t; THETA(V2~WT) POWER volume ~WT "

::

    $THETA  ;; must be one THETA per line.
    (0.001,100) ; THETA(1) CL UNITS =  L/HR
    (0.001,500) ; THETA(2) V  UNITS = L
    (0.001,2)   ; THETA(3) KA UNITS = 1/HR

    {V2~WT[2]}    

Note the use of the escape syntax, "\\t" for a tab. Newlines will be coded similarly as "\\n" (actual CRLFs are not permitted in JSON, and \\n must be used). 
NONMEM comments (text after ";") are permitted. However, the user must be aware of the impact that comments in token text may have on any code that follows. This $THETA block has 3 fixed THETA initial estimates - THETA(1), 
THETA(2), and THETA(3). These will appear in all control files in the search. These fixed initial estimates are then followed by searched initial estimates. Searched 
initial estimates may or may not appear, depending on the model specification (:ref:`phenotype<phenotype>`). Searched initial estimates must be placed after all 
fixed initial estimates. Each initial estimate must be on a separate line and must be surrounded by parentheses. The standard combinations of (lower, initial, upper) 
are all supported. 

Token sets for each feature to be searched will be defined as these :ref:`token key-text pairs<token key-text pair>` (analogous to key-value pairs 
in JSON, but only text values are permitted).

Each of these dimensions has two options. Therefore, the total number of candidate models 
in the search space is the number of permutations: 2^6 = 64. 

In the :download:`template text <../examples/NONMEM/user/Example1/template.txt>`, note the
special text in curly brace ({}). These are :ref:`tokens<token>`. Tokens come in sets, as typically 
multiple text substitutions must be made to result in a syntactically correct NMTRAN control file. For 
example, if ALAG1 is to be used in the $PK block, a corresponding initial estimate for 
this parameter must be provided in the $THETA block. These tokens (collectively called a token set) 
are then replaced by the corresponding text value in the :ref:`token key-text pair <token key-text pair>`. 


**Note !!!**
In order to parse the text in the initial estimates blocks (THETA, OMEGA, and SIGMA), the user MUST include token stem text as a comment (i.e., after ";"). There is 
no other way to identify which initial estimates are to be associated with which THETA. 
For example, if a token stem has two THETAs and the text in the $PK block is:

Effect = THETA(EMAX) * CONC/(THETA(EC50) + CONC)

The resulting $THETA block for this initial feature will be:

::

 "  (0,100) \t; THETA(EMAX) "
 "  (0,1000) \t; THETA(EC50) "

Where \\t is a tab. Without this THETA(EMAX) and THETA(EC50) as a comment, there wouldn't be any way to identify which initial estimate is to be associated with which 
THETA. Note that NONMEM assigns THETAs by sequence of appearance in $THETA. Given that the actual indices for THETA cannot be determined until the control file 
is created, this approach would lead to ambiguity. Each initial estimate must be on a new line and include the THETA (or ETA or EPS) + parameter identifier.

Other covariate effects are coded similarly. 


Variance terms
====================

Between subject variability is handled similarly, with the "{}" text. Typically, the first tokens in the token sets will be in the $PK, $DES, or $ERROR block and the  
2nd in $OMEGA, with the *required* ETA(IndexText) after a NONMEM comment (the same as for THETA initial estimates). ERR and EPS are handled similarly, either syntax is permitted.

Example 1 template file: :download:`template file <../examples/NONMEM/user/Example1/template.txt>`
Example 1 searches a 6 dimensional space. The dimensions correspond to :ref:`token group <token group>`. 

Data file path
====================
Typically, the NMTRAN data file will be in the :ref:`working directory<working directory>`. As the models are run in a directory two levels down 
(home directory/generation/model). The path to the dataset can be given as:

::

    $DATA {data_dir}/data.csv

Alternatively (and possibly preferred), the full path can be given.


Final template file
====================
As the search space is small (and the run time is fast), we'll perform an exhaustive search.
The final template file for Example 1 is given below.

::

    $PROBLEM    2 compartment fitting
    $INPUT       ID TIME AMT DV WTKG GENDER AGE DROP
    $DATA      {data_dir}/dataExample1.csv IGNORE=@
            
    $SUBROUTINE ADVAN2
    $ABBR DERIV2=NO
    $PK      
    CWTKG = WTKG/70  ;; CENTERED ON ONE 
    CAGE = AGE/40 
    TVV2=THETA(2){V2~WT[1]} {V2~GENDER[1]}
    V2=TVV2*EXP(ETA(2)) 
    TVCL= THETA(1) {CL~WT[1]}  
    CL=TVCL*EXP(ETA(1)) 
    K=CL/V2  
    TVKA=THETA(3) 
    KA=TVKA  {KAETA[1]}  
    S2 	= V2/1000 
    {ALAG[1]}
    $ERROR     
    REP = IREP      
    IPRED =F  
    IOBS = F {RESERR[1]}
    Y=IOBS
    $THETA  ;; must be one THETA per line.
    (0.001,100)	; THETA(1) CL UNITS =  L/HR
    (0.001,500) 	; THETA(2) V  UNITS = L
    (0.001,2) 	; THETA(3) KA UNITS = 1/HR  
    
    {V2~WT[2]}    
    {V2~GENDER[2]}     
    {CL~WT[2]}  
    {ALAG[2]}
    
    $OMEGA   ;; must be one ETA/line
    0.2  		; ETA(1) CLEARANCE
    ;; test for comments in blocks
    0.2  	; ETA(2) VOLUME
    ;; optional $OMEGA blocks
    {KAETA[2]}   
    
    $SIGMA   

    {RESERR[2]} 
    $EST METHOD=COND INTER MAX = 9999 MSFO=MSF1 
    $COV UNCOND PRINT=E
    
.. _tokens File:

******************
The Tokens file
******************

Example 1 tokens file: :download:`json tokens file <../examples/NONMEM/user/Example1/tokens.json>`

The :ref:`tokens file <tokens_file_target>` provides the :ref:`token key-text pairs<token key-text pair>` that 
are substituted into the template file. This file uses a `JSON <https://www.json.org/json-en.html>`_ file format. 
Unfortunately, comments are not  permitted in JSON files and so this file is without any annotation. Requirements are that 
each :ref:`token set <token set>` within a :ref:`token group <token group>` must have the same number of :ref:`tokens <token>` 
and new lines must be coded using the escape syntax ("\\n"), not just a new line in the file (which will be ignored in JSON). Any number of levels of 
nested tokens (tokens within tokens) is permitted. This can be useful, when one might want to search for covariates 
on a search parameter, as in searching for an effect of FED vs FASTED state on ALAG1, when ALAG1 is also searched (see
:ref:`PK example 2 <Example2_nested_tokens>`). Additional levels of nested tokens are permitted, but the logic of correctly coding them can become quickly daunting. 
The tokens file for Example 1 is given below.

::

    {
    
        "V2~WT": [
            ["",
            ""
            ],
            ["*CWTKG**THETA(V2~WT)",
                "  (-4,0.8,4) \t; THETA(V2~WT) POWER volume~WT "
            ]
        ],
        "V2~GENDER": [
            ["",
                ""
            ],
            ["*EXP(GENDER*THETA(V2~GENDER))",
                "  (-4,0.1,4) \t; THETA(V2~GENDER) exponential volume~GENDER "
            ]
        ],
        "CL~WT": [
            ["",
                ""
            ],
            ["*CWTKG**THETA(CL~WT)",
                "  (-4,.7,4) \t; THETA(CL~WT) POWER clearance~WT "
            ] 
        ],
        "KAETA": [
            ["",
            ""
            ],
            ["*EXP(ETA(KAETA)) ",
                "$OMEGA ;; 2nd??OMEGA block \n  0.1\t\t; ETA(KAETA) ETA ON KA"
            ]
        ],
        "ALAG": [
            ["",
                "" 
            ],
            ["ALAG1 = THETA(ALAG)",
                "  (0, 0.1,3) \t; THETA(ALAG) ALAG1 "
            ]
        ] ,
        "RESERR": [
            ["*EXP(EPS(RESERRA))+EPS(RESERRB)",
                "  0.3 \t; EPS(RESERRA) proportional error\n  0.3 \t; EPS(RESERRB) additive error"
            ],
            ["+EPS(RESERRA)",
                "  3000 \t; EPS(RESERRA) additive error"
            ]
        ]
    }

Note again, the **required** parameter identifier as a comment in all initial estimates, e.g., 

::

  "  (-4,0.8,4) \t; THETA(V2~WT) POWER volume ~WT "
  "  (-4,0.1,4) \t; THETA(V2~GENDER) POWER volume ~SEX "
  "  0.1\t\t; ETA(KAETA) ETA ON KA"
  "  0.3 \t; EPS(RESERRA) proportional error\n  0.3 \t; EPS(RESERRB) additive error"


.. _The Options File:

*****************
The Options file
*****************

Example 1 :ref:`Options file <options file>`  :download:`json options file <../examples/NONMEM/user/Example1/options.json>`
The options file will likely need to be edited, as the path to nmfe??.bat (Windows) or nmfe?? (Linux) must be provided

The user should provide an appropriate path for :ref:`"nmfe_path"<nmfe_path_options_desc>`. NONMEM version 7.4 and 7.5 are supported. 


Note that, to run in the environment used for this example, the directories are set to:

::

	
    "working_dir": "u:/pyDarwin/example1/working",
    "temp_dir": "u:/pyDarwin/example1/rundir",
    "output_dir": "u:/pyDarwin/example1/output",

It is recommended that the user set the directories to something appropriate for their environment. If directories are not set, 
the default is:

::

	{user_dir}\pydarwin\{project_name}

In either case, the folder names are given in the initial and final output to facilitate finding the files and debugging.


::

    {
        {
    "author": "Certara",
    "algorithm": "EX",
    "exhaustive_batch_size": 100,
 
    "num_parallel": 4,
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
    "model_run_timeout": 1200
    }
    }

Penalties
====================

The base value for the "fitness" (for GA) or "reward/cost" for other algorithms is the -2LL value from the NONMEM output. Typically, penalties for increased complexity are added to this. If one 
parameter is added, and the models are nested, a value of 3.84 points per parameter corresponds to p< 0.05. We'll use 10 points for each estimated parameter. Generally, a model that converges 
and has a successful covariance step is viewed as "better" than a model that doesn't. Therefore, to capture this, we'll add 100 points for failing to converge, failing a covariance step, 
and failing the correlation test. Note that if the covariance step is not requested, the failed covariance penalty is added, as is the failed correlation test and the failed condition number test. 
Similarly, if the PRINT=E option is not included in the $COV record, the eigenvalues will not be printed and this will be regarded as a failed condition number test. 
The non_influential_tokens penalty is added if any tokens selected for this model do not influence the final control file, as may be the case for nested tokens. This number should be small, as 
it is only intended to break ties between otherwise identical models.

The data file
====================

Example 1 data file: :download:`dataExample1.csv <../examples/NONMEM/user/Example1/dataExample1.csv>`
  

******************
Execute Search
******************

Usage details for starting a search in ``pyDarwin`` can be found :ref:`here<Execution>`.

See :ref:`"Examples"<examples_target>` for additional details about accessing example files.

Initialization of the run should generate output similar to this:

::

    [10:50:33] Options file found at ..\examples\user\Example1\options.json
    [10:50:33] Preparing project working folder...
    [10:50:33] Preparing project output folder...
    [10:50:33] Preparing project temp folder...
    [10:50:41] Model run priority is below_normal
    [10:50:41] Using darwin.MemoryModelCache
    [10:50:41] Project dir: c:\fda\pyDarwin\examples\user\Example1
    [10:50:41] Data dir: c:\fda\pyDarwin\examples\user\Example1
    [10:50:41] Project working dir: u:/pyDarwin/example1/working
    [10:50:41] Project temp dir: u:/pyDarwin/example1/rundir
    [10:50:41] Project output dir: u:/pyDarwin/example1/output
    [10:50:41] Writing intermediate output to u:/pyDarwin/example1/output\results.csv
    [10:50:41] Models will be saved in u:/pyDarwin/example1/working\models.json
    [10:50:41] Template file found at ..\examples\user\Example1\template.txt
    [10:50:41] Tokens file found at ..\examples\user\Example1\tokens.json
    [10:50:41] Search start time = Sun Jul 31 10:50:41 2022
    [10:50:41] Total of 64 to be run in exhaustive search
    [10:50:41] NMFE found: c:/nm744/util/nmfe74.bat
    [10:50:42] Not using Post Run R code
    [10:50:42] Not using Post Run Python code
    [10:50:42] Checking files in u:\pyDarwin\example1\rundir\0\01
    [10:50:42] Data set # 1 was found: c:\fda\pyDarwin\examples\user\Example1/dataExample1.csv

It is important to notice that the temp directory (temp_dir) is listed and since:
    
    ::

        "remove_temp_dir": false,

is set to false in the options file, all key NONMEM outputs are saved. This temp directory is where you should look for the output after the
inevitable errors.
During the search, the current, interim best model files can be found in the working dir, along with the messages (same content as output 
to console) and a models.json file that can be used to restart searches that are interrupted. 
The final outputs will be found in the Project output dir. 
At the end of the run, the output should look like:

::
        
    [11:16:28] Current Best fitness = 4818.765528670225
    [11:16:28] Final output from best model is in u:/pyDarwin/example1/output\FinalResultFile.lst
    [11:16:28] Number of unique models to best model = 51
    [11:16:28] Time to best model = 9.7 minutes
    [11:16:28] Best overall fitness = 4818.765529, iteration 0, model 47
    [11:16:28] Elapsed time = 12.8 minutes

The final best model files and a list of all runs (results.csv) can be found in the output folder. 