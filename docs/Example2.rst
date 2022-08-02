.. _startpk2:


Example 2: PK Model 2, Simulation model by GP with Python code
================================================================

Example 2 is still a fairly simple search. The search space contains 12,960 models, 10 dimensions. The dimensions are:

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
| | Is the zero order        | | D1LAG                  | | D1 or ALAG or Both       |
| | infusion and/or ALAG1    | |                        | |                          |
+----------------------------+--------------------------+----------------------------+
| | Residual Error Model     | | RESERR                 | | Additive or combined     |
| |                          | |                        | | Additive and Proportional|
+----------------------------+--------------------------+----------------------------+

This gives a search space of 3 x 2 x 2 x 3 x 2 x 3 x 2 x 5 x 3 x 2 = 12960 models. We'll use the :ref:`Gaussian Process<GP_desc>` algorithm for the search, 
with a population size of 40 models, for up to 7 iterations. We'll run the downhill (1 and 2 bit search) each 5 iterations. The dowhill step will be 
done starting with 2 models. The models are selected as the best in each of the two best niches. To selected the best models in each of 2 niches, first 
the best model in the entire population is identified. This will be the model for the first niche. Then all models within a :ref:`niche radius<Niche Radius>` 
of 2 are identified. The best in the 2nd niche then is the best model that is not in a niche. In this way we ensure that the downhill step is done starting 
with 2 models that are at least somewhat dissimilar (by at least a distance of 2). Commonly the :ref:`niche radius<Niche Radius>` would be larger than 2, 
but, given that there are only 10 bits in the entire genome, a 2 bit radius will span a significant part of the search space. All parsimony penalties (THETA, OMEGA, 
and SIGMA) will be 10 points, and we would really like a model that converges, has a successful covariance step, passes the correlation test and has a condition 
number < 100, so all of these penalties will be 100. As there are nested tokens in this search, there is a reason to penalize models with non-influential 
tokens, the penalty for non-influential tokens will be set to 0.00001. This small penalty is only to insure that in a tournament selection the model that 
does not have non-influential tokens will be selected. 


Notes on Gaussian Process performance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Gaussian Process is an approach in `Bayesian Optimization <https://proceedings.neurips.cc/paper/2012/file/05311655a15b75fab86956663e1819cd-Paper.pdf>`_ 
and `here <https://scikit-optimize.github.io/stable/auto_examples/bayesian-optimization.html#sphx-glr-auto-examples-bayesian-optimization-py>`_  where the samples are drawn from 
a Gaussian Process. There are reasons to beleive that this this approach should be the most effecient (fewer reward evaluations to convergence). However, the sampling itself can be very 
computionally  expensive. Therefore the :ref:`GP option <GP_desc>` is best suited when the number of reward calculation number of NONMEM models run) is relatively small, perhaps < 1000, 
and the NONMEM run time is long (1 hour). Below is a table of the `ask and tell <https://scikit-optimize.github.io/stable/modules/optimizer.html#>`_ step times  (hh:mm:ss), by iteration. The sample size ws 80, with 4 chains on a 4 core computer: 

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



note the essentially linear increase in the ask step time (time to generate samples for next iteration) as the data set size increases.
For problems with larger search spaces, and greater number of model evaluations, :ref:`Genetic algorithm<GA_desc>` or :ref:`Random Forest <RF_desc>` may 
be more appropriate.

Below is a table of recommenations for algorithm selection.

 - Fast execution, large search space (> 100,000 models, expected sample > 1000 models)– :ref:`GA<GA_desc>` or :ref:`RF<RF_desc>`
 - Small seach space (<100,000, expected # of samples < 1000) - :ref:`Gaussian Process<GP_desc>`.
 - Very small search space (< 500 models), many cores (> 20) – :ref:`exhaustive search <EX_desc>`.

The Template file 
~~~~~~~~~~~~~~~~~

The template file for example 2 is given below

::

   $PROBLEM    2 compartment fitting
   $INPUT       ID TIME AMT DV WTKG GENDER AGE {D1LAG[1]}
   $DATA      {data_dir}/datalarge.csv IGNORE=@
            
   $SUBROUTINE {ADVAN[1]} ;; ADVAN2, ADVAN4, ADVAN12
   $PK      
   CWTKGONE = WTKG/70  ;; CENTERED ON ONE
   CWTKGZERO = WTKG-70  ;; CENTERED ON ZERO
   CAGE = AGE/40 
   TVV2=THETA(2){V2~WT[1]} {V2~GENDER[1]} ;; optional covariates effects of WT and Gender
   V2=TVV2*EXP(ETA(2)) 
   TVCL= THETA(1) {CL~WT[1]}  {CL~AGE[1]} ;; optional covariates effects of WT and AGE
   CL=TVCL*EXP(ETA(1)) 
   K=CL/V2  
   {ADVAN[2]}         ;; for K23,K32,K24,K42 needed?
   {D1LAG[2]}         ;; include D1 and lag, with diag or block OMEGA
   
   TVKA=THETA(3) 
   KA=TVKA  {KAETA[1]}  
   S2 	= V2/1000 
   $ERROR     
   REP = IREP      
   IPRED =F  
   IOBS = F {RESERR[1]}
   Y=IOBS
   $THETA  ;; must be one THETA per line.
   (0.001,100)	; THETA(1) CL UNITS =  L/HR
   (0.001,500) 	; THETA(2) V  UNITS = L
   (0.001,2) 	; THETA(3) KA UNITS = 1/HR  

   {ADVAN[3]}  ;; are initial estimates for K23,K32,K24,K42 needed?
   {V2~WT[2]}   ;;; is initial estimate for Volume a function of weight needed?
   {V2~GENDER[2]}   ;;; is initial estimate for Volume a function of gender needed?
   {CL~WT[2]} 
   {CL~AGE[2]} 
   {D1LAG[3]}
   $OMEGA   ;; must be one ETA/line
   0.2  		; ETA(1) CLEARANCE
   $OMEGA 
   0.2 	; ETA(2) VOLUME
   ;; optional $OMEGA blocks
   {KAETA[2]}   ;; optional initial estimates for ETA on KA
   
   {D1LAG[4]}   ;; optional initial estimates for ETA on D1 and ALAG1
   $SIGMA   

   {RESERR[2]}   ;; additive or proportional or combined
   $EST METHOD=COND INTER MAX = 9999 MSFO=MSF1 
   $COV UNCOND PRINT=E

Example 2 template file :download:`text <../examples/user/Example2/template.txt>`

The Tokens file
~~~~~~~~~~~~~~~~
Notes:

.. _Example2_nested_tokens:


#. The example includes nested tokens. The K23~WT token group is nested within the ADVAN token group and the ETAD1LAG token group is nested with the D1LAG group

#. Nested tokens can result in non-influential tokens. E.g., if ADVAN2 is selected, the selection of K23~WT tokens will have no effect on the constructed control file


::

   {
      "ADVAN": [
         ["ADVAN2 ;; advan2",
            ";; PK 1 compartment ",
            ";; THETA 1 compartment"
         ],
         ["ADVAN4 ;; advan4",
            " K23=THETA(ADVANA){K23~WT[1]}\n K32=THETA(ADVANB){K23~WT[1]}",
            "  (0.001,0.02)  \t ;; THETA(ADVANA) K23 \n (0.001,0.3) \t ;; THETA(ADVANB) K32 \n{K23~WT[2]} \t ;; init for K23~WT "
         ],
         ["ADVAN12 ;; advan12",
            " K23=THETA(ADVANA){K23~WT[1]}\n  K32=THETA(ADVANB){K23~WT[1]}\n  K24=THETA(ADVANC)\n  K42=THETA(ADVAND)",
            "  (0.001,0.1) \t;; THETA(ADVANA) k23 \n (0.001,0.1) \t ;;THETA(ADVANB) k32 \n (0.001,0.1) \t;; THETA(ADVANC) k24  \n (0.001,0.1) \t;; THETA(ADVAND)k42  \n {K23~WT[2]} \t ;; init for K23~WT"
         ]
      ],
      "K23~WT": [
         ["",
         ""
         ],
         ["*CWTKGONE**THETA(K23~WT)",
            "  (0,0.1) \t; THETA(K23~WT) K23~WT"
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
      "V2~WT": [
         ["",
         ""
         ],
         ["*CWTKGONE**THETA(V2~WT)",
            "  (-4,0.8,4) \t; THETA(V2~WT) POWER volume ~WT "
         ],
         ["*EXP(CWTKGZERO*THETA(V2~WT))",
            "  (-1,0.01,2) \t; THETA(V2~WT) EXPONENTIAL volume ~WT "
         ]
      ],

      "V2~GENDER": [
         ["",
            ""
         ],
         ["*CWTKGONE**THETA(V2~GENDER)",
            "  (-4,0.1,4) \t; THETA(V2~GENDER) POWER volume ~SEX "
         ]
      ],
      "CL~WT": [
         ["",
            ""
         ],
         ["*CWTKGONE**THETA(CL~WT)",
            "  (-4,.7,4) \t; THETA(CL~WT) POWER clearance~WT "
         ],
         ["*EXP(CWTKGZERO*THETA(CL~WT))",
            "  (-1,0.01,4) \t; THETA(CL~WT) EXPONENTIAL clearance~WT "
         ]
      ],
      "CL~AGE": [
         ["",
         ""
         ],
         ["*CAGE**THETA(CL~AGE)",
            "  (-4,-0.2,4) \t; THETA(CL~AGE) POWER clearance~AGE "
         ]
      ],
      "ETAD1LAG": [
         ["",
            "",
            ""
         ],
         ["*EXP(ETA(ETALAG))",
            "",
            "$OMEGA ;; 3rd OMEGA block \n  0.1 \t\t;; ETA(ETALAG) ETA ON ALAG1"
         ],
         ["",
            "*EXP(ETA(ETALAG1))",
            "$OMEGA ;; 3rd??OMEGA block \n  0.1 \t\t;; ETA(ETALAG1) ETA ON D1"
         ],
         ["*EXP(ETA(ETALAG1))",
            "*EXP(ETA(ETALAG2))",
            "$OMEGA  ;; diagonal OMEGA \n  0.1 \t\t;; ETA(ETALAG1) ETA ON ALAG1\n  0.1 \t\t;; ETA(ETALAG2) ETA ON D1"
         ],
         ["*EXP(ETA(ETALAG1))",
            "*EXP(ETA(ETALAG2))",
            "$OMEGA BLOCK(2) ;; block OMEGA block \n  0.1 \t\t;; ETA(ETALAG1) ETA ON ALAG1\n  0.01 0.1 \t\t;; ETA(ETALAG2) ETA ON D1"
         ]
      ],
      "D1LAG": [
         ["DROP",
            " ALAG1=THETA(ALAG){ETAD1LAG[1]}\n;; No D1",
            "  (0.001,0.3) \t; ALAG1 THETA(ALAG) ",
            "{ETAD1LAG[3]}"
         ],
         ["RATE",
            "  D1=THETA(D1) {ETAD1LAG[1]} ; infusion only",
            "  (0.01,0.2) \t\t;; D1 THETA ",
            "{ETAD1LAG[3]} \t\t;; D1 ETA only"
         ],
         ["RATE",
            "  ALAG1=THETA(ALAG){ETAD1LAG[1]}\n  D1=THETA(D1){ETAD1LAG[2]}",
            "  (0.001,0.1,1) \t\t;; D1 THETA Init\n  (0.001,0.1,1) ;; ALAG THETA Init",
            "{ETAD1LAG[3]} \t\t;; ETA on D1 and lag, block"
         ]
      ],
      "RESERR": [
         ["*EXP(EPS(RESERRA))+EPS(RESERRB)",
            "  0.3 \t; EPS(RESERRA) proportional error\n  0.3 \t; EPS(RESERRB) additive error"
         ],
         ["+EPS(RESERRA)",
            "  3000 \t; EPS(RESERRA) additive error"
         ]
      ]
   }

**NOTE AGAIN!!**
The use of THETA(paremeter identifier), e.g.


::

   (-4,.7,4) \t; THETA(CL~WT)


for **ALL** initial estimate token text (THETA, OMEGA and SIGMA).

Example 2 tokens file :download:`json <../examples/user/Example2/tokens.json>`

The Options file
~~~~~~~~~~~~~~~~


The user should provide an appropriate path for :ref:`"nmfePath"<nmfePath>`. NONMEM version 7.4 and 7.5 are supported. 


Note that to run in the enviroment used for this example, the directories are set to:

::

	
    "working_dir": "u:/pyDarwin/example2/working",
    "temp_dir": "u:/pyDarwin/example2rundir",
    "output_dir": "u:/pyDarwin/example2/output",

It is recommended that the user set the directories to something appropriate for their enviroment. If directories are not set 
the default is:

::

	{user_dir}\pydarwin\{project_name}

In either case, the folder names are given in the initial and final output to facilitate finding the files and debuggins.

::

   {
    "author": "Certara",
    "algorithm": "GP",
    "num_opt_chains": 2,
    
    "random_seed": 11,
    "population_size": 10,
    "num_parallel": 4,
    "num_generations": 7,

    "downhill_period": 5,
    "num_niches": 2,
    "niche_radius": 2,
    "local_2_bit_search": false,
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
    "model_run_timeout": 1200
   }

Once again, note that remove_run_dir is set to false, so NONMEM model and output files will be preserved in the temp_dir.


Example 2 options file :download:`json <../examples/user/Example2/options.json>`
 