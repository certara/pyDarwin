""""
Sponsor:FDA OGD 
Program:
Programmer’s Name: Mark Sale
Date:19May2022
Purpose:
Brief Description:
Platform: Windows
Environment: 
Input:
Output:
Notes:  
Modified By: Mark Sale
    Date: 19 May, 2022
    Details: call NONMEM and R from thread with wait
    Effective
"""
import os
import shutil
from darwin.run_search import run_search #, run_search_in_folder
from darwin.options import options
  


    # exhaustive example
final = run_search("C:\\fda\\fda-ogd-ml-examples\\nested\\example5_template.txt",
                    "C:\\fda\\fda-ogd-ml-examples\\nested\\example5_tokens.json",
                    "C:\\fda\\fda-ogd-ml-examples\\nested\\NestedOptions.json")
with open(os.path.join(options.homeDir, "finalModel.mod"), "w") as final_control:
    final_control.write(final.control)
if os.path.exists(os.path.join(options.homeDir, final.outputFileName)):
    os.remove(os.path.join(options.homeDir, final.outputFileName))
if final.doutputfile is not None:
    shutil.copyfile(os.path.join(final.runDir, final.oldoutputfile),
                    os.path.join(options.homeDir, "finaloutput.lst"))
else:
    shutil.copyfile(os.path.join(final.runDir, final.outputFileName),
                    os.path.join(options.homeDir, "finaloutput.lst"))