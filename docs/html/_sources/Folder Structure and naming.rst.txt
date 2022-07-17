File Structure and Naming
==========================

NONMEM control, executable and output file naming

Saving NONMEM outputs
---------------------
NONMEM generates a great deal of file output. For a search of perhaps up to 10,000 models, this can become an isssue for disc space. 
By default, key NONMEM output files are retained. Most temporary files (e.g., FDATA, FCON) and the temp_dir are always removed to save disc space. 
In addition, the data file(s) are not copied to the run directory, but all models use the same copy of the data file(s).
Care should be take to not generate unneeded table files, as these can become quite large, and will not be removed by pyDarwin. 

File Structure
---------------
Three user define file locations can be set in the :ref:`options file<Options>`. In addition to the fodlers that are user defined
the project directory (project_dir) is the folder where template, token and options files are located. The user define folders are:

#. output_dir - Folder where all the files that considered as results will be put, such as results.csv and Final* files. Default value is working_dir/output. May make sense to be set to project_dir if version control of the project and the results is intended.

#. temp_dir - NONMEM models are run in subfolders of this folder Default value is working_dir/temp. May be deleted after search finished/stopped if remove_temp_dir is set to true.  

#. working_dir - Folder where all intermediate files will be created, such as models.json (model run cache), messages.txt (log file), Interim* files and stop files. Default value - %USER_HOME%/pydarwin/project_name where project name is defined in the :ref:`options file<Options>`
 

Model/folder naming
--------------------


A model stem is generated from the current generation/iteration and model number or the form NM_genration_model_num. For example, if this is iteration 2, model 3 the model stem would be 
NM_2_3. For the 1 bit downhill, the model stem is NM_generationDdownhillstep_modelnum, and for the 2 bit local search the model stem is NM_generationSdownhillstepSearchStep_modelnum. Final downhill 
model stem is NM_FNDDownhillStep_ModelNum. This model stem is then used to name the .exe file, the .mod file, the .lst file etc. This results in unique names for all models in the search. Models 
are also frequently duplicated. Duplicated files are not rerun, and so those will not appear in the file structure.

Run folders are similarly named for the generation/iteration and model number. Below is a folder tree for :ref:`Example 2<startpk2>`

.. figure:: FileStructure.png

Saving models
-------------

Model results are by default saved in a JSON file so that searches can be restarted or rerun with different algorithms more efficients. The name of the saved JSON file can be set by the user. A .csv 
file describing the course of the search is also save to results.csv. This file can be used to monitor the progress of the search. 
