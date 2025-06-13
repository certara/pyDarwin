import re

from darwin.DarwinError import DarwinError

info_blocks = ['Author:', 'Description:', 'Based on:', 'AUTHOR:', 'DESCRIPTION:', 'BASED ON:']
one_line_blocks = ['DATA', 'DATA1', 'DATA2', 'MAP', 'MAP1', 'MAP2']
multiline_blocks = ['COLDEF', 'MODEL', 'TABLES', 'ESTARGS', 'DOSING CYCLE']
all_blocks = info_blocks
all_blocks.extend(one_line_blocks)
all_blocks.extend(multiline_blocks)


def get_end_block_re() -> str:
    res = '|'.join(all_blocks)

    return f"(?=\\s*##\\[^\\S\\n]*(?:{res})|\\Z)"


def get_comment_re() -> str:
    res = '|'.join(all_blocks)

    return f"##(?![^\\S\\n]*(?:{res}))[^\\S\\n]*.+$"


def extract_multiline_block(model_text: str, block_name: str):
    end_block = get_end_block_re()

    match = re.search(f"##[^\\S\\n]*{block_name}\\s*(.+?){end_block}", model_text,
                      flags=re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)

    if match is not None:
        return match.group(1).strip()

    return None


def extract_bracketed(text: str) -> str:
    depth = 0
    start = -1
    end = -1

    for i in range(len(text)):
        if text[i] == '(':
            if depth == 0:
                start = i
            depth = depth + 1
        elif text[i] == ')':
            depth = depth - 1
            if depth == 0:
                end = i
                break

    if start != -1 and end != -1:
        return text[start+1:end]

    return ''


def extract_data(name: str, text: str) -> list:
    matches = re.findall(f"\\b{name}\\b(.+?)(?=\\b{name}\\b|\\Z)", text,
                         flags=re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)

    data = []

    for occ in matches:
        content = extract_bracketed(occ)

        if content != '':
            data.append(content.strip())

    return data


def extract_lhs(data: list) -> tuple:
    res = []
    freeze = []

    for d in data:
        d = re.sub(r'enable\s*=\s*c\s*\(.*?\)', '', d, flags=re.RegexFlag.MULTILINE)

        matches = re.findall(r'(\w+)\s*(.*?)\s*(?:=|<-)', d, flags=re.RegexFlag.MULTILINE)

        for (name, mod) in matches:
            res.append(name)
            freeze.append(mod is not None and re.search(r'\bfreeze\b', mod, flags=re.RegexFlag.MULTILINE) is not None)

    return res, freeze


def extract_rhs_array(data: list) -> list:
    res = []

    for d in data:
        d = re.sub(r'enable\s*=\s*c\s*\(.*?\)', '', d, flags=re.RegexFlag.MULTILINE)
        val = re.findall(r'(?:=|<-)\s*c\((.*?)\)', d, flags=re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)

        for values in val:
            values = re.sub(r'\s', '', values, flags=re.RegexFlag.MULTILINE)
            res.append(values.split(','))

    return res


def extract_ranefs(ranefs: list) -> tuple:
    all_omegas = []
    freezes = []
    sames = []
    blocks = []
    block_fix = []
    diag_vals = {}

    prev_freeze = 0
    prev_block_size = 0

    for r in ranefs:
        match = re.findall(r'(block|diag|same)\s*\((.+?)\)\s*(?:\(\s*(freeze)\s*\))?(?:(?:=|<-)\s*c\((.*?)\))?', r,
                           flags=re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)

        i = 0

        for (t, omega, freeze, values) in match:
            omega = re.sub(r'\s', '', omega, flags=re.RegexFlag.MULTILINE)
            omegas = omega.split(',')

            omega_len = len(omegas)

            values = re.sub(r'\s', '', values, flags=re.RegexFlag.MULTILINE)
            values = values.split(',')

            if t == 'diag':
                if omega_len != len(values):
                    raise DarwinError(f"ranef values mismatch: {omegas} vs. {values}")
                diag_vals |= dict(zip(omegas, values))

            same = t == 'same'

            fix = freeze != '' or same and prev_freeze

            all_omegas.extend(omegas)

            if not same:
                prev_freeze = freeze
                prev_block_size = omega_len

                same_block = [''] * omega_len
            else:
                if omega_len != prev_block_size:
                    raise DarwinError(f"same block mismatch: block size is {omega_len},"
                                      f" expected size is {prev_block_size}")
                if sames[i-1] != '':
                    same_block = sames[i-omega_len:i]
                else:
                    same_block = all_omegas[i-omega_len:i]

            i += len(omegas)

            sames.extend(same_block)
            freezes.extend([fix] * len(omegas))
            blocks.extend([t == 'block'] * len(omegas))

            if not same:
                bt = t == 'block'

                for j in range(1, len(omegas)+1):
                    block_fix.extend([fix] * j if bt else [fix])

    return all_omegas, sames, blocks, freezes, diag_vals, block_fix
