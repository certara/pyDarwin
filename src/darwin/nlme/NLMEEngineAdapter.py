import sys
import os
import re
import glob
import json
import csv

from collections import OrderedDict

from darwin.ModelEngineAdapter import ModelEngineAdapter, register_engine_adapter
from darwin.ModelRun import ModelRun

import darwin.utils as utils

from darwin.Log import log
from darwin.options import options

from darwin.Template import Template
from darwin.ModelCode import ModelCode

from .utils import extract_multiline_block, get_comment_re, extract_data, extract_lhs, extract_rhs_array, extract_ranefs


class NLMEEngineAdapter(ModelEngineAdapter):

    def __init__(self):
        os.environ['INSTALLDIR'] = r'C:/Program Files/Certara/NLME_Engine'
        os.environ['NLMEGCCDir64'] = r'C:/Program Files/Certara/mingw64'
        os.environ['PhoenixLicenseFile'] = r'c:/workspace/Pirana/lservrc'

    @staticmethod
    def get_engine_name() -> str:
        return 'nlme'

    @staticmethod
    def init_template(template: Template):
        pass

    @staticmethod
    def check_settings():
        nlme_dir = options.get('nlme_dir', None)

        if not nlme_dir:
            raise RuntimeError(f"nlme_dir must be set for running NLME models")

        if not os.path.isdir(nlme_dir):
            raise RuntimeError(f"NLME directory '{nlme_dir}' seems to be missing")

        log.message(f"NLME found: {nlme_dir}")

    @staticmethod
    def get_error_messages(run: ModelRun):
        """
        """
        nm_translation_message = prd_err = ""

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

        token_found, control = utils.replace_tokens(template.tokens, control, phenotype, non_influential_tokens)

        non_influential_token_num = sum(non_influential_tokens)

        model_code_str = str(model_code.FullBinCode if (options.isGA or options.isPSO) else model_code.IntCode)

        control = re.sub(r'^[^\S\r\n]*', '  ', control, flags=re.RegexFlag.MULTILINE)
        control = re.sub(r'^ {2}(?=##|$)', '', control, flags=re.RegexFlag.MULTILINE)

        control += "\n## Phenotype: " + str(phenotype) + "\n## Genotype: " + model_code_str \
                   + "\n## Num non-influential tokens: " + str(non_influential_token_num)

        return phenotype, control, non_influential_token_num

    @staticmethod
    def cleanup(run_dir: str, file_stem: str):
        """
        | Deletes all unneeded files after run.
          If :mono_ref:`remove_run_dir <remove_run_dir_options_desc>` is set to ``true`` then
          entire :mono_ref:`run_dir <model_run_dir>` is deleted.
        """

        try:
            if options.remove_run_dir:
                try:
                    utils.remove_dir(run_dir)
                except OSError:
                    log.error(f"Cannot remove folder {run_dir} in call to cleanup")
            else:
                file_to_delete = dict.fromkeys(glob.glob('*', root_dir=run_dir))

                file_to_delete.pop(f'{file_stem}.mmdl', None)
                file_to_delete.pop(f'{file_stem}_out.txt', None)

                for file in ['dmp.json', 'omega.csv', 'omega_stderr.csv', 'out.txt', 'theta.csv', 'residuals.csv',
                             'ConvergenceData.csv', 'nlme7engine.log', 'thetaCorrelation.csv', 'thetaCovariance.csv']:
                    file_to_delete.pop(file, None)

                for f in file_to_delete:
                    try:
                        path = os.path.join(run_dir, f)
                        os.remove(path)
                    except OSError:
                        pass
        except OSError as e:
            log.error(f"OS Error {e}")

        return

    @staticmethod
    def get_model_run_command(run: ModelRun) -> list:
        return [options.tmp_rscript, options.tmp_runscript, run.control_file_name, run.run_dir]

    @staticmethod
    def get_stem(generation, model_num) -> str:
        return f'NLME_{generation}_{model_num}'

    @staticmethod
    def get_file_names(stem: str):
        return stem + ".mmdl", stem + "_out.txt", stem + ".exe"

    @staticmethod
    def read_data_file_name(control_file_name: str) -> list:
        datalines = []

        with open(control_file_name, "r") as f:
            text = f.read()
            match = re.search(r'##[^\S\n]*DATA1[^\S\n]+(.*)$', text)

            if match is not None:
                datalines.append(match.group(1).strip())

        return datalines

    @staticmethod
    def read_results(run: ModelRun) -> bool:
        success = covariance = correlation = False
        ofv = condition_num = options.crash_value

        res = run.result

        res_file = os.path.join(run.run_dir, 'dmp.json')

        if not os.path.exists(res_file):
            return False

        with open(res_file) as file:
            text = file.read()
            text = re.sub(r',"residuals":.+$', '}', text, flags=re.RegexFlag.MULTILINE)
            data = json.loads(text)

            success = (data['returnCode'][0] in [1, 2, 3])
            ofv = float(data['logLik'][0] * -2)

        try:
            with open(os.path.join(run.run_dir, 'out.txt')) as file:
                text = file.read()

                match = re.search(r'^\s*condition\s*=\s*(\S+)', text, flags=re.RegexFlag.MULTILINE)

                if match is not None:
                    condition_num = float(match.group(1).strip())
        except:
            pass

        try:
            with open(os.path.join(run.run_dir, 'thetaCovariance.csv')) as file:
                lines = file.readlines()

                covariance = len(lines) > 1
        except:
            pass

        try:
            with open(os.path.join(run.run_dir, 'thetaCorrelation.csv')) as file:
                lines = file.readlines()

                correlation = len(lines) > 1

            with open(os.path.join(run.run_dir, 'thetaCorrelation.csv')) as file:
                lines = csv.reader(file)

                lines.__next__()

                i = 0
                for line in lines:
                    i += 1
                    for cell in line[1:i]:
                        if float(cell) > 0.95:
                            correlation = False
                            raise 'enough'

        except:
            pass

        res.success = success
        res.ofv = ofv
        res.condition_num = condition_num
        res.covariance = covariance
        res.correlation = correlation

        return True

    @staticmethod
    def read_model(run: ModelRun) -> bool:
        path = os.path.join(run.run_dir, run.control_file_name)

        # path = r'C:\workspace\Pirana\mmdl_examples\ex11.mmdl'

        if not os.path.exists(path):
            return False

        with open(path, "r") as file:
            model_text = file.read()

        model_text = re.sub(get_comment_re(), '', model_text, flags=re.RegexFlag.MULTILINE)

        mdl = extract_multiline_block(model_text, 'MODEL')

        match = re.search(r'^\s*\w+\s*\(.*?\)\s*\{(.+)}', mdl, flags=re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)

        if match is None:
            return False

        mdl = remove_comments(match.group(1).strip())

        fixef = extract_data('fixef', mdl)
        ranef = extract_data('ranef', mdl)
        error = extract_data('error', mdl)

        (th_descr, th_fix) = extract_lhs(fixef)
        th_val = extract_rhs_array(fixef)
        th_low = [x[0] for x in th_val]
        th_up = [x[2] for x in th_val]

        (om_descr, om_same, om_fix, om_block_struct_fix) = extract_ranefs(ranef)

        (si_descr, si_fix) = extract_lhs(error)

        theta_num = len(th_descr)
        omega_num = len(om_descr)
        sigma_num = len(si_descr)

        estimated_theta = theta_num
        estimated_omega = omega_num
        estimated_sigma = sigma_num

        for i in range(theta_num):
            estimated_theta -= (th_fix[i] or th_low[i] == th_up[i] and th_low[i] != '')

        for i in range(omega_num):
            estimated_omega -= (om_fix[i])

        for i in range(sigma_num):
            estimated_sigma -= (si_fix[i])

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

        return False, 'Not now.'


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

            if bool(re.search(r'\b(fixef|ranef|error)\b', trimmed_token, flags=re.MULTILINE)):
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


def remove_comments(code: str) -> str:
    """ Remove any comments from the *code*

    :param code: Input code
    :type code: str
    :rtype: str
    """

    code = re.sub(r'[^\S\n]*(#|//).*?$', '', code, flags=re.RegexFlag.MULTILINE)
    code = re.sub('/\\*.*?\\*/', '', code, flags=re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)

    return code


def register():
    register_engine_adapter('nlme', NLMEEngineAdapter())
