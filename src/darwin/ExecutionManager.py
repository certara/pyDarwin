import threading
import psutil
from time import sleep
import os
from os.path import exists

from darwin.Log import log

import darwin.utils as utils


class _FakeMan:
    _ok = True

    def keep_going(self) -> bool:
        return not self._ok

    def interrupted(self) -> bool:
        return not self._ok

    def dont_even_start(self):
        pass

    def wait_for_subprocesses(self, timeout: int) -> bool:
        return self._ok or timeout


_exec_man = _FakeMan()


class ExecutionManager:
    def __init__(self, working_dir, clean=False):
        self._keep_going = utils.AtomicFlag(True)
        self._hard_stop = utils.AtomicFlag(False)
        self._all_finished_flag = True
        self._all_finished = threading.Condition()
        self._stop = False
        self._soft_stop = False
        self.stop_file = os.path.join(working_dir, 'stop.darwin')
        self.soft_stop_file = os.path.join(working_dir, 'soft_stop.darwin')
        self.clean = clean
        self._mon = None

    def __del__(self):
        self.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def keep_going(self) -> bool:
        return self._keep_going.get()

    def interrupted(self) -> bool:
        return self._hard_stop.get()

    def dont_even_start(self):
        self._keep_going.set(False)

    def wait_for_subprocesses(self, timeout: int) -> bool:
        with self._all_finished:
            if self._all_finished_flag:
                return True

            return self._all_finished.wait(timeout)

    def start(self):
        if self.clean:
            utils.remove_file(self.stop_file)
            utils.remove_file(self.soft_stop_file)

        if exists(self.stop_file) or exists(self.soft_stop_file):
            self._keep_going.set(False)

            log.warn('Chose not to start')

            return

        self._mon = threading.Thread(target=self._stop_mon)
        self._mon.start()

        global _exec_man
        _exec_man = self

    def stop(self):
        if not self._mon:
            return

        global _exec_man
        _exec_man = _FakeMan()

        self._stop = True

        self._mon.join()

        self._mon = None

    def _set_all_finished(self):
        with self._all_finished:
            self._all_finished.notify_all()
            self._all_finished_flag = True

    def _stop_mon(self):
        while not self._stop:
            sleep(1)

            if exists(self.stop_file):
                log.warn('Execution has been interrupted')

                with self._all_finished:
                    self._all_finished_flag = False

                self._stop = True
                self._hard_stop.set(True)
                self._keep_going.set(False)

                utils.terminate_processes(psutil.Process().children(True))

                self._set_all_finished()

            elif not self._soft_stop and exists(self.soft_stop_file):
                log.warn('Execution will stop after finishing ongoing model runs')
                self._soft_stop = True
                self._keep_going.set(False)

                # if soft_stopped all subprocesses should be finished by the time it goes to delete temp_dir
                self._set_all_finished()


def keep_going() -> bool:
    return _exec_man.keep_going()


def interrupted() -> bool:
    return _exec_man.interrupted()


def dont_even_start():
    _exec_man.dont_even_start()


def wait_for_subprocesses(timeout: int) -> bool:
    return _exec_man.wait_for_subprocesses(timeout)
