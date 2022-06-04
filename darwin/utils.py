import os
import re
import shutil


def replaceTokens(tokens, text, phenotype, tokenSet_Non_influential):
    """
    note zero based phenotype, all representations are zero based.
    """

    any_found = False
    current_token_set = 0

    for thisKey in tokens.keys():
        tokenSet = tokens.get(thisKey)[phenotype[thisKey]]
        tokenNum = 1
         
        for this_token in tokenSet:
            replacement_text = this_token
            # if replacement has THETA/OMEGA and sigma in it but it doesn't end up getting inserted, increment

            fullKey = "{" + thisKey + "[" + str(tokenNum)+"]"+"}"

            if fullKey in text:
                text = text.replace(fullKey, replacement_text)
                any_found = True
                tokenSet_Non_influential[current_token_set] = False  # is influential
            
            tokenNum = tokenNum + 1  
            
        current_token_set += 1

    return any_found, text
 

def getTokenParts(token):
    match = re.search("{.+\[", token).span()
    stem = token[match[0]+1:match[1]-1]  
    restPart = token[match[1]:]
    match = re.search("[0-9]+]", restPart).span()
    try:
        index = int(restPart[match[0]:match[1]-1]) ## should be integer
    except:  
        return "none integer found in " + stem + ", " + token
        # json.load seems to return it's own error and exit immediately
        # this try/except doesn't do anything

    return stem,int(index)


def expandTokens(tokens,textBlock,phenotype):
    ## only supports one level of nesting
    expandedTextBlock = []
    #anyFound = False 
    for thisLine in textBlock: 
        thiskey,thisIndex = getTokenParts(thisLine) 
        thisToken = tokens.get(thiskey)[phenotype[thiskey]][thisIndex-1] ## problem here??? 
        ## remove comments
        thisToken = remove_comments(thisToken).splitlines()
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
            
    return expandedTextBlock
  

def remove_comments(code):
    if type(code) != list:
        lines = code.splitlines()
        newCode = ""
        for thisline in lines:
            if thisline.find(";") > -1:
                thisline = thisline[:thisline.find(";")]
            newCode = newCode + thisline.strip() + '\n' 
        return newCode
    else:
        lines = code
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

    return control


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
                    newString = remove_comments(newString).strip()
                    fullToken = fullToken +  newString + "\n"
            ## get THETA(alphas)
            fullIndices = re.findall("THETA\(.+\)", fullToken)
    
            for i in range(len(fullIndices)):
                # have to get only part between THETA( and )
                start_theta = fullIndices[i].find("THETA(") + 6
                last_parens = fullIndices[i].find(")",(start_theta-2))
                THETAIndex = fullIndices[i][start_theta:last_parens] #.replace("THETA(","").replace(")","")
                thetaMatchs[THETAIndex] = curTHETA
                curTHETA += 1
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
                    newString = tokens[stem][thisPhenotype][thisToken]#replace(" ", "") # can't always replace spaces, sometimes needed
                    newString = remove_comments(newString).strip()
                    fullToken = fullToken +  newString + "\n"
                    ### if this is repalcebnoreplace THETA with XXXXXX so it doesn't conflict with ETA
                    if whichRand == "ETA":
                        fullToken = fullToken.replace("THETA","XXXXX")
            ## get ETA/EPS(alphas)
            fullIndices = re.findall(whichRand+"\(.+?\)", fullToken) # non greedy with ?
    
            for i in range(len(fullIndices)): 
                start = fullIndices[i].find((whichRand + "(")) + 4
                last_parens = fullIndices[i].find(")",(start-2))
                randIndex = fullIndices[i][start:last_parens]  
                randMatchs[randIndex] = curRand
                curRand += 1
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

    return control


def remove_file(file_path: str):
    if os.path.isfile(file_path) or os.path.islink(file_path):
        os.unlink(file_path)


def remove_dir(file_path: str):
    if os.path.isdir(file_path):
        shutil.rmtree(file_path)
