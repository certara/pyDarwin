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
    Date: 19 May 2022
    Details: call NONMEM and R from thread with wait
    Effective
""" 
from darwin.run_search import run_search


if __name__ == '__main__':
    final = run_search("..\\examples\\user\\Example1\\template.txt",
                       "..\\examples\\user\\Example1\\tokens.json",
                       "..\\examples\\user\\Example1\\options.json")

    final = run_search("..\\examples\\user\\example2\\template.txt",
                       "..\\examples\\user\\Example2\\tokens.json",
                       "..\\examples\\user\\Example2\\options.json")

    final = run_search("..\\examples\\user\\Example3\\template.txt",
                       "..\\examples\\user\\Example3\\tokens.json",
                       "..\\examples\\user\\Example3\\options.json")

    final = run_search("..\\examples\\user\\Example4\\template.txt",
                       "..\\examples\\user\\Example4\\tokens.json",
                       "..\\examples\\user\\Example4\\options.json")

    final = run_search("..\\examples\\user\\Example5\\template.txt",
                       "..\\examples\\user\\Example5\\tokens.json",
                       "..\\examples\\user\\Example5\\options.json")
