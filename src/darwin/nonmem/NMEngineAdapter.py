import sys
import os
import re
import glob
import xmltodict
import numpy as np

from collections import OrderedDict

from darwin.ModelEngineAdapter import ModelEngineAdapter, register_engine_adapter
from darwin.ModelRun import ModelRun

import darwin.utils as utils

from darwin.Log import log
from darwin.options import options

from darwin.Template import Template
from darwin.ModelCode import ModelCode
from darwin.omega_search import apply_omega_bands, get_bands, get_max_search_block

from .utils import match_vars, remove_comments, get_omega_block


class NMEngineAdapter(ModelEngineAdapter):

    @staticmethod
    def get_engine_name() -> str:
        return 'nonmem'

    @staticmethod
    def init_template(template: Template):
        template_text = template.template_text

        template.theta_block = _get_variable_block(template_text, "$THETA")
        template.omega_block = _get_variable_block(template_text, "$OMEGA")
        template.sigma_block = _get_variable_block(template_text, "$SIGMA")

        _check_for_prior(template_text)
        _check_for_multiple_probs(template_text)

    @staticmethod
    def get_max_search_block(template: Template) -> tuple:
        return get_max_search_block(template.template_text, template.tokens,
                                    r'(^\s*\$OMEGA\b[^$]*;\s*search\s+band.*?\n([^$]+))', get_omega_block)

    @staticmethod
    def init_engine():
        nmfe_path = options.get('nmfe_path', None)

        if not nmfe_path:
            log.error('nmfe_path must be set for running NONMEM models')
            return False

        if not os.path.exists(nmfe_path):
            log.error(f"NMFE path '{nmfe_path}' seems to be missing")
            return False

        log.message(f"NMFE found: {nmfe_path}")

        if options.use_parallel:
            pnm_path = options.pnm_file

            if not os.path.exists(pnm_path):
                log.error(f"PNM file '{pnm_path}' seems to be missing")

                return False

            log.message('Parallel NONMEM will be used')
            log.message(f"PNM file found: {pnm_path}")

        return True

    @staticmethod
    def get_error_messages(run: ModelRun, run_dir: str):
        """
        Reads NMTRAN messages from the FMSG file and error messages from the PRDERR file.
        """
        nm_translation_message = prd_err = ""

        lst = _read_file(run.output_file_name, run.run_dir)
        if re.search(r'\*\*\*\* NONMEM LICENSE HAS EXPIRED \*\*\*\*', lst, flags=re.RegexFlag.MULTILINE):
            return '', '**** NONMEM LICENSE HAS EXPIRED ****'

        errors = ['PK PARAMETER FOR',
                  'IS TOO CLOSE TO AN EIGENVALUE',
                  'F OR DERIVATIVE RETURNED BY PRED IS INFINITE (INF) OR NOT A NUMBER (NAN)',
                  'OCCURS DURING SEARCH FOR ETA AT INITIAL VALUE, ETA=0',
                  'A ROOT OF THE CHARACTERISTIC EQUATION IS ZERO BECAUSE',
                  'THE CHARACTERISTIC EQUATION CANNOT BE SOLVED']

        lines = _file_to_lines(os.path.join(run.run_dir, 'PRDERR'))

        if lines:
            found = False
            for error in errors:
                for line in lines:
                    if error in line and not (line.strip() + " ") in prd_err:
                        prd_err += line.strip() + " "
                        found = True

            if not found:  # only write this once, if nothing is found
                prd_err += f"Unidentified error in PRDERR for model run {run.generation}, {run.model_num}\n"

        warnings = [' (WARNING  31) $OMEGA INCLUDES A NON-FIXED INITIAL ESTIMATE CORRESPONDING TO\n',
                    ' (WARNING  41) NON-FIXED PARAMETER ESTIMATES CORRESPONDING TO UNUSED\n',
                    ' (WARNING  40) $THETA INCLUDES A NON-FIXED INITIAL ESTIMATE CORRESPONDING TO\n',
                    ' (MU_WARNING 26) DATA ITEM(S) USED IN DEFINITION OF MU_(S) SHOULD BE CONSTANT FOR INDIV. REC.:\n',
                    ' ONE OR MORE RANDOM VARIABLES ARE DEFINED WITH "IF" STATEMENTS THAT DO NOT\n']

        # really not sure what to do with the mu referencing warning, warning is generated regardless
        # of whether there are time varying covariates
        short_warnings = ['NON-FIXED OMEGA',
                          'NON-FIXED PARAMETER',
                          'NON-FIXED THETA',
                          'Covars should not be time varying with MU ref',
                          'RANDOM VARIABLES DEFINED WITH IF NOT IF..ELSE']

        f_msg = _file_to_lines(os.path.join(run.run_dir, "FMSG"))

        for warning, short_warning in zip(warnings, short_warnings):
            if warning in f_msg:
                if warning == ' (MU_WARNING 26) DATA ITEM(S) USED IN DEFINITION OF MU_(S) SHOULD BE CONSTANT FOR INDIV. REC.:\n':
                    where = f_msg.index(' (MU_WARNING 26) DATA ITEM(S) USED IN DEFINITION OF MU_(S) SHOULD BE CONSTANT FOR INDIV. REC.:\n')
                    covar_name = f_msg[where + 1].strip()
                    warning_message = f"With MU ref {covar_name} should be constant for indiv"
                else:
                    warning_message = short_warning

                nm_translation_message += warning_message

        errors = [' AN ERROR WAS FOUND IN THE CONTROL STATEMENTS.\n']

        # if an error is found, print out the rest of the text immediately, and add to errors
        for error in errors:
            if error in f_msg:
                start = f_msg.index(error)

                error_text = ''.join(f_msg[start:])

                nm_translation_message += error_text

                break

        if nm_translation_message.strip() == ",":
            nm_translation_message = ''

        # try to sort relevant message?
        # key are
        # (WARNING  31) - non-fixed OMEGA
        # (WARNING  41) - non-fixed parameter
        # (WARNING  40) - non-fixed theta

        return prd_err, nm_translation_message

    @staticmethod
    def make_control(template: Template, model_code: ModelCode):
        """
        Constructs control file from intcode.
        Ignore last value if self_search_omega_bands.
        """

        phenotype = OrderedDict(zip(template.tokens.keys(), model_code.IntCode))

        non_influential_tokens = _get_non_inf_tokens(template.tokens, phenotype)

        control = template.template_text

        token_found, control = utils.replace_tokens(template.tokens, control, phenotype, non_influential_tokens,
                                                    options.TOKEN_NESTING_LIMIT)

        non_influential_token_num = sum(non_influential_tokens)

        control = match_vars(control, template.tokens, template.theta_block, phenotype, "THETA")
        control = match_vars(control, template.tokens, template.omega_block, phenotype, "ETA")
        control = match_vars(control, template.tokens, template.sigma_block, phenotype, "EPS")
        control = match_vars(control, template.tokens, template.sigma_block, phenotype, "ERR")

        model_code_str = str(model_code.FullBinCode if (options.isGA or options.isPSO) else model_code.IntCode)

        control = re.sub(r'^[^\S\r\n]*', '  ', control, flags=re.RegexFlag.MULTILINE)
        control = re.sub(r'^ {2}(?=\$|$)', '', control, flags=re.RegexFlag.MULTILINE)

        control, bands = apply_omega_bands(control, model_code, template.omega_band_pos, set_omega_bands)

        control = re.sub(r'^\s*\$OMEGA(?=(?:\s*;.+\n)?(?:\s+|;.*\n)+(?:\$|\Z))', '; empty $OMEGA',
                         control, flags=re.RegexFlag.MULTILINE)

        phenotype = str(phenotype)
        phenotype = phenotype.replace('OrderedDict', '')
        phenotype += bands

        control += "\n;; Phenotype: " + phenotype + "\n;; Genotype: " + model_code_str \
                   + "\n;; Num non-influential tokens: " + str(non_influential_token_num) + "\n"

        return phenotype, control, non_influential_token_num

    @staticmethod
    def cleanup(run_dir: str, file_stem: str):
        """
        | Deletes all unneeded files after run.
        | By default, key files (.lst, .xml, .mod) are retained.
          If :mono_ref:`remove_run_dir <remove_run_dir_options_desc>` is set to ``true`` then
          entire :mono_ref:`run_dir <model_run_dir>` is deleted.
        """

        if options.remove_run_dir:
            try:
                utils.remove_dir(run_dir)
            except OSError:
                log.error(f"Cannot remove folder {run_dir} in call to cleanup")
        else:
            try:
                utils.remove_dir(os.path.join(run_dir, 'temp_dir'))
            except OSError:
                pass

            files_to_delete = dict.fromkeys(glob.glob('*', root_dir=run_dir))

            files_to_delete.pop(f'{file_stem}.mod', None)
            files_to_delete.pop(f'{file_stem}.lst', None)
            files_to_delete.pop(f'{file_stem}.xml', None)
            files_to_delete.pop('FMSG', None)
            files_to_delete.pop('PRDERR', None)
            files_to_delete.pop('FSTREAM', None)

            for f in files_to_delete:
                try:
                    os.remove(os.path.join(run_dir, f))
                except OSError:
                    pass

        return

    @staticmethod
    def get_model_run_commands(run: ModelRun) -> list:

        command = [options['nmfe_path'], run.control_file_name, run.output_file_name,
                   f"-rundir={run.run_dir}"]

        # fails with full command, problem is exe name. The exe name will be nonmem.exe, but,
        # the xml, .lst etc. is written to the correct name, since this is the .mod file name
        # just the .exe file name is wrong
        if options.use_parallel:
            command.append(f"-parafile={options['pnm_file']}")
        else:
            command.append(f"-nmexec={run.executable_file_name}")

        return [
            {
                'command': command,
                'dir': run.run_dir,
                'timeout': options.model_run_timeout
            }
        ]

    @staticmethod
    def get_stem(generation, model_num) -> str:
        return f'NM_{generation}_{model_num}'

    @staticmethod
    def get_file_names(stem: str):
        return stem + ".mod", stem + ".lst", stem + ".exe"

    @staticmethod
    def get_final_file_names():
        return 'FinalControlFile.mod', 'FinalResultFile.lst'

    @staticmethod
    def read_data_file_name(control_file_name: str) -> list:
        datalines = []

        with open(control_file_name, "r") as f:
            for ln in f:
                if ln.strip().startswith("$DATA"):
                    line = ln.strip()
                    line = line.replace("$DATA ", "").strip()

                    # remove comments
                    if ";" in line:
                        pos = line.index(";")
                        line = line[:pos]

                    # look for quotes, single or double. if no quotes, find first white space
                    if "\"" in line:
                        ll = line.split('"')[1::2]
                        datalines.append(ll[0].strip())
                    elif "\'" in line:
                        ll = line.split("'")[1::2]
                        datalines.append(ll[0].strip())
                    else:
                        # find first while space
                        result = re.search(r'\s', line)
                        if result is None:
                            datalines.append(line.strip())
                        else:
                            datalines.append(line[:result.regs[0][0]].strip())

        return datalines

    @staticmethod
    def read_results(run: ModelRun) -> bool:
        success = covariance = correlation = False
        ofv = condition_num = options.crash_value

        res = run.result
        res_file = os.path.join(run.run_dir, run.file_stem + ".xml")

        if not os.path.exists(res_file):
            return False

        corr_th = options.CORRELATION_THRESHOLD

        try:
            with open(res_file) as xml_file:
                data_dict = xmltodict.parse(xml_file.read())

            version = data_dict['nm:output']['nm:nonmem']['@nm:version']  # string
            # keep first two digits
            dots = [_.start() for _ in re.finditer(r"\.", version)]
            # and get the first two
            major_version = float(version[:dots[1]])  # float

            if major_version < 7.4 or major_version > 7.5:
                log.error(f"NONMEM is version {version}, NONMEM 7.4 and 7.5 are supported, exiting")
                sys.exit()

            problem = data_dict['nm:output']['nm:nonmem']['nm:problem']

            # if more than one problem, use the first, assume that is the estimation, assume final is simulation
            # really not sure what to do if there is more than one estimation problem
            if isinstance(problem, list):  # > 1 one $PROB
                problem = problem[0]  # use the first

            estimations = problem['nm:estimation']

            # similar, may be more than one estimation, if > 1, we want the final one
            if isinstance(estimations, list):  # > 1 one $EST
                last_estimation = estimations[-1]
            else:
                last_estimation = estimations

            if 'nm:final_objective_function' in last_estimation:
                ofv = float(last_estimation['nm:final_objective_function'])

                if last_estimation['nm:termination_status'] == '0':
                    success = True

            # IS COVARIANCE REQUESTED:
            if 'nm:covariance_status' in last_estimation\
                    and last_estimation['nm:covariance_status']['@nm:error'] == '0':

                covariance = True

                corr_data = last_estimation.get('nm:correlation', {}).get('nm:row', [])
                num_rows = len(corr_data)

                correlation = num_rows > 0

                for this_row in range(1, num_rows):
                    row_data = corr_data[this_row]['nm:col'][:-1]

                    for x in row_data:
                        if abs(float(x['#text'])) > corr_th:
                            correlation = False
                            break

                if 'nm:eigenvalues' in last_estimation:
                    # if last_estimation['nm:eigenvalues'] is None:
                    eigenvalues = last_estimation['nm:eigenvalues']['nm:val']
                    max_val = -9999999
                    min_val = 9999999

                    for i in eigenvalues:
                        val = abs(float(i['#text']))
                        if val < min_val:
                            min_val = val
                        if val > max_val:
                            max_val = val

                    condition_num = max_val / min_val

            res.success = success
            res.covariance = covariance
            res.correlation = correlation
            res.ofv = ofv
            res.condition_num = condition_num

            return True

        except:
            pass

        return False

    @staticmethod
    def read_model(run: ModelRun) -> bool:
        if not os.path.exists(os.path.join(run.run_dir, "FCON")):
            return False

        with open(os.path.join(run.run_dir, "FCON"), "r") as fcon:
            fcon_lines = fcon.readlines()

        # IF MORE THAN ONE PROB only use first, the number of parameters will be the same, although
        # the values in subsequent THTA etc. will be different
        prob = [bool(re.search("^PROB", i)) for i in fcon_lines]
        prob_lines = [i for i, x in enumerate(prob) if x]
        # assume only first problem is estimation, subsequent are simulation?
        if len(prob_lines) > 1:
            fcon_lines = fcon_lines[:prob_lines[1]]

        # replace all BLST or DIAG with RNBL (random block) - they will be treated the same
        strc_lines = [idx for idx in fcon_lines if idx[0:4] == "STRC"]

        theta_num = int(strc_lines[0][9:12])

        # HOW MAY LINES IN THETA BLOCK:
        lowr_start = [bool(re.search("^LOWR", i)) for i in fcon_lines]
        lowr_start_line = [i for i, x in enumerate(lowr_start) if x][0]
        uppr_start = [bool(re.search("^UPPR", i)) for i in fcon_lines]
        uppr_start_line = [i for i, x in enumerate(uppr_start) if x][0]

        lowr_lines = fcon_lines[lowr_start_line:uppr_start_line]
        lowr = " ".join(lowr_lines).replace("LOWR", "").strip().replace("\n", ",")
        # remove "," at end
        lowr = lowr.split(",")
        # convert to float
        lowr = [float(a) for a in lowr]

        # find end of UPPR, next will be anything with char in 0-4
        rest_after_uppr_start = fcon_lines[(uppr_start_line + 1):]
        # does line start with non-blank?
        end_of_uppr_bool = [bool(re.search(r"^\S{4}", i)) for i in rest_after_uppr_start]
        end_of_uppr_line = [i for i, x in enumerate(end_of_uppr_bool) if x]
        end_of_uppr = end_of_uppr_line[0]

        uppr_lines = fcon_lines[uppr_start_line:(uppr_start_line + end_of_uppr + 1)]
        uppr = " ".join(uppr_lines).replace("UPPR", "").strip().replace("\n", ",")
        # remove "," at end
        uppr = uppr.split(",")
        # convert to float
        uppr = [float(a) for a in uppr]

        estimated_theta = theta_num

        for i in range(theta_num):
            estimated_theta -= (lowr[i] == uppr[i])  # if upper == lower than this is fixed, not estimated

        fcon_lines = [w.replace('BLST', 'RNBL') for w in fcon_lines]
        fcon_lines = [w.replace('DIAG', 'RNBL') for w in fcon_lines]
        # and all random blocks

        rnbl_start = [bool(re.search("^RNBL", n)) for n in fcon_lines]
        rnbl_start_lines = [i for i, x in enumerate(rnbl_start) if x]

        nomegablocks = int(strc_lines[0][32:36])  # field 7, 0 or blank if diagonal, otherwise # of blocks for omega

        if nomegablocks == 0:
            nomegablocks = 1

        nsigmablocks = int(strc_lines[0][40:44])  # field 9, 0 or 1 if diagonal, otherwise # of blocks for sigma

        if nsigmablocks == 0:
            nsigmablocks = 1

        estimated_sigma = estimated_omega = 0
        omega_num = sigma_num = 0

        for this_omega in range(nomegablocks):
            # if position 8 == 1,this block is fixed, need to remove that value to parse

            if fcon_lines[rnbl_start_lines[this_omega]][7] == '1':
                vals_this_block = _get_block(rnbl_start_lines[this_omega], fcon_lines, True)
            else:
                vals_this_block = _get_block(rnbl_start_lines[this_omega], fcon_lines, False)
                estimated_omega += vals_this_block
            omega_num += vals_this_block

        for sigma in range(nomegablocks, (nomegablocks + nsigmablocks)):
            if fcon_lines[rnbl_start_lines[sigma]][7] == '1':
                vals_this_block = _get_block(rnbl_start_lines[sigma], fcon_lines, True)
            else:
                vals_this_block = _get_block(rnbl_start_lines[sigma], fcon_lines, False)
                estimated_sigma += vals_this_block

            sigma_num += vals_this_block

        model = run.model

        model.theta_num = theta_num
        model.omega_num = omega_num
        model.sigma_num = sigma_num

        model.estimated_theta_num = estimated_theta
        model.estimated_omega_num = estimated_omega
        model.estimated_sigma_num = estimated_sigma

        return True

    @staticmethod
    def can_omega_search(template_text: str) -> tuple:
        """
        Tell if it's possible to perform omega search with current template

        If submatrices are already defined with any BLOCK or DIAG, can't do omega_search
        """

        lines = template_text.splitlines()

        omega_starts = [idx for idx, element in enumerate(lines) if re.search(r'^\$OMEGA', element)]

        if not omega_starts:
            return False, 'No omega blocks.'

        for this_start in omega_starts:
            # if FIX (fix) do not add off diagonals
            rest_of_text = lines[this_start:]
            next_block_start = [idx for idx, element in enumerate(rest_of_text[1:]) if re.search(r'^\$', element)]

            if next_block_start is None:
                next_block_start = len(rest_of_text)
            else:
                next_block_start = next_block_start[0]

            this_omega_ends = next_block_start + this_start + 1

            cur_block = remove_comments(lines[this_start:this_omega_ends]).splitlines()

            for line in cur_block:
                match = re.search(r'\b(BLOCK|DIAG|SAME|FIX)\b', line.upper())
                if match is not None:
                    return False, f"{match.group(1)} omega structure is not compatible with omega search."

        return True, ''

    @staticmethod
    def get_omega_search_pattern() -> str:
        """
        """

        return r'\$OMEGA.*?;\s*search\s+band\b'

    @staticmethod
    def remove_comments(text: str) -> str:

        return remove_comments(text)


def _read_file(file: str, run_dir: str) -> str:
    log_file = os.path.join(run_dir, file)

    if not os.path.exists(log_file):
        return ''

    with open(log_file) as file:
        return file.read()


def _file_to_lines(file_name: str):
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            return file.readlines()

    return []


def _get_non_inf_tokens(tokens: dict, phenotype: OrderedDict):
    """
    Looks at the token set to see if it contains OMEGA/SIGMA/THETA/ETA/EPS or ERR, if so it is influential.
    If not (e.g., the token is empty) it is non-influential.
    """

    token_set_num = 0
    non_influential_tokens = [False] * len(tokens)

    for key, val in tokens.items():
        token_set = val[phenotype[key]]

        for token in token_set:
            trimmed_token = remove_comments(token)

            if "THETA" in trimmed_token or "OMEGA" in trimmed_token or "SIGMA" in trimmed_token \
                    or "ETA(" in trimmed_token or "EPS(" in trimmed_token or "ERR(" in trimmed_token:
                # doesn't contain parm, so can't contribute to non-influential count
                non_influential_tokens[token_set_num] = True
                break

        token_set_num += 1

    return non_influential_tokens


def _get_block(start, fcon, fixed=False):
    # how many lines? find next RNBL
    rnbl_block = fcon[start:]
    rest_of_block = fcon[(1 + start):]
    next_start = [bool(re.search("^RNBL", n)) for n in rest_of_block]

    if any(next_start):
        rnbl_start_lines = [i for i, x in enumerate(next_start) if x][0]  # RNBL lines
        this_block = rnbl_block[:(rnbl_start_lines + 1)]
    else:
        next_start = [bool(re.search(r"^\S+", n)) for n in rest_of_block]
        next_start = [i for i, x in enumerate(next_start) if x][0]  # RNBL lines
        this_block = rnbl_block[:(next_start + 1)]

    # if next_start:
    this_block = " ".join(this_block)

    if fixed:
        # remove 1 i position 7
        this_block = list(this_block)
        this_block[7] = ' '
        this_block = "".join(this_block)

    this_block = this_block[4:].strip().replace("\n", ",")
    this_block = this_block.split(",")

    # convert to float
    this_block = [float(a) for a in this_block]

    # have to remove any 0's they will be 0's for band OMEGA
    this_block = [i for i in this_block if i != 0]

    return len(this_block)


def _not_empty_line(line: str) -> bool:
    return line and remove_comments(line) != ''


def _get_variable_block(template_text, key) -> list:
    code = _get_full_block(template_text, key)

    lines = list(filter(_not_empty_line, code))

    var_block = []

    # how many $ blocks - assume only 1 (for now??)

    for line in lines:
        if re.search(r"{.+}|;\s*\w+", line) is not None:
            var_block.append(line)

    return var_block


def _get_full_block(code, key):
    nkeys = code.count(key)
    # get the block from NONMEM control/template
    # e.g., $THETA, even if $THETA is in several sections
    # were key is $THETA,$OMEGA,$SIGMA
    block = ""
    start = 0
    full_block = []

    for _ in range(nkeys):
        start = code.find(key, start)
        end = code.find("$", start + 1)
        block = block + code[start: end] + '\n'
        start = end
        # remove blank lines, and trim

    lines = block.splitlines()
    full_block.extend(lines)

    return full_block


def _check_for_prior(template_text: str):
    all_lines = remove_comments(template_text)

    any_prior = re.search(r"\$PRIOR", all_lines, flags=re.MULTILINE)

    if any_prior is not None:
        log.error(f"$PRIOR found in template, PRIOR routine is not supported, exiting")
        sys.exit()


def _check_for_multiple_probs(template_text: str):
    # can't have multiple problems, issues with counting $OMEGA and
    # putting all $OMEGA at end of control
    # next version, put $OMEGAs back in original place?

    if not options.search_omega_blocks:
        return

    all_lines = remove_comments(template_text)

    prob_lines = re.findall(r"\$PROB", all_lines)  #

    if len(prob_lines) > 1:
        log.error(f"Search Omega bands is not supported with multiple $PROBs, exiting")
        sys.exit()


def set_omega_bands(control: str, band_width: list, mask_idx: list) -> tuple:
    """
    Removes ALL existing omega blocks from control, then inserts a series of $OMEGAs. These will be unchanged
    if the source is BLOCK or DIAG. If it is not specified BLOCK or DIAG (and so is by default DIAG), will convert
    to BLOCK with the number of bands specified in the model code.
    Will then split up the OMEGA matrix into sub matrices (individual $OMEGA block) based on omega_band_pos

    :param control: existing control file
    :type control: str

    :param band_width: require band widths
    :type band_width: list

    :param mask_idx: require array of 0|1 whether to continue the omega block into the next one
    :type mask_idx: ndarray

    :return: modified control file
    :rtype: str
    """
    # cut out all $OMEGA block, just put all at th end

    control_list = control.splitlines()
    lines = control_list
    omega_starts = [idx for idx, element in enumerate(lines) if re.search(r"^\$OMEGA", element)]
    omega_ends = []
    omega_blocks = []
    temp_final_control = []
    not_omega_start = 0
    band_arr = []

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
        omega_blocks.append(lines[this_start:this_omega_ends])
        temp_final_control.extend(lines[not_omega_start:this_start])
        not_omega_start = this_omega_ends
    # and the last one
    # get next block after $OMEGA

    temp_final_control.extend(lines[not_omega_start:])

    final_control = "\n".join(temp_final_control)

    omega_idx = 0

    for n, start in enumerate(omega_blocks):
        if re.search(r'.*?;\s*search\s+band\b', start[0], re.IGNORECASE) is None:  # $OMEGA should be first line
            final_control += "\n" + '\n'.join(str(x) for x in start)
            continue

        diag_block = get_omega_block(start[1:])

        max_len = options.max_omega_search_lens[omega_idx]

        bands = get_bands(diag_block, band_width[omega_idx], mask_idx[omega_idx], max_len)

        band_start = 0

        for band, block_size in bands:
            if len(band) == 0:
                continue

            # and add $OMEGA to start
            if block_size == 0:
                final_control += "\n" + "$OMEGA  ;; block omega searched for bands\n"
            else:
                final_control += "\n" + "$OMEGA BLOCK(" + str(block_size) + ") ;; block omega searched for bands\n"

                band_arr.append(f"([{n+1}]{band_start}, {len(band)}: {band_width[omega_idx]})")

            band_start += len(band)
            this_rec = 0

            for i in band:
                final_control += " ".join(map(str, np.around(i[:(this_rec + 1)], 7))) + " \n"

                this_rec += 1

        if options.individual_omega_search:
            omega_idx += 1

    return final_control, band_arr


def register():
    register_engine_adapter('nonmem', NMEngineAdapter())
