Trouble shooting
-------------------

.. _Non integer index to THETA/OMEGA/SIGMA:

**Non integer index to THETA/OMEGA/SIGMA**

The error from NONMEM (nmtran) will be something like

::
    
   AN ERROR WAS FOUND ON LINE 11 AT THE APPROXIMATE POSITION NOTED:
   TVV2=THETA(2) *EXP(GENDER*THETA(V~GENDER))
   
In order to parse the text in the initial estimates blocks (THETA, OMEGA and SIGMA) the user MUST include token stem text as a comment (i.e. after ";") in the tokens file. There is 
no other way to identify which intial estimates are to be associated with which THETA. 
E.g, if an token stem as two THETAs:


Effect = THETA(EMAX) * CONC/(THETA(EC50) + CONC)
for the text in the $PK block, then code to be put into the $THETA block will be:


The resulting $THETA block for this initial feature will be:

::

 "  (0,100) \\t; THETA(EMAX) "
 "  (0,1000) \\t; THETA(EC50) "

Without this THETA(EMAX) and THETA(EC50) as a comment, there wouldn't be any way to identify which initial estiamate is to be associated with which 
THETA. Note that NONMEM assigns THETAs by sequence of appearance in $THETA. Given that the actual indices for THETA cannot be determined until the control file 
is created, this approach would lead to ambiguity. Each initial estimate must be on a new line and include the THETA (or ETA or EPS) + parameter identifier.

Other covariate effects are coded similarly. 

Failing to do so will result in pyDarwin not finding an appropriate initial estimate for that parameter and then being unable to calculate the appropriate index.

.. _can't delete temp_dir:


**can't delete temp_dir** 

To insure valid results all folders that pyDarwin uses (output dir, temp dir and working dir) are removed prior to start. If that folder, or a file in the folder is open pyDarwin will be unable 
to remove it.




.. _can't open r:

**can't open results.csv** pyDarwin opens and closes the models.json, results.csv and messages.txt file with each model completed. This is done so that if the search 
is interupted it can be restarted with a little lost time as possible, and so the use can read and parse the messages.txt file to monitor progress.


  
