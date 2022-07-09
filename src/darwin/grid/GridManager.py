from abc import ABC, abstractmethod

from darwin.ModelRun import ModelRun

_grid_man_classes = {}


class GridManager(ABC):

    @abstractmethod
    def add_model_run(self, run: ModelRun):
        pass

    @abstractmethod
    def poll_model_runs(self, runs: list):
        pass

    @abstractmethod
    def remove_all(self):
        pass


def create_grid_manager(man_name: str) -> GridManager:
    return _grid_man_classes[man_name]()


def register_grid_man(man_name, grid_man_class):
    _grid_man_classes[man_name] = grid_man_class
