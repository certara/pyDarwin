from abc import ABC, abstractmethod

from collections import OrderedDict

import darwin.utils as utils
from darwin.options import options

from .Template import Template
from .ModelCode import ModelCode
from .Model import Model

_ENGINES = {}


class ModelEngineAdapter(ABC):

    @staticmethod
    @abstractmethod
    def get_engine_name() -> str:
        pass

    @staticmethod
    @abstractmethod
    def init_engine():
        pass

    @staticmethod
    @abstractmethod
    def read_model(run) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def read_data_file_name(control_file_name: str) -> list:
        """
        Parses the control file to read the data file name.

        :return: Data file path string
        """

        pass

    @staticmethod
    @abstractmethod
    def read_results(run) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def cleanup(run_dir: str, file_stem: str):
        """
        Deletes all unneeded files after run completes.
        """

        pass

    @staticmethod
    @abstractmethod
    def get_error_messages(run, run_dir: str):
        """
        Reads error messages from any available source.
        """

        pass

    @abstractmethod
    def _make_control_impl(self, control: str, template: Template, model_code: ModelCode, phenotype: OrderedDict):
        pass

    def make_control(self, template: Template, model_code: ModelCode):
        """
        Constructs control file from intcode.
        """

        phenotype = OrderedDict(zip(template.tokens.keys(), model_code.IntCode))

        non_inf_tokens = [True] * len(template.tokens)

        control = utils.replace_tokens(template.tokens, template.template_text, phenotype, non_inf_tokens,
                                       options.TOKEN_NESTING_LIMIT)

        non_influential_token_num = sum(non_inf_tokens)

        model_code_str = str(model_code.FullBinCode if (options.isGA or options.isPSO) else model_code.IntCode)

        control, comment_mark, bands = self._make_control_impl(control, template, model_code, phenotype)

        phenotype = str(OrderedDict((k, v) for (k, v), inf in zip(phenotype.items(), non_inf_tokens) if not inf))
        phenotype = phenotype.replace('OrderedDict', '')
        phenotype += bands

        control += f"\n{comment_mark} Phenotype: " + phenotype + f"\n{comment_mark} Genotype: " + model_code_str \
                   + f"\n{comment_mark} Num non-influential tokens: " + str(non_influential_token_num) + "\n"

        return phenotype, control, non_influential_token_num

    @staticmethod
    @abstractmethod
    def get_model_run_commands(run) -> list:

        pass

    @staticmethod
    @abstractmethod
    def get_stem(generation, model_num) -> str:

        pass

    @staticmethod
    @abstractmethod
    def get_file_names(stem: str) -> tuple:

        pass

    @staticmethod
    @abstractmethod
    def get_final_file_names() -> tuple:

        pass

    def create_new_model(self, template: Template, model_code: ModelCode, num_effects=-1) -> Model:

        model = Model(model_code)

        model.phenotype, model.control, model.non_influential_token_num = \
            self.make_control(template, model_code)

        if num_effects > -1:
            self.add_comment(f"Number of effects = {num_effects}\n", model.control)

        return model

    @staticmethod
    @abstractmethod
    def add_comment(comment: str, control: str):
        """
        Add a comment to the control
        """

        pass

    @staticmethod
    @abstractmethod
    def init_template(template: Template):
        """
        Perform any adapter-specific initialization, e.g., initialize THETA/OMEGA/SIGMA blocks.
        """

        pass

    @staticmethod
    @abstractmethod
    def can_omega_search(template_text: str) -> tuple:
        """
        Tell if it's possible to perform omega search with current template
        If not, second member tells why
        """

        pass

    @staticmethod
    @abstractmethod
    def get_max_search_block(template: Template) -> tuple:
        """
        """

        pass

    @staticmethod
    @abstractmethod
    def get_omega_search_pattern() -> str:
        """
        """

        pass

    @staticmethod
    @abstractmethod
    def remove_comments(text: str) -> str:
        """
        """

        pass


def register_engine_adapter(name: str, engine):
    global _ENGINES

    _ENGINES[name] = engine


def get_engine_adapter(name: str) -> ModelEngineAdapter:
    global _ENGINES

    return _ENGINES[name]
