
$PROBLEM    2 compartment fitting
$INPUT       ID TIME AMT DV WTKG GENDER AGE RATE
$DATA      C:\Workspace\Example2/datalarge.csv IGNORE=@

$SUBROUTINE ADVAN4 ;; advan4 ;; ADVAN2, ADVAN4, ADVAN12
$PK      
  CWTKGONE = WTKG/70  ;; CENTERED ON ONE
  CWTKGZERO = WTKG-70  ;; CENTERED ON ZERO
  CAGE = AGE/40 
  TVV2=THETA(2)  ;; optional covariates effects of WT and Gender
  V2=TVV2*EXP(ETA(2)) 
  TVCL= THETA(1)    ;; optional covariates effects of WT and AGE
  CL=TVCL*EXP(ETA(1)) 
  K=CL/V2 
  K23=THETA(4)
  K32=THETA(5)         ;; for K23,K32,K24,K42 needed?
  D1=THETA(6)  ; infusion only         ;; include D1 and lag, with diag or block OMEGA

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

  (0.001,0.02)	 ;; THETA(4) K23
  (0.001,0.3) 	 ;; THETA(5) K32
  ;; init for K23~WT   ;; are initial estimates for K23,K32,K24,K42 needed?
  ;;; is initial estimate for Volume a function of weight needed?
  ;;; is initial estimate for Volume a function of gender needed?


  (0.01,0.2) 		;; THETA(6)
$OMEGA   ;; must be one ETA/line
  0.2  		; ETA(1) CLEARANCE
$OMEGA 
  0.2 	; ETA(2) VOLUME
  ;; optional $OMEGA blocks
  ;; optional initial estimates for ETA on KA


  ;; optional initial estimates for ETA on D1 and ALAG1

$SIGMA   

  0.3 	; EPS(1) proportional error
  0.3 	; EPS(2) additive error   ;; additive or proportional or combined
$EST METHOD=COND INTER MAX = 9999 MSFO=MSF1 
$COV UNCOND PRINT=E

;; Phenotype 
;; OrderedDict([('ADVAN', 1), ('K23~WT', 0), ('KAETA', 0), ('V2~WT', 0), ('V2~GENDER', 0), ('CL~WT', 0), ('CL~AGE', 0), ('ETAD1LAG', 0), ('D1LAG', 1), ('RESERR', 0)])
;; Genotype 
;; [1, 0, 0, 0, 0, 0, 0, 0, 1, 0]
;; Num non-influential tokens = 0