import sys

from .Template import Template
from .ModelRun import ModelRun
from .DarwinApp import DarwinApp


def run_search_in_folder(
        folder: str,
        template_file: str = 'template.txt', tokens_file: str = 'tokens.json', options_file: str = 'options.json'
) -> ModelRun:

    app = DarwinApp(options_file, folder)

    model_template = Template(template_file, tokens_file)

    return app.run_template(model_template)


if __name__ == '__main__':
    run_search_in_folder(sys.argv[1])
