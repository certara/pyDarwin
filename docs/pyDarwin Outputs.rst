pyDarwin Outputs
-----------------------

Command Line output
---------------------

When pyDarwin first starts, it starts by confirming that key files are available. These files include:

#. The template file
#. The tokens file
#. The options file
#. nmfe??.bat - executes NONMEM
#. The data file(s) for the first control that is intiated
#. If post run R code is requested, Rscript.exe


The start up output also lists the location of:
 
#. Data dir - folder where datasets are located. It is recommended that this be an absolute path
#. Project working dir - folder where template, token and options files are located, this is not set by the user
#. Project temp dir - root folder where model file will be found, if the option is not set to remove them
#. Project output dir - folder where all the files that considered as results will be put, such as results.csv and Final* files. 
#. Where intermediate output will be written (e.g. u:/user/example2/output\results.csv)
#. Where models will be saved to (e.g., u:/user/example2/working\models.json)
#. NMFE??.bat file
#. Rscript.exe, if used


When run from command line (`or from Visual Studio Code <https://code.visualstudio.com/>`_) pyDarwin provides significant output about whether individual models 
have executed successfully. A typical line of output might be::

    [16:22:11] Iteration = 1, Model     1,       Done,    fitness = 123.34,    message =  No important warnings


The columns in this output are::
    
    [Time of completion] Iteration = Iteration/generation, Model     Model Number,       Final Staus,    fitness = fitness/reward,    message =  Messages from NMTRAN

If there are messages from NONMEM execution, these will also be written to command line, as well as if excecution failed, and, if request, if R execution failed.

If the XXXXXX is not set to true, the NONMEM control file, output file and other key files can be found in {temp_dir}\Iteration/generation\Model Number for debugging. 

File output
---------------

The file output from pyDarwin is generated real time. That is, as soon as a model is finished, the results are written to the results.csv and models.json files. Similarly, 
messages (what appears on the command line output) is written continuously to the messages.txt file.

**NOTE**. As these files are continuous opened, written to and closed, an exception will occur if they are opened in an application the "locks" them, e.g. Excel. If, for example 
the results.csv file is opened in Excel, the next time pyDarwin trys to open it to write the next model output, an exception will occur. The work around is to copy the file to 
another file (e.g., cp results.csv results1.csv), then open the copied file.

Messages.txt
-----------------

The messages.txt file will be found in the working dir. This file contents is the same as that output to the command line


models.json
-----------------

The models.json will contain the key output from all models that are run. This is not a very user friendly file, as a fairly complex json. The primary (maybe only) use 
for this file is if a search is interupted, it can be restarted, and the contents of this file read in, rather than rerunning all of the models. If the goal is to make simple diagnostics 
of the search progress, the results.csv file is likely more useful.


results.csv
----------------

The results.csv file contains key information about all models that are run in a more user-friendly format. This file can be used to make plots to monitor progress of the search 
or to identify models that had unexpected results (Crashes)

