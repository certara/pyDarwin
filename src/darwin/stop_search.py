import sys
import os

from darwin.options import options
from darwin.Log import log


def _stop_search(now: bool):
    stop_file = 'stop.darwin' if now else 'soft_stop.darwin'

    with open(os.path.join(options.working_dir, stop_file), 'w'):
        pass


if __name__ == '__main__':
    arg_count = len(sys.argv)

    if not (1 < arg_count < 4) or arg_count == 3 and sys.argv[1] != '-f':
        print('usage: stop_search.py [-f] <path>')
        sys.exit()

    if arg_count == 2:
        force = False
        path = sys.argv[1]
    else:
        force = True
        path = sys.argv[2]

    if os.path.isfile(path):
        options.initialize(path)
    elif os.path.isdir(path):
        options.initialize(os.path.join(path, 'options.json'))
    else:
        log.error(f'Path not found: {path}')
        sys.exit()

    _stop_search(force)
