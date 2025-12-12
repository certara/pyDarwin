General Principles
===================
In all cases, the post processing code is called from the directory where NONMEM or NLME has run, and before
any files are removed. Therefore, all output from NONMEM (i.e, $TABLE files, .ext, .xml, .phi etc) file and 
all NLME (i.e. dmp.txt, err?, nlme?engine.log, tables etc) will be available in the working directory for R 
or python to read. In addition, you can be confident that only files that pyDarwin/NONMEM/NLME put there 
will be there, there will be no additional files that might cause problems, if, for examples, you looked for 
the .xml NONMEM output (e.g., NM_1_01.xml) file in R with 

.. code-block:: R

    list.files(path = ".", pattern = "xml$")

this will return a list of files with the file extension .xml. Unless NONMEM put some additional files 
(e.g., from $TABLE) it will be the only .xml file present, and can then be used to extract model information. 
In NONMEM, the file name stem for output files such as the .lst, .ext and .xml file will 
be the same as the folder name, specifially NM_{Generation}_{model}, e.g., NM_1_01.xml for the xml file 
from generation 1, model 1 (if there are 10-99 models in the population).


The MOGA algorithm option in pyDarwin does not accept user defined code. MOGA3 requires user defined code.
In MOGA3, in all cases the code must return the required number of variables. python code must return 
2 arrays, one of objectives and one of constraints, from a function. For R, the same values 
are passed back to python by outputing them to the standard output in R with two print() statement. 
As for post processing code with other algorithms, the R code will be a script and the python code will 
be a function. 
The lengths of the vectors/arrays must match the number of objectives and constraints specified 
in the options.json file. Any other return values will result in a crash in pyDarwin. 
Practically, this means the use of error trapping and the return of "crash" values for exceptions with 
required structure; 2 vectors or arrays of length defined in the options.json file as,
`objectives and constraints <https://certara.github.io/pyDarwin/html/Options.html/>`_. 
Further, in the case of R, other output to the standard output (e.g., messages from loading packages) must 
be suppressed. 
In general post run R and python code is not compatible between NONMEM and NLME, as the output files are very 
different, e.g., the xml for NONMEM and the dmp.txt file for NLME.  The exception is when the post_process2 
function in python is used, and only information available in the pyDarwin run object is used. 
(:ref:`moga3-nlme_post_process2`).

In general, there is little reason to have more than one constraint in MOGA3, as the results from number 
of infeasible results can be used to set a single contraint to a value > 0.



R
------------
In all cases the R code will include a script. The script may call any defined functions. For MOGA3 the 
script should print to the standard output two vectors, the first being the objectives, and the second the constraint(s).
Both outputs may be numeric or character, but character values must be convertable to numeric. In MOGA3 the use of 
the print() statement is required, as there will be two outputs to the standard error, and just 

.. code-block:: R

    c(OFV1, OFV2, OFV3) 
    c(constraint1)

Would only output the final to the standard output. The correct syntax is:

.. code-block:: R

    print(c(OFV1, OFV2, OFV3)) 
    print(c(constraint1))
 
and the code can be tested by calling rscript with the code file as an argument, from the run directory. It should return the 
required output the the console, e.g. for DOS command line:

.. code-block:: console

    c:\git\mogaexamples\moga3NLMER\temp\1\01>"C:/Program Files/R/R-4.5.1/bin/Rscript.exe" ..\..\..\RSE3penaltyb.R
    [1] 8438.10000    7.00000   61.60081
    [1] 1

    

python
------------
In contrast to R, post run code in python is a function. In fact, syntax is available for two functions. The first (and 
likely the most useful) is to write a function called post_process 
(:ref:`moga3-nlme_post_process`) and takes the argument run_dir. The function signature is 


.. code-block:: python

    def post_process(rundir):
    .
    .
    .

    return [OFV1, OFV2, OFV3], [constraint1]

where rundir is a string. The function must return 2 vectors with the lenghth of the first described by the 
value of "objectives" in the options.json file:

.. code-block:: JSON

   "MOGA" : { 
        
        "objectives" : 3, 
   },

and the length of the 2nd described by the value of "constraints"

.. code-block:: JSON

   "MOGA" : { 
        
      "constraints" : 1,
   },


If the search is to be unconstrained, it is most stable to still use 1 contraint, but always return [0] in the constraint vector.

The second syntax is for post_process2, with the function signature below:

.. code-block:: python

    def post_process2(run):
    .
    .
    .

    return [OFV1, OFV2, OFV3], [constraint1]

where "run" is the python object model run object. Developing code for post_process2 is challenging in that it must be 
developed within a full pyDarwin run in order to create the run objects. This is likely non-trivial for the causal user. 
However, Certara is happy to provide support for interested user. In contrast with post_process, one can simply send 
the run path as a argument, e.g., 


.. code-block:: console

    

or use your favorite IDE, with the NLME run folder as the working directory.
