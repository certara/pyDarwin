from abc import ABC, abstractmethod

from .ModelRun import ModelRun

_model_cache = None


class ModelCache(ABC):

    @abstractmethod
    def store_model_run(self, run: ModelRun):
        pass

    @abstractmethod
    def find_model_run(self, key: str) -> ModelRun:
        pass

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def dump(self):
        pass


def set_model_cache(cache):
    global _model_cache

    _model_cache = cache


def get_model_cache() -> ModelCache:
    return _model_cache
