# pyDarwin
Research repo for NONMEM GA 
Python solution for using several machine learning methods to search a candidate solution space for the optimal population models in NONMEM. 

## Python Packages

Execute the following command to install required Python package versions as specified in `required_packages.txt`

```
pip install -r required_packages.txt
```

Requirements are a NONMEM installation, with nmfe??.bat available. R is optional.
Three files are required to define the search:
1. Template file (e.g., example5_template.txt) - basic shell for NONMEM control files
2. Tokens file (e.g., example5_tokens.json) - json file describing the dimensions of the search space and the options in each dimension
3. Options file (e.g., exhaustiveoptions75.json, gaoptions.json, gpoptions.json, rfoptions.json, gbrtoptions.json)
Template file and token file are provided for a very small search (example_small_template??.txt and example_small_tokens??.json) or a small search (example5_template.txt and example5_tokens.json), for 1 or 2 $EST steps, and with and without $SIM.

 The options files are (nearly) identical except which algorithm is implemented and calling NONMEM 7.4 or 7.5:
 1. exhaustiveoptions74.json - full exhaustive search of candidate model space (12,960 models for large model, 64 for small model), uses NONMEM 7.4
 2. exhaustiveoptions75.json - full exhaustive search of candidate model space (12,960 models for large model, 64 for small model), uses NONMEM 7.5
 3. gaoptions.json - Genetic Algorithm - implemented with deap package (https://github.com/deap/deap)
 4. gpoptions.json - Gaussian process/Bayesian optimization - implemented with scikit-optimize (https://scikit-optimize.github.io/stable/index.html)
 5. rfoptions.json - Random forest optimization - implemented with scikit-optimize (https://scikit-optimize.github.io/stable/index.html)
 6. gbrtoptions.json - Gradient boosted random tree optimization - implemented with scikit-optimize (https://scikit-optimize.github.io/stable/index.html)

R and or Python code can be executed at the end of each run by including those options in the options json file, e.g.,:

	"useR": true,  
	"postRunRCode": "c:/fda/FDA-OGD-ML/simplefunc.r",  
	"usePython": true,  
	"postRunPythonCode": "simplefunc", 
 will run the code in c:/fda/FDA-OGD-ML/simplefunc.r and then the code in simplefunc.py after each run, with the calls returning a array/list of:
 [penalty, text_to_append_to_output]. Note that the python file name must NOT include the .py extenation and MUST be in the same folder as the main.py (a Python requirement, could, if needed have it someplace else and copy it to the folder that has main.py)
 
 The optimization can be run from the main.py module, in Visual studio code (VScode). To run from VScode, load the folder, open the main.py and hit F5 (note that the paths to the three arguments
 are absolute paths, the first two arguments are specified in the launch.json file in the .vscode folder. Currently this has been tested only on Windows, likely signifcant changes will be needed to run on Linux.
GA model selection requires the package DEAP (distributed Evolutionary Algorithm in python). This package is not compatible as of April 8, 2020 with Python versions greater than 3.8.1. Newer versions of Python can be used with DEAP, but requires recompiling the package. This repo has been tested with Python 3.7 and 3.8 and NONMEM 7.4 and NONMEM 7.5. Current version of Pharmpy is 0.62, seems to be compatability issues with Pharmpy  0.61.
 
For example_small_1est_withsim and example_small_2est_withsim, a simple plot is generated for each model, saved in the run directory
