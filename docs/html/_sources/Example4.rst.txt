

Example 4: PK Model, DMAG by GA with post-run R code
====================================================
  

.. _startpk4:

Example 4 is the first realistic model search example, with real data (courtesy of `Dr. Rob Bies <https:/pharmacy.buffalo.edu/content/pharmacy/faculty-staff/faculty-profile.html?ubit=robertbi>`_ and the 
`CATIE study <https://www.nimh.nih.gov/funding/clinical-research/practical/catie#:~:text=The%20NIMH%2Dfunded%20Clinical%20Antipsychotic,medications%20used%20to%20treat%20schizophrenia>`_ ).
This search again uses :ref:`nested tokens<Nested Tokens>`, as it searches whether K32 is a function of Weight, and 1 vs 2 vs 3 compartments. 
Another important feature of example 4 is the use of post run R code. In this case, it was of interest to capture the Cmax value. The is no straightforward way to include a penalty for missing the Cmax 
in the NONMEM control stream. Therefore, the penalty for missing Cmax is added after the NONMEM run is complete. Any R code can be provided by the user, and should return a vector of two values. The 
first is a real values penalty to be added to the fitness/reward. The 2nd is text that will be appended to NONMEM output file to desribe the results of the R code execution.


The search space contains 1.66 million possible models, and searches:


+----------------------------+--------------------------+----------------------------+
| Description                | Token Stem               | Values                     |
+============================+==========================+============================+
| Number of compartments     | ADVAN                    | 1|2|3                      |
+----------------------------+--------------------------+----------------------------+
| Is K23 related to weight?  | K23~WT                   | Yes|No                     |
+----------------------------+--------------------------+----------------------------+
| Is there ETA on Ka?        | KAETA                    | Yes|No                     |
+----------------------------+--------------------------+----------------------------+
| Is V2 related to weight?   | V2~WT                    | None|Power|exponential     |
+----------------------------+--------------------------+----------------------------+
| Is V2 related to Gender?   | V2~GENDER                | Yes|No                     |
+----------------------------+--------------------------+----------------------------+
| Is CL related to weight?   | CL~WT                    | None|Power|exponential     |
+----------------------------+--------------------------+----------------------------+
| Is CL related to Age?      | CL~AGE                   | Yes|No                     |
+----------------------------+--------------------------+----------------------------+
| | Is there ETA on D1 and/or| | ETAD1LAG               | | None or ETA on D1 or ETA |
| | and/or ALAG1 (nested     | |                        | | ETA on ALAGa or ETA on   | 
| | the D1LAG token group)   | |                        | | both or on both (BLOCK)  |
+----------------------------+--------------------------+----------------------------+


1,2,3 compartments

Between occasion variability

Multiple covaraiates (but probably still not as many as a real search)

Different absorption models

Different residual error models

Block OMEGA structures

Different initial estimates (also likely not as many as a real search should include).
