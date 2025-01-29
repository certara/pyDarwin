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

        self.post_run_r_text = self.post_run_python_text = ''
        self.post_run_python_penalty = self.post_run_r_penalty = 0

        self.messages = self.errors = ''
        self.ref_run = ''

    def get_message_text(self) -> str:
        message = f"From {self.ref_run}: " if self.ref_run != '' else ''
        message += self.messages or 'No important warnings'

        return message

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
        if options.algorithm == "MOGA":
            fitness = self.ofv # really isn't a fitness for MOGA
        else:
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
                if self.condition_num > 1000:
                    fitness += penalties['condition_number']

            fitness += model.estimated_theta_num * penalties['theta']
            fitness += model.estimated_omega_num * penalties['omega']
            fitness += model.estimated_sigma_num * penalties['sigma']

            fitness += self.post_run_r_penalty
            fitness += self.post_run_python_penalty

            if fitness > options.crash_value:
                fitness = options.crash_value

            self.fitness = fitness

        return fitness
