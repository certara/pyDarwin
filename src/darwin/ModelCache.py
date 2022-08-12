from abc import ABC, abstractmethod

from .ModelRun import ModelRun

_model_cache = None
_model_cache_classes = {}


class ModelCache(ABC):
    """
    Abstract Model Cache. Describes the interface that must be implemented by every Model Cache.
    """

    @abstractmethod
    def store_model_run(self, run: ModelRun):
        """
        Store a run.
        """
        pass

    @abstractmethod
    def find_model_run(self, key: str) -> ModelRun:
        """
        Find a run by genotype.
        """
        pass

    @abstractmethod
    def load(self):
        """
        Load the cache from a saved state.
        """
        pass

    @abstractmethod
    def dump(self):
        """
        Dump the cache to a saved state.
        """
        pass

    def finalize(self):
        """
        Finalize all ongoing activities.
        """
        pass


def set_model_cache(cache):
    """
    Set current Model Cache instance. Supposed to be called once at the startup.
    """
    global _model_cache

    _model_cache = cache


def get_model_cache():
    """
    Get current Model Cache instance.
    """
    return _model_cache


def register_model_cache(cache_name, mc_class):
    """
    Register Model Cache class. *cache_name* is arbitrary, must be unique among all registered caches.
    """
    _model_cache_classes[cache_name] = mc_class


def create_model_cache(cache_name) -> ModelCache:
    """
    Create Model Cache instance. The cache class must be registered under *cache_name*.
    """
    return _model_cache_classes[cache_name]()
