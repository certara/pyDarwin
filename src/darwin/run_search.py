import logging
import sys

from .Template import Template
from .ModelRun import ModelRun
from .app import DarwinApp, run_template

logger = logging.getLogger(__name__)


def run_search(template_file: str, tokens_file: str, options_file: str) -> ModelRun:
    """
    The run_search function run algorithm selected in options_file, based on template_file and tokens_file
    At the end, write best control and output file to project_dir (specified in options_file)
    options_file path name should, in general, be absolute, other file names can be absolute path
    or path relative to the project_dir
    function returns the final model object
    """

    _ = DarwinApp(options_file)

    try:
        model_template = Template(template_file, tokens_file)
    except Exception as e:
        logger.error(e)
        raise

    return run_template(model_template)


if __name__ == '__main__':
    run_search(sys.argv[1], sys.argv[2], sys.argv[3])
