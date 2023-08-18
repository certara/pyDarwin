import sys
import os

from darwin.options import options
import darwin.utils as utils


def _run_grid_search(template_file: str, tokens_file: str, options_file: str):
    options.initialize(options_file)

    opts = options.get('generic_grid_adapter', {})

    python_path = opts['python_path']

    submit_command = options.apply_aliases(opts['submit_search_command'])

    has_run_cmd = submit_command.find('{darwin_cmd}') != -1

    aliases = {
        'darwin_cmd': f"{python_path} -m darwin.run_search {template_file} {tokens_file} {options_file}",
    }

    if has_run_cmd:
        submit_command = utils.apply_aliases(submit_command, aliases)
    else:
        submit_command += f' {python_path} -m darwin.run_search {template_file} {tokens_file} {options_file}'

    os.system(submit_command)


if __name__ == '__main__':
    _run_grid_search(sys.argv[1], sys.argv[2], sys.argv[3])
