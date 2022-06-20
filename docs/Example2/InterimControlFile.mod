$PROBLEM    2 compartment fitting
$INPUT       ID TIME AMT DV WTKG GENDER AGE DROP
$DATA      ..\..\datalarge.csv IGNORE=@
           
$SUBROUTINE ADVAN2 ;; advan2 
$PK      
  CWTKGONE = WTKG/70  ;; CENTERED ON ONE
  CWTKGZERO = WTKG-70  ;; CENTERED ON ZERO
  CAGE = AGE/40
;; thetas out of sequence
  TVV2=THETA(2) *CWTKGONE**THETA(4)
  V2=TVV2*EXP(ETA(2)) 
  TVCL= THETA(1) *EXP(CWTKGZERO*THETA(5))  
  CL=TVCL*EXP(ETA(1)) 
  K=CL/V2 
  ;; thetas out of sequence here
  ;; PK 1 compartment  
   ALAG1=THETA(6)
;; No D1 ; include D1 and lag, with diag or block OMEGA
  
  TVKA=THETA(3) 
  KA=TVKA    
  S2 	= V2/1000 
$ERROR     
 REP = IREP      
 IPRED =F  
 IOBS = F *EXP(EPS(1))+EPS(2)
 Y=IOBS
$THETA  ;; must be one THETA per line.
 (0.001,100)	; THETA(1) CL UNITS =  L/HR
 (0.001,500) 	; THETA(2) V  UNITS = L
 (0.001,2) 	; THETA(3) KA UNITS = 1/HR 
;; test for comments in blocks
;; test for comments in blocks

 ;; THETA 1 compartment  ;; comment
    ;;; comment ;; comment
   (-4,0.1,4) 	; THETA(4) POWER volume ~SEX    ;;; comment ;; comment
;; test for comments in blocks
   (-1,0.01,4) 	; THETA(5) EXPONENTIAL clearance~WT  
  
   (0.001,0.3) 	; ALAG1 THETA(6) 
$OMEGA   ;; must be one ETA/line
  0.2  		; ETA(1) CLEARANCE
$OMEGA
;; test for comments in blocks
  0.2 	; ETA(2) VOLUME
;; optional $OMEGA blocks
  
;; test for comments in blocks
 
 
$SIGMA  
;; test for comments in blocks

  0.3 	; EPS(1) proportional error
  0.3 	; EPS(2) additive error
$EST METHOD=COND INTER MAX = 9999 MSFO=MSF1 
$COV UNCOND PRINT=E
 
 ;; Phenotype 
 ;; OrderedDict([('ADVAN', 0), ('K23~WT', 1), ('KAETA', 0), ('V2~WT', 0), ('V2~GENDER', 1), ('CL~WT', 2), ('CL~AGE', 0), ('ETAD1LAG', 0), ('D1LAG', 0), ('RESERR', 0)])
;; Genotype 
 ;; [0, 1, 0, 0, 1, 2, 0, 0, 0, 0]
;; Num non-influential tokens = [False, True, False, False, False, False, False, False, False, False]