import sys
import os

from darwin.options import options


def _run_grid_search(folder: str):
    os.chdir(folder)

    options.initialize('options.json', folder)

    opts = options.get('grid_manager', {})

    python_path = opts['python_path']

    submit_command = options.apply_aliases(opts['submit_search_command'])
    submit_command += f' {python_path} -m darwin.run_search_in_folder {folder}'

    os.system(submit_command)


if __name__ == '__main__':
    _run_grid_search(sys.argv[1])
