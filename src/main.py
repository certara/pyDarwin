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

# Example PK1, trival exhaustive search

# Example PK2, GA search with R code

# Example PK3, ODE 

# print("\n\n\n\n Example 1, Trivial Exhaustive\n\n\n")

# final = run_search("C:\\fda\\pyDarwin\\docs\\Example1\\Example1_template.txt",
#                    "C:\\fda\\pyDarwin\\docs\\Example1\\Example1_tokens.json",
#                    "C:\\fda\\pyDarwin\\docs\\Example1\\Example1_options.json")
 
# with open(os.path.join(options.home_dir, "finalModel.mod"), "w") as final_control:
#     final_control.write(final.control)
# if os.path.exists(os.path.join(options.home_dir, final.output_file_name)):
#     os.remove(os.path.join(options.home_dir, final.output_file_name))
# if final.output_file_name is not None:
#     shutil.copyfile(os.path.join(final.run_dir, final.output_file_name),
#                     os.path.join(options.home_dir, "finaloutput.lst"))

# print("\n\n\n\n Example 2, Simple GA\n\n\n")


# final = run_search("C:\\fda\\pyDarwin\\docs\\Example2\\Example2_template.txt",
#                    "C:\\fda\\pyDarwin\\docs\\Example2\\Example2_tokens.json",
#                    "C:\\fda\\pyDarwin\\docs\\Example2\\Example2_options.json")
 
# with open(os.path.join(options.home_dir, "finalModel.mod"), "w") as final_control:
#     final_control.write(final.control)
# if os.path.exists(os.path.join(options.home_dir, final.output_file_name)):
#     os.remove(os.path.join(options.home_dir, final.output_file_name))
# if final.output_file_name is not None:
#     shutil.copyfile(os.path.join(final.run_dir, final.output_file_name),
#                     os.path.join(options.home_dir, "finaloutput.lst"))

# print("\n\n\n\n Example 3, ODE\n\n\n")


# final = run_search("C:\\fda\\pyDarwin\\docs\\Example3\\Example3_template.txt",
#                    "C:\\fda\\pyDarwin\\docs\\Example3\\Example3_tokens.json",
#                    "C:\\fda\\pyDarwin\\docs\\Example3\\Example3_options.json")
 
# with open(os.path.join(options.home_dir, "finalModel.mod"), "w") as final_control:
#     final_control.write(final.control)
# if os.path.exists(os.path.join(options.home_dir, final.output_file_name)):
#     os.remove(os.path.join(options.home_dir, final.output_file_name))
# if final.output_file_name is not None:
#     shutil.copyfile(os.path.join(final.run_dir, final.output_file_name),
#                     os.path.join(options.home_dir, "finaloutput.lst"))


print("\n\n\n\n Example 4, Full GA, DMAG data n\n\n")
                     


final = run_search("C:\\fda\\pyDarwin\\docs\\Example4\\Example4_template.txt",
                   "C:\\fda\\pyDarwin\\docs\\Example4\\Example4_tokens.json",
                   "C:\\fda\\pyDarwin\\docs\\Example4\\Example4_options.json")
 
with open(os.path.join(options.home_dir, "finalModel.mod"), "w") as final_control:
    final_control.write(final.control)
if os.path.exists(os.path.join(options.home_dir, final.output_file_name)):
    os.remove(os.path.join(options.home_dir, final.output_file_name))
if final.output_file_name is not None:
    shutil.copyfile(os.path.join(final.run_dir, final.output_file_name),
                    os.path.join(options.home_dir, "finaloutput.lst"))



# Example PK4, DMAG