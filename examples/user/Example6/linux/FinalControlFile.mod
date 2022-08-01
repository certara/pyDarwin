$PROBLEM    2 compartment fitting
$INPUT       ID TIME AMT DROP DV MDV EVID WT AGE SEX BUN SCR OCC CRCL COV1 COV2

$DATA      /home/ppolozov/darwin/examples/user/Example6/dmag_with_period.csv IGNORE=@

$SUBROUTINE ADVAN4 ;; advan4 
$PK      
  CWTKGONE = WT/81  ;; WEIGHT CENTERED ON ONE
  CWTKGZERO = WT-81 ;; WEIGHT CENTERED ON ZERO
  CAGE = AGE/60     ;; AGE CENTERED ON ONE
  CCRCL = CRCL/85.6 ;; CRCL CENTERD ON ONE
  CCOV1 = COV1-15.4 ;; COVARIATE 1 CENTERED ON ZERO
  IOVV = 0  
  TVV2=THETA(1)      *EXP(IOVV)
  V2=TVV2*EXP(ETA(2))   
  IF(OCC.EQ.1) IOVCL = ETA(4) 
  IF(OCC.EQ.2) IOVCL = ETA(5) 
  IF(OCC.EQ.3) IOVCL = ETA(6)
  TVCL= THETA(3) *EXP(CWTKGZERO*THETA(6))  *CCRCL**THETA(7)  *EXP(IOVCL)
  CL=TVCL*EXP(ETA(1)) 

  K=CL/V2      
  K23=THETA(4)
  K32=THETA(5)  
  ALAG1=THETA(8)
  ;; No D1    
  TVKA=THETA(2) 
  KA=TVKA  *EXP(ETA(3))     
  S2 = V2 
$ERROR     	
  REP = IREP      
  IPRED =F  
  IOBS = F *EXP(EPS(1))+EPS(2)
  Y=IOBS
$THETA      
  (0.001,100) 	; THETA(1) V  UNITS = L
  (0.001, 10) 	; THETA(2) KA UNITS = 1/HR    
  (0.001,20)	; THETA(3) CL UNITS =  L/HR
  (0.001,0.02)  	 ; THETA(4) K23 
  (0.001,0.3) 	 ; THETA(5) K32 
  ; init for K23~WT    




  (-1,0.01) 	; THETA(6) EXPONENTIAL clearance~WT  

  (-4,-0.2) 	; THETA(7) POWER clearance~CRCL 

  (0.001,0.1) 	; THETA(8) ALAG1   
$OMEGA    
  0.1  		; ETA(1) CLEARANCE 
  0.4  		; ETA(2) VOLUME  
$OMEGA ;; 2nd OMEGA block 
  0.1		; ETA(3) ETA ON KA  

$OMEGA BLOCK(1) ; ETA(4)
  0.1 
$OMEGA BLOCK SAME ; ETA(5)
$OMEGA BLOCK SAME ; ETA(6)
  ;; no iov ON V
$SIGMA   
  0.1 	; EPS(1) proportional error
  100 	; EPS(2) additive error

$EST METHOD=COND INTER MAX = 9999 MSFO=MSF1 PRINT = 10
$COV UNCOND PRINT=E  PRECOND=1 PRECONDS=TOS  MATRIX = R

$TABLE REP ID TIME DV EVID NOPRINT FILE = ORG.DAT ONEHEADER NOAPPEND

$PROB SIMULATION FOR CMAX

$INPUT       ID TIME AMT DROP DV MDV EVID WT AGE SEX BUN SCR OCC CRCL COV1 COV2
$DATA      /home/ppolozov/darwin/examples/user/Example6/dmag_with_period.csv IGNORE=@  REWIND
$MSFI = MSF1
$SIMULATION (1) ONLYSIM  
$TABLE REP ID TIME IOBS EVID  NOAPPEND NOPRINT FILE = SIM.DAT ONEHEADER NOAPPEND

;; Phenotype 
;; OrderedDict([('ADVAN', 1), ('K23~WT', 0), ('KAETA', 1), ('V2~WT', 0), ('V2~AGE', 0), ('V2~SEX', 0), ('V2~COV2', 0), ('CL~WT', 2), ('CL~AGE', 0), ('CL~CRCL', 1), ('CL~COV1', 0), ('IOVCL', 0), ('IOVV', 1), ('INITCL', 1), ('ETAD1LAG', 0), ('D1LAG', 0), ('RESERR', 0)])
;; Genotype 
;; [0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0]
;; Num non-influential tokens = 0