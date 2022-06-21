from copy import copy

import darwin.GlobalVars as GlobalVars

from .ModelCode import ModelCode

JSON_ATTRIBUTES = [
    'control', 'non_influential_token_num',
    'theta_num', 'omega_num', 'sigma_num',
    'estimated_theta_num', 'estimated_omega_num', 'estimated_sigma_num'
]


class Model:
    """
    The full model, used for GA, GP, RF, GBRF and exhaustive search.

    Model instantiation takes a template as an argument, along with the model code, model number and generation
    function include constructing the control file, executing the control file, calculating the fitness/reward.

    model_code : a ModelCode object
        contains the bit string/integer string representation of the model. Includes the Fullbinary
        string, integer string and minimal binary representation of the model
        (for GA, GP/RF/GBRT and downhill respectively)

    """

    def __init__(self, code: ModelCode):
        """
        Create model object.

        :param code: ModelCode Object, contains the bit string/integer string representation of the model.
            Includes the Fullbinary string, integer string and minimal binary representation of the model
            (for GA, GP/RF/GBRT and downhill respectively)
        :type code: ModelCode
        """

        self.model_code = copy(code)

        self.theta_num = self.estimated_theta_num = 0
        self.omega_num = self.estimated_omega_num = 0
        self.sigma_num = self.estimated_sigma_num = 0

        self.non_influential_token_num = 0

        self.phenotype = self.control = None

    def genotype(self) -> list:
        return self.model_code.IntCode

    def to_dict(self):
        res = {}

        for attr in JSON_ATTRIBUTES:
            res[attr] = self.__getattribute__(attr)

        res['model_code'] = self.model_code.to_dict()

        return res

    @classmethod
    def from_dict(cls, src):
        code = ModelCode.from_dict(src['model_code'])

        res = cls(code)

        for attr in JSON_ATTRIBUTES:
            res.__setattr__(attr, src[attr])

        return res


def write_best_model_files(control_path: str, result_path: str):
    """
    Copies the current model control file and output file to the home_directory.

    :param control_path: path to current best model control file
    :type control_path: str

    :param result_path: path to current best model result file
    :type result_path: str
    """

    with open(control_path, 'w') as control:
        control.write(GlobalVars.BestRun.model.control)

    with open(result_path, 'w') as result:
        result.write(GlobalVars.BestModelOutput)
