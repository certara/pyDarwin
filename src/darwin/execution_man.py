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
_all_finished_flag = False
_all_finished = threading.Condition()


def keep_going() -> bool:
    return _keep_going.get()


def dont_even_start():
    _keep_going.set(False)
    # in order to enable cleanup_folders
    _set_all_finished()


def interrupted() -> bool:
    return _hard_stop.get()


def wait_for_subprocesses(timeout: int) -> bool:
    with _all_finished:
        if _all_finished_flag:
            return True

        return _all_finished.wait(timeout)


def start_execution_manager(clean=False):
    stop_file = os.path.join(options.output_dir, 'stop.darwin')
    soft_stop_file = os.path.join(options.output_dir, 'soft_stop.darwin')

    if clean:
        utils.remove_file(stop_file)
        utils.remove_file(soft_stop_file)

    if exists(stop_file) or exists(soft_stop_file):
        _keep_going.set(False)

        log.warn('Chose not to start')

        return

    mon = threading.Thread(target=_stop_mon, args=(stop_file, soft_stop_file), daemon=True)
    mon.start()


def _set_all_finished():
    with _all_finished:
        global _all_finished_flag
        _all_finished.notify_all()
        _all_finished_flag = True


def _stop_mon(stop_file: str, soft_stop_file: str):
    stop = False
    soft_stop = False

    while not stop:
        sleep(1)

        if exists(stop_file):
            log.warn('Execution has been interrupted')

            with _all_finished:
                global _all_finished_flag
                _all_finished_flag = False

            stop = True
            _hard_stop.set(True)
            _keep_going.set(False)

            utils.terminate_processes(psutil.Process().children(True))

            _set_all_finished()

        elif not soft_stop and exists(soft_stop_file):
            log.warn('Execution will stop after finishing ongoing model runs')
            soft_stop = True
            _keep_going.set(False)

            # if soft_stopped all subprocesses should be finished by the time it goes to delete temp_dir
            _set_all_finished()
