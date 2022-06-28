from abc import ABC, abstractmethod

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
    def read_model(run) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def read_data_file_name(control_file_name: str) -> list:
        """
        Parses the control file to read the data file name

        :return: data file path string
        :rtype: list
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
        Deletes all unneeded files after run.
        Note that an option "remove_run_dir" in the options file to remove the entire run_dir.
        """

        pass

    @staticmethod
    @abstractmethod
    def get_error_messages(run):
        """
        Reads error messages from any available source.
        """

        pass

    @staticmethod
    @abstractmethod
    def make_control(template: Template, model_code: ModelCode):
        """
        Constructs control file from intcode.
        Ignore last value if self_search_omega_bands.
        """

        pass

    @staticmethod
    @abstractmethod
    def get_model_run_command(run) -> list:

        pass

    @staticmethod
    @abstractmethod
    def get_stem(generation, model_num) -> str:

        pass

    @staticmethod
    @abstractmethod
    def get_file_names(stem: str):

        pass

    def create_new_model(self, template: Template, model_code: ModelCode) -> Model:
        """
        """

        model = Model(model_code)

        model.phenotype, model.control, model.non_influential_token_num = self.make_control(template, model_code)

        return model

    @staticmethod
    def restore_model(src: dict):
        """
        """

        pass


def register_engine_adapter(name: str, engine):
    global _ENGINES

    _ENGINES[name] = engine


def get_engine_adapter(name: str) -> ModelEngineAdapter:
    global _ENGINES

    return _ENGINES[name]
