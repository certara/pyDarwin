import threading
import psutil
from time import sleep
import os
from os.path import exists

from darwin.Log import log
from darwin.options import options

import darwin.utils as utils

_keep_going = utils.AtomicFlag(True)
_hard_stop = utils.AtomicFlag(False)


def keep_going() -> bool:
    return _keep_going.get()


def interrupted() -> bool:
    return _hard_stop.get()


def start_execution_manager():
    mon = threading.Thread(target=_stop_mon, daemon=True)
    mon.start()


def _stop_mon():
    global _keep_going

    stop = False
    soft_stop = False

    stop_file = os.path.join(options.project_dir, 'stop.darwin')
    soft_stop_file = os.path.join(options.project_dir, 'soft_stop.darwin')

    utils.remove_file(stop_file)
    utils.remove_file(soft_stop_file)

    while not stop:
        sleep(1)
        if exists(stop_file):
            log.warn('Execution has been interrupted')
            stop = True
            _hard_stop.set(True)
        elif exists(soft_stop_file):
            log.warn('Execution will stop after finishing ongoing model runs')
            stop = soft_stop = True

    _keep_going.set(False)

    if not soft_stop:
        log.warn('Terminating all subprocesses...')

        for p in psutil.Process().children(True):
            p.terminate()
