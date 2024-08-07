$PROBLEM    2 compartment fitting
$INPUT       ID TIME AMT DROP DV MDV EVID WT AGE SEX BUN SCR OCC CRCL COV1 COV2

$DATA      /home/jcraig/Example4/dataWithPeriod.csv IGNORE=@

$SUBROUTINE ADVAN4 ;; advan4 
$PK      
  CWTKGONE = WT/81  ;; WEIGHT CENTERED ON ONE
  CWTKGZERO = WT-81 ;; WEIGHT CENTERED ON ZERO
  CAGE = AGE/60     ;; AGE CENTERED ON ONE
  CCRCL = CRCL/85.6 ;; CRCL CENTERD ON ONE
  CCOV1 = COV1-15.4 ;; COVARIATE 1 CENTERED ON ZERO
  IF(OCC.EQ.1) IOVV = ETA(6) 
  IF(OCC.EQ.2) IOVV = ETA(7) 
  IF(OCC.EQ.3) IOVV = ETA(8)  
  TVV2=THETA(1) *EXP(CWTKGZERO*THETA(6)) *EXP(SEX*THETA(7))  *EXP(COV2*THETA(8))  *EXP(IOVV)
  V2=TVV2*EXP(ETA(2))   
  IOVCL = 0
  TVCL= THETA(3)   *CCRCL**THETA(9)  *EXP(IOVCL)
  CL=TVCL*EXP(ETA(1)) 

  K=CL/V2      
  K23=THETA(4)
  K32=THETA(5)  
  ALAG1=THETA(10)*EXP(ETA(4))
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
  (0.001,2)	; THETA(3) CL UNITS =  L/HR
  (0.001,0.02)  	 ; THETA(4) K23 
  (0.001,0.3) 	 ; THETA(5) K32 
  ; init for K23~WT    
  (-1,0.01) 	; THETA(6) EXPONENTIAL volume ~WT    
  (-4,0.1) 	; THETA(7) EXPONENTIAL volume~SEX    

  (-4,0.1) 	; THETA(8) EXPONENTIAL volume ~COV2 


  (-4,-0.2) 	; THETA(9) POWER clearance~CRCL 

  (0.001,0.1) 	; THETA(10) ALAG1   
$OMEGA    
  0.1  		; ETA(1) CLEARANCE 
  0.4  		; ETA(2) VOLUME  
$OMEGA ;; 2nd OMEGA block 
  0.1		; ETA(3) ETA ON KA  
$OMEGA  ;; diagonal OMEGA 
  0.1 		;; ETA(4) ETA ON ALAG1
  0.1 		;; ETA(5) ETA ON D1 
  ;; no iov ON CL
$OMEGA BLOCK(1) ; ETA(6)
  0.1 
$OMEGA BLOCK SAME ; ETA(7)
$OMEGA BLOCK SAME ; ETA(8)
$SIGMA   
  0.1 	; EPS(1) proportional error
  100 	; EPS(2) additive error

$EST METHOD=COND INTER MAX = 9999 MSFO=MSF1 PRINT = 10
$COV UNCOND PRINT=E  PRECOND=1 PRECONDS=TOS  MATRIX = R

$TABLE REP ID TIME DV EVID NOPRINT FILE = ORG.DAT ONEHEADER NOAPPEND

$PROB SIMULATION FOR CMAX

$INPUT       ID TIME AMT DROP DV MDV EVID WT AGE SEX BUN SCR OCC CRCL COV1 COV2
$DATA      /home/jcraig/Example4/dataWithPeriod.csv IGNORE=@  REWIND
$MSFI = MSF1
$SIMULATION (1) ONLYSIM  
$TABLE REP ID TIME IOBS EVID  NOAPPEND NOPRINT FILE = SIM.DAT ONEHEADER NOAPPEND

;; Phenotype 
;; OrderedDict([('ADVAN', 1), ('K23~WT', 0), ('KAETA', 1), ('V2~WT', 2), ('V2~AGE', 0), ('V2~SEX', 1), ('V2~COV2', 1), ('CL~WT', 0), ('CL~AGE', 0), ('CL~CRCL', 1), ('CL~COV1', 0), ('IOVCL', 1), ('IOVV', 0), ('INITCL', 0), ('ETAD1LAG', 3), ('D1LAG', 0), ('RESERR', 0)])
;; Genotype 
;; [0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0]
;; Num non-influential tokens = 0