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
from darwin.options import options

if __name__ == '__main__':
    # final = run_search("C:\\fda\\shuans_example\\IIVnotSearched_template.txt",
    #                    "C:\\fda\\shuans_example\\IIVnotSearched_tokens.json",
    #                    "C:\\fda\\shuans_example\\options.json")
    # with open(os.path.join(options.homeDir, "finalModel.mod"), "w") as final_control:
    #     final_control.write(final.control)
    # if os.path.exists(os.path.join(options.homeDir, final.outputFileName)):
    #     os.remove(os.path.join(options.homeDir, final.outputFileName))
    # if final.oldoutputfile is not None:
    #     shutil.copyfile(os.path.join(final.runDir, final.oldoutputfile),
    #                     os.path.join(options.homeDir, "finaloutput.lst"))
    # else:
    #     shutil.copyfile(os.path.join(final.runDir, final.outputFileName),
    #                     os.path.join(options.homeDir, "finaloutput.lst"))

     



    final = run_search("C:\\fda\\fda-ogd-ml-examples\\example5_GP\\example5_template.txt",
            "C:\\fda\\fda-ogd-ml-examples\\example5_GP\\example5_tokens.json",
	        "C:\\fda\\fda-ogd-ml-examples\\example5_GP\\GPoptions.json")
    with open(os.path.join(final.template.homeDir,"finalModel.mod"),"w") as finalcontrol:
        finalcontrol.write(final.control) 
    if os.path.exists(os.path.join(final.template.homeDir,final.outputFileName)):
        os.remove(os.path.join(final.template.homeDir,final.outputFileName))
    if not final.oldoutputfile is None:
        shutil.copyfile(os.path.join(final.runDir,final.oldoutputfile), os.path.join(final.template.homeDir,"finaloutput.lst"))

    final = run_search("C:\\fda\\fda-ogd-ml-examples\\example5_GA\\example5_template.txt",
            "C:\\fda\\fda-ogd-ml-examples\\example5_GA\\example5_tokens.json",
	        "C:\\fda\\fda-ogd-ml-examples\\example5_GA\\GPoptions.json")
    with open(os.path.join(final.template.homeDir,"finalModel.mod"),"w") as finalcontrol:
        finalcontrol.write(final.control) 
    if os.path.exists(os.path.join(final.template.homeDir,final.outputFileName)):
        os.remove(os.path.join(final.template.homeDir,final.outputFileName))
    if not final.oldoutputfile is None:
        shutil.copyfile(os.path.join(final.runDir,final.oldoutputfile), os.path.join(final.template.homeDir,"finaloutput.lst"))


        # exhaustive example
    final = run_search("C:\\fda\\fda-ogd-ml-examples\\example5_EX\\example5_template.txt",
                       "C:\\fda\\fda-ogd-ml-examples\\example5_EX\\example5_tokens.json",
                       "C:\\fda\\fda-ogd-ml-examples\\example5_EX\\exhaustiveoptions74.json")
    with open(os.path.join(options.homeDir, "finalModel.mod"), "w") as final_control:
        final_control.write(final.control)
    if os.path.exists(os.path.join(options.homeDir, final.outputFileName)):
        os.remove(os.path.join(options.homeDir, final.outputFileName))
    if final.oldoutputfile is not None:
        shutil.copyfile(os.path.join(final.runDir, final.oldoutputfile),
                        os.path.join(options.homeDir, "finaloutput.lst"))
    else:
        shutil.copyfile(os.path.join(final.runDir, final.outputFileName),
                        os.path.join(options.homeDir, "finaloutput.lst"))