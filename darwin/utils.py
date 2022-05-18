
from distutils.command.clean import clean
from lib2to3.pgen2 import token
import re   
import math

# def convert_full_bin_int(bin_pop,gene_max,length): 
#     ''' 
#     converts a "full binary" (e.g., from GA to integer (used to select token sets))
#     arguments are:
#     bin_pop - population of binaries
#     gene_max - integer list,maximum value- number of tokens sets in that token group
#     length - integer list, how long each gene is
#     return integer array of which token goes into this model
#     ''' 
#     start = 0 
#     phenotype = []
#     for thisNumBits,this_max in zip(length,gene_max):  
#        # max = gene_max[gene_num]  # user specified maximum value of gene - how many token sets are there, max is 0 based?
#         thisGene = bin_pop[start:start+thisNumBits]      
#         baseInt  = int("".join(str(x) for x in thisGene), 2)  
#         maxValue = 2**len(thisGene) - 1 ## # zero based, max number possible from bit string , 0 based (has the -1)
#         maxnumDropped = maxValue-this_max  # maximum possoible number of indexes that must be skipped to get max values to fit into fullMax possible values.
#         numDropped = math.floor(maxnumDropped*(baseInt/maxValue))
#         full_int_val = baseInt - numDropped 
#         phenotype.append(full_int_val) ## value here???
#         start += thisNumBits 
#     return  phenotype
 
# def int2bin(n,length):
#     value = bin(n)[2:]
#     value = list(value.rjust(length,"0"))
#     value = map(int, value)
#     value = list(value)
#     return value
# def convert_int_full_bin(int_pop,gene_max,length):
#     ''' 
#     converts an integer arry to "full binary" (e.g., from integer (used to select token sets) back to GA compatible code, opposite of convert_full_bin_int)
#     arguments are:
#     int_pop - population of integers
#     gene_max - integer list,maximum value- number of tokens sets in that token group
#     length - integer list, how long each gene is
#     return array of binaries compatible with GA
#     '''  
#     result = []
#     for baseInt,this_max,this_length in zip(int_pop,gene_max,length): 
#         maxValue = (2**this_length)-1 # zero based
#         maxnumAdded = maxValue-this_max  # max is zero based 
#         numAdded = math.floor(maxnumAdded*(baseInt/(maxValue-maxnumAdded)))
#         full_int_val = baseInt + numAdded 
#         full_bin_val = int2bin(full_int_val,this_length)
        
#         result.extend(full_bin_val)
#     return result 

 
 
# def convert_min_bin_int(bin_pop,max,length):
#     ''' 
#     converts a "minimal binary" (e.g., used for downhill, just the integer value converted to binary - doesn't fill in the entire n bit array)
#     arguments are:
#     bin_pop - population of minimal binaries
#     max - integer list,maximum value- number of tokens sets in that token group
#     length - integer list, how long each gene is
#     return integer array of which token goes into this model
#     ''' 
#     start = 0
#     result = []
#     for this_gene,this_max in zip(length,max):
#         # max is 0 based, everything is zero based
#         last = start + this_gene    
#         binary =  bin_pop[start:last] 
#         string_ints = [str(int) for int in binary]  
#         x = "".join(string_ints)
#         int_val = int(x,2)
#         start = last
#         if int_val > this_max: # int_val and this_max are both zero based
#             int_val -=this_max -1 # e.g if 1,1, converts to 3, if max is 2 (3 values, 0,1,2) then rolls over to 0, so need to subtractg one more
#                                      # of value is 7 and max is 4 (5 options), should wrap to 2
#         result.append(int_val)
#     return result 

 

# def convert_int_min_bin(int_pop,length):
#     ''' 
#     converts an integer arry to "minimal binary"  (e.g., used for downhill, just the integer value converted to binary - doesn't fill in the entire n bit array)
#     arguments are:
#     int_pop - population of integers 
#     length - integer list, how long each gene is
#     return array of binaries, same length as the full binary
#     '''  
 
#     full_results = [] 
#     if isinstance(int_pop[0],list): # FULL POPULATION if first element is list, will be int if just one individual
#         for ind in int_pop: 
#             results = [] 
#             for thisgene,this_length in zip(ind,length): 
#                 results.extend(int2bin(thisgene,this_length)) 
#             full_results.append(results) 
#     else: # just on individual
#         cur_gene = 0
#         for this_length in length: 
#             this_gene = int_pop[cur_gene]
#             full_results.extend(int2bin(this_gene,this_length))  
#             cur_gene += 1
#     return full_results


def replaceTokens(tokens,text,phenotype,tokenSet_Non_influential):
    '''
    note zero based phenotype, all representations are zero based.
    '''
    anyFound = False
    curtokenSet = 0
    for thisKey in tokens.keys():   
        tokenSet = tokens.get(thisKey)[phenotype[thisKey]] ## 
        tokenNum = 1
         
        for thistoken in tokenSet:  
            replacementText = thistoken  
            #if replacement has THETA/OMEGA and sigma in it but it doesn't end up getting inserted, increment
            
             
            fullKey = "{" + thisKey + "[" + str(tokenNum)+"]"+"}"
            if fullKey in text:
                #tempTemplate=tempTemplate.replace(fullKey,replacementText) \
                text=text.replace(fullKey,replacementText)
                anyFound = True 
                #if containsParm:
                #    cur_tokenSet_influential = True # if influential once, then this token set is always influential for this model
                tokenSet_Non_influential[curtokenSet] = False  # is influential
            
            tokenNum = tokenNum + 1  
            
        curtokenSet += 1 
    return(anyFound,text) 
 
def getTokenParts(token):
    match = re.search("{.+\[",token).span()
    stem = token[match[0]+1:match[1]-1]  
    restPart = token[match[1]:]
    match = re.search("[0-9]+\]",restPart).span()
    try:
        index = int(restPart[match[0]:match[1]-1]) ## should be integer
    except:  
        return "none integer found in " + stem  + ", " +  token
        ### json.load seems to return it's own error and exit immediately
        ## this try/except doesn't do anything

    return stem,int(index)


def expandTokens(tokens,textBlock,phenotype):
    ## only supports one level of nesting
    expandedTextBlock = []
    #anyFound = False 
    for thisLine in textBlock: 
        thiskey,thisIndex = getTokenParts(thisLine) 
        thisToken = tokens.get(thiskey)[phenotype[thiskey]][thisIndex-1] ## problem here??? 
        ## remove comments
        thisToken = removeComments(thisToken).splitlines()
        ## any tokens?? {k23~WT}, if so stick in new textblock
        ## any line without a new token gets the old token
        ## and include the new token
        ## so:
        # {ADVAN[3]} becomes
        # {ADVAN[3]}
        # {ADVAN[3]}
        # {K23~WT} 
        ## for the final - 3 thetas, numbered sequentially
        ## must be by line!! 
        for line in thisToken:
            
            if  re.search("{.+}",line) == None:   # not a nested token
                if len(line) > 0:
                    expandedTextBlock.append(thisLine)    
            else:
                ## add token 
                match = re.search("{.+}",line).span() 
                newToken = line[match[0]:match[1]] 
                expandedTextBlock.append(newToken) 
            
    return(expandedTextBlock) 
  

def removeComments(Code):
    if type(Code) != list:
        lines = Code.splitlines()
        newCode = ""
        for thisline in lines:
            if thisline.find(";") > -1:
                thisline = thisline[:thisline.find(";")]
            newCode = newCode + thisline.strip() + '\n' 
        return newCode
    else:
        lines = Code
    newCode = ""
    for thisline in lines[0]:
        if thisline.find(";") > -1:
            thisline = thisline[:thisline.find(";")]
        newCode = newCode + thisline.strip() + '\n' 
    return newCode


def matchTHETAs(control,tokens,varTHETABlock,phenotype,lastFixedTHETA):
    
 
    expandedTHETABlock  = expandTokens(tokens,varTHETABlock,phenotype) 
  
        ## then look at each  token, get THETA(alpha) from non-THETA block tokens
    THETAIndices = getTHETAMatches(expandedTHETABlock,tokens,phenotype)  
        # add last fixed theta value to all 
    for _, (k, v) in enumerate(THETAIndices.items()):   
        # add last fixed theta value to all
        # and put into control file
        control = control.replace("THETA(" + k +")", "THETA(" + str(v + lastFixedTHETA) +")") 
    return(control)


def getTHETAMatches(expandedTHETABlock,tokens,phenotype):
    ## shouldn't be any THETA(alpha) in expandedTHETABlock, should  be trimmed out
    ## get stem and index, look in other tokens in this token set (phenotype)
    # tokens can be ignored here, they are already expanded, just list the alpha indices of each THETA(alpha) in order
    # and match the row in the expandedTHETAblock
    # note that commonly a stem will have more than one THETA, e.g, THETA(ADVANA) and THETA(ADVANB) for ADVAN4, K23 and K32
    # however, an alpha index MAY NOT appear more than once, e.g.,
    # e.g. TVCL = THETA()**THETA(CL~WT)
    #      TVQ  = THETA()**THETA(CL~WT)
    # is NOT PERMITTED, need to do:
    # CLPWR = THETA(CL~WT)
    # TVCL = THETA()**CLPWR
    # TVQ  = THETA()**CLPWR
    thetaMatchs = {}
    curTHETA = 1
    allCheckedTokens = [] # keep track of added/check token, don't want to repeat them, 
                          # otherwise sequence of THETA indices will be wrong
    for thisTHETARow in expandedTHETABlock:
        ## get all THETA(alpha) indices in other tokens in this token set
        stem,index = getTokenParts(thisTHETARow)
        thisPhenotype = phenotype[stem]
        fullToken = "" # assemble full token, except the one in $THETA, to search for THETA(alpha)
        if not(any(stem in s for s in allCheckedTokens)): # add if not already in list
            #for thisToken in range(len(tokens[stem][thisPhenotype-1])): 
            for thisToken in range(len(tokens[stem][thisPhenotype])): 
                if thisToken != index-1:
                  #  newString = tokens[stem][thisPhenotype-1][thisToken].replace(" ", "")
                    newString = tokens[stem][thisPhenotype][thisToken].replace(" ", "")
                    newString = removeComments(newString).strip()
                    fullToken = fullToken +  newString + "\n"
            ## get THETA(alphas)
            fullIndices = re.findall("THETA\(.+\)", fullToken)
    
            for i in range(len(fullIndices)):
                THETAIndex = fullIndices[i].replace("THETA(","").replace(")","")
                thetaMatchs[THETAIndex] = curTHETA
                curTHETA +=1
            allCheckedTokens.append(stem)  
        thisTHETARow = tokens[stem][phenotype[stem]-1][index-1]
        ## number should match #of rows with stem in expandedTHETABlock
         
    return thetaMatchs


def getRandVarMatches(expandedBlock,tokens,phenotype,whichRand):
    randMatchs = {}
    curRand = 1
    allCheckedTokens = [] # keep track of added/check token, don't want to repeat them, 
                          # otherwise sequence of THETA indices will be wrong
    for thisRandRow in expandedBlock:
        ## get all THETA(alpha) indices in other tokens in this token set
        stem,index = getTokenParts(thisRandRow)
        thisPhenotype = phenotype[stem]
        fullToken = "" # assemble full token, except the one in $THETA, to search for THETA(alpha)
        if not(any(stem in s for s in allCheckedTokens)): # add if not already in list
            #for thisToken in range(len(tokens[stem][thisPhenotype-1])): 
            for thisToken in range(len(tokens[stem][thisPhenotype])): 
                if thisToken != index-1:
                    newString = tokens[stem][thisPhenotype][thisToken].replace(" ", "")
                    newString = removeComments(newString).strip()
                    fullToken = fullToken +  newString + "\n"
            ## get ETA/EPS(alphas)
            fullIndices = re.findall(whichRand+"\(.+?\)", fullToken) # non greedy with ?
    
            for i in range(len(fullIndices)):
                randIndex = fullIndices[i].replace(whichRand + "(","").replace(")","")
                randMatchs[randIndex] = curRand
                curRand +=1
            allCheckedTokens.append(stem)  
        thisRandRow = tokens[stem][phenotype[stem]-1][index-1]
        ## number should match #of rows with stem in expandedTHETABlock
         
    return randMatchs
 
def matchRands(control,tokens,varRandBlock,phenotype,lastFixedRand,stem):
    expandedRandBlock  = expandTokens(tokens,varRandBlock,phenotype) 
        ## then look at each  token, get THETA(alpha) from non-THETA block tokens
    randIndices = getRandVarMatches(expandedRandBlock,tokens,phenotype,stem)  
        # add last fixed theta value to all 
    for i, (k, v) in enumerate(randIndices.items()):  
        # add last fixed random parm value to all
        # and put into control file
        control = control.replace(stem +"(" + k+")", stem +"(" + str(v + lastFixedRand) +")") 
    return(control)