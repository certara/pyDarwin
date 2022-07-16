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
from darwin.run_search import run_search #, run_search_in_folder
from darwin.options import options
   
  

final = run_search("C:\\fda\\pyDarwin\\examples\\user\\Example1\\template.txt",
                   "C:\\fda\\pyDarwin\\examples\\user\\Example1\\tokens.json",
                   "C:\\fda\\pyDarwin\\examples\\user\\Example1\\options.json")
 


final = run_search("C:\\fda\\pyDarwin\\examples\\user\\example2\\template.txt",
                   "C:\\fda\\pyDarwin\\examples\\user\\Example2\\tokens.json",
                   "C:\\fda\\pyDarwin\\examples\\user\\Example2\\options.json")
  


final = run_search("C:\\fda\\pyDarwin\\examples\\user\\Example3\\template.txt",
                   "C:\\fda\\pyDarwin\\examples\\user\\Example3\\tokens.json",
                   "C:\\fda\\pyDarwin\\examples\\user\\Example3\\options.json")
  


final = run_search("C:\\fda\\pyDarwin\\examples\\user\\Example4\\template.txt",
                   "C:\\fda\\pyDarwin\\examples\\user\\Example4\\tokens.json",
                   "C:\\fda\\pyDarwin\\examples\\user\\Example4\\options.json")
  

final = run_search("C:\\fda\\pyDarwin\\examples\\user\\Example5\\template.txt",
                   "C:\\fda\\pyDarwin\\examples\\user\\Example5\\tokens.json",
                   "C:\\fda\\pyDarwin\\examples\\user\\Example5\\options.json")