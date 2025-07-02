import sys
import os

from darwin.options import options
import darwin.utils as utils


def run_grid_search_in_folder(folder: str):
    os.chdir(folder)

    options.initialize('options.json', folder)

    opts = options.get('generic_grid_adapter', {})

    python_path = opts['python_path']

    submit_command = options.apply_aliases(opts['submit_search_command'])

    has_run_cmd = submit_command.find('{darwin_cmd}') != -1

    aliases = {
        'darwin_cmd': f"{python_path} -m darwin.run_search_in_folder {folder}",
    }

    if has_run_cmd:
        submit_command = utils.apply_aliases(submit_command, aliases)
    else:
        submit_command += f' {python_path} -m darwin.run_search_in_folder {folder}'

    os.system(submit_command)


if __name__ == '__main__':
    run_grid_search_in_folder(sys.argv[1])
