# FDA-OGD-ML
Research repo for NONMEM GA 
Python solution for using several machine learning methods to search a candidate solution space for the optimal population models in NONMEM. 
Requirements are a NONMEM installation, with nmfe??.bat available. R is optional.
Three files are required to define the search:
    Template file (example5_template.txt) - basic shell for NONMEM control files
    Tokens file (example5_tokens.json) - json file describing the dimensions of the search space and the options in each dimension
    Options file (exhaustiveoptions.json, gaoptions.json, gpoptions.json, rfoptions.json, gbrtoptions.json)
 The options file are (nearly) identical except which algorithm is implemented:
     exhaustive.json - full exhaustive search of candidate model space (12,690 models)
     gaoptions.json - Genetic Algorithm - implemented with deap package (https://github.com/deap/deap)
     gpoptions.json - Gaussian process/Bayesian optimization - implemented with scikit-optimize (https://scikit-optimize.github.io/stable/index.html)
     rfoptions.json - Random forest optimization - implemented with scikit-optimize (https://scikit-optimize.github.io/stable/index.html)
     gbrtoptions.json - Gradient boosted random tree optimization - implemented with scikit-optimize (https://scikit-optimize.github.io/stable/index.html)
     
 The optimization can be run from the main.py module, in Visual studio code, load the folder, open the main.py and hit F5 (note that the paths to the three arguments
 are absolute paths, the first two arguments are specified in the launch.json file in the .vscode folder. Currently this has been tested only on Windows, likely signifcant
 changes will be needed to run on Linux.
 
