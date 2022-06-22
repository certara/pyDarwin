import sys
import os
import re
import glob
import xmltodict

from collections import OrderedDict

from .ModelEngineAdapter import ModelEngineAdapter
from .ModelRun import ModelRun

import darwin.utils as utils

from darwin.Log import log
from darwin.options import options

from .Template import Template
from .ModelCode import ModelCode

from .omega_utils import set_omega_bands


class NMEngineAdapter(ModelEngineAdapter):

    @staticmethod
    def get_engine_name() -> str:
        return 'nonmem'

    @staticmethod
    def get_error_messages(run: ModelRun):
        """
        Reads NMTRAN messages from the FMSG file and error messages from the PRDERR file.
        """
        nm_translation_message = prd_err = ""

        errors = ['PK PARAMETER FOR',
                  'IS TOO CLOSE TO AN EIGENVALUE',
                  'F OR DERIVATIVE RETURNED BY PRED IS INFINITE (INF) OR NOT A NUMBER (NAN)',
                  'OCCURS DURING SEARCH FOR ETA AT INITIAL VALUE, ETA=0']

        lines = _file_to_lines(os.path.join(run.run_dir, "PRDERR"))

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
                    ' (WARNING  40) $THETA INCLUDES A NON-FIXED INITIAL ESTIMATE CORRESPONDING TO\n']
        short_warnings = ['NON-FIXED OMEGA ', 'NON-FIXED PARAMETER ', 'NON-FIXED THETA']

        f_msg = _file_to_lines(os.path.join(run.run_dir, "FMSG"))

        for warning, short_warning in zip(warnings, short_warnings):
            if warning in f_msg:
                nm_translation_message += short_warning

        errors = [' AN ERROR WAS FOUND IN THE CONTROL STATEMENTS.']

        # if an error is found, print out the rest of the text immediately, and add to errors
        for error in errors:
            if error in f_msg:
                start = f_msg.index(error)

                error_text = ", ".join(f_msg[start:])

                # log.error("ERROR in Model " + str(self.model_num) + ": " + error_text)

                nm_translation_message += error_text

                break

        if nm_translation_message == "" or nm_translation_message.strip() == ",":
            nm_translation_message = "No important warnings"

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

        # this appears to be OK with search_omega_bands
        phenotype = OrderedDict(zip(template.tokens.keys(), model_code.IntCode))

        non_influential_tokens = _get_non_inf_tokens(template.tokens, phenotype)

        control = template.template_text

        any_found = True  # keep looping, looking for nested tokens
        token_found = False  # error check to see if any tokens are present

        for _ in range(5):  # up to 4 levels of nesting?
            any_found, control = utils.replace_tokens(template.tokens, control, phenotype, non_influential_tokens)
            token_found = token_found or any_found

            if not any_found:
                break

        non_influential_token_num = sum(non_influential_tokens)

        if not token_found:
            log.error("No tokens found, exiting")
            raise RuntimeError("No tokens found")

        if any_found:
            log.error("It appears that there is more than four level of nested tokens."
                      " Only four levels are supported, exiting")
            raise RuntimeError("Are there more than 4 levels of nested tokens?")

        control = utils.match_thetas(control, template.tokens, template.var_theta_block, phenotype,
                                     template.last_fixed_theta)
        control = utils.match_rands(control, template.tokens, template.var_omega_block, phenotype,
                                    template.last_fixed_eta, "ETA")
        control = utils.match_rands(control, template.tokens, template.var_sigma_block, phenotype,
                                    template.last_fixed_eps, "EPS")
        control = utils.match_rands(control, template.tokens, template.var_sigma_block, phenotype,
                                    template.last_fixed_eps, "ERR")  # check for ERRo as well

        model_code_str = str(model_code.FullBinCode if (options.isGA or options.isPSO) else model_code.IntCode)

        control += "\n ;; Phenotype \n ;; " + str(phenotype) + "\n;; Genotype \n ;; " + model_code_str \
                   + "\n;; Num non-influential tokens = " + str(non_influential_token_num)

        # add band OMEGA
        if options.search_omega_bands:
            # bandwidth must be last gene
            bandwidth = model_code.IntCode[-1]

            control = set_omega_bands(control, bandwidth)

        return phenotype, control, non_influential_token_num

    @staticmethod
    def cleanup(run_dir: str, file_stem: str):
        """
        Deletes all unneeded files after run.
        Note that an option "remove_run_dir" in the options file to remove the entire run_dir.
        By default, key files (.lst, .xml, mod and any $TABLE files are retained).

        Note however that any files that starts 'FILE' or 'WK' will be removed even if remove_run_dir is set to false.
        """

        try:
            if options.remove_run_dir:
                try:
                    utils.remove_dir(run_dir)
                except OSError:
                    log.error(f"Cannot remove folder {run_dir} in call to cleanup")
            else:
                file_to_delete = [
                    "PRSIZES.F90",
                    "GFCOMPILE.BAT",
                    "FSTREAM",
                    "fsubs.90",
                    "compile.lnk",
                    "FDATA",
                    "FCON",
                    "FREPORT",
                    "LINK.LNK",
                    "FSIZES"
                    "ifort.txt",
                    "nmpathlist.txt",
                    "nmprd4p.mod",
                    "PRSIZES.f90",
                    "INTER",
                    file_stem + ".ext",
                    file_stem + ".clt",
                    file_stem + ".coi",
                    file_stem + ".cor",
                    file_stem + ".cov",
                    file_stem + ".cpu",
                    file_stem + ".grd",
                    file_stem + ".phi",
                    file_stem + ".shm",
                    file_stem + ".smt",
                    file_stem + ".shk",
                    file_stem + ".rmt",
                    file_stem + ".exe"
                ]

                file_to_delete += glob.glob('FILE*') + glob.glob('WK*.*') + glob.glob('*.lnk') + glob.glob("FSUB*.*")

                for f in file_to_delete:
                    try:
                        os.remove(os.path.join(run_dir, f))
                    except OSError:
                        pass

                utils.remove_dir(os.path.join(run_dir, "temp_dir"))
        except OSError as e:
            log.error(f"OS Error {e}")

        return

    @staticmethod
    def get_model_run_command(run: ModelRun) -> list:
        return [options.nmfe_path, run.control_file_name, run.output_file_name,
                " -nmexec=" + run.executable_file_name, f'-rundir={run.run_dir}']

    @staticmethod
    def get_stem(generation, model_num) -> str:
        return f'NM_{generation}_{model_num}'

    @staticmethod
    def get_file_names(stem: str):
        return stem + ".mod", stem + ".lst", stem + ".exe"

    @staticmethod
    def read_data_file_name(control_file_name: str) -> list:
        """
        Parses the control file to read the data file name

        :return: data file path string
        :rtype: list
        """

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
    def read_results(run: ModelRun):
        success = covariance = correlation = False
        ofv = condition_num = options.crash_value

        res = run.result
        res_file = os.path.join(run.run_dir, run.file_stem + ".xml")

        if not os.path.exists(res_file):
            return

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
                problem = problem[0]       # use the first

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
            if 'nm:covariance_status' in last_estimation:
                if last_estimation['nm:covariance_status']['@nm:error'] == '0':
                    covariance = True

                corr_data = last_estimation.get('nm:correlation', {}).get('nm:row', [])
                num_rows = len(corr_data)

                correlation = num_rows > 0

                for this_row in range(1, num_rows):
                    row_data = corr_data[this_row]['nm:col'][:-1]

                    def abs_function(t):
                        return abs(t) > 99999

                    row_data = [abs_function(float(x['#text'])) for x in row_data]

                    if any(row_data):
                        correlation = False
                        break

                if 'nm:eigenvalues' in last_estimation:
                    # if last_estimation['nm:eigenvalues'] is None:
                    eigenvalues = last_estimation['nm:eigenvalues']['nm:val']
                    max_val = -9999999
                    min_val = 9999999

                    for i in eigenvalues:
                        val = float(i['#text'])
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

        except:
            pass

    @staticmethod
    def read_model(run: ModelRun):
        if not os.path.exists(os.path.join(run.run_dir, "FCON")):
            return

        try:
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
            rest_after_uppr_start = fcon_lines[(uppr_start_line+1):]
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

            for sigma in range(nomegablocks, (nomegablocks+nsigmablocks)):
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

        except:
            pass


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
            trimmed_token = utils.remove_comments(token)

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
    rest_of_block = fcon[(1+start):]
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
