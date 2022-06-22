

.. _startpk1:

PK Model 1, trivial exhaustive search
==============================================
This first model is quite simple, the search space consistes of 6 dimensions, each with 2 options. Thus, the total number of candiate models is 
2^6 = 64 models. As the search space if very small, we'll search by exhaustive search. 

The Template file
~~~~~~~~~~~~~~~~~~~~~

Example 1 template file :download:`text <../examples/Example1/Example1_template.txt>`
Example 1 searchs a 6 dimensional space. The dimensions corresponds to :ref:`token group <token group>`. 
Each token group is identified by a :ref:`token stem <token stem>`, e.g. "V2~WT" for the dimension of the 
relationship between weight a volume of distribution. Each token group includes 
2 or more :ref:`token set <token set>`, one for each option in the that dimension, These dimensions are:

1. Effect of Weight on Volume ("V2~WT") - None or a power model.
2. Effect of Sex (Gender) on Volume ("V2~GENDER") - None or a power model
3. Effect of Weight on Clearance ("CL~WT") - None or a power model
4. Presence of between subject variability (BSF) on Ka ("KAETA")- None or exponential model
5. Presence of an absorption lag time - ALAG1 ("ALAG") - Present or not
6. Residual error model ("RESERR") - additive or combined additive and proportional

Each token set in turn will include (in this case) two :ref:`token key-text pairs<token key-text pair>` (analagous to key-value pairs 
in JSON, but only text values are permitted)

Each of these dimensions has two options. Therefore the total number of candidate models 
in the search space is number of permutations - 2^6 = 64. 

In the :download:`template text <../examples/Example1/Example1_template.txt>` note the 
special text in curly braces({}). These are :ref:`tokens<token>`. Tokens come in sets, as typically 
multiple text substittion must be made to results in a syntactically correct NMTRAN control file. For 
example, if ALAG1 is to be used in the $PK block, a corresponding initial estimate for 
this parameter must be provided in the $THETA block. These tokens (collectively called a token set) 
are then replaced by the corresponding text value in the :ref:`token key-text pair <token key-text pair>`. 


As the search space is small 
(and the run time is fast), we'll search by exhaustive search.
The Tokens file
~~~~~~~~~~~~~~~~

Example 1 tokens file :download:`json <../examples/Example1/Example1_tokens.json>`

The :ref:`tokens file <tokens file>` provide the :ref:`token key-text pairs<token key-text pair>` that 
are substitued into the template file. This is a `JSON <https://www.json.org/json-en.html>`_ file format. 
Unfortunately, comments are not  permitted in JSON files and so this file without annotation. Requirements are that 
each :ref:`token set <token set>` within a :ref:`token group <token group>` must have the same number of :ref:`tokens <token>` 
and new lines must be coded as ASCII text ("\n"), not just a new line in the file (which will be ignored). One level of 
nest tokens (tokens within tokens is permitted. This can be useful, when for example one might want to search for covariates 
on an search parameter, as in searching for an effect of FED vs FASTED state on ALAG1, when ALAG1 is also searched (see
:ref:`PK example 3 <startpk3>`)


The Options file
~~~~~~~~~~~~~~~~

Example 1 :ref:`Options file <options file>`  :download:`json <../examples/Example1/Example1_options.json>` 

  
 