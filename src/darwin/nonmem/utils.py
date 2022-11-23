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
    control_list = control.splitlines()
    lines = control_list  # can't remove comments remove_comments(control).splitlines()
    omega_starts = [idx for idx, element in enumerate(lines) if re.search(r"^\$OMEGA", element)]
    omega_ends = []
    omega_blocks = []
    not_omega_blocks = []
    not_omega_start = 0
    num_omega_starts = len(omega_starts)
    # in the position of the original $OMEGAs?
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
        not_omega_blocks.append(copy.copy(lines[not_omega_start:this_start]))
        not_omega_start = this_omega_ends
    # and the last one
    # get next block after $OMEGA
    # next_block_start = [idx for idx, element in enumerate(rest_of_text[1:]) if re.search(r"^\$", element)]
    # next_block_start = next_block_start[0]
    not_omega_blocks.append(copy.copy(lines[not_omega_start:]))
    all_omega_blocks = []
    num_diag_omega = []

    start_num = 0  # keep track of which omega start this, do add multiple new omega block when we put control back
    for this_start in omega_blocks:
        if re.search(r".*;.*search.*band", this_start[0], re.IGNORECASE) is not None:  # $OMEGA should be first line
            this_block = copy.deepcopy(this_start)
            this_block = remove_comments(this_block).splitlines()
            this_block[0] = this_block[0].replace("$OMEGA", "")
            # remove any blank lines
            this_block[:] = [x for x in this_block if x]
            # and collect the values, to be used on diagonal
            this_block = ' '.join([str(elem) for elem in this_block]).replace("\n", "") \
                .replace("  ", " ").replace("  ", " ").strip()
            this_block = this_block.split(" ")
            this_block = np.array(this_block, dtype=np.float32)  # this_block.split(" ")
            # round to 6 digits (? is this enough digits, ever a need for > 6?)
            this_block = np.around(this_block, decimals=6, out=None)
        num_diag_omega.append(this_block)  # numerical diagonal omegas
    # if using omega_sub_matrices, split omega_blocks here
    if omega_band_pos[0] > -99:
        omega_blocks_in_start = np.zeros(num_omega_starts,
                                         dtype=int)  # after we divide up the omega matrices (how many go
        new_omega_blocks = []
        for old_diag_block in num_diag_omega:
            temp_omega_band_pos = copy.copy(omega_band_pos)
            divided_omega_blocks = []  # numerical diagonal blocks
            while len(old_diag_block) > 0:
                current_omega_block = [old_diag_block[0]]
                old_diag_block = old_diag_block[1:]
                omega_blocks_in_start[start_num] += 1
                # current_omega_block = old_diag_block.pop()
                include_next = temp_omega_band_pos.pop(0)
                while include_next & (
                        len(old_diag_block) > 0):  # & (next_diag_element < (len(old_diag_block)) - 1):  # append to current block
                    #omega_blocks_in_start[start_num] += 1
                    # next_diag_element += 1
                    current_omega_block.append(old_diag_block[0])
                    old_diag_block = old_diag_block[1:]
                    if len(temp_omega_band_pos) > 0:
                        include_next = temp_omega_band_pos.pop(0)
                    else:
                        include_next = False
                        break
                # num_blocks += 1
                # this_rec = 0  # new block, start over in omega_band_pos
                temp_omega_band_pos = copy.copy(omega_band_pos)  # reset
                divided_omega_blocks.append(current_omega_block)
                # next_diag_element -= 1
                #    current_omega_block = []
            start_num += 1
            for this_mat in divided_omega_blocks:
                new_omega_blocks.append(this_mat)
    else:
        new_omega_blocks = num_diag_omega
        omega_blocks_in_start = np.ones(len(omega_blocks), dtype=int)  # just one per block
    # for each value in omega_band_pos, if 0 then separate from next, if 1, include next one.
    for this_start in new_omega_blocks:
        size = len(this_start)
        # get max value, for first guess at diagonals
        # build matrix, check if positive definite
        is_pos_def = False
        count = 0
        matrix = []
        # note that initial assumption of off-diagonals is 0, we do want them to be small, will randomly pick number
        # between + and + largest number that makes it pos definite
        init_off_diags = np.ones([size, size])
        is_pos_def = False
        factor = 1.0
        while not is_pos_def and count < 51:
            factor *= 0.5
            for this_row in range(size):
                row_diag = math.sqrt(this_start[this_row])
                init_off_diags[this_row, this_row] = this_start[this_row]
                for this_col in range(this_row):
                    col_diag = math.sqrt(this_start[this_col])
                    # for off diagonals, pick a random number between +/- val
                    val = factor * row_diag * col_diag
                    val = random.uniform(-val, val)
                    # minimum abs value of 0.0000001
                    val = np.size(val) * (max(abs(val), 0.0000001))  # keep sign, but abs(val) >=0.0000001
                    # give nmtran error
                    init_off_diags[this_row, this_col] = init_off_diags[this_col, this_row] = val
            is_pos_def = np.all(np.linalg.eigvals(init_off_diags) > 0)  # works if matrix is symmetrical
            count += 1
            if count > 50:
                log.error(f"Cannot find positive definite Omega matrix, consider not using search_omega")

        for this_row in range(size):
            for this_col in range(this_row + 1):
                # get how far from diagonal
                band = abs(this_row - this_col)
                if band > bandwidth:
                    init_off_diags[this_row, this_col] = init_off_diags[this_col, this_row] = 0
        all_omega_blocks.append(init_off_diags)
    new_control = ""
    cur_new_omega_block = 0
    # reassemble control file
    for num in range(num_omega_starts):
        for this_line in not_omega_blocks[num]:
            new_control += (this_line.strip() + "\n")
        #cur_row = 1  # only want lower triangle + diagonal
        #cur_overall_block = 0
        for this_new_block in range(omega_blocks_in_start[num]):
            new_control += ("$OMEGA BLOCK(" + str(int(math.sqrt(all_omega_blocks[cur_new_omega_block].size))) +
                            ") ;; omega band width = " +
                            str(bandwidth) + ", omega continuation = " + str(omega_band_pos) + "\n ")
            cur_row = 1
            for this_line in all_omega_blocks[cur_new_omega_block]:
                this_row = ""
                for this_eta in np.asarray(this_line)[0:cur_row]:
                    this_row += (str(this_eta) + " ")
                new_control += (this_row + "\n")
                cur_row += 1
            cur_new_omega_block += 1

        for this_line in not_omega_blocks[num + 1]:
            new_control += this_line
            new_control += "\n"
    return new_control
