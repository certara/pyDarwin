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

$INPUT       ID TIME AMT CMT DROP DV DVID EVID MDV 
$DATA      /home/ppolozov/darwin/examples/user/Example3/OralBolus_PlasmaUrine_ResetCpt4.csv IGNORE=@


  ; ====================================================================================================
  ; SUBROUTINE
  ; ====================================================================================================          
$SUBROUTINE ADVAN13 TOL = 6

$MODEL
  NCOMP =  4 
  COMP = (DEPOT) 
  COMP = (CENTRAL) 
  COMP = (PERIPH)
  COMP = (URINE)


  ; ===================================================================================================
  ; STRUCTURAL PARAMETERS 
  ; ===================================================================================================
$PK      

  KA = THETA(1) * EXP(ETA(1)) 

  VC = THETA(2) * EXP(ETA(2)) 

  VP = THETA(3) * EXP(ETA(3)) 

  CLQ = THETA(4) * EXP(ETA(4)) 

  CLC = THETA(5) * EXP(ETA(5))

  TEMP = EXP(THETA(6) + ETA(6)) 
  F1 = TEMP/(1 + TEMP)

  ; ====================================================================================================
  ; INITIAL VALUES FOR FIXED EFFECTS
  ; ====================================================================================================
$THETA  

  (0, 1) 	 ; THETA(1) TVKA 
  (0, 5) 	 ; THETA(2) TVVC 
  (0, 5) 	 ; THETA(3) TVVP 
  (0, 1) 	 ; THETA(4) TVCLQ 
  (0, 2) 	 ; THETA(5) TVCLC 
  3 	 ; THETA(6) TVLOGITF  


  ; ====================================================================================================
  ; INITIAL VALUES FOR OMEGA
  ; ====================================================================================================
$OMEGA 

  1 	 ; ETA(1) ETA ON KA 
  1 	 ; ETA(2) ETA ON VC 
  1 	 ; ETA(3) ETA ON VP 
  1 	 ; ETA(4) ETA ON CLQ 
  1 	 ; ETA(5) ETA ON CLC
  1 	 ; ETA(6) ETA ON LOGITF


  ; ====================================================================================================
  ; ODE MODEL 
  ; ====================================================================================================
$DES

  C = A(2)/VC 

  DADT(1) = - KA * A(1) 
  DADT(2) = KA * A(1) - CLC * C - CLQ * (A(2)/VC - A(3)/VP) 
  DADT(3) = CLQ * (A(2)/VC - A(3)/VP) 
  DADT(4) = CLC * C


  ; ===================================================================================================
  ; RESIDUAL ERROR MODEL
  ; ===================================================================================================
$ERROR  

  ; IPRED 
  IPREDC = A(2)/VC 
  IPREDU = A(4)

  ; RESIDUAL ERROR MODEL 
  IF (DVID == 1) Y = IPREDC * (1 + EPS(1))
  IF (DVID == 2) Y = IPREDU * (1 + EPS(2)) + EPS(3)


$SIGMA  

  0.01 	 ; EPS(1) VARIANCE OF PROPORTIONAL ERROR FOR PLASMA OBSERVATION
  0.01 	 ; EPS(2)) VARIANCE OF PROPORTIONAL ERROR FOR URINE OBSERVATIONS 
  0.1 	 ; EPS(3) VARIANCE OF ADDITIVE ERROR FOR URINE OBSERVATIONS


  ; ==================================================================================================
  ; ESTIMATION METHOD AND SE 
  ; ================================================================================================== 

$EST METHOD = 0 NOABORT MAX = 9999 SIGL = 6 NSIG = 2 PRINT = 5

$COV UNCOND PRINT = E


;; Phenotype 
;; OrderedDict([('ODE', 4), ('ELIM', 0), ('BIOAVAIL', 2), ('RESERRC', 0), ('RESERRU', 2)])
;; Genotype 
;; [4, 0, 2, 0, 2]
;; Num non-influential tokens = 0