
Required Files
==============================================
 
.. _startRequiredFiles:
 
 
The same 3 files are required for any search, whether exhausitve, GA, GP, RF or GBRF. Which algorithm is used is defined in the options file
 
.. _The template file:

The Template File
~~~~~~~~~~~~~~~~~~~
The template file is a plain ASCII text file. it is the framework for the construction of the NONMEM control files. 
Typically, the structure will be quite similar to a NONMEM control file, with all of the 
usual blocks, e.g. $PROB, $INPUT, $DATA, $SUBS, $PK, $ERROR, $THETA, $OMEGA, $SIGMA, $EST. However, this format is 
completely flexible and entire blocks may be missing from the template file (to be provided from the `The tokens file`_)

The difference between a standard NONMEM control file and the temlate file is that the user will define code 
segments in the temlate file that will be replaced by other text. These code segments are refered to as "token keys". 
Tokens keys come in sets, as in most case several code segements will need to be replace together to generate syntacatically 
correct code. The syntax for a token key is:

{Token_stem[N]}

Where Token_stem is a unique identified for that token set and N is which target text is to be substituted. An 
example is useful.

Assume the user would like to consider 1 compartment (ADVAN1) and 2 compartment (ADVAN3) as candidates for the structural model. 
The relevant template file for this might be:

$SUBS {ADVAN[1]}

.

.

$PK

.

.

.

{ADVAN[2]}

.

.

.

$THETA

(0,1) ; Volume - fixed THETA - always appears

(0,1) ; Clearance - fixed THETA - always appears

{ADVAN[3]}

For a one compartment model the following substutions would be made:

{ADVAN[1]} -> ADVAN1

{ADVAN[2]} -> ;; 1 compartment

{ADVAN[3]} -> ;; 1 compartment

and for 2 compartment:

{ADVAN[1]} -> ADVAN3

{ADVAN[2]} -> K = THETA(?) ;; 2 compartment

{ADVAN[3]} ->(0,0.5)) ;; 2 compartment non fixed THETA

These sets of tokens are called tokens sets (2 tokens sets in this example one for ADVAN1, one for ADVAN3). The group of token sets 
is called a token group. In this example {ADVAN[1]} is the token key, and for the first set of options the text "ADVAN1" is refered to as 
the token text. Each set consists of key-text pairs: 

token keys (described above) and 

token text

The token key in the template file is replaced by the token text, specified in the tokens file. 
Which set of token key-text pairs is substitituted is determined by the search algorithm.  

Note that the THETA indices cannot be determined until the final control file is defined, as THETAs may be included in one and not another. 
For this reason, all fixed initial estimates in the $THETA block MUST occur before the THETA values that are not fixed. This is so the 
algorithm can parse the resulting file and correctly calculate the appropriate THETA (and ETA and EPS) indices.





.. _The tokens file:

The Tokens File
~~~~~~~~~~~~~~~~~~~
 
.. _The options file:

Options File
~~~~~~~~~~~~~~~~~~~


Note that the the options are saved to a json file. Json supports string, numeric and Boolen (true|false)
Options include

author: String, Author, currently not used, Default - blank

homeDir: String, Linux style for the home directory, generation/interation subfolders will be placed here, Required

algorithm: String, Required GA (
:ref:`Genetic Algorithm` ) EX (
:ref:`Exhaustive Search` ) GP (
:ref:`Gaussian Process (Bayesian Optimization)` ) RF (
:ref:`Random Forest`  ) GBRT (
:ref:`Gradient Boosted Random Tree`). Which algorithm to use.

random_seed: Integer, required if using GA/GP/RF or GBRT, 

population_size: Integer, required if using algorithm other than exhaustive search

nmfePath: String, required, path to nmfe??.bat file. Currently supported are nmfe74.bat and nmfe75.bat. 

num_parallel: Integer, optional. Number of NONMEM models to run in parallel, Default = 4

num_generations: Integer, required if using GA/GP/RF or GBRT

niche_penalty: Numeric, required if using GA. Require for calculation of the crowding penalty. 
The niche penalty is calculate by first calculating the "distance matrix", the pair wise Mikowski distance (https://en.wikipedia.org/wiki/Minkowski_distance) from the present model to all other models in the generation. 
The "crowding" quantity is then calculated a the sum of:
1 - (distance/niche_radius)**sharing_alpha for all other models in the generation for which the Mikowski distance is less than the niche radius. 
Finally, the penalty is calculated as:
exp((crowding-1)*niche_penalty)-1
The objective of using a niche penalty is to maintain diversity of models, to avoid premature convergence of the search, by penalizing when models are too 
similar to other models in the current generation.
A typical value for the penalty is 10.

num_niches: Integer, required if using GA.

niche_radius: Numeric, required if using GA. A typical value for niche_radius is 2.

THETAPenalty: Numeric, required  

OMEGAPenalty: Numeric, required  

SIGMAPenalty: Numeric, required  

conditionNumberPenalty: Numeric, required   

covariancePenalty: Numeric, required 

covergencePenalty: Numeric, required 

correlationLimit: Numeric, required

correlationPenalty: Numeric, required. Penalty if the absolute value of any off diagonal of the OMEGA matrix exceeds correlationLimit

crash_value: numeric, required. The fitness/reward value to assign to a model that fails to complete. Typical value is 99999999, should be larger than that 
expected from any model that does complete.  

crossoverRate: 0.95, 

downhill_q:5,

elitist_num: 4,

mutationRate: 0.95, 

attribute_mutation_probability: 0.1, 

input_model_json: None, 

max_model_list_size: Integer, required. The algorithm generates models in batches. For exhausitve search in particular, this may result in a very large number of 
model (100,000's?). This can lead to memory issues with a very large array of large objects. To address this, the user can (and should) define that only a 
limited number of models will be gnerated at a time, all those model run, then the list recreated. A typical value for a capable computer is 10,000.

mutate: string, required for GA. What method to use for mutation, only available option is flipBit

non_influential_tokens_penalty: 0.00001,

remove_run_dir: Boolean, options (false), Delete entire run directory. By default, all F*, WKS* file, the executable file and other non-essential files will be deleted.
NONMEM $TABLE files (unless deleted as F* or WKS*) will be retained. If large $TABLE files are written for each run, a great deal of disk space can be required. If $TABLE 
file are needed to postRunRCode, they can be deleted in the user provided R code to preserve disc space.

fullExhaustiveSearch_qdownhill: Boolean, required. The option exists to run a local exhausitve search with 2 bit radius after each dowhill search. Note that for large dimension 
search space, this can be time consuming. The number of models in each step is (dimension*dimension)/2 + dimension/2, where dimension is the number of bits Required
to define the search space.

final_fullExhaustiveSearch:  Boolean, required. The option exists to run a local exhausitve search with 2 bit radius at the end of the search. Note that for large dimension 
search space, this can be time consuming. The number of models in each step is (dimension*dimension)/2 + dimension/2, where dimension is the number of bits Required
to define the search space.

selection: string, required for GA. The algorithm used for the selection step in GA, only currently available algorithm is tournament.

selection_size: integer, required for GA. How many "parents" to select for the tournament  

sharing_alpha: 0.1,  

timeout_sec: numeric (seconds), optional(1200);. NONMEM run will be terminated (and result will be CRASH) if run time exceeds this. 

useR: boolean, optional (false). Whether to call user provided R code after each NONMEM run. If true, postRunRCode must provide path to R code

postRunRCode: string, required if useR is true. Path to R code to be run after each NONMEM run. Required return values a vector of 
length 2. The first will be a numeric (or character that can be cast as numeric) that will be added to the fitness/reward values. The 2nd is a character 
string that will be appended to the NONMEM output file.

usePython: boolean, optional (false). Whether to call user provided Python code after each NONMEM run. If true, postRunPythonCode must provide path to R code   

postRunPythonCode: string, required if usePython is true.  
crossoverOperator: cxOnePoint ,

NM_priority_class: string, optional, default = normal. Recommended to maintain interface responsiveness is below_normal,

search_omega_bands: false,

max_omega_band_width: integer, required if seach_omega_bands is true. Unfortunately is was not possible to query the temlate file and token groups to, in general,
determine the maximum size of all $OMEGA blocks. Therefore, the user is required to provide the maximum number of off diagonal bands that would be searched. This is 
required to determine the number of bits to be included in the bit string/search space.

