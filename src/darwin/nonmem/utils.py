import re
import math
import numpy as np
import copy
import random
from darwin.utils import remove_comments, get_token_parts, replace_tokens

from darwin.Log import log

_var_regex = {}


def match_vars(control: str, tokens: dict, var_block: list, phenotype: dict, stem: str) -> str:
    """
    Finds every occurrence of the variable (defined by *stem*, 'ETA', 'THETA', etc.) in the *control*, assigns it
    appropriate index according to *var_block*, and replaces original variable entries with those with indices.

    :param control: Control file text
    :type control: str

    :param tokens: Token groups
    :type tokens: dict

    :param var_block: Variable definition block
    :type var_block: str

    :param phenotype: Phenotype for model
    :type phenotype: dict

    :param stem: Variable stem
    :type stem: str

    :return: Modified control content
    :rtype: str
    """
    # EXAMPLED_THETA_BLOCK IS THE FINAL $THETA BLOCK FOR THIS MODEL, WITH THE TOKEN TEXT SUBSTITUTED IN
    # EXPANDED TO ONE LINE PER THETA
    # token ({'ADVAN[3]}) will be present on if there is a THETA(???) in it
    # one instance of token for each theta present, so they can be counted
    # may be empty list ([]), but each element must contain '{??[N]}

    any_found, expanded_var_block = replace_tokens(tokens, '\n'.join(var_block), phenotype, [])

    # then look at each token, get THETA(alpha) from non-THETA block tokens
    var_indices = _get_var_matches(expanded_var_block.split('\n'), tokens, phenotype, stem)

    # add last fixed var value to all
    for k, v in var_indices.items():
        # and put into control file
        control = control.replace(stem + "(" + k + ")", stem + "(" + str(v) + ")")

    return control


def _get_var_regex(var_type: str):
    """
    Get compiled regex for the variable.

    :param var_type: Variable stem ('ETA', 'THETA', etc.)
    :return: Compiled regex
    """
    regex = _var_regex.get(var_type)

    if not regex:
        var_name_pattern = r'([\w~]+)'

        simple_def = r";\s*" + var_name_pattern + r"\s*(?![^;])"
        bracket_def = r";.*?\b" + var_type + r"\(" + var_name_pattern + r"\)"
        on_def = r";.*?\b" + var_type + r"\s(?:ON|on)\s" + var_name_pattern

        regex = re.compile(f'{simple_def}|{bracket_def}|{on_def}')
        _var_regex[var_type] = regex

    return regex


def _get_var_names(row: str, var_type: str) -> list:
    """
    Find all *var_type* variable names in the *row*.
    """

    regex = _get_var_regex(var_type)

    res = [m for t in [x.groups() for x in regex.finditer(row)] for m in t if m is not None]

    return res


def _get_var_matches(expanded_block: list, tokens: dict, full_phenotype: dict, var_type: str) -> dict:
    """
    Get indices for all *var_type* variable entries in *expanded_block*.
    """

    var_matches = {}
    var_index = 1

    full_block = ""

    for var_row in expanded_block:
        stem, index = get_token_parts(var_row)

        if stem:
            phenotype = full_phenotype[stem]

            new_string = tokens[stem][phenotype][index - 1]
        else:
            new_string = var_row

        full_block += new_string + '\n'

    for row in full_block.split('\n'):
        if not remove_comments(row):
            continue

        variables = _get_var_names(row, var_type)

        for var in variables:
            if var and var not in var_matches:
                var_matches[var] = var_index
                var_index += 1

    return var_matches


def set_omega_bands(control: str, bandwidth: int, omega_band_pos):
    """
    Removes ALL existing omega blocks from control, then inserts a series of $OMEGAs. These will be unchanged
    if the source is BLOCK or DIAG. If it is not specified BLOCK or DIAG (and so is by default DIAG), will convert
    to BLOCK with the number of bands specified in the model code.
    Will then split up the OMEGA matrix into sub matrices (individual $OMEGA block) based on omega_band_pos

    :param control: existing control file
    :type control: str

    :param bandwidth: require band width
    :type bandwidth: int

    :param omega_band_pos: require array of 0|1 whether to continue the omega block into the next one
    :type omega_band_pos: ndarray

    :return: modified control file
    :rtype: str
    """
    # cut out all $OMEGA block, just put all at th end

    control_list = control.splitlines()
    lines = control_list
    omega_starts = [idx for idx, element in enumerate(lines) if re.search(r"^\$OMEGA", element)]
    omega_ends = []
    omega_blocks = []
    temp_final_control = list()
    not_omega_start = 0

    for this_start in omega_starts:
        # if FIX (fix) do not add off diagonals
        rest_of_text = lines[this_start:]
        next_block_start = [idx for idx, element in enumerate(rest_of_text[1:]) if re.search(r"^\$", element)]
        if next_block_start is None:
            next_block_start = len(rest_of_text)
        else:
            next_block_start = next_block_start[0]
        this_omega_ends = next_block_start + this_start + 1
        omega_ends.append(this_omega_ends)
        omega_blocks.append(copy.copy(lines[this_start:this_omega_ends]))
        temp_final_control.append(copy.copy(lines[not_omega_start:this_start]))
        not_omega_start = this_omega_ends
    # and the last one
    # get next block after $OMEGA

    temp_final_control.append(copy.copy(lines[not_omega_start:]))
    # and convert final_control to string, probably a better way to do this?
    final_control = ""
    for i in temp_final_control:
        for n in i:
            final_control = final_control + "\n" + n

    for this_start in omega_blocks:
        # what if no ; search_band? or only some with search Omega band??
        if re.search(r".*;.*search.*band", this_start[0], re.IGNORECASE) is not None:  # $OMEGA should be first line
            temp_omega_band_pos = copy.deepcopy(omega_band_pos)  # temp copy, to use pop, start over each new block
            this_block = copy.deepcopy(this_start)  # still full text of $OMEGA block
            this_block = remove_comments(this_block).splitlines()   # remove comments, each value
                                                                    # in $OMEGA needs to be new line
            this_block = this_block[1:]  # first line must be only $OMEGA + comments
            # remove any blank lines
            this_block[:] = [x for x in this_block if x]
            # and collect the values, to be used on diagonal
            this_block = ' '.join([str(elem) for elem in this_block]).replace("\n", "") \
                .replace("  ", " ").replace("  ", " ").strip()
            this_block = this_block.split(" ")  # should be numbers only at this point
            this_block = np.array(this_block, dtype=np.float32)  # this_block.split(" ")
            # round to 6 digits (? is this enough digits, ever a need for > 6?, cannot round to 0, that is error)
            this_block = np.around(this_block, decimals=7, out=None) # just the diagonal
            old_diag_block = this_block
            while len(old_diag_block) > 0:  # any left?
                current_omega_block = [old_diag_block[0]]  # start with first
                old_diag_block = old_diag_block[1:]      # save the remaining lines
                omega_size = 1  # how big  is current $OMEGA?
                if len(temp_omega_band_pos) > 0 and temp_omega_band_pos[0] != -99:
                    include_next = temp_omega_band_pos[0]  # is next record in omega block to be continuous?
                else:
                    include_next = 0  # reached max block size
                if len(temp_omega_band_pos) >= 1:
                    temp_omega_band_pos = temp_omega_band_pos[1:]
                else:
                    temp_omega_band_pos = []
                while include_next & (len(old_diag_block) > 0):  # & (next_diag_element < (len(old_diag_block)) - 1):  # append to current block
                    current_omega_block.append(old_diag_block[0])
                    old_diag_block = old_diag_block[1:]
                    omega_size += 1
                    if len(temp_omega_band_pos) > 0:
                        include_next = temp_omega_band_pos.pop(0)
                    else:
                        include_next = False

                # diagonals for $OMEGA done, add bands to current_omega_block
                init_off_diags = current_omega_block  # will overwrite late if band is used
                if bandwidth > 0 and any(omega_band_pos) and omega_band_pos[0] != -99:
                    init_off_diags = np.ones([omega_size, omega_size])
                    is_pos_def = False
                    factor = 1.0
                    count = 0
                    while not is_pos_def and count < 51:
                        factor *= 0.5
                        for this_row in range(omega_size):
                            row_diag = math.sqrt(current_omega_block[this_row])
                            init_off_diags[this_row, this_row] = current_omega_block[this_row]

                            for this_col in range(this_row):
                                col_diag = math.sqrt(current_omega_block[this_col])
                                # for off diagonals, pick a random number between +/- val
                                val = factor * row_diag * col_diag
                                val = random.uniform(-val, val)
                                # minimum abs value of 0.0000001, 0.0 will give error in NONMEM
                                val = np.size(val) * (max(abs(val), 0.0000001))  # keep sign, but abs(val) >=0.0000001
                                # give nmtran error
                                init_off_diags[this_row, this_col] = \
                                    init_off_diags[this_col, this_row] = val
                        # set any bands > bandwidth to 0
                        for this_band_row in range((bandwidth + 1), omega_size):  # start in row after bandwidth
                            for this_band_col in range(0, (this_band_row-bandwidth)):
                                init_off_diags[this_band_col, this_band_row] = \
                                    init_off_diags[this_band_row, this_band_col] = 0
                        is_pos_def = np.all(np.linalg.eigvals(init_off_diags) > 0)  # matrix must be symmetrical
                        count += 1
                        if count > 50:
                            log.error(f"Cannot find positive definite Omega matrix, consider not using search_omega")

                # and add $OMEGA to start
                if omega_size == 1 or bandwidth == 0:
                    final_control = final_control + "\n" + "$OMEGA  ;; block omega searched for bands\n"
                else:
                    final_control = final_control + "\n" + "$OMEGA BLOCK(" + str(omega_size) + \
                                    ") ;; block omega searched for bands, omegasize = " + str(omega_size) + "\n"

                this_rec = 0
                for i in init_off_diags:
                    if isinstance(i, (float, np.float32, np.float64)):  # a float, not a np.array
                        final_control = final_control + str(round(i, 7)) + " \n"
                    else:
                        final_control = final_control + " ".join(map(str, np.around(i[:(this_rec+1)], 7).tolist())) \
                                        + " \n"
                    this_rec += 1
        else:
            final_control = final_control + "\n" + '\n'.join(str(x) for x in this_start)
    return final_control
