$PROBLEM    2 compartment fitting
$INPUT       ID TIME AMT DV WTKG GENDER AGE DROP
$DATA      C:\workspace\ffe\user\Example1/datalarge.csv IGNORE=@

$SUBROUTINE ADVAN2
$ABBR DERIV2=NO
$PK      
  CWTKG = WTKG/70  ;; CENTERED ON ONE 
  CAGE = AGE/40
  ;; thetas out of sequence
  TVV2=THETA(2) 
  V2=TVV2*EXP(ETA(2)) 
  TVCL= THETA(1)   
  CL=TVCL*EXP(ETA(1)) 
  K=CL/V2  
  TVKA=THETA(3) 
  KA=TVKA    
  S2 	= V2/1000 
  ALAG1 = THETA(4)
$ERROR     
  REP = IREP      
  IPRED =F  
  IOBS = F *EXP(EPS(1))+EPS(2)
  Y=IOBS
$THETA  ;; must be one THETA per line.
  (0.001,100)	; THETA(1) CL UNITS =  L/HR
  (0.001,500) 	; THETA(2) V  UNITS = L
  (0.001,2) 	; THETA(3) KA UNITS = 1/HR  

  ;;; comment must consist of more than one word
  ;;; otherwise it's a definition, and it will push you back

  (0, 0.1,3) 	; THETA(4) ALAG1 

$OMEGA   ;; must be one ETA/line
  0.2  		; ETA(1) CLEARANCE
  ;; test for comments in blocks
  0.2  	; ETA(2) VOLUME
  ;; optional $OMEGA blocks


$SIGMA   

  0.3 	; EPS(1) proportional error
  0.3 	; EPS(2) additive error 
$EST METHOD=COND INTER MAX = 9999 MSFO=MSF1 
$COV UNCOND PRINT=E

;; Phenotype 
;; OrderedDict([('V2~WT', 1), ('V2~GENDER', 0), ('CL~WT', 1), ('KAETA', 1), ('ALAG', 0), ('RESERR', 1)])
;; Genotype 
;; [1, 0, 1, 1, 0, 1]
;; Num non-influential tokens = 0