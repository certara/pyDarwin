import os
import platform
import re
import glob
import math
import numpy as np

from collections import OrderedDict

from darwin.ModelEngineAdapter import ModelEngineAdapter, register_engine_adapter
from darwin.ModelRun import ModelRun

import darwin.utils as utils

from darwin.Log import log
from darwin.options import options

from darwin.Template import Template
from darwin.ModelCode import ModelCode
from darwin.omega_search import apply_omega_bands, get_bands

from .utils import extract_multiline_block, get_comment_re, extract_data, extract_lhs, extract_rhs_array, extract_ranefs


class NLMEEngineAdapter(ModelEngineAdapter):

    @staticmethod
    def get_engine_name() -> str:
        return 'nlme'

    @staticmethod
    def init_template(template: Template):
        pass

    @staticmethod
    def init_engine():
        nlme_dir = options.get('nlme_dir', None)

        if not nlme_dir:
            log.error('nlme_dir must be set for running NLME models')
            return False

        if not os.path.isdir(nlme_dir):
            log.error(f"NLME directory '{nlme_dir}' seems to be missing")
            return False

        log.message(f"NLME found: {nlme_dir}")

        gcc_dir = options.get('gcc_dir', None)

        if not gcc_dir:
            log.error('gcc_dir must be set for running NLME models')
            return False

        if not os.path.isdir(gcc_dir):
            log.error(f"GCC directory '{gcc_dir}' seems to be missing")
            return False

        log.message(f"GCC found: {gcc_dir}")

        os.environ['INSTALLDIR'] = nlme_dir
        os.environ['NLMEGCCDir64'] = gcc_dir

        lic_file = options.get('nlme_license', None)

        if lic_file is not None:
            if not os.path.exists(lic_file):
                log.error(f"TDL license file '{lic_file}' seems to be missing")
                return False

            log.message(f"Using TDL license file: {lic_file}")

            os.environ['PhoenixLicenseFile'] = lic_file

        return True

    @staticmethod
    def get_error_messages(run: ModelRun):
        """
        """

        # TDL errors
        patterns_tdl = [
            r'TDL5: Startup error.+$',
            r'Failed to get license for NLME',
            r'^Error:.+$',
        ]

        text = _read_file('log.txt', run.run_dir)

        err = _find_errors(text, patterns_tdl)

        if err != '':
            return err, ''

        warning = _find_errors(text, [r'^Warning:.+$'])

        stderr = _read_file('err2.txt', run.run_dir)
        stdout = _read_file('err1.txt', run.run_dir)
        engine_log = _read_file('nlme7engine.log', run.run_dir)

        patterns1 = [
            r'Fatal error:.+$',
            r'^error in boundmap$',
            r'^error in boundmapinv$',
            r'^Initial parameter values result in -LL = NaN$',
            r'^Out of range Optimal objective value.+$'
            r'Error: etablups called.+$'
            r'^illegal parameter settings in call to estblups$',
            r'^Numerical LL integration produced bad.+$'
            r'^MAXACTem needs to be reset as large as npoint$',
            r'^MAXSUBem needs to be reset as large as nsub$',
            r'^primaldual failure:.+$',
            r'^psi matrix not non-negative',
            r'^psi has a zero \w+',
            r'^Out ofrange pseudoLL.+$',
        ]

        # the first two are always followed by Fortran Exception, the last one happens on its own
        patterns2 = [
            r'Fatal error:.+$',
            r'^Execution failed due to integration error.$',
            r'^Model not suitable for QRPEM analysis$'
        ]

        patterns7 = [
            r'Fatal error:.+$'
        ]

        # check NLME stderr first
        err = _find_error(stderr, patterns2)

        if err != '':
            return warning, err

        err = re.search(r'Error: Model Exception: (.+)$', stderr, flags=re.RegexFlag.MULTILINE)

        if err is not None:
            err = err.group(1).strip()

            if err == 'Fortran Exception':
                err = _find_error(stdout, patterns1) or _find_error(engine_log, patterns7) or err

            return warning, err

        elif stderr != '':
            return warning, f"Unidentified error in err2.txt for model run {run.generation}, {run.model_num}"

        err = _find_error(engine_log, [r'^Model not suitable for QRPEM analysis$'])

        return warning, err

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

        control = apply_omega_bands(control, model_code, template.omega_band_pos, _set_omega_bands)

        control = re.sub(r'\branef:search_band\b', 'ranef', control, flags=re.MULTILINE)

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

                for file in ['test.mdl', 'log.txt', 'dmp.txt', 'omega.csv', 'omega_stderr.csv', 'out.txt', 'theta.csv',
                             'residuals.csv', 'ConvergenceData.csv', 'nlme7engine.log', 'err1.txt', 'err2.txt',
                             'TDL5Warnings.log', 'integration_errors.txt', 'fort.27']:
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
    def get_model_run_commands(run: ModelRun) -> list:
        return [
            {
                'command': [options.rscript_path, '-e', f"Certara.RsNLME::extract_mmdl('{run.control_file_name}', '.')"],
                'timeout': 30
            },
            {
                'command': _get_run_command(run),
                'timeout': options.model_run_timeout
            }
        ]

    @staticmethod
    def get_stem(generation, model_num) -> str:
        return f'NLME_{generation}_{model_num}'

    @staticmethod
    def get_file_names(stem: str):
        return stem + ".mmdl", stem + "_out.txt", stem + ".exe"

    @staticmethod
    def get_final_file_names():
        return 'FinalControlFile.mmdl', 'FinalResultFile.txt'

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
        correlation = False
        ofv = condition_num = options.crash_value

        res = run.result

        res_file = os.path.join(run.run_dir, 'dmp.txt')

        if not os.path.exists(res_file):
            return False

        with open(res_file) as file:
            text = file.read()

            rc = re.search(r'"returnCode" = c\((\d+)', text, flags=re.RegexFlag.MULTILINE)
            success = (rc is not None and int(rc.group(1)) in [1, 2, 3])

            ll = re.search(r'"logLik" = c\(([^,]+)\)', text, flags=re.RegexFlag.MULTILINE)

            if ll is not None:
                ofv = float(ll.group(1)) * -2

            covariance = re.search(r'"Covariance" = matrix', text, flags=re.RegexFlag.MULTILINE) is not None

            cor = re.search(r'"Correlation" = matrix\(\s*as\.numeric\(c\(([^)]+)\)\)', text,
                            flags=re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)

            if cor is not None:
                correlation = True

                arr = re.sub(r'\s', '', cor.group(1), flags=re.RegexFlag.MULTILINE)
                arr = arr.split(',')

                n = int(math.sqrt(len(arr)))

                lines = [arr[i:i + n] for i in range(0, len(arr), n)]

                try:
                    i = 0
                    for line in lines:
                        i += 1
                        for cell in line[1:i]:
                            if abs(float(cell)) > 0.95:
                                raise 'nope'
                except:
                    correlation = False

        try:
            with open(os.path.join(run.run_dir, 'out.txt')) as file:
                text = file.read()

                match = re.search(r'^\s*condition\s*=\s*(\S+)', text, flags=re.RegexFlag.MULTILINE)

                if match is not None:
                    condition_num = float(match.group(1).strip())
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

        if not os.path.exists(path):
            return False

        with open(path, "r") as file:
            model_text = file.read()

        mdl = _get_mdl(model_text)

        if mdl == '':
            return False

        fixef = extract_data('fixef', mdl)
        ranef = extract_data('ranef', mdl)
        error = extract_data('error', mdl)

        (th_descr, th_fix) = extract_lhs(fixef)
        th_val = extract_rhs_array(fixef)
        th_low = [x[0] for x in th_val]
        th_up = [x[2] for x in th_val]

        (om_descr, om_same, om_block, om_fix) = extract_ranefs(ranef)

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
        """

        return True, 'Always'


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


def remove_comments(code: str) -> str:
    """ Remove any comments from the *code*

    :param code: Input code
    :type code: str
    :rtype: str
    """

    code = re.sub(r'[^\S\n]*(#|//).*?$', '', code, flags=re.RegexFlag.MULTILINE)
    code = re.sub('/\\*.*?\\*/', '', code, flags=re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)

    return code


def _get_run_command(run: ModelRun) -> list:
    nlme_dir = options.get('nlme_dir', '')

    if platform.system() == 'Windows':
        return ['powershell', '-noninteractive', '-executionpolicy', 'remotesigned', '-file',
                f"{nlme_dir}/execNLMECmd.ps1", '-NLME_EXE_POSTFIX', f"_{run.generation}_{run.model_num}",
                '-RUN_MODE', 'COMPILE_AND_RUN', '-MODELFILE', 'test.mdl', '-WORKING_DIR', run.run_dir,
                '-MPIFLAG', 'MPINO', '-LOCAL_HOST', 'YES', '-NUM_NODES', '1', '-NLME_ARGS', '@nlmeargs.txt']

    return [f"{nlme_dir}/execNLMECmd.sh", 'COMPILE_AND_RUN', 'test.mdl', run.run_dir,
            'MPINO', 'YES', '1', '', '', '', '@nlmeargs.txt', '', f"_{run.generation}_{run.model_num}"]


def _read_file(file: str, run_dir: str) -> str:
    log_file = os.path.join(run_dir, file)

    if not os.path.exists(log_file):
        return ''

    with open(log_file) as file:
        return file.read()


def _find_error(text: str, patterns: list) -> str:
    for p in patterns:
        err = re.search(p, text, flags=re.RegexFlag.MULTILINE)

        if err is not None:
            err = err.group(0).strip()
            return str(err)

    return ''


def _find_errors(text: str, patterns: list) -> str:
    res = ''
    count = 0

    for p in patterns:
        matches = re.findall(p, text, flags=re.RegexFlag.MULTILINE)

        if not matches:
            continue

        if res == '':
            res = matches[0]

        count += len(matches)

    if count != 0:
        res += f" (+{count-1} more)"

    return res


def _get_mdl(model_text: str) -> str:
    model_text = re.sub(get_comment_re(), '', model_text, flags=re.RegexFlag.MULTILINE)

    mdl = extract_multiline_block(model_text, 'MODEL')

    match = re.search(r'^\s*\w+\s*\(.*?\)\s*\{(.+)}', mdl, flags=re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)

    if match is None:
        return ''

    mdl = remove_comments(match.group(1).strip())

    return mdl


def _set_omega_bands(control: str, band_width: int, omega_band_pos: list) -> str:
    mdl = _get_mdl(control)

    ranefs = extract_data('ranef:search_band', mdl)

    if len(ranefs) == 0:
        return control

    for ranef in ranefs:
        (om_descr, om_same, om_block, om_fix) = extract_ranefs([ranef])

        if any(om_same) or any(om_block) or any(om_fix):
            continue

        om_val = extract_rhs_array([ranef])
        om_val = [float(item) for sublist in om_val for item in sublist]

        bands = get_bands(om_val, band_width, omega_band_pos)

        if not any([b[1] for b in bands]):
            # no block ranefs
            continue

        omega_rep = []

        for band, block_size in bands:
            if block_size == 0 or band_width == 0:
                omega_text = 'diag'
            else:
                omega_text = 'block'

            this_rec = 0

            rows = []

            for i in band:
                rows.append(", ".join(map(str, np.around(i[:(this_rec + 1)], 7))))
                this_rec += 1

            names = ', '.join(om_descr[:len(band)])
            vals = ', '.join(rows)

            omega_text += f"({names}) = c({vals})"

            omega_rep.append(omega_text)

            om_descr = om_descr[len(band):]

        control = control.replace(ranef, ', '.join(omega_rep))

    return control


def register():
    register_engine_adapter('nlme', NLMEEngineAdapter())