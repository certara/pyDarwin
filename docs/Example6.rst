

Example 6: PK Model, DMAG by RF with post-run Python code
=========================================================

Example 6 is again the same data and search as Example 4 and 5, but using :ref:`Random Forest<RF_desc>` for search, and python code for 
post run PPC penalty calculation.
  
As before, that to run in the enviroment used for this example, the directories are set to:

::
        
    "working_dir": "u:/pyDarwin/example5/working",
    "temp_dir": "u:/pyDarwin/example5/rundir",
    "output_dir": "u:/pyDarwin/example5/output",

It is recommended that the user set the directories to something appropriate for their enviroment. If directories are not set 
the default is:

::

	{user_dir}\pydarwin\{project_name}

In either case, the folder names are given in the initial and final output to facilitate finding the files and debuggins.


.. _startpk6:

::

        
    [06:15:40] Options file found at ..\examples\user\Example6\options.json
    [06:15:40] Preparing project working folder...
    [06:15:40] Preparing project output folder...
    [06:15:40] Preparing project temp folder...
    [06:15:40] Model run priority is below_normal
    [06:15:40] Using darwin.MemoryModelCache
    [06:15:40] Project dir: C:\fda\pyDarwin\examples\user\Example6
    [06:15:40] Data dir: C:\fda\pyDarwin\examples\user\Example6
    [06:15:40] Project working dir: u:/pyDarwin/example6/working
    [06:15:40] Project temp dir: u:/pyDarwin/example6/rundir
    [06:15:40] Project output dir: u:/pyDarwin/example6/output
    [06:15:40] Writing intermediate output to u:/pyDarwin/example6/output\results.csv
    [06:15:40] Models will be saved in u:/pyDarwin/example6/working\models.json
    [06:15:40] Template file found at ..\examples\user\Example6\template.txt
    [06:15:40] Tokens file found at ..\examples\user\Example6\tokens.json
    [06:15:40] Search start time = Tue Aug  2 06:15:40 2022
    [06:15:40] Algorithm is RF
