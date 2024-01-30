import numpy as np
import os
import re

import darwin.GlobalVars as GlobalVars

from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import keep_going

from darwin.Template import Template
from darwin.ModelRun import ModelRun
from darwin.ModelCode import ModelCode
from darwin.Population import Population


def set_checkout(control_text: str) -> str:
    """
    set control file to checkout model, don't run estimation, remove $COV
    """
    lines = control_text.split('\n')
    n_lines = len(lines)
    est_found = False
    i = 0

    while i < n_lines:
        if re.search(r'^\s*\$EST', lines[i].upper()):
            if not est_found:
                lines[i] = '$EST METH=0 MAX=0 ;; - ' + lines[i]
            else:
                lines[i] = ';; additional $EST removed - ' + lines[i]

            i += 1

            # if multiline $EST block, loop to next block
            while i < n_lines:
                if re.search(r'^\s*\$', lines[i]):  # another block
                    break

                if est_found:
                    lines[i] = ';; - ' + lines[i]

                i += 1

            est_found = True

            continue

        elif re.search(r'^\s*\$COV', lines[i].upper()):
            lines[i] = ';; removed $COV - ' + lines[i]

        i += 1

    res = '\n'.join(lines)

    return res


def run_check(model_template: Template) -> ModelRun:
    """
    Run full exhaustive search on the Template, all possible combinations.
    All models will be run in iteration number 0.

    :param model_template: Model Template
    :type model_template: Template

    :return: Returns final/best model run
    :rtype: ModelRun
    """
    # edit control file, replace $EST with $EST METH = 0 MAX=0 PRINT=0
    # remove any other $EST
    # and remove $COV, keep tables
    model_template.template_text = set_checkout(model_template.template_text)
    codes = _get_search_space(model_template)

    num_models = codes.shape[0]

    error_messages = []

    log.message(f"Check out mode will run {num_models} models")

    # break into smaller list, for memory management
    batch_size = options.get('exhaustive_batch_size', 100)

    for start in range(0, num_models, batch_size):
        pop = Population.from_codes(model_template, '0', codes[start:start + batch_size], ModelCode.from_int,
                                    start_number=start, max_number=num_models)

        pop.run(remaining_models=(num_models - GlobalVars.unique_models_num))

        if not keep_going():
            break

        error_messages.extend(collect_check_out_errors(pop.runs))

    for err in error_messages:
        log.message(err)

    return GlobalVars.best_run


def collect_check_out_errors(runs) -> list[str]:
    # READ FMSG, PRDERR AND .LST FOR "PROGRAM TERMINATED BY OBJ", THEN READ UNTIL #CPUT
    white_list = ['WARNINGS AND ERRORS (IF ANY) FOR PROBLEM    1',
                  '(WARNING  2) NM-TRAN INFERS THAT THE DATA ARE POPULATION.']
    error_messages = []

    for run in runs:
        file_path = os.path.join(run.run_dir, 'FMSG')

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    FMSG = file.read().split('\n')

                for msg in FMSG:
                    msg = msg.strip()
                    if len(msg) > 0 and msg not in white_list:
                        error_messages.append('FMSG from model ' + str(run.model_num) + ': ' + msg)

            except Exception as e:
                log.message(f"An error occurred reading FMSG: {e}")

        # if PRDERR exists, copy all of it
        file_path = os.path.join(run.run_dir, 'PRDERR')

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    PRDERR = file.read()
                    error_messages.append("PRDERR from model " + str(run.model_num) + " " + PRDERR)

            except Exception as e:
                log.message(f"An error occurred reading PRDERR: {e}")

        # look for PROGRAM TERMINATED BY in .lst
        file_path = os.path.join(run.run_dir, run.output_file_name)

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    lst_lines = file.read().split('\n')

                line = 0

                for msg in lst_lines:
                    msg = msg.strip()
                    line += 1

                    if 'PROGRAM TERMINATED BY' in msg:
                        for tline in range(line, (line + 3)):
                            error_messages.append(str(run.model_num) + ': ' + lst_lines[tline])

            except Exception as e:
                log.message(f"An error occurred reading .lst file: {e}")

    return error_messages


def _get_search_space(template: Template) -> np.ndarray:
    num_groups = template.get_search_space_coordinates()

    # will get max_dimension models, recycle any dimension with < max_dimension value, e.g.
    # 0,0,0; then 1,1,1, then 0,0,2 if dimension 3 has the max value of 2
    lengths = list(map(len, num_groups))
    n_elements = len(lengths)
    n_models = max(lengths)

    # generate values
    check_codes = []

    for this_model in range(n_models):
        new_codes = np.ones(n_elements, dtype=int) * this_model

        # replace out of range elements
        for this_val in range(n_elements):
            if new_codes[this_val] > (lengths[this_val] - 1):
                new_codes[this_val] = 0

        check_codes.append(new_codes)

    return np.array(check_codes)
