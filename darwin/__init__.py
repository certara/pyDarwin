# allows calling darwin.run_search instead of darwin.run_search.run_search
from .run_search import run_search, run_search_in_folder

__all__ = ['run_search', 'run_search_in_folder']
