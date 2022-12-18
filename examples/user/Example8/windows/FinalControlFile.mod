$PROBLEM EMAX  
  ; 
  ; CONTINUOUS COVARIATE, BW
  ;	- E0   : NONE, POWER 
  ; 	- EMAX : NONE, POWER
  ; 
  ; CATEGORICAL COVRIATE, SEX
  ;	- E0   : NONE, EXPONENTIAL
  ; 	- EMAX : NONE, EXPONENTIAL 
  ;
  ; CATEGORICAL COVRIATE, RACE
  ;	- E0   : NONE, EXPONENTIAL 
  ; 	- EMAX : NONE, EXPONENTIAL 
  ;
  ; IIV ON EC50     : NO OR YES 
  ; 
  ; SIGMOID         : NO OR YES (THE ASSOCIATED IIV IS ALSO SEARCHED)
  ; 
  ; RESIDUAL ERROR  : ADDITIVE OR PROPORTIONAL OR COMBINED 


  ; ====================================================================================================
  ; DATA
  ; ====================================================================================================          

$INPUT ID TIME SEX RACE BW C DV 
$DATA C:\Workspace\Example8\PDdata.csv IGNORE = @


  ; ====================================================================================================
  ; PRED
  ; ====================================================================================================    

$PRED 

  ; SCALED BW
  BWONE = BW/70

  ; INDICATOR FOR SEX = 1
  SEXEQ1 = 0
  IF(SEX == 1) SEXEQ1 = 1

  ; INDICATOR FOR RACE = 1
  RACEEQ1 = 0
  IF(RACE == 1) RACEEQ1 = 1

  ; E0
  TVE0 = THETA(1)
  E0 = TVE0 * BWONE**THETA(4) * EXP(THETA(5) * SEXEQ1) * EXP(THETA(6) * RACEEQ1) * EXP(ETA(1))

  ; EMAX
  TVEMAX = THETA(2)
  EMAX = TVEMAX    * EXP(ETA(2))

  ; EC50 
  TVEC50 = THETA(3)
  EC50 = TVEC50 

  ; NEWLY ADDED STRUCTURAL PARAMETERS 


  ; EMAX MODEL 
  CGAM = C
  E = E0 + EMAX * CGAM/(EC50 + CGAM)

  ; RESIDUAL ERROR MODEL 
  Y = E * (1 + EPS(1))


  ; ====================================================================================================
  ; INITIAL VALUES FOR THETA
  ; ====================================================================================================

$THETA
  (0, 1) ; THETA(1) tvE0
  (0, 1) ; THETA(2) tvEmax
  (0, 100) ; THETA(3) tvEC50

  ; INITIAL VALUES FOR NEWLY ADDED THETA

  1 	 ; THETA(4) BW ON E0
  1 	 ; THETA(5) SEX ON E0
  -1 	 ; THETA(6) RACE ON E0




  ; ====================================================================================================
  ; INITIAL VALUES FOR OMEGA
  ; ====================================================================================================

$OMEGA
  1 ; ETA(1) nE0
  1 ; ETA(2) nEmax

  ; INITIAL VALUES FOR NEWLY ADDED OMEGA



  ; ====================================================================================================
  ; INITIAL VALUES FOR SIGMA
  ; ====================================================================================================

$SIGMA 
  0.01 	 ; EPS(1) VARIANCE OF PROPORTIONAL ERROR

  ; ==================================================================================================
  ; ESTIMATION METHOD AND SE 
  ; ==================================================================================================

$EST METHOD = CONDITIONAL INTERACTION NOABORT MAXEVAL = 9999 PRINT = 5

$COV UNCOND PRINT = E
;; Phenotype 
;; OrderedDict([('E0_BW', 1), ('E0_SEX', 1), ('E0_RACE', 1), ('EMAX_BW', 0), ('EMAX_SEX', 0), ('EMAX_RACE', 0), ('EC50ETA', 0), ('GAM', 0), ('RESERR', 1)])
;; Genotype 
;; [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1]
;; Num non-influential tokens = 0