from darwin.options import options

from .Model import Model

JSON_ATTRIBUTES = [
    'fitness', 'ofv', 'success', 'covariance', 'correlation', 'condition_num',
    'post_run_r_text', 'post_run_r_penalty', 'post_run_python_text', 'post_run_python_penalty',
    'messages', 'errors'
]


class ModelResults:
    def __init__(self):
        self.fitness = options.crash_value

        self.ofv = options.crash_value
        self.condition_num = options.crash_value

        self.success = self.covariance = self.correlation = False

        self.post_run_r_text = self.post_run_python_text = ""
        self.post_run_python_penalty = self.post_run_r_penalty = 0

        self.messages = self.errors = ""

    def to_dict(self):
        res = {attr: self.__getattribute__(attr) for attr in JSON_ATTRIBUTES}

        return res

    @classmethod
    def from_dict(cls, src):
        res = cls()

        for attr in JSON_ATTRIBUTES:
            res.__setattr__(attr, src.get(attr))

        return res

    def calc_fitness(self, model: Model):
        """
        Calculates the fitness, based on the model output, and the penalties (from the options file).
        """

        penalties = options.penalty

        fitness = self.ofv

        # non influential tokens penalties
        fitness += model.non_influential_token_num * penalties['non_influential_tokens']

        if not self.success:
            fitness += penalties['convergence']

        if not self.covariance:
            fitness += penalties['covariance']
            fitness += penalties['correlation']
            fitness += penalties['condition_number']
        else:
            if not self.correlation:
                fitness += penalties['correlation']
            if not self.condition_num > 1000:
                fitness += penalties['condition_number']

        fitness += model.estimated_theta_num * penalties['theta']
        fitness += model.omega_num * penalties['omega']
        fitness += model.sigma_num * penalties['sigma']

        fitness += self.post_run_r_penalty
        fitness += self.post_run_python_penalty

        if fitness > options.crash_value:
            fitness = options.crash_value

        self.fitness = fitness

        return fitness
