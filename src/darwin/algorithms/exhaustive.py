import numpy as np
import re

import darwin.GlobalVars as GlobalVars

from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import keep_going

from darwin.Template import Template
from darwin.ModelRun import ModelRun
from darwin.ModelCode import ModelCode
from darwin.Population import Population
from darwin.DarwinError import DarwinError

generator_names = ['l-to-r', 'r-to-l', 'meshgrid', 'unique']


def run_exhaustive(template: Template) -> ModelRun:
    """
    Run full exhaustive search on the Template, all possible combinations.
    All models will be run in iteration number 0.

    :param template: Model Template
    :type template: Template

    :return: Returns final/best model run
    :rtype: ModelRun
    """

    batch_size = options.get('exhaustive_batch_size', 100)
    num_models = template.get_search_space_size()

    start = 0

    for codes in exhaustive_batch_generator(template, num_models, batch_size):
        pop = Population.from_codes(template, '0', codes, ModelCode.from_int,
                                    start_number=start, max_number=num_models)

        start += batch_size

        pop.run(remaining_models=(num_models - GlobalVars.unique_models_num))

        if not keep_going():
            break

        if GlobalVars.best_run is not None:
            log.message(f"Current Best fitness = {GlobalVars.best_run.result.fitness}")

    return GlobalVars.best_run


def get_search_space(template: Template) -> np.ndarray:
    num_groups = template.get_search_space_coordinates()

    codes = np.array(np.meshgrid(*num_groups)).T.reshape(-1, len(num_groups))

    return codes


def exhaustive_batch_generator(template: Template, num_models: int, batch_size: int):
    gen_name = options.get('exhaustive_generator', 'r-to-l')

    if gen_name not in generator_names:
        raise DarwinError(f"exhaustive_generator must be one of {generator_names}, got '{gen_name}'")

    if gen_name == 'meshgrid':
        codes = get_search_space(template)

        for start in range(0, num_models, batch_size):
            yield codes[start:start + batch_size].tolist()

        return

    batch = []

    cnt = 0

    coordinates = template.get_search_space_coordinates()

    gen = unique_code_generator(template, coordinates) if gen_name == 'unique' \
        else int_code_generator(coordinates, gen_name == 'r-to-l')

    for code in gen:
        batch.append(code)
        cnt += 1

        if cnt == batch_size:
            yield batch
            batch = []
            cnt = 0

    if batch:
        yield batch


def unique_code_generator(template: Template, coordinates: list):
    tokens = template.tokens.copy()
    gene_nums = {name: i for i, name in enumerate(tokens.keys())}
    initial = [x[0] for x in coordinates]

    num_coord = len(coordinates)

    step = 2 if options.max_omega_band_width is not None else 1

    if template.omega_band_pos is not None:
        for i, s in enumerate(range(template.omega_band_pos, num_coord, step)):
            gene_nums[f"search band {i+1}"] = s
            gene_nums[f"search_block {i+1}"] = s

    def _replace_tokens(text: str, genome_in: list, looping_over: list, looped_over_in: list, effective_subst: dict, sb_idx: int):

        for key in effective_subst.keys():
            text = text.replace(key, effective_subst[key])

        genome = genome_in.copy()
        looped_over = looped_over_in.copy()

        while x := re.search(r'\{([\w~]+)\[\d+]}', text, flags=re.RegexFlag.MULTILINE) \
                or re.search(r';; (search band)', text, flags=re.RegexFlag.MULTILINE) \
                or re.search(r'^\s*#(search_block)\(', text, flags=re.RegexFlag.MULTILINE):

            key = x.group(1)
            key_i = key

            if key == 'search band' or key == 'search_block':
                key_i += f" {sb_idx}"

            gene_num = gene_nums[key_i]

            if gene_num >= num_coord or looped_over[gene_num]:
                break

            if looping_over[gene_num]:
                continue

            if key == 'search band' or key == 'search_block':
                token_sets = []

                for gene_val in coordinates[gene_num]:
                    if step == 2:
                        for second_val in coordinates[gene_num+1]:
                            token_sets.append([gene_val, second_val])
                    else:
                        token_sets.append([gene_val])

                orig_text = text

                text = text.replace(key, 'searched', 1)

                for gene_vals in token_sets:
                    genome[gene_num:gene_num+step] = gene_vals

                    looping_over[gene_num] = True

                    yield from _replace_tokens(text, genome, looping_over, looped_over, effective_subst, sb_idx + 1)

                    looping_over[gene_num] = False

                looped_over[gene_num] = True

                text = orig_text

                continue

            for gene_val, token_set in enumerate(tokens[key]):
                token_num = 1

                any_found = False
                orig_text = text

                this_subst = {}

                for token in token_set:
                    full_key = "{" + key + "[" + str(token_num) + "]" + "}"

                    if full_key in text:
                        text = text.replace(full_key, token)
                        this_subst[full_key] = token
                        any_found = True

                    token_num += 1

                if any_found:
                    genome[gene_num] = gene_val

                    looping_over[gene_num] = True

                    yield from _replace_tokens(text, genome, looping_over, looped_over,
                                               effective_subst | this_subst, sb_idx)

                    looping_over[gene_num] = False
                    looped_over[gene_num] = True

                    text = orig_text
                else:
                    break

        if not re.findall(r'\{[\w~]+\[\d+]}|;; search band|^\s*#search_block\(', text, flags=re.RegexFlag.MULTILINE):
            code = [x or i for x, i in zip(genome, initial)]
            yield code

    yield from _replace_tokens(template.template_text, [None] * num_coord, [False] * num_coord, [False] * num_coord, {}, 1)


def int_code_generator(coordinates, reverse: bool):
    gene_max = [x[-1] for x in coordinates]
    initial = [x[0] for x in coordinates]

    gene_max_len = len(gene_max)

    lgm_range = range(gene_max_len-1, -1, -1) if reverse else range(gene_max_len)

    last_gene = 0 if reverse else gene_max_len-1

    current = initial.copy()

    while True:
        yield current.copy()

        overflown = -1

        for i in lgm_range:
            current[i] += 1

            if current[i] > gene_max[i]:
                current[i] = initial[i]
                overflown = i
            else:
                break

        if overflown == last_gene:
            break
