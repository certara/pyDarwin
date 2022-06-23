import logging
import sys

from .Template import Template
from .ModelRun import ModelRun
from .app import init_app, run_template

logger = logging.getLogger(__name__)


def run_search_in_folder(
        folder: str,
        template_file: str = 'template.txt', tokens_file: str = 'tokens.json', options_file: str = 'options.json'
) -> ModelRun:

    init_app(options_file, folder)

    try:
        model_template = Template(template_file, tokens_file)
    except Exception as e:
        logger.error(e)
        raise

    return run_template(model_template)


if __name__ == '__main__':
    run_search_in_folder(sys.argv[1])
