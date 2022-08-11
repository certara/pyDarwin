
################
Troubleshooting
################

.. _Non integer index to THETA/OMEGA/SIGMA:

**Non integer index to THETA/OMEGA/SIGMA**

The error from NONMEM (nmtran) will look something like:

::
    
   AN ERROR WAS FOUND ON LINE 11 AT THE APPROXIMATE POSITION NOTED:
   TVV2=THETA(2) *EXP(GENDER*THETA(V~GENDER))
   
To parse the text in the initial estimates blocks (THETA, OMEGA, and SIGMA), the user MUST include token stem text as a comment (i.e., after ";") in the tokens file. There is 
no other way to identify which initial estimates are to be associated with which THETA. 

For example, if a token stem as two THETAs and the text in the $PK block is:

::
   
   Effect = THETA(EMAX) * CONC/(THETA(EC50) + CONC)

the required $THETA block for initial estimates for this feature will be:

::

 "  (0,100) \\t; THETA(EMAX) "
 "  (0,1000) \\t; THETA(EC50) "

Without the THETA(EMAX) and THETA(EC50) as comments, there would be no way to identify which initial estimate is to be associated with which 
THETA. Note that NONMEM assigns THETAs by sequence of appearance in $THETA. Given that the actual indices for THETA cannot be determined until the control file 
is created, this approach would lead to ambiguity, or at least confusion, about which initial estimate was associated with which THETA index. 
Each initial estimate must be on a new line and include the THETA (or ETA or EPS) + parameter identifier as a comment.

Failing to do so will result in ``pyDarwin`` not finding an appropriate initial estimate for that parameter and then being unable to calculate the appropriate index.

.. _can't delete temp_dir:


**can't delete temp_dir** 

To ensure valid results, all folders that ``pyDarwin`` uses (output dir, temp dir, and working dir) are removed prior to start. If one of those folders,
or a file in a folder is open, ``pyDarwin`` will be unable to remove it.

.. _can't access messages.txt:


**can't access messages.txt**

::
   
   Exception has occurred: PermissionError (note: full exception trace is shown but execution is paused at: <module>)
   [WinError 32] The process cannot access the file because it is being used by another process: 'c:\\pydarwin\\Example6\\messages.txt'

This error occurs when ``run_search`` is called from python in Visual Studio Code without the "if __name__ == '__main__': " `syntax <https://stackoverflow.com/questions/419163/what-does-if-name-main-do>`_. 

::
   
   "if __name__ == '__main__': "

isn't used to call ``run_search``, it tries to reopen messages.txt and fails.

.. _can't open r:

**can't open results.csv** pyDarwin opens and closes the :file:`results.csv` file with each model completed. 
If it is opened in an application the "locks" it, e.g., Excel, an exception will occur. The work around is to 
copy the file to another file (e.g., cp results.csv results1.csv), then open the copied file.



  
