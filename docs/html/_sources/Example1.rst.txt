

.. _startpk1:

Example 1: PK Model, Trivial Exhaustive Search
==============================================

This first model is quite simple, the search space consistes of 6 dimensions, each with 2 options. Thus, the total number of candiate models is 
2^6 = 64 models. As the search space if very small, we'll search by exhaustive search. 

First step:

As is the usual practise in POPPK model selection, the first step will be exploratory data analysis. This serves at least two purposes: To validate the data set 
and to generate initial hypotheses. We will however, for the purpose of this tutorial, skip this step and assume that we have a "correct" data set and list of 
hypotheses to be tests. 

The next step for ML model selection is to get a simple model running. The control file for this simple model is given below:

::

    $PROBLEM    2 compartment fitting
    $INPUT       ID TIME AMT DV WTKG GENDER AGE DROP
    $DATA      ..\..\datalarge.csv IGNORE=@
            
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
    


This text will serve as the starting point for developing the template file
Note that the relative path to the data file is up two folders. When pyDarwin runs models, it does not copy the data file to the run directory. Rather, 
typically the data file is in the home directory, and the models are run in home directory/generation/model. Therefore, the relative path to the run directory will 
be up two levels.


.. _template file: 

The Template file
~~~~~~~~~~~~~~~~~
The initial simple model can then be editted by adding tokens. This first example will include covariates, residual error and one structural feature. 
Each token group is identified by a :ref:`token stem <token stem>`, e.g. "V2~WT" for the dimension of the 
relationship between weight a volume of distribution. Each token group includes 
2 or more :ref:`token set <token set>`, one for each option in the that dimension, These dimensions are:

1. Effect of Weight on Volume ("V2~WT") - None or a power model.
2. Effect of Sex (Gender) on Volume ("V2~GENDER") - None or a power model
3. Effect of Weight on Clearance ("CL~WT") - None or a power model
4. Presence of between subject variability (BSF) on Ka ("KAETA")- None or exponential model
5. Presence of an absorption lag time - ALAG1 ("ALAG") - Present or not
6. Residual error model ("RESERR") - additive or combined additive and proportional

Covariate effects
------------------

For the effect of Weight on Volume, we've chosen the :ref:`token stem<token stem>` of "V2~WT". Two tokens will be required for this :ref:`token set<token set>`. The first will be 
adding the relationship to the definition of TVV2 in the $PK block and the 2nd will be providing an initial estimate in the $THETA block for the estimated 
THETA. Note that the index for THETA for this feature cannot be defined until the model is constructed. Only then can the number and sequence of the added THETAs be 
determined. In the token set THETAs will be indexed with text, e.g., THETA(V2~WT). As there will be two tokens in the token set, the first have and index of 1
and the 2nd an index of 2:

::

     {V2~WT[1]}
     and
     {V2~WT[2]} 
    

note the curly braces, these are required for tokens in the template file. The record in the $PK will have the token appended to it, resulting this text:


::

    TVV2=THETA(2){V2~WT[1]}
    
Two options for the text to be substituted for {V2~WT[1]} will 
be defined:

1. ""
2. "\*CWTKG**THETA(V2~WT)"

The first will have no text in that record, resulting in

::

    TVV2=THETA(2)


and the 2nd text being substituted will result in

::

    TVV2=THETA(2)*CWTKG**THETA(V2~WT)


The 2nd token for the initial estimate for THETA(V2~WT) wil be similar. The token text options will be:

1. ""
2. "  (-4,0.8,4) \\t; THETA(V2~WT) POWER volume ~WT "


The resulting $THETA block for this initial feature will be:

::

    $THETA  ;; must be one THETA per line.
    (0.001,100) ; THETA(1) CL UNITS =  L/HR
    (0.001,500) ; THETA(2) V  UNITS = L
    (0.001,2)   ; THETA(3) KA UNITS = 1/HR

    {V2~WT[2]}    

Note the use of the escape syntax, "\\t" for a tab. Newlines will be coded simlarly as "\\n". NONMEM comments (text after ";") are permitted. However, the 
user must be aware of the impact that comments in token text may have on any code that follows. This $THETA block has 3 fixed THETA initial estimates - THETA(1), 
THETA(2) and THETA(3). These will appear in all control files in the search. These fixed initial estimates are then followed by searched initial estimates. Searched 
initial estimates may or may not appear, depending on the model specification (:ref:`phenotype<phenotype>`). Searched initial estimates must be placed after all 
fixed initial estimates. Each initial estimate must be on a separate line and must be surrounded by parentheses. The standard combinations of (lower, initial,upper) 
are all supported. 

Tokens sets for each feature to be searched will be defined as these :ref:`token key-text pairs<token key-text pair>` (analagous to key-value pairs 
in JSON, but only text values are permitted)

Each of these dimensions has two options. Therefore the total number of candidate models 
in the search space is number of permutations - 2^6 = 64. 

In the :download:`template text <../examples/user/Example1/template.txt>` note the 
special text in curly braces({}). These are :ref:`tokens<token>`. Tokens come in sets, as typically 
multiple text substittion must be made to results in a syntactically correct NMTRAN control file. For 
example, if ALAG1 is to be used in the $PK block, a corresponding initial estimate for 
this parameter must be provided in the $THETA block. These tokens (collectively called a token set) 
are then replaced by the corresponding text value in the :ref:`token key-text pair <token key-text pair>`. 


Other covariate effects are coded similarly. 


Between subject variability
-----------------------------



Example 1 template file :download:`template file <../examples/user/Example1/template.txt>`
Example 1 searchs a 6 dimensional space. The dimensions corresponds to :ref:`token group <token group>`. 

Data file path
--------------
Typically, the NMTRAN data file will be located in the :ref:`working directory directory<working directory>`. As the models are run in a directory two levels down 
(home directory/generation/model) the path to the data set can be given as 

::

    $DATA ..\..\data.csv

Alternatively, the full path can be given.


Final template file
--------------------
As the search space is small (and the run time is fast), we'll search by exhaustive search.
The final template file for Example 1 is given below.

::

    $PROBLEM    2 compartment fitting
    $INPUT       ID TIME AMT DV WTKG GENDER AGE DROP
    $DATA      ..\..\datalarge.csv IGNORE=@
            
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

The Tokens file
~~~~~~~~~~~~~~~~

Example 1 tokens file :download:`json tokens file <../examples/user/Example1/tokens.json>`

The :ref:`tokens file <tokens_file_target>` provide the :ref:`token key-text pairs<token key-text pair>` that 
are substitued into the template file. This is a `JSON <https://www.json.org/json-en.html>`_ file format. 
Unfortunately, comments are not  permitted in JSON files and so this file without annotation. Requirements are that 
each :ref:`token set <token set>` within a :ref:`token group <token group>` must have the same number of :ref:`tokens <token>` 
and new lines must be coded using the escape syntax ("\\n"), not just a new line in the file (which will be ignored). One level of 
nest tokens (tokens within tokens is permitted. This can be useful, when for example one might want to search for covariates 
on an search parameter, as in searching for an effect of FED vs FASTED state on ALAG1, when ALAG1 is also searched (see
:ref:`PK example 3 <startpk3>`). The tokens file for Example 1 is given below.

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
            ["*CWTKG**THETA(V2~GENDER)",
                "  (-4,0.1,4) \t; THETA(V2~GENDER) POWER volume ~SEX "
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


.. _The Options File:

The Options file
~~~~~~~~~~~~~~~~

Example 1 :ref:`Options file <options file>`  :download:`json options file <../examples/user/Example1/options.json>` 
The options file will likely need to be editted, as the path to nmfe??.bat must be provided
The options file for Example 1 is given below:

::

    {
        "author": "Certara",
        "homeDir": "C:\\fda\\pydarwin\\examples\\Example1",
        "algorithm":"EXHAUSTIVE",
        "random_seed": 11,  
        "max_model_list_size": 500,
        "num_parallel": 40,
        "THETAPenalty": 10,
        "OMEGAPenalty": 10,
        "SIGMAPenalty": 10,
        "covergencePenalty": 100,
        "covariancePenalty": 100,
        "correlationPenalty": 100,
        "correlationLimit": 0.95,
        "conditionNumberPenalty": 100,  
        "input_model_json": "None", 
        "crash_value": 99999999,
        "non_influential_tokens_penalty": 0.00001,
        "remove_run_dir": false, 
        "timeout_sec": 1200, 
        "useR": false,     
        "usePython": false,   
        "nmfePath": "c:/nm741/util/nmfe74.bat " , 
        "NM_priority_class": "below_normal"
    }



The data file
~~~~~~~~~~~~~~~~

Example 1 Data file :download:`datalarge.csv <../examples/user/Example1/datalarge.csv>` 

  
 