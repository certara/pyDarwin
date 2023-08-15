import math
import numpy as np
import re
from collections import OrderedDict
from copy import deepcopy

from darwin.Log import log

from darwin.options import options
from darwin.ModelCode import ModelCode
from darwin.Template import Template
from darwin.DarwinError import DarwinError

_masks = []
_max_mask_len = 0


def apply_omega_bands(control: str, model_code: ModelCode, omega_band_pos: int, set_bands_impl: callable,
                      nlme: bool = False) -> tuple:
    bands = ''

    if not options.search_omega_blocks:
        return control, bands

    if nlme:
        band_width = []
        mask_idx = model_code.IntCode[omega_band_pos:]
    else:
        band_width = model_code.IntCode[omega_band_pos::2]
        mask_idx = model_code.IntCode[omega_band_pos + 1::2]

    # need to know where the band width is specified, rest is omega submatrices
    control, band_arr = set_bands_impl(control, band_width, mask_idx)

    if band_arr:
        bands = ', '. join(band_arr)
        bands = f", bands: ({bands})"

    return control, bands


def get_bands(diag_block: list, band_width: int, mask_idx: int, max_len: int, nlme: bool = False) -> list:
    res = []

    len_d = len(diag_block)

    if len_d < 2:
        return res

    len_d = min(len_d, max_len)

    all_masks = get_omega_block_masks(len_d)
    i = int(mask_idx * len(all_masks) / _max_mask_len)

    masks = all_masks[i]

    last_end = 0

    for start, size in masks:
        end = start + size

        if start > last_end:
            init_off_diags = [[j] for j in diag_block[last_end:start]]
            res.append((init_off_diags, 0))

        if nlme:
            init_off_diags = np.zeros([size, size])
            for row in range(size):
                init_off_diags[row, row] = diag_block[start + row]
        else:
            init_off_diags = find_band(size, band_width, diag_block[start:end])

        res.append((init_off_diags, size))

        last_end = end

    if len(diag_block) > last_end:
        init_off_diags = [[j] for j in diag_block[last_end:]]
        res.append((init_off_diags, 0))

    return res


def find_band(omega_size: int, band_width: int, omega_block: list):
    factor = 1.0
    count = 0

    init_off_diags = np.ones([omega_size, omega_size])

    is_pos_def = False

    while not is_pos_def:
        factor *= 0.5

        # same random numbers each time, for all models and each loop looking PD
        rng = np.random.default_rng(seed=options.random_seed)

        for row in range(omega_size):
            row_diag = math.sqrt(omega_block[row])
            init_off_diags[row, row] = omega_block[row]

            for this_col in range(row):
                col_diag = math.sqrt(omega_block[this_col])

                # for off diagonals, pick a random number between +/- val
                val = factor * row_diag * col_diag
                val = rng.uniform(-val, val)

                # minimum abs value of 0.0000001, 0.0 will give error in NONMEM
                val = np.size(val) * (max(abs(val), 0.0000001))  # keep sign, but abs(val) >=0.0000001

                # give nmtran error
                init_off_diags[row, this_col] = init_off_diags[this_col, row] = val

        # set any bands > bandwidth to 0
        for band_row in range((band_width + 1), omega_size):  # start in row after bandwidth
            for band_col in range(0, (band_row - band_width)):
                init_off_diags[band_col, band_row] = init_off_diags[band_row, band_col] = 0

        is_pos_def = np.all(np.linalg.eigvals(init_off_diags) > 0)  # matrix must be symmetrical

        count += 1

        if count > 50:
            log.error("Cannot find positive definite Omega matrix, consider not using search_omega \
            or increasing diagonal element initial estimates")
            break

    return init_off_diags


def get_masks2(start: int, end: int, min_size: int, max_size: int):
    me = min(max_size, end) + 1

    for i in range(min_size, me):
        if i + start > end:
            return

        t = [(start, i)]

        yield t

        for j in range(start + i, end):
            for m2 in get_masks2(j, end, min_size, max_size):
                yield t + m2


def _get_masks(end: int, min_size: int, max_size: int) -> list:
    if not options.search_omega_sub_matrix:
        return [[(0, 0)], [(0, end)]]

    masks = [[(0, 0)]]

    for start in range(0, end - 1):
        for mask in get_masks2(start, end, min_size, max_size):
            masks.append(mask)

    return masks


def get_omega_block_masks(search_len: int = 0) -> list:
    global _masks
    global _max_mask_len

    search_len = search_len or options.max_omega_search_len

    if not _masks:
        _masks = [[], []]
        for i in range(2, options.OMEGA_SEARCH_LIMIT + 1):
            _masks.append(_get_masks(i, 2, options.max_omega_sub_matrix))

        _max_mask_len = len(get_omega_block_masks(options.max_omega_search_len))

    return _masks[search_len]


def extract_omega_search_blocks(pattern: str, text: str) -> tuple:
    matches = re.findall(pattern, text, flags=re.MULTILINE | re.DOTALL)

    data = []
    data0 = []

    for occ0, occ in matches:
        data0.append(occ0)
        data.append(occ)

    return data, data0


def _get_subtree(text: str, tokens: dict, is_sb: bool, pattern: str, full: bool = True):
    """
    full = False only when called from _get_max_search_blocks
    in this case there will be no search block in any token
    """
    if not is_sb:
        (sblocks, full_search_blocks) = extract_omega_search_blocks(pattern, text)

        for i, sb in enumerate(full_search_blocks if full else sblocks):
            for tt in _get_subtree(sb, tokens, True, pattern):
                yield tt

            text = text.replace(sb, '')

    toks = re.findall(r'\{([^\[{}]+)\[(\d+)]}', text, flags=re.MULTILINE | re.DOTALL)

    if not toks:
        if is_sb:
            yield text
        return

    (tok, i) = toks[0]

    for x in tokens[tok]:
        for tt in _get_subtree(text.replace('{' + f"{tok}[{i}]" + '}', x[int(i)-1]), tokens, is_sb, pattern):
            yield tt


def _merge_trees(tree: OrderedDict, subtree: dict):
    for k in subtree:
        if k not in tree:
            tree[k] = subtree[k]
        else:
            tree[k].update(subtree[k])


def _get_subtree2(text: str, tokens: dict, is_sb: bool, pattern: str, subtree=None, depth=1) -> OrderedDict:
    tree = OrderedDict()

    if not is_sb:
        (sblocks, full_search_blocks) = extract_omega_search_blocks(pattern, text)

        for i, sb in enumerate(full_search_blocks):
            tt = _get_subtree2(sb, tokens, True, pattern, depth=depth+1)
            _merge_trees(tree, tt)
            text = text.replace(sb, '')
            if subtree:
                _merge_trees(tree, subtree)

    toks = re.findall(r'\{([^\[{}]+)\[(\d+)]}', text, flags=re.MULTILINE | re.DOTALL)

    if toks and depth > options.TOKEN_NESTING_LIMIT:
        raise DarwinError(f"There are more than {options.TOKEN_NESTING_LIMIT} levels of nested tokens.")

    for (tok, i) in toks:
        for x in tokens[tok]:
            tt = _get_subtree2(x[int(i)-1], tokens, is_sb, pattern, {tok: {int(i) - 1: 1}}, depth=depth+1)
            if not is_sb and len(tt) == 0:
                continue
            _merge_trees(tree, tt)
            _merge_trees(tree, {tok: {int(i) - 1: 1}})

    return tree


def _trim_model(text: str, tokens: OrderedDict, pattern: str) -> tuple:
    tree = _get_subtree2(text, tokens, False, pattern)

    tokens = deepcopy(tokens)

    for k in tokens:
        for i in range(len(tokens[k]) - 1, -1, -1):
            for j in range(len(tokens[k][i])):
                if k not in tree or j not in tree[k]:
                    tokens[k][i][j] = ''
                    text = text.replace('{' + f"{k}[{j+1}]" + '}', '')
            if not any(tokens[k][i]):
                del tokens[k][i]

    return text, tokens


def _get_max_search_block(text: str, tokens: dict, pattern: str, get_omega_block: callable) -> int:
    max_len = 0

    for i in _get_subtree(text, tokens, False, pattern):
        (sblocks, full_search_blocks) = extract_omega_search_blocks(pattern, i)

        for sb in sblocks:
            sb = re.sub(r'^\s+|^\s*\n(\s*\n)+', '', sb, flags=re.MULTILINE | re.DOTALL)

            max_len = max(len(get_omega_block(sb.split("\n"))), max_len)

    return max_len


def get_max_search_block(template: Template, pattern: str, get_omega_block: callable) -> tuple:
    (text, tokens) = _trim_model(template.template_text, template.tokens, pattern)

    if options.individual_omega_search:
        return _get_max_search_blocks(text, tokens, pattern, get_omega_block)

    return _get_max_search_block(text, tokens, pattern, get_omega_block), []


def _get_max_search_blocks(text: str, tokens: dict, pattern: str, get_omega_block: callable) -> tuple:
    max_len = 0
    max_lens = []

    (sblocks, full_search_blocks) = extract_omega_search_blocks(pattern, text)

    for k, fsb in enumerate(full_search_blocks):
        ll = 0

        for sb in _get_subtree(fsb, tokens, False, pattern, False):
            sb = re.sub(r'^\s+|^\s*\n(\s*\n)+', '', sb, flags=re.MULTILINE | re.DOTALL)

            ll = max(ll, len(get_omega_block(sb.split("\n"))))

        if ll > options.OMEGA_SEARCH_LIMIT:
            log.warn(fsb)
            log.warn(f"Omega search block size is too big, resetting to {options.OMEGA_SEARCH_LIMIT}")
            ll = options.OMEGA_SEARCH_LIMIT

        max_lens.append(ll)

        max_len = max(ll, max_len)

    return max_len, max_lens
