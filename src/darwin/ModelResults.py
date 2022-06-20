from darwin.options import options

from .Model import Model


class ModelResults:
    def __init__(self):
        self.fitness = options.crash_value

        self.ofv = options.crash_value
        self.condition_num = options.crash_value

        self.success = self.covariance = self.correlation = False

        self.post_run_r_text = self.post_run_python_text = ""
        self.post_run_python_penalty = self.post_run_r_penalty = 0

        self.nm_translation_message = self.prd_err = ""

    def calc_fitness(self, model: Model):
        """
        Calculates the fitness, based on the model output, and the penalties (from the options file).
        Need to look in output file for parameter at boundary and parameter non-positive.
        """

        fitness = options.crash_value

        try:
            fitness = self.ofv
            # non influential tokens penalties
            fitness += model.non_influential_token_num * options['non_influential_tokens_penalty']

            if not self.success:
                fitness += options['covergencePenalty']

            if not self.covariance:
                fitness += options['covariancePenalty']
                fitness += options['correlationPenalty']
                fitness += options['conditionNumberPenalty']
            else:
                if not self.correlation:
                    fitness += options['correlationPenalty']

            fitness += model.estimated_theta_num * options['THETAPenalty']
            fitness += model.omega_num * options['OMEGAPenalty']
            fitness += model.sigma_num * options['SIGMAPenalty']

            fitness += self.post_run_r_penalty
            fitness += self.post_run_python_penalty

            if fitness > options.crash_value:
                fitness = options.crash_value

            self.fitness = fitness
        except:
            pass

        return fitness
