from copy import copy

from .ModelCode import ModelCode

JSON_ATTRIBUTES = [
    'control', 'non_influential_token_num',
    'theta_num', 'omega_num', 'sigma_num',
    'phenotype'
]


class Model:
    """
    The full model, used for GA, GP, RF, GBRF and exhaustive search.

    Model instantiation takes a template as an argument, along with the model code, model number,
    and generation. Functions include constructing the control file, executing the control file,
    calculating the fitness/reward.

    model_code : a ModelCode object
        Contains the bit string/integer string representation of the model. Includes the full binary string,
        integer string, and minimal binary representation of the model (for GA, GP/RF/GBRT and downhill, respectively).

    """

    def __init__(self, code: ModelCode):

        self.model_code = copy(code)

        self.theta_num = 0
        self.omega_num = 0
        self.sigma_num = 0

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
