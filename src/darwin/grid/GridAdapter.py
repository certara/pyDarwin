from abc import ABC, abstractmethod

from darwin.ModelRun import ModelRun

_grid_man_classes = {}


class GridAdapter(ABC):

    @abstractmethod
    def add_model_run(self, run: ModelRun):
        pass

    @abstractmethod
    def poll_model_runs(self, runs: list):
        pass

    @abstractmethod
    def remove_all(self):
        pass


def create_grid_adapter(man_name: str) -> GridAdapter:
    return _grid_man_classes[man_name]()


def register_grid_adapter(man_name, grid_man_class):
    _grid_man_classes[man_name] = grid_man_class
