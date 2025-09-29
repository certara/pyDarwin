import re
import numpy as np

from darwin.options import options
from darwin.utils import get_token_parts, replace_tokens
from darwin.Log import log

MUReferenceMessageDone = False

_var_regex = {}


def _do_mu_ref(control: str, k: str, v: str) -> str:
    global MUReferenceMessageDone

    if 'MU_' in control and not MUReferenceMessageDone:
        log.message(f"Mu Reference variable(s) found for {k}")
        MUReferenceMessageDone = True

    return control.replace(f"MU({k})", f"MU_{v}")


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

    expanded_var_block = replace_tokens(tokens, '\n'.join(var_block), phenotype, [], options.TOKEN_NESTING_LIMIT)

    # then look at each token, get THETA(alpha) from non-THETA block tokens
    var_indices = _get_var_matches(expanded_var_block.split('\n'), tokens, phenotype, stem)

    # add last fixed var value to all
    for k, v in var_indices.items():
        # and put into control file
        control = control.replace(f"{stem}({k})", f"{stem}({v})")

        # and if ETA, look for MU(stem)
        if stem == 'ETA':
            control = _do_mu_ref(control, k, v)

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

    # Filter out any variable name containing 'LOG'
    res = [v for v in res if 'LOG' not in v]

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
        
        # Make units work w/ mu ref
        if len(variables) > 1:
            variables = variables[:1]

        for var in variables:
            if var and var not in var_matches:
                var_matches[var] = var_index
                var_index += 1

    return var_matches


def get_omega_block(start: list) -> np.array:
    # remove comments, each value in $OMEGA needs to be new line
    block = remove_comments(start).splitlines()
    # remove any blank lines
    block[:] = [x for x in block if x]
    # and collect the values, to be used on diagonal
    block = ' '.join([str(elem) for elem in block]).replace("\n", "") \
        .replace("  ", " ").replace("  ", " ").strip()
    block = block.split(" ")  # should be numbers only at this point

    if block == ['']:
        return []

    block = np.array(block, dtype=np.float32)

    # round to 6 digits (? is this enough digits, ever a need for > 6?, cannot round to 0, that is error)
    block = np.around(block, decimals=7, out=None)  # just the diagonal

    return block


def remove_comments(code, comment_mark=';') -> str:
    """ Remove any comments from the *code*

    :param code: Input code
    :type code: str or list
    :param comment_mark: Mark of the beginning of a comment in the line
    :return: Code with comments removed
    :rtype: str
    """

    if type(code) != list:
        lines = code.splitlines()
    else:
        lines = code

    lines = [(line[:line.find(comment_mark)] if line.find(comment_mark) > -1 else line).strip() for line in lines]

    return '\n'.join(lines)
