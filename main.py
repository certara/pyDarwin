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
from darwin.run_search import run_search, run_search_in_folder
 

if __name__ == '__main__': 
 final = run_search("C:\\fda\\FDA-OGD-ML-examples\\example5_EX\\example5_template.txt",
            "C:\\fda\\FDA-OG    D-ML-examples\\example5_EX\\example5_tokens.json",
	        "C:\\fda\\FDA-OGD-ML-examples\\example5_EX\\exhaustiveoptions74.json")
with open(os.path.join(final.template.homeDir,"finalModel.mod"),"w") as finalcontrol:
    finalcontrol.write(final.control) 
if os.path.exists(os.path.join(final.runDir,final.outputFileName)):
    os.remove(os.path.join(final.template.homeDir,final.outputFileName))
if not final.oldoutputfile is None:
    shutil.copyfile(os.path.join(final.runDir,final.oldoutputfile), os.path.join(final.template.homeDir,"finaloutput.lst"))
else:
    shutil.copyfile(os.path.join(final.runDir,final.outputFileName), os.path.join(final.template.homeDir,"finaloutput.lst"))