import os

from abc import ABC, abstractmethod

import darwin.utils as utils

from darwin.Log import log
from darwin.options import options

_model_run_man = None
_model_run_man_classes = {}


class ModelRunManager(ABC):

    @staticmethod
    def init_folders():
        log.message('Preparing project working folder...')

        os.makedirs(options.working_dir, exist_ok=True)

        log.message('Preparing project output folder...')

        utils.remove_dir(options.output_dir)
        os.makedirs(options.output_dir, exist_ok=True)

        utils.remove_dir(options.key_models_dir)

        if options.keep_key_models:
            os.makedirs(options.key_models_dir, exist_ok=True)

        if options.isMOGA:
            utils.remove_dir(options.non_dominated_models_dir)
            os.makedirs(options.non_dominated_models_dir, exist_ok=True)

    @staticmethod
    def cleanup_folders():
        pass

    @abstractmethod
    def _preprocess_runs(self, runs: list) -> list:
        pass

    @abstractmethod
    def _process_runs(self, runs: list) -> list:
        pass

    @abstractmethod
    def _postprocess_runs(self, runs: list) -> list:
        pass

    def run_all(self, runs: list):
        """
        Runs the models. Always runs from integer representation. For GA will need to convert to integer.
        For downhill, will need to convert to minimal binary, then to integer.
        """

        runs = self._preprocess_runs(runs)

        runs = self._process_runs(runs)

        runs = self._postprocess_runs(runs)

        return runs


def set_run_manager(man):
    global _model_run_man

    _model_run_man = man


def get_run_manager() -> ModelRunManager or None:
    return _model_run_man


def rerun_models(models: list):
    if not models:
        return

    for r in models:
        r.rerun = True
        r.source = 'new'
        r.reference_model_num = -1
        r.status = 'Not Started'
        r.result.ref_run = ''

    get_run_manager().run_all(models)


def register_model_run_man(man_name, mrm_class):
    _model_run_man_classes[man_name] = mrm_class


def create_model_run_man(man_name) -> ModelRunManager:
    return _model_run_man_classes[man_name]()
