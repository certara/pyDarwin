
################
Troubleshooting
################

******************
Installation
******************

.. _installation_troubleshooting:

**SSL: CERTIFICATE_VERIFY_FAILED**

The likely cause of this error is you are installing behind a company/corporate firewall. The solution is
to add `--trusted-host` params into the installation command.

.. code:: python

    pip install pyDarwin-Certara --index-url https://certara.jfrog.io/artifactory/api/pypi/certara-pypi-release-public/simple --extra-index-url https://pypi.python.org/simple/ --trusted-host=pypi.python.org --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --trusted-host=certara.jfrog.io --trusted-host=jfrog-prod-use1-shared-virginia-main.s3.amazonaws.com

**Cannot install updated version**

If you are attempting to update pyDarwin-Certara and do not see that the latest version has been installed, please specify the additional `--upgrade` argument to the installation command.

.. code:: python

    pip install pyDarwin-Certara --upgrade --index-url https://certara.jfrog.io/artifactory/api/pypi/certara-pypi-release-public/simple --extra-index-url https://pypi.python.org/simple/ --trusted-host=pypi.python.org --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --trusted-host=certara.jfrog.io --trusted-host=jfrog-prod-use1-shared-virginia-main.s3.amazonaws.com

*******************
Error Messages
*******************

.. _Non integer index to THETA/OMEGA/SIGMA:

**Non integer index to THETA/OMEGA/SIGMA**

The error from NONMEM (nmtran) will look something like:

::
    
   AN ERROR WAS FOUND ON LINE 11 AT THE APPROXIMATE POSITION NOTED:
   TVV2=THETA(2) *EXP(GENDER*THETA(V~GENDER))
   
To parse the text in the initial estimates blocks (THETA, OMEGA, and SIGMA), the user MUST include token stem text as a comment (i.e., after ";") in the tokens file. There is 
no other way to identify which initial estimates are to be associated with which THETA. 

For example, if a token stem has two THETAs and the text in the $PK block is:

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

**can't open results.csv** 

pyDarwin opens and closes the :file:`results.csv` file with each model completed. 
If it is opened in an application that "locks" it, e.g., Excel, an exception will occur. The workaround is to 
copy the file to another file (e.g., ``cp results.csv results1.csv``), then open the copied file.

*******************
Post Run Code
*******************

**FCON overwritten when using post run R code**

pyDarwin reads the FCON file to obtain the OMEGA structure and number of estimated OMEGAs. If you do another run in
the same folder, the FCON file will be overwritten. If using post run R code, it is suggested to add something similar
to below:

::

    dir.create("simFolder")
    setwd("simFolder")
    writelines("myNewControl.mod", mymyNewControl)
    shell("nmfe75 myNewControl.mod myNewControl.lst")
    setwd("..")

  
