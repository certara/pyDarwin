import os
import re
import shutil


def replace_tokens(tokens, text, phenotype, non_influential_tokens):
    """
    note zero based phenotype, all representations are zero based.
    """

    any_found = False
    current_token_set = 0

    for thisKey in tokens.keys():
        token_set = tokens.get(thisKey)[phenotype[thisKey]]
        token_num = 1
         
        for this_token in token_set:
            replacement_text = this_token
            # if replacement has THETA/OMEGA and sigma in it, but it doesn't end up getting inserted, increment

            full_key = "{" + thisKey + "[" + str(token_num)+"]"+"}"

            if full_key in text:
                text = text.replace(full_key, replacement_text)
                any_found = True
                non_influential_tokens[current_token_set] = False  # is influential
            
            token_num = token_num + 1
            
        current_token_set += 1

    return any_found, text
 

def get_token_parts(token):
    match = re.search("{.+\[", token).span()
    stem = token[match[0]+1:match[1]-1]  
    rest_part = token[match[1]:]
    match = re.search("[0-9]+]", rest_part).span()

    try:
        index = int(rest_part[match[0]:match[1]-1])  # should be integer
    except:  
        return "none integer found in " + stem + ", " + token
        # json.load seems to return its own error and exit immediately
        # this try/except doesn't do anything

    return stem, int(index)


def expand_tokens(tokens, text_block, phenotype):
    # only supports one level of nesting
    expanded_text_block = []

    for text_line in text_block:
        key, index = get_token_parts(text_line)
        token = tokens.get(key)[phenotype[key]][index-1]  # problem here???
        token = remove_comments(token).splitlines()
        # any tokens?? {k23~WT}, if so stick in new text block
        # any line without a new token gets the old token
        # and include the new token
        # so:
        # {ADVAN[3]} becomes
        # {ADVAN[3]}
        # {ADVAN[3]}
        # {K23~WT} 
        # for the final - 3 thetas, numbered sequentially
        # must be by line!!
        for token_line in token:
            
            if re.search("{.+}", token_line) is None:  # not a nested token
                if len(token_line) > 0:
                    expanded_text_block.append(text_line)
            else:
                # add token
                match = re.search("{.+}", token_line).span()
                new_token = token_line[match[0]:match[1]]
                expanded_text_block.append(new_token)
            
    return expanded_text_block
  

def remove_comments(code):
    new_code = ""

    if type(code) != list:
        lines = code.splitlines()

        for line in lines:
            if line.find(";") > -1:
                line = line[:line.find(";")]
            new_code = new_code + line.strip() + '\n'
        return new_code
    else:
        lines = code

    for line in lines[0]:
        if line.find(";") > -1:
            line = line[:line.find(";")]
        new_code = new_code + line.strip() + '\n'

    return new_code


def match_thetas(control, tokens, var_theta_block, phenotype, last_fixed_theta):

    expanded_theta_block = expand_tokens(tokens, var_theta_block, phenotype)
  
    # then look at each  token, get THETA(alpha) from non-THETA block tokens
    theta_indices = get_theta_matches(expanded_theta_block, tokens, phenotype)

    # add last fixed theta value to all
    for _, (k, v) in enumerate(theta_indices.items()):
        # add last fixed theta value to all
        # and put into control file
        control = control.replace(f"THETA({k})", "THETA(" + str(v + last_fixed_theta) + ")")

    return control


def get_theta_matches(expanded_theta_block, tokens, phenotype):
    # shouldn't be any THETA(alpha) in expandedTHETABlock, should  be trimmed out
    # get stem and index, look in other tokens in this token set (phenotype)
    # tokens can be ignored here, they are already expanded, just list the alpha indices of each THETA(alpha) in order
    # and match the row in the expandedTHETAblock
    # note that commonly a stem will have more than one THETA, e.g, THETA(ADVANA)
    # and THETA(ADVANB) for ADVAN4, K23 and K32
    # however, an alpha index MAY NOT appear more than once, e.g.,
    # e.g. TVCL = THETA()**THETA(CL~WT)
    #      TVQ  = THETA()**THETA(CL~WT)
    # is NOT PERMITTED, need to do:
    # CLPWR = THETA(CL~WT)
    # TVCL = THETA()**CLPWR
    # TVQ  = THETA()**CLPWR

    theta_matchs = {}
    cur_theta = 1
    # keep track of added/check token, don't want to repeat them, otherwise sequence of THETA indices will be wrong
    all_checked_tokens = []

    for theta_row in expanded_theta_block:
        # get all THETA(alpha) indices in other tokens in this token set
        stem, index = get_token_parts(theta_row)
        phenotype = phenotype[stem]
        full_token = ""  # assemble full token, except the one in $THETA, to search for THETA(alpha)

        if not(any(stem in s for s in all_checked_tokens)):  # add if not already in list
            # for thisToken in range(len(tokens[stem][thisPhenotype-1])):
            for token in range(len(tokens[stem][phenotype])):
                if token != index-1:
                    # newString = tokens[stem][thisPhenotype-1][thisToken].replace(" ", "")
                    new_string = tokens[stem][phenotype][token].replace(" ", "")
                    new_string = remove_comments(new_string).strip()
                    full_token = full_token + new_string + "\n"

            # get THETA(alphas)
            full_indices = re.findall("THETA\(.+\)", full_token)
    
            for i in range(len(full_indices)):
                # have to get only part between THETA( and )
                start_theta = full_indices[i].find("THETA(") + 6
                last_parens = full_indices[i].find(")", (start_theta-2))
                theta_index = full_indices[i][start_theta:last_parens]
                theta_matchs[theta_index] = cur_theta
                cur_theta += 1
            all_checked_tokens.append(stem)

        # number should match #of rows with stem in expandedTHETABlock
         
    return theta_matchs


def get_rand_var_matches(expanded_block, tokens, phenotype, which_rand):
    rand_matches = {}
    cur_rand = 1

    # keep track of added/check token, don't want to repeat them, otherwise sequence of THETA indices will be wrong
    all_checked_tokens = []

    for rand_row in expanded_block:
        # get all THETA(alpha) indices in other tokens in this token set
        stem, index = get_token_parts(rand_row)
        phenotype = phenotype[stem]
        full_token = ""  # assemble full token, except the one in $THETA, to search for THETA(alpha)

        if not(any(stem in s for s in all_checked_tokens)):  # add if not already in list
            for thisToken in range(len(tokens[stem][phenotype])):
                if thisToken != index-1:
                    new_string = tokens[stem][phenotype][thisToken]  # can't always replace spaces, sometimes needed
                    new_string = remove_comments(new_string).strip()
                    full_token = full_token + new_string + "\n"

                    # if this is repalcebnoreplace THETA with XXXXXX, so it doesn't conflict with ETA
                    if which_rand == "ETA":
                        full_token = full_token.replace("THETA", "XXXXX")

            # get ETA/EPS(alphas)
            full_indices = re.findall(which_rand + "\(.+?\)", full_token)  # non-greedy with ?
    
            for i in range(len(full_indices)):
                start = full_indices[i].find((which_rand + "(")) + 4
                last_parens = full_indices[i].find(")", (start-2))
                rand_index = full_indices[i][start:last_parens]
                rand_matches[rand_index] = cur_rand
                cur_rand += 1
            all_checked_tokens.append(stem)

        # number should match #of rows with stem in expandedTHETABlock
         
    return rand_matches
 

def match_rands(control, tokens, var_rand_block, phenotype, last_fixed_rand, stem):
    expanded_rand_block = expand_tokens(tokens, var_rand_block, phenotype)

    # then look at each  token, get THETA(alpha) from non-THETA block tokens
    rand_indices = get_rand_var_matches(expanded_rand_block, tokens, phenotype, stem)

    # add last fixed theta value to all
    for i, (k, v) in enumerate(rand_indices.items()):
        # add last fixed random parm value to all
        # and put into control file
        control = control.replace(stem + "(" + k + ")", stem + "(" + str(v + last_fixed_rand) + ")")

    return control


def remove_file(file_path: str):
    if os.path.isfile(file_path) or os.path.islink(file_path):
        os.unlink(file_path)


def remove_dir(file_path: str):
    if os.path.isdir(file_path):
        shutil.rmtree(file_path)
