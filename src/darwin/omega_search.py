import math
import numpy as np

from darwin.Log import log

from darwin.options import options
from darwin.ModelCode import ModelCode


def apply_omega_bands(control: str, model_code: ModelCode, omega_band_pos: int, set_bands_impl: callable) -> tuple:
    bands = ''

    if options.search_omega_bands:
        # band width must be last gene
        band_width = model_code.IntCode[omega_band_pos]

        if band_width > 0:
            if options.search_omega_sub_matrix:
                submatrices = model_code.IntCode[(omega_band_pos + 1):]
            else:
                submatrices = [1] * 10  # if no search, max is permitted, then unlimited size of omega matrices

            # need to know where the band width is specified, rest is omega submatrices
            control, band_arr = set_bands_impl(control, band_width, submatrices)

            if band_arr:
                bands = ', '. join(band_arr)
                bands = f", bands: ({bands})"

    return control, bands


def get_bands(diag_block: list, band_width: int, omega_band_pos: list) -> list:
    res = []

    bands = omega_band_pos.copy()

    any_band = band_width > 0 and any(bands)

    rng = np.random.default_rng(seed=options.random_seed)

    bands.extend([0] * (len(diag_block) - len(bands)))

    for i in range(len(bands) - 1):
        if bands[i] == 1 and bands[i + 1] == 0:
            bands[i + 1] = 2

    block = [[], []]
    last_band = bands[0]

    omega_size = 0  # current omega block size

    def add_res():
        nonlocal omega_size

        if any_band and last_band and omega_size > 1:
            init_off_diags = find_band(omega_size, band_width, block[last_band], rng)
        else:
            init_off_diags = [[j] for j in block[last_band]]
            omega_size = 0

        res.append((init_off_diags, omega_size))

    for omega, band in zip(diag_block, bands):
        idx = band if band < 2 else 1
        block[idx].append(omega)

        if band != last_band and band != 2:
            add_res()

            block[last_band] = []
            omega_size = 0

        if band:
            omega_size += 1

        last_band = idx

    if len(block[last_band]):
        add_res()

    return res


def find_band(omega_size: int, band_width: int, omega_block: list, rng):
    factor = 1.0
    count = 0

    init_off_diags = np.ones([omega_size, omega_size])

    is_pos_def = False

    while not is_pos_def:
        factor *= 0.5

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
