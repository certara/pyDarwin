import re 
import math
import numpy as np
import copy

from darwin.utils import remove_comments, expand_tokens, get_token_parts


def match_vars(control: str, tokens: dict, var_block: list, phenotype: dict, last_fixed_var: int, stem: str) -> str:
    """
    Parses current control file text, looking for THETA(*) and calculates the appropriate index for that THETA
    (starting with the last_fixed_theta - the largest value used for THETA() in the fixed code)

    :param control: control file text
    :type control: str

    :param tokens: token groups
    :type tokens: dict

    :param var_block: variable block
    :type var_block: str

    :param phenotype: phenotype for model
    :type phenotype: dict

    :param last_fixed_var: highest value used for variable in fixed code. Fixed values for variables must start with 1
        and be continuous until the last fixed variable
    :type last_fixed_var: int

    :param stem:
    :type stem: str

    :return: new control content
    :rtype: str
    """
    # EXAMPLED_THETA_BLOCK IS THE FINAL $THETA BLOCK FOR THIS MODEL, WITH THE TOKEN TEXT SUBSTITUTED IN
    # EXPANDED TO ONE LINE PER THETA
    # token ({'ADVAN[3]}) will be present on if there is a THETA(???) in it
    # one instance of token for each theta present, so they can be counted
    # may be empty list ([]), but each element must contain '{??[N]}
    expanded_var_block = expand_tokens(tokens, var_block, phenotype)

    # then look at each token, get THETA(alpha) from non-THETA block tokens
    rand_indices = _get_var_matches(expanded_var_block, tokens, phenotype, stem)

    # add last fixed var value to all
    for k, v in rand_indices.items():
        # add last fixed parm value to all
        # and put into control file
        control = control.replace(stem + "(" + k + ")", stem + "(" + str(v + last_fixed_var) + ")")

    return control


def _get_var_matches(expanded_block, tokens, full_phenotype, var_type):
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

    var_matches = {}
    var_index = 1

    # keep track of added/check token, don't want to repeat them, otherwise sequence of THETA indices will be wrong
    all_checked_tokens = []

    for var_row in expanded_block:
        # get all THETA(alpha) indices in other tokens in this token set
        stem, index = get_token_parts(var_row)
        phenotype = full_phenotype[stem]
        full_token = ""  # assemble full token, except the one in $THETA, to search for THETA(alpha)

        if not (any(stem in s for s in all_checked_tokens)):  # add if not already in list
            for thisToken in range(len(tokens[stem][phenotype])):
                if thisToken != index - 1:
                    new_string = tokens[stem][phenotype][thisToken]  # can't always replace spaces, sometimes needed
                    new_string = remove_comments(new_string).strip()
                    full_token = full_token + new_string + "\n"

            # get ETA/EPS(alphas)
            variables = list(dict.fromkeys(x[1] for x in re.finditer(r"\b" + var_type + r"\((.+?)\)", full_token)))

            for var in variables:
                if var not in var_matches:
                    var_matches[var] = var_index
                    var_index += 1

            all_checked_tokens.append(stem)

    return var_matches


def set_omega_bands(control: str, bandwidth: int):
    """
    Removes ALL existing omega blocks from control, then inserts a series of $OMEGAs. These will be unchanged
    if the source is BLOCK or DIAG. Not specified BLOCK or DIAG (and so is by default DIAG), will convert
    to BLOCK with the number of bands specified in the model code.

    :param control: existing control file
    :type control: str

    :param bandwidth: require band width
    :type bandwidth: int

    :return: modified control file
    :rtype: str
    """

    control_list = control.splitlines()
    lines = remove_comments(control).splitlines()
    omega_starts = [idx for idx, element in enumerate(lines) if re.search(r"^\$OMEGA", element)]
    omega_ends = []
    omega_blocks = []
    for this_start in omega_starts:
        rest_of_text = lines[this_start:]
        next_block_start = [idx for idx, element in enumerate(rest_of_text[1:]) if re.search(r"^\$", element)]
        if next_block_start is None:
            next_block_start = len(rest_of_text)
        else:
            next_block_start = next_block_start[0]
        this_omega_ends = next_block_start + this_start + 1
        omega_ends.append(this_omega_ends)
        omega_blocks.append(copy.copy(lines[this_start:this_omega_ends]))
    all_omega_blocks = []

    for this_start in omega_blocks:
        # see if BLOCK(*) of DIAG appears, if user explicitly states it is DIAG, it will remain DIAG
        is_block_or_diag = any(re.search("BLOCK", line) for line in this_start) \
                           or any(re.search("DIAG", line) for line in this_start)
        # if so, keep block as is,
        if is_block_or_diag:
            all_omega_blocks.append(copy.deepcopy(this_start))
                
        else:  # is diagonal, but not explicitly stated to be diagonal
            # get values, start by replacing $OMEGA, and if present, DIAG
            this_block = copy.deepcopy(this_start)
            this_block[0] = this_block[0].replace("$OMEGA", "")
            # and collect the values, to be used on diagonal
            this_block = ' '.join([str(elem) for elem in this_block]).replace("\n", "")\
                .replace("  ", " ").replace("  ", " ").strip()
            this_block = this_block.split(" ")
            this_block = np.array(this_block, dtype=np.float32)  # this_block.split(" ")
            
            size = len(this_block)
            # get max value, for first guess at diagonals
            off_diag = math.sqrt(float(max(this_block))/2)  # no good reason to start here, assum +ive covariances
            # build matrix, check if positive definite
            is_pos_def = False
            
            count = 0
            matrix = []

            while not is_pos_def and count < 100:
                off_diag *= 0.5 
                matrix = np.zeros([size, size])
                # bands up to bandwidth
                for this_row in range(size-1):
                    if this_row < bandwidth:
                        val = off_diag
                    else:
                        val = 0 
                    for this_col in range(this_row):
                        matrix[this_row, this_col] = val
                
                np.fill_diagonal(matrix, this_block)
                is_pos_def = np.all(np.linalg.eigvals(matrix) > 0)  # works if matrix is symmetrical
                count += 1
            # only include band width up to band width
            new_block = ["$OMEGA BLOCK(" + str(size) + ")"]
            for this_eta in range(size):
                new_block.append(np.array2string(matrix[this_eta][:(1+this_eta)]).replace("[", "").replace("]", ""))
            new_omega_block = copy.copy(new_block)
            new_omega_block = '\n'.join(str(x) for x in new_omega_block)
            new_omega_block = new_omega_block.replace(",", "\n").replace("[", "").replace("]", "")
            all_omega_blocks.append(copy.deepcopy(new_omega_block))
        # start from the bottom (so the line number doesn't change) delete all $OMEGA,
        # but replace the first one with the new_omega_block
            
    num_omega_blocks = len(omega_starts) 
    for num in range(num_omega_blocks):
        line_in_block = 0
        # split this omega block into lines ONLY if it is just a string (will already be array if BLOCK)
        if isinstance(all_omega_blocks[num], str):
            this_new_omega_block = all_omega_blocks[num].split("\n")
        else:
            this_new_omega_block = all_omega_blocks[num]
        for this_line in range(omega_starts[num], omega_ends[num]):
            if line_in_block < len(this_new_omega_block):
                control_list[this_line] = this_new_omega_block[line_in_block]
            else:
                control_list[this_line] = ""
            line_in_block += 1
            # reassemble into a single string
    control = '\n'.join(control_list)
    
    return control
