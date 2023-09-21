import sys

from .Template import Template
from .DarwinApp import init_search, go_to_folder

from darwin.options import options


def get_search_info(
        folder: str,
        template_file: str = 'template.txt', tokens_file: str = 'tokens.json', options_file: str = 'options.json'
):
    # if running in folder, options_file may be a relative path, so need to cd to the folder first
    # but if it's an absolute path, then folder may not even exist, in which case we create it
    if folder:
        go_to_folder(folder)

    options.initialize(options_file, folder)

    model_template = Template(template_file, tokens_file)
    init_search(model_template)


if __name__ == '__main__':
    get_search_info(sys.argv[1])
