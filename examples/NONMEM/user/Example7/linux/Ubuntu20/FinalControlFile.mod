
$PROBLEM    2 compartment fitting
$INPUT       ID TIME AMT DV WTKG GENDER AGE DROP
$DATA      /home/CertaraUser/examples/user/Example7/dataExample1.csv IGNORE=@

$SUBROUTINE ADVAN4
$ABBR DERIV2=NO
$PK      
  CWTKG = WTKG/70  ;; CENTERED ON ONE 
  CAGE = AGE/40
  TVV2=THETA(2) 
  V2=TVV2*EXP(ETA(4)) 
  TVCL= THETA(1)  
  CL=TVCL*EXP(ETA(3)) 
  K=CL/V2  
  TVKA=THETA(3) 
  KA=TVKA    
  S2 	= V2/1000 
  ALAG1 = THETA(6)
  K23=THETA(4)*EXP(ETA(1))
  K32 = THETA(5)*EXP(ETA(2))
$ERROR     
  REP = IREP      
  IPRED =F  
  IOBS = F*EXP(EPS(1)) + EPS(2)
  Y=IOBS
$THETA  ;; must be one THETA per line.
  (0.001,100)	; THETA(1) CL UNITS =  L/HR
  (0.001,500) 	; THETA(2) V  UNITS = L
  (0.001,2) 	; THETA(3) KA UNITS = 1/HR  
  (0,0.1)	; THETA(4) k23
  (0,0.1)	; THETA(5) k32

  (0, 0.1,3) 	; THETA(6) ALAG1  

$SIGMA   
  0.1
  10 


$EST METHOD=COND INTER MAX = 9999 MSFO=MSF1 
$COV UNCOND PRINT=E

;; Phenotype 
;; OrderedDict([('KAETA', 1), ('ALAG', 0)])
;; Genotype 
;; [1, 0, 0, 0, 0]
;; Num non-influential tokens = 0
$OMEGA   
  0.6  	 ; ETA(1) K23
  0.5  	; ETA(2) K32
$OMEGA  ;; block omega searched for bands
0.4 

$OMEGA  ;; block omega searched for bands
0.3 
