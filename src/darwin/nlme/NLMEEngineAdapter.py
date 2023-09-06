import os
import platform
import re
import glob
import math
import numpy as np
import shutil

from collections import OrderedDict

from darwin.ModelEngineAdapter import ModelEngineAdapter, register_engine_adapter
from darwin.ModelRun import ModelRun

import darwin.utils as utils

from darwin.Log import log
from darwin.options import options

from darwin.Template import Template
from darwin.ModelCode import ModelCode
from darwin.omega_search import apply_omega_bands, get_bands, get_max_search_block, extract_omega_search_blocks
from darwin.DarwinError import DarwinError

from .utils import extract_multiline_block, get_comment_re, extract_data, extract_lhs, extract_rhs_array, extract_ranefs

omega_search_re = r'(^\s*#search_block\s*\(\s*(\w+(?:\s*,\s*\w*)*)\))'
omega_search_re2 = r'(^\s*#search_block\s*\(\s*([^\)]*)\))'


class NLMEEngineAdapter(ModelEngineAdapter):

    @staticmethod
    def get_engine_name() -> str:
        return 'nlme'

    @staticmethod
    def init_template(template: Template):
        pass

    @staticmethod
    def get_max_search_block(template: Template) -> tuple:
        return get_max_search_block(template.template_text, template.tokens, omega_search_re2, _get_searched_omegas)

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
    def get_error_messages(run: ModelRun, run_dir: str):
        """
        """

        # TDL errors
        patterns_tdl = [
            r'TDL5: Startup error.+$',
            r'Failed to get license for NLME',
            r'^Error:.+$',
            r'^Error line \d+: Error:.+$',
            'license not found'
        ]

        err_files = []

        for f in glob.glob('err?', root_dir=run.run_dir) + glob.glob('err??', root_dir=run.run_dir):
            text = _read_file(f, run.run_dir)

            err = _find_errors(text, patterns_tdl)

            if err != '':
                return '', err

            if os.path.getsize(f"{run.run_dir}/{f}") > 0:
                err_files.append(f)

        if err_files:
            err = ', '.join(err_files)
            return '', f"See {err} for details"

        text = _read_file('log.txt', run_dir)

        err = _find_errors(text, patterns_tdl)

        if err != '':
            return '', err

        warning = _find_errors(text, [r'^Warning:.+$'])

        stderr = _read_file('err2.txt', run_dir)
        stdout = _read_file('err1.txt', run_dir)
        engine_log = _read_file('nlme7engine.log', run_dir)

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
            r'^Out of range pseudoLL.+$',
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
        err = _find_error(stderr, [r'Model not suitable for QRPEM analysis'])
        if err != '':
            run.set_status('Invalid model')
            return warning, err

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

        phenotype = OrderedDict(zip(template.tokens.keys(), model_code.IntCode))

        non_influential_tokens = _get_non_inf_tokens(template.tokens, phenotype)

        control = template.template_text

        token_found, control = utils.replace_tokens(template.tokens, control, phenotype, non_influential_tokens,
                                                    options.TOKEN_NESTING_LIMIT)

        non_influential_token_num = sum(non_influential_tokens)

        model_code_str = str(model_code.FullBinCode if (options.isGA or options.isPSO) else model_code.IntCode)

        control = re.sub(r'^[^\S\r\n]*', '  ', control, flags=re.RegexFlag.MULTILINE)
        control = re.sub(r'^ {2}(?=##|$)', '', control, flags=re.RegexFlag.MULTILINE)

        control, bands = apply_omega_bands(control, model_code, template.omega_band_pos, _set_omega_bands, True)

        phenotype = str(phenotype)
        phenotype = phenotype.replace('OrderedDict', '')
        phenotype += bands

        control += "\n## Phenotype: " + phenotype + "\n## Genotype: " + model_code_str \
                   + "\n## Num non-influential tokens: " + str(non_influential_token_num) + "\n"

        return phenotype, control, non_influential_token_num

    @staticmethod
    def cleanup(run_dir: str, file_stem: str):
        """
        | Deletes all unneeded files after run.
          If :mono_ref:`remove_run_dir <remove_run_dir_options_desc>` is set to ``true`` then
          entire :mono_ref:`run_dir <model_run_dir>` is deleted.
        """

        if options.remove_run_dir:
            try:
                utils.remove_dir(run_dir)
            except OSError:
                log.error(f"Cannot remove folder {run_dir} in call to cleanup")
        else:
            files_to_delete = dict.fromkeys(glob.glob('*', root_dir=run_dir))

            files_to_delete.pop(f'{file_stem}.mmdl', None)
            files_to_delete.pop(f'{file_stem}_out.txt', None)

            for file in ['log.txt', 'out.txt', 'err1.txt', 'err2.txt',
                         'nlme7engine.log', 'TDL5Warnings.log', 'integration_errors.txt', 'fort.27']:
                files_to_delete.pop(file, None)

            for f in files_to_delete:
                if re.search(r'^(err|out)\d+$|^sim-.*|^data\w+\.txt$', f):
                    continue

                try:
                    path = os.path.join(run_dir, f)
                    os.remove(path)
                except OSError:
                    pass

            for f in glob.glob(f"{run_dir}/*/"):
                try:
                    shutil.rmtree(f)
                except OSError:
                    pass

        return

    @staticmethod
    def get_model_run_commands(run: ModelRun) -> list:
        run_dir = run.run_dir

        command = {
            'command': [options.rscript_path, '-e', f"Certara.RsNLME::extract_mmdl('{run.control_file_name}', '.')"],
            'dir': run_dir,
            'timeout': 30
        }

        if not run.run_command(0, command):
            return []

        run_dir = run_dir.replace('\\', '/')

        folders = glob.glob('*/', root_dir=run_dir)
        folders = [f for f in folders if f.find('-') != -1]
        folders.sort(key=lambda f: int(f[:f.index('-')]))
        folders = [f"{run_dir}/"+f.removesuffix('\\').removesuffix('/') for f in folders]

        res = [
            {
                'command': _get_run_command(run, folders[0]),
                'dir': folders[0],
                'timeout': options.model_run_timeout
            }
        ]

        last_est = folders[0]
        last_sim = None

        for f in folders[1:]:
            res.append(
                {
                    'command': [options.rscript_path, '-e',
                                f"Certara.NLME8::UpdateMDLfrom_dmptxt(dmpfile='{last_est}/dmp.txt', compile=FALSE,"
                                f"model_file='{last_est}/test.mdl', output_file='{f}/test.mdl')"],
                    'dir': run_dir,
                    'timeout': 30
                }
            )
            res.append(
                {
                    'command': _get_run_command(run, f),
                    'dir': f,
                    'timeout': options.model_run_timeout
                }
            )

            if f.endswith('est'):
                last_est = f
            elif f.endswith('sim'):
                last_sim = f

        res.append(
            {
                'fun': lambda: _copy_res_files(last_est, run_dir)
            }
        )

        if last_sim is not None:
            res.append(
                {
                    'fun': lambda: _copy_res_files(last_sim, run_dir, True)
                }
            )

        return res

    @staticmethod
    def get_stem(generation, model_num) -> str:
        return f'NLME_{generation}_{model_num}'

    @staticmethod
    def get_file_names(stem: str):
        return stem + ".mmdl", stem + "_out.txt", f"{stem}.exe".replace('NLME', 'NLME7')

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
        if run.status == 'Invalid model':
            return False

        correlation = False
        ofv = condition_num = options.crash_value

        run_dir = run.run_dir

        res = run.result

        res_file = os.path.join(run_dir, 'dmp.txt')

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
            with open(os.path.join(run_dir, 'out.txt')) as file:
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

        (om_descr, om_same, om_blocks, om_fix, diag_vals, om_block_fix) = extract_ranefs(ranef)

        (si_descr, si_fix) = extract_lhs(error)

        theta_num = len(th_descr)
        omega_num = len(om_block_fix)
        sigma_num = len(si_descr)

        estimated_theta = theta_num
        estimated_omega = omega_num
        estimated_sigma = sigma_num

        for i in range(theta_num):
            estimated_theta -= (th_fix[i] or th_low[i] == th_up[i] and th_low[i] != '')

        for ob in om_block_fix:
            estimated_omega -= ob

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

    @staticmethod
    def get_omega_search_pattern() -> str:
        """
        """

        return r'^\s*#search_block\b'


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


def _copy_res_files(src_dir: str, dst_dir: str, sim: bool = False):
    log_files = ['TDL5Warnings.log', 'integration_errors.txt', 'fort.27', 'log.txt', 'err1.txt', 'err2.txt']
    sim_files = ['dat2.txt', 'dat3.txt']
    est_files = ['nlme7engine.log', 'dmp.txt', 'out.txt']

    prefix = 'sim-' if sim else ''

    files = sim_files if sim else est_files
    files.extend(log_files)

    for file in log_files:
        try:
            shutil.copy(f"{src_dir}/{file}", f"{dst_dir}/{prefix}{file}")
        except OSError:
            pass

    for file in files:
        try:
            shutil.copy(f"{src_dir}/{file}", dst_dir)
        except OSError:
            pass

    for file in glob.glob(f"{src_dir}/*.csv"):
        shutil.copy(file, dst_dir)

    if not sim:
        for file in glob.glob(f"{src_dir}/data*.txt"):
            shutil.copy(file, dst_dir)


def _get_run_command(run: ModelRun, folder: str) -> list:
    nlme_dir = options.get('nlme_dir', '')

    if platform.system() == 'Windows':
        return ['powershell', '-noninteractive', '-executionpolicy', 'remotesigned', '-file',
                f"{nlme_dir}/execNLMECmd.ps1", '-NLME_EXE_POSTFIX', f"_{run.generation}_{run.wide_model_num}",
                '-RUN_MODE', 'COMPILE_AND_RUN', '-MODELFILE', 'test.mdl', '-WORKING_DIR', folder,
                '-MPIFLAG', 'MPINO', '-LOCAL_HOST', 'YES', '-NUM_NODES', '1', '-NLME_ARGS', '@nlmeargs.txt']

    return [f"{nlme_dir}/execNLMECmd.sh", 'COMPILE_AND_RUN', 'test.mdl', folder,
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

    if count > 1:
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


def _cleanup_search_block(block: str) -> str:
    sb = re.sub(r'\s+', '', block, flags=re.MULTILINE | re.DOTALL)
    sb = re.sub(r',,+', ',', sb, flags=re.MULTILINE | re.DOTALL)

    return sb


def _get_searched_omegas(search_blocks: list) -> set:
    searched_omegas = set()

    for sb in search_blocks:
        sb = _cleanup_search_block(sb)

        for name in sb.split(','):
            searched_omegas.add(name)

    return searched_omegas


def _get_values(ranefs: list, searched_omegas: set) -> dict:
    vals = {}

    for ranef in ranefs:
        (om_descr, om_same, om_blocks, om_fix, diag_vals, om_block_fix) = extract_ranefs([ranef])
        vals |= diag_vals

        same_omegas = dict.fromkeys(om_same)
        del same_omegas['']

        i = -1

        for name, same, block, fix in zip(om_descr, om_same, om_blocks, om_fix):
            i += 1

            if name in same_omegas:
                raise DarwinError(f"Omega search cannot be performed for '{name}'"
                                  f" due to dependent omega structure (same): {ranef}")

            if name not in searched_omegas:
                continue

            if same != '' or block or fix:
                raise DarwinError(f"Omega search cannot be performed for '{name}': {ranef}")

    return vals


def _remove_searched_omegas(control: str, blocks: dict) -> str:
    matches = re.findall(r'(diag\s*\(([^)]+)\)\s*(?:<-|=)\s*c\(([^)]+)\))', control, flags=re.MULTILINE | re.DOTALL)

    for (total, omegas, values) in matches:
        omegas = re.sub(r'\s+', '', omegas, flags=re.MULTILINE | re.DOTALL).split(',')
        values = re.sub(r'\s+', '', values, flags=re.MULTILINE | re.DOTALL).split(',')

        res_omegas = []
        res_values = []

        for om, val in zip(omegas, values):
            if om in blocks:
                continue

            res_omegas.append(om)
            res_values.append(val)

        if omegas != res_omegas:
            names = ', '.join(res_omegas)
            values = ', '.join(res_values)
            control = control.replace(total, f"diag({names}) = c({values})")

    return control


def _find_block_structure(bands: list, band_arr: list, blocks: dict, sb: list) -> str:
    omega_rep = []

    for band, block_size in bands:
        if block_size == 0:
            omega_text = 'diag'
        else:
            omega_text = 'block'

        this_rec = 0

        rows = []

        for i in band:
            rows.append(", ".join(map(str, np.around(i[:(this_rec + 1)], 7))))
            this_rec += 1

        names = ', '.join(sb[:len(band)])
        vals = ', '.join(rows)

        blocks |= dict.fromkeys(sb[:len(band)])

        names = f"({names})"

        if omega_text == 'block':
            band_arr.append(names)

        omega_text += f"{names} = c({vals})"

        omega_rep.append(omega_text)

        sb = sb[len(band):]

    return ', '.join(omega_rep)


def _add_search_ranef_blocks(control: str, block_omegas: list) -> str:
    full_blocks = {}

    for x in block_omegas:
        full_blocks[x[0]] = x[0].replace('#search_block', 'ranef')

    for full_block, block, omega_rep in block_omegas:
        full_blocks[full_block] = full_blocks[full_block].replace(block, omega_rep)

    for search_block, ranef_block in full_blocks.items():
        control = control.replace(search_block, f"{search_block}\n{ranef_block}")

    return control


def _set_omega_bands(control: str, band_width: list, mask_idx: list) -> tuple:
    mdl = _get_mdl(control)

    ranefs = extract_data('ranef', mdl)

    (search_blocks, full_search_blocks) = extract_omega_search_blocks(omega_search_re, control)
    searched_omegas = _get_searched_omegas(search_blocks)
    vals = _get_values(ranefs, searched_omegas)

    band_arr = []
    blocks = {}
    block_omegas = []

    omega_idx = 0

    for sblock, full_block in zip(search_blocks, full_search_blocks):
        sb = _cleanup_search_block(sblock)
        sb = sb.split(',')

        sb = [o for o in sb if o in vals]
        om_val = [float(vals[o]) for o in sb]

        max_len = options.max_omega_search_lens[omega_idx]

        bands = get_bands(om_val, -1, mask_idx[omega_idx], max_len, True)

        if options.individual_omega_search:
            omega_idx += 1

        if not any([b[1] for b in bands]):
            # no block ranefs
            continue

        omega_rep = _find_block_structure(bands, band_arr, blocks, sb)

        block_omegas.append((full_block, sblock, omega_rep))

    control = _remove_searched_omegas(control, blocks)

    control = _add_search_ranef_blocks(control, block_omegas)

    empty_diag = r'diag\(\) = c\(\)'

    control = re.sub(f",?\\s*{empty_diag}", '', control, flags=re.MULTILINE | re.DOTALL)
    control = re.sub(f"{empty_diag}\\s*,?", '', control, flags=re.MULTILINE | re.DOTALL)

    control = re.sub(r'^\s*ranef\(\)\s*\n', '', control, flags=re.MULTILINE)

    return control, band_arr


def register():
    register_engine_adapter('nlme', NLMEEngineAdapter())
