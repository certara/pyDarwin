import re

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
        val = re.findall(r'(?:=|<-)\s*c\((.*?)\)', d, flags=re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)

        for values in val:
            values = re.sub(r'\s', '', values, flags=re.RegexFlag.MULTILINE)
            res.append(values.split(','))

    return res


def extract_ranefs(ranefs: list) -> tuple:
    all_omegas = []
    freezes = []
    sames = []
    block_fix = []
    blocks = []

    prev_freeze = 0

    for r in ranefs:
        match = re.findall(r'(block|diag|same)\s*\((.+?)\)\s*(?:\(\s*(freeze)\s*\))?', r,
                           flags=re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)

        for (t, omega, freeze) in match:
            omega = re.sub(r'\s', '', omega, flags=re.RegexFlag.MULTILINE)
            omegas = omega.split(',')

            same = t == 'same'

            fix = freeze is not None or same and prev_freeze

            if not same:
                prev_freeze = freeze

            all_omegas.extend(omegas)

            sames.extend([same] * len(omegas))
            freezes.extend([fix] * len(omegas))

            if not same:
                bt = t == 'block'
                block = []

                for i in range(1, len(omegas)):
                    block.append([fix] * i if bt else [fix])

                blocks.append(block)

    for block in blocks:
        block_fix.extend(block)

    return all_omegas, sames, freezes, block_fix
