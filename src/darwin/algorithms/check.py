import numpy as np
import os
import time

import darwin.GlobalVars as GlobalVars

from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import keep_going

from darwin.Template import Template
from darwin.ModelRun import ModelRun
from darwin.ModelCode import ModelCode
from darwin.Population import Population

def set_checkout(control_text) -> str:
    """
    set control file to checkout model, don't run estimation, remove $COV
    """
    ESTfound = False
    control_str = control_text.split('\n')
    this_line = 0
    while this_line < len(control_str):
        if "$EST" in control_str[this_line]:
            if not(ESTfound):
                control_str[this_line] = "$EST METH=0 MAX=0"
                ESTfound = True
            else:
                control_str[this_line] = ";; additional $EST removed"
            # in the event of multiple lines in the $EST block, need to loop to next block ($ in position 1 of trimmed line)
            trim_string = control_str[this_line + 1].rstrip()

            while (this_line + 1) < len(control_str):
                if "$EST" in control_str[this_line + 1]: # another $EST record
                    break
                if len(trim_string) > 0:
                    if trim_string[0] != "$":
                        break
                this_line += 1
                trim_string = control_str[this_line].rstrip()
        if "$COV" in control_str[this_line]:
            control_str[this_line] = ";; removed $COV"
        this_line += 1
    control_str = '\n'.join(control_str)
    return control_str


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
    codes = get_search_space(model_template)

    num_models = codes.shape[0]

    log.message(f"Check out mode will run {num_models} models")
    # break into smaller list, for memory management
    batch_size = options.get('exhaustive_batch_size', 100)

    for start in range(0, num_models, batch_size):
        pop = Population.from_codes(model_template, '0', codes[start:start + batch_size], ModelCode.from_int,
                                    start_number=start, max_number=num_models)

        pop.run(remaining_models=(num_models - GlobalVars.unique_models_num))

        if not keep_going():
            break
            # collect error messages
    error_messages = collect_check_out_errors(pop.runs)
    for this_error in error_messages:
        log.message(f"{this_error}")

    return GlobalVars.best_run


def collect_check_out_errors(runs) -> str:
    # READ FMSG, PRDERR AND .LST FOR "PROGRAM TERMINATED BY OBJ", THEN READ UNTIL #CPUT
    OKwarning = ['WARNINGS AND ERRORS (IF ANY) FOR PROBLEM    1', '(WARNING  2) NM-TRAN INFERS THAT THE DATA ARE POPULATION.']
    error_messages = []
    for this_model in runs:
        file_path = os.path.join(this_model.run_dir, "FMSG")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    FMSG = file.read()
                    FMSG = FMSG.split("\n")

                for this_line in FMSG:
                    this_line = this_line.strip()
                    if this_line in OKwarning:
                        pass
                    else:
                        if len(this_line) > 0:
                            error_messages.append("FMSG from model " + str(this_model.model_num) + " " + this_line)
            except Exception as e:
                log.message(f"An error occurred reading FMSG: {e}")
            # if PRDERR exists, copy all of it
        file_path = os.path.join(this_model.run_dir, "PRDERR")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    PRDERR = file.read()
                error_messages.append("PRDERR from model " + str(this_model.model_num) + " " + PRDERR)
            except Exception as e:
                log.message(f"An error occurred reading PRDERR: {e}")
        # look for PROGRAM TERMINATED BY in .lst

        file_path = os.path.join(this_model.run_dir, this_model.output_file_name)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    lstFile = file.read()
                    lstFile = lstFile.split("\n")
                line = 0
                for this_line in lstFile:
                    this_line = this_line.strip()
                    line += 1
                    if "0PROGRAM TERMINATED BY" in this_line:
                        for tline in range(line , (line + 3)):
                            error_messages.append(str(this_model.model_num) + " " + lstFile[tline])
            except Exception as e:
                log.message(f"An error occurred reading .lst file: {e}")
    return error_messages


def get_search_space(template: Template) -> np.ndarray:


    num_groups = template.get_search_space_coordinates()

    # will get max_dimension models, recycle any dimension with < max_dimension value, e.g.
    # 0,0,0; then 1,1,1, then 0,0,2 if dimension 3 has the max value of 2
    lengths = list(map(len, num_groups))
    num_elements = len(lengths)
    nModels = max(lengths)
    #generate values
    check_codes = []
    for this_model in range(nModels):
        new_codes = np.ones(num_elements, dtype=int) * this_model
        # replace out of range elements
        for this_val in range(num_elements):
            if new_codes[this_val] > (lengths[this_val] - 1):
                new_codes[this_val] = 0
        check_codes.append(new_codes)
    codes = np.array(check_codes)
    return codes


def get_search_space_size(model_template: Template) -> int:
    return get_search_space(model_template).shape[0]
