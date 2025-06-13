import shlex
import re

from darwin.options import options

from .Model import Model


def _cleanup_message(message: str) -> str:
    message = re.sub(r',', '', message, flags=re.RegexFlag.MULTILINE)
    message = re.sub(r'\n', '  ', message, flags=re.RegexFlag.MULTILINE)

    return message


class BaseModelResults:
    JSON_ATTRIBUTES = ['fitness', 'ofv', 'success', 'covariance', 'correlation', 'condition_num', 'messages', 'errors',
                       'estimated_theta_num', 'estimated_omega_num', 'estimated_sigma_num']

    def __init__(self):
        self.fitness = options.crash_value

        self.ofv = options.crash_value
        self.condition_num = options.crash_value

        self.estimated_theta_num = 0
        self.estimated_omega_num = 0
        self.estimated_sigma_num = 0

        self.success = self.covariance = self.correlation = False

        self.messages = self.errors = ''

    def calc_fitness(self, model: Model):
        pass

    @staticmethod
    def can_postprocess() -> bool:
        return True

    def decode_r_stdout(self, r_stdout, file_path: str):
        pass

    def handle_python_pp_result(self, pp_res: tuple, file_path: str):
        pass

    def get_results_str(self):
        pass

    def get_message_text(self, ref_run: str = '') -> str:
        return (f"From {ref_run}: " if ref_run != '' else '') + (self.messages or 'No important warnings')

    def to_dict(self):
        res = {attr: self.__getattribute__(attr) for attr in self.JSON_ATTRIBUTES}

        return res

    @classmethod
    def from_dict(cls, src):
        res = cls()

        for attr in cls.JSON_ATTRIBUTES:
            res.__setattr__(attr, src.get(attr))

        return res


class ModelResults(BaseModelResults):
    JSON_ATTRIBUTES = BaseModelResults.JSON_ATTRIBUTES + [
        'post_run_r_text', 'post_run_python_text', 'post_run_r_penalty', 'post_run_python_penalty'
    ]

    def __init__(self):
        super().__init__()

        self.post_run_r_text = self.post_run_python_text = ''
        self.post_run_python_penalty = self.post_run_r_penalty = 0

    def calc_fitness(self, model: Model):
        """
        Calculates the fitness, based on the model output, and the penalties (from the options file).
        """

        if options.skip_running:
            fitness = 0
            fitness += self.post_run_r_penalty
            fitness += self.post_run_python_penalty

            self.fitness = fitness

            return fitness

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

        fitness += self.estimated_theta_num * penalties['theta']
        fitness += self.estimated_omega_num * penalties['omega']
        fitness += self.estimated_sigma_num * penalties['sigma']

        fitness += self.post_run_r_penalty
        fitness += self.post_run_python_penalty

        if fitness > options.crash_value:
            fitness = options.crash_value

        self.fitness = fitness

        return fitness

    def decode_r_stdout(self, r_stdout, file_path: str):
        new_val = r_stdout.decode('utf-8').replace('[1]', '').strip()
        # comes back a single string
        val = shlex.split(new_val)

        self.post_run_r_penalty = float(val[0])
        self.post_run_r_text = val[-1]

        with open(file_path, "a") as f:
            f.write(f"Post run R code Penalty = {str(self.post_run_r_penalty)}\n")
            f.write(f"Post run R code text = {str(self.post_run_r_text)}\n")

    def handle_python_pp_result(self, pp_res: tuple, file_path: str):
        (self.post_run_python_penalty, self.post_run_python_text) = pp_res

        with open(file_path, "a") as f:
            f.write(f"Post run Python code Penalty = {str(self.post_run_python_penalty)}\n")
            f.write(f"Post run Python code text = {str(self.post_run_python_text)}\n")

    def to_str(self, is_unique: bool) -> str:
        if is_unique:
            fitness_crashed = self.fitness == options.crash_value
            fitness_text = f"{self.fitness:.0f}" if fitness_crashed else f"{self.fitness:.3f}"
        else:
            fitness_text = ''

        return f"fitness = {fitness_text:>9}"

    def get_results_str(self):
        message = _cleanup_message(self.messages)
        err = _cleanup_message(self.errors)

        return f"{self.fitness:.6f},{self.ofv},{self.post_run_r_penalty},{self.post_run_python_penalty}," \
            f"{self.condition_num},{self.success},{self.covariance},{self.correlation},{message},{err}"


def _format_ofv(ofv, pts: int = 3) -> str:
    return f"{ofv}" if isinstance(ofv, int) else "{v:.{p}f}".format(v=ofv, p=pts)


class MOGAModelResults(BaseModelResults):
    @staticmethod
    def can_postprocess() -> bool:
        return False

    def to_str(self, is_unique: bool = True) -> str:
        if is_unique:
            n_params = self.estimated_theta_num + self.estimated_sigma_num + self.estimated_omega_num
            ofv_text = _format_ofv(self.ofv)
            return f" OFV = {ofv_text:>9}, NEP = {n_params:>2}"
        else:
            return f" OFV =          , NEP =   "

    def get_results_str(self):
        message = _cleanup_message(self.messages)
        err = _cleanup_message(self.errors)
        n_params = self.estimated_theta_num + self.estimated_sigma_num + self.estimated_omega_num

        return f"{self.ofv},{n_params}," \
            f"{self.condition_num},{self.success},{self.covariance},{self.correlation},{message},{err}"


class MOGA3ModelResults(BaseModelResults):
    JSON_ATTRIBUTES = BaseModelResults.JSON_ATTRIBUTES + ['f', 'g']
    n_obj = 3

    def __init__(self):
        super().__init__()
        self.f = [options.crash_value] * self.n_obj
        self.g = []

    def decode_r_stdout(self, r_stdout, file_path: str):
        new_val = r_stdout.decode('utf-8').replace('[1]', '').strip()
        vals = new_val.splitlines()

        self.f = [float(v) for v in shlex.split(vals[0])]

        g = shlex.split(vals[1])

        if g[0] != 'NULL':
            self.g = [float(v) for v in g]

        with open(file_path, "a") as f:
            f.write(f"F: {self.f}\n")
            f.write(f"G: {self.g}\n")

    def handle_python_pp_result(self, pp_res: tuple, file_path: str):
        (self.f, self.g) = pp_res

        if not self.f:
            self.f = [options.crash_value] * self.n_obj

        with open(file_path, "a") as f:
            f.write(f"F: {self.f}\n")
            f.write(f"G: {self.g}\n")

    def to_str(self, is_unique: bool = True) -> str:
        if is_unique:
            f = [_format_ofv(v) for v in self.f]
            f = [f" f{i+1} = {v:>9}" for i, v in enumerate(f)]
        else:
            f = [f" f{i} =          " for i in range(1, len(self.f)+1)]

        return ','.join(f)

    def get_results_str(self):
        message = _cleanup_message(self.messages)
        err = _cleanup_message(self.errors)

        f = [_format_ofv(v, 6) for v in self.f]
        f_str = ','.join(f)

        return f"{f_str},{self.ofv}," \
            f"{self.condition_num},{self.success},{self.covariance},{self.correlation},{message},{err}"
