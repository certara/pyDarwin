
################
Troubleshooting
################

.. _installation_troubleshooting:

******************
Installation
******************

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
to the following:

::

    dir.create("simFolder")
    setwd("simFolder")
    writelines("myNewControl.mod", mymyNewControl)
    shell("nmfe75 myNewControl.mod myNewControl.lst")
    setwd("..")

  

.. _troubleshooting_grid_search:

*******************
Grid Execution
*******************

**No such file or directory: 'run_results/NM_1_01.json'**

When you see something like below in either console output (local search, grid model runs) or the search job output file it usually indicates some misconfiguration:

::
  
  Traceback (most recent call last):
    File "/home/user01/darwin/venv/lib/python3.10/site-packages/darwin/utils.py", line 324, in _pump
      pumped, rest = self._fn(tank)
    File "/home/user01/darwin/venv/lib/python3.10/site-packages/darwin/grid/GridRunManager.py", line 60, in _gather_results
      finished, remaining = self.grid_adapter.poll_model_runs(submitted)
    File "/home/user01/darwin/venv/lib/python3.10/site-packages/darwin/grid/GenericGridAdapter.py", line 116, in poll_model_runs
      run = json_to_run(job.output_path)
    File "/home/user01/darwin/venv/lib/python3.10/site-packages/darwin/ModelRun.py", line 614, in json_to_run
      with open(file) as f:
  FileNotFoundError: [Errno 2] No such file or directory: '/home/user01/pydarwin/example/run_results/NM_1_01.json'

| Check corresponding err- and out-files.
| If it managed to run pyDarwin, then there will be some output in the out-file:

::
  
  less /home/user01/pydarwin/example/run_results/NM_1_01.out

  [05:57:54] Options file found at /home/user01/darwin/example/options.json
  [05:57:54] !!! NMFE path '/opt/nm751/util/nmfe75' seems to be missing
  /home/user01/pydarwin/example/run_results/NM_1_01.out (END)

Otherwise see the err-file:

::
  
  less /home/user01/pydarwin/example/run_results/NM_1_01.err

  /var/spool/slurmd/job51925/slurm_script: line 4: /home/user01/darwin/venv/bin/python: No such file or directory
  /home/user01/pydarwin/example/run_results/NM_1_01.err (END)

::
  
  less /home/user01/pydarwin/example/run_results/NM_1_01.err

  /home/user01/darwin/venv/bin/python: Error while finding module specification for 'darwin.run_model' (ModuleNotFoundError: No module named 'darwin')
  /home/user01/pydarwin/example/run_results/NM_1_01.err (END)

The latter means you either picked the wrong venv, didn't install pyDarwin, or didn't :ref:`switch to the appropriate module <customizing_python_script>`.

**Failed search job -- SGE**

The search job can fail due to different reasons. Here we address two most common kinds: the job wasn't enqueued and the job failed after it was run.

::
  
  (venv) [user01@sge-grid darwin]$ python -m darwin.grid.run_search example
  [15:29:28] Options file found at options.json
  Your job 463046 ("example") has been submitted

  (venv) [user01@sge-grid darwin]$ qstat
  job-ID  prior   name       user         state submit/start at     queue                          slots ja-task-ID
  -----------------------------------------------------------------------------------------------------------------
   463046 0.55500 example    user01       Eqw   07/07/2025 15:29:28                                    1

  (venv) [user01@sge-grid darwin]$ qstat -j 463046
  ==============================================================
  job_number:                 463046
  exec_file:                  job_scripts/463046
  submission_time:            Mon Jul  7 15:29:28 2025
  owner:                      user01
  uid:                        51162
  group:                      pmx
  gid:                        1520
  sge_o_home:                 /home/user01
  sge_o_log_name:             user01
  sge_o_shell:                /bin/bash
  sge_o_workdir:              /home/user01/darwin/example
  sge_o_host:                 sge-grid
  account:                    sge
  cwd:                        example
  stderr_path_list:           NONE:NONE:example.err
  notify:                     FALSE
  job_name:                   example
  stdout_path_list:           NONE:NONE:example.out
  jobshare:                   0
  env_list:                   TERM=NONE
  job_args:                   -m,darwin.run_search_in_folder,example
  script_file:                /home/user01/darwin/venv2/bin/python
  binding:                    NONE
  job_type:                   binary
  error reason          1:      07/07/2025 15:29:36 [51162:2714234]: error: can't chdir to example: No such file or directory
  scheduling info:            (Collecting of scheduler job information is turned off)

Here you can see the job wasn't enqueued due to an invalid working directory.
When a job is stuck in this state, you can examine it with ``qstat -j``.

.. note::
  This particular issue (passing relative path to the search directory) was fixed in pyDarwin 3.1.0, but there may be other issues leading to the same outcome.

If the job was successfully enqueued but failed to run, it will transit to the finished state.

::

  (venv) [user01@sge-grid darwin]$ qstat -s z
  job-ID  prior   name       user         state submit/start at     queue                          slots ja-task-ID
  -----------------------------------------------------------------------------------------------------------------
   463047 0.00000 example    user01       z     07/07/2025 15:40:12                                    1

``qstat -j`` won't find this job, but you can peek into ``example.err`` and ``example.out``.


**Failed search job -- Slurm**

Similar to SGE.

::

  (venv) [user01@slurm-grid darwin]$ python -m darwin.grid.run_search_in_folder example
  [06:09:56] Options file found at options.json
  Submitted batch job 51967

  (venv) [user01@slurm-grid darwin]$ python -m darwin.grid.run_search_in_folder /home/user01/darwin/example
  [06:14:55] Options file found at options.json
  Submitted batch job 51968

  (venv) [user01@slurm-grid darwin]$ squeue -t F
               JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
               51967    slgrid  example   user01  F       0:00      1 (JobLaunchFailure)
               51968    slgrid  example   user01  F       0:00      1 (NonZeroExitCode)

Note the (REASON).

::

  (venv) [user01@slurm-grid darwin]$ scontrol show job 51967
  JobId=51967 JobName=example
     <...>
     WorkDir=/home/user01/darwin/example
     StdErr=/home/user01/darwin/example/example/example.err
     StdIn=/dev/null
     StdOut=/home/user01/darwin/example/example/example.out
     Power=

  (venv) [user01@slurm-grid darwin]$ less /home/user01/darwin/example/example/example.err
  /home/user01/darwin/example/example/example.err: No such file or directory

.. note::
  This particular issue (passing relative path to the search directory) was fixed in pyDarwin 3.1.0, but there may be other issues leading to the same outcome.

::

  (venv) [user01@slurm-grid darwin]$ scontrol show job 51968
  JobId=51968 JobName=example
     <...>
     WorkDir=/home/user01/darwin/example
     StdErr=/home/user01/darwin/example/example.err
     StdIn=/dev/null
     StdOut=/home/user01/darwin/example/example.out
     Power=

  (venv) [user01@slurm-grid darwin]$ less /home/user01/darwin/example/example.err
  /var/spool/slurmd/job51968/slurm_script: line 4: /home/user01/darwin/venv/bin/python: No such file or directory
  /home/user01/darwin/example/example.err (END)

::

  (venv) [user01@slurm-grid darwin]$ less /home/user01/darwin/example/example.err
  /home/user01/darwin/venv/bin/python: Error while finding module specification for 'darwin.run_search_in_folder' (ModuleNotFoundError: No module named 'darwin')
  /home/user01/darwin/example/example.err (END)

The latter means you either picked the wrong venv, didn't install pyDarwin, or didn't :ref:`switch to the appropriate module <customizing_python_script>`.
