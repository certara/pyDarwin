import itertools

from collections import OrderedDict

from darwin.ModelEngineAdapter import register_engine_adapter

from darwin.Template import Template
from darwin.ModelCode import ModelCode

from .NMEngineAdapter import NMEngineAdapter, get_variable_block

from .utils import match_vars


class DVNMEngineAdapter(NMEngineAdapter):
    pk_block = None

    @staticmethod
    def get_engine_name() -> str:
        return 'nonmem.dyn_var'

    @staticmethod
    def init_template(template: Template):
        NMEngineAdapter.init_template(template)

        DVNMEngineAdapter.pk_block = get_variable_block(template.template_text, '$PK')

    def _make_control_impl(self, control: str, template: Template, model_code: ModelCode, phenotype: OrderedDict):
        control = match_vars(control, template.tokens, self.pk_block, phenotype, 'MU')

        # Get compartment info
        num_cpt_key = 'NUMBER_COMPARTMENTS'
        assert control.count(num_cpt_key) == 1  # Check keyword only used once
        cpt_info = get_cpt_info(control)

        # Get maps for dynamic variables
        rate_constant_map = get_rate_constants(cpt_info)
        c_mass_map = get_c_mass_map(cpt_info)
        s_scale_map = get_s_scale_map(cpt_info)

        # Update compartment count and dynamic variables
        control = control.replace(num_cpt_key, str(len(cpt_info) - 1))  # -1 for elimination cmt

        for key, value in rate_constant_map.items():
            control = control.replace(key, value)
        for key, value in c_mass_map.items():
            control = control.replace(key, value)
        for key, value in s_scale_map.items():
            control = control.replace(key, value)

        return super(DVNMEngineAdapter, self)._make_control_impl(control, template, model_code, phenotype)


def get_cpt_info(control):
    """
    Extracts compartment information from a given NONMEM control string.
    Args:
        control (str): The control string for NONMEM file
    Returns:
        list: A list of dictionaries, each containing the index ('i') and
              compartment name ('cpt'). The list includes an additional
              dictionary for 'ELIMINATION' with index 0.
    """

    control_lines = control.split("\n")
    control_lines = [x.strip() for x in control_lines if x != ""]
    comp_lines = [x for x in control_lines if "comp=(" in x.lower().replace(" ", "")]

    # Extract compartment info
    cpt_info_list = []
    for i, cpt in enumerate(comp_lines):
        cpt = cpt.split("(")[1]
        cpt = cpt.split(",")[0]
        cpt = cpt.replace(")", "")
        cpt = cpt.strip()
        cpt_info = {
            "i": i + 1,
            "cpt": cpt
        }
        cpt_info_list.append(cpt_info)

    # Add elimination
    cpt_info_list.append({
        "i": 0,
        "cpt": "ELIMINATION"
    })

    return cpt_info_list


def get_rate_constants(cpt_info):
    """
    Generate a map of rate constants based on compartment information.
    Args:
        cpt_info (list of dict): A list of dictionaries where each dictionary contains
                                 information about a compartment. Each dictionary must
                                 have the keys 'i' (compartment index) and 'cpt' (compartment name).
    Returns:
        dict: A dictionary where the keys are rate constant identifiers in the format
              "RATE_CONSTANT(cpt1, cpt2)" and the values are rate constant values in the
              format "k{i}T{j}".
    """

    cpt_combinations = list(itertools.product(cpt_info, cpt_info))
    rate_constant_map = {}
    for pair in cpt_combinations:
        if pair[0]["i"] != pair[1]["i"]:
            # print()
            # print(pair)
            rate_constant_key = f"RATE_CONSTANT({pair[0]['cpt']}, {pair[1]['cpt']})"
            rate_constant_value = f"k{pair[0]['i']}T{pair[1]['i']}"
            rate_constant_map[rate_constant_key] = rate_constant_value

    return rate_constant_map


def get_c_mass_map(cpt_info):
    """
    Generate a mapping of compartment mass keys to their corresponding values.
    This function takes a list of compartment information dictionaries and creates
    a mapping where the keys are formatted as "AMT_COMPARTMENT({cpt})" and the values
    are formatted as "A({i})".
    Args:
        cpt_info (list of dict): A list of dictionaries containing compartment information.
            Each dictionary should have the keys 'cpt' and 'i'.
    Returns:
        dict: A dictionary mapping compartment mass keys to their corresponding values.
    """

    c_mass_map = {}

    for row in cpt_info:
        c_mass_key = f"AMT_COMPARTMENT({row['cpt']})"
        c_mass_value = f"A({row['i']})"
        c_mass_map[c_mass_key] = c_mass_value

    return c_mass_map


def get_s_scale_map(cpt_info):
    """
    Generates a mapping of scaling keys to scaling values based on the provided component information.
    Args:
        cpt_info (list of dict): A list of dictionaries where each dictionary contains information about a component.
            Each dictionary is expected to have the keys 'cpt' and 'i'.
    Returns:
        dict: A dictionary where the keys are formatted as "DATA_SCALING({cpt})" and the values are formatted as "S{i}".
    """

    s_scale_map = {}

    for row in cpt_info:
        s_scale_key = f"DATA_SCALING({row['cpt']})"
        s_scale_value = f"S{row['i']}"
        s_scale_map[s_scale_key] = s_scale_value

    return s_scale_map


def register():
    register_engine_adapter('nonmem.dyn_var', DVNMEngineAdapter())


register()
