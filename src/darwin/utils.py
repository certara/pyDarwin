import os
import re
import shutil
import heapq
import threading
import multiprocessing as mp
import traceback
import psutil
import math

from darwin.Log import log

from .DarwinError import DarwinError


def convert_full_bin_int(population, gene_max: list, length: list):
    """
    Converts a "full binary" (e.g., from GA to integer (used to select token sets))
    modified from the function in ModelCode.py
    :param population: population, including fitness and bits
    :param gene_max: integer list, maximum number of token sets in that token group
    :param length: integer list, how long each gene is
    :return: an integer array of which token goes into this model.
    :rtype: integer array
    """
    phenotype = list()

    for this_ind in population:
        this_phenotype = []
        start = 0

        for this_num_bits, this_max in zip(length, gene_max):
            this_gene = this_ind[start:start + this_num_bits] or [0]
            base_int = int("".join(str(x) for x in this_gene), 2)
            max_value = 2 ** len(this_gene) - 1  # zero based, max number possible from bit string, 0 based (has the -1)

            # maximum possible number of indexes that must be skipped to get max values
            # to fit into fullMax possible values.
            max_num_dropped = max_value - this_max
            num_dropped = math.floor(max_num_dropped * (base_int / max_value))
            full_int_val = base_int - num_dropped

            this_phenotype.append(full_int_val)  # value here???

            start += this_num_bits

        phenotype.append(this_phenotype)

    return phenotype


def replace_tokens(tokens: dict, text: str, phenotype: dict, non_influential_tokens: list, max_depth: int):
    """ 
    Loops over tokens in a single token set, replaces any token stem in the control file with the assigned token.
    Called once for each token group, until no more token stems are found. 
    Also determines whether a token set is "influential" (i.e., the choice of token set results in a change
    in the resulting control file).

    :param tokens: A dictionary of token sets
    :type tokens: dict
    :param text: Current control file text
    :type text: string
    :param phenotype: Integer array specifying which token set in the token group to substitute into the text
    :type phenotype: dict
    :param non_influential_tokens: Boolean list of whether the token group appears in the control file
    :type non_influential_tokens: list
    :param max_depth: Maximum depth of nested tokens
    :type max_depth: int
    :return: Modified control file text
    :rtype: string
    
    """

    any_found = True  # keep looping, looking for nested tokens

    for _ in range(max_depth):  # levels of nesting

        any_found, text = _replace_tokens(tokens, text, phenotype, non_influential_tokens)

        if not any_found:
            break

    if any_found:
        raise DarwinError(f"There are more than {max_depth} levels of nested tokens.")

    return text


def _replace_tokens(tokens: dict, text: str, phenotype: dict, non_influential_tokens: list):
    any_found = False
    current_token_set = 0

    for thisKey in tokens.keys():
        token_set = tokens.get(thisKey)[phenotype[thisKey]]
        token_num = 1

        for this_token in token_set:
            # if replacement has THETA/OMEGA and sigma in it, but it doesn't end up getting inserted, increment

            full_key = "{" + thisKey + "[" + str(token_num) + "]" + "}"

            if full_key in text:
                text = text.replace(full_key, this_token)
                any_found = True

                if non_influential_tokens:
                    non_influential_tokens[current_token_set] = False  # is influential

            token_num = token_num + 1

        current_token_set += 1

    return any_found, text


def get_token_parts(token):
    match = re.search(r"{(.+?)\[(\d+)]", token)

    if match is None:
        return None, None

    return match.group(1), int(match.group(2))


def remove_file(file_path: str):
    if os.path.isfile(file_path):
        os.unlink(file_path)


def remove_dir(file_path: str):
    if os.path.isdir(file_path):
        shutil.rmtree(file_path)


def get_n_best_index(n, arr):
    return heapq.nsmallest(n, range(len(arr)), arr.__getitem__)


def get_n_worst_index(n, arr):
    return heapq.nlargest(n, range(len(arr)), arr.__getitem__)


class AtomicFlag:
    def __init__(self, initial):
        self._value = initial
        self._lock = threading.Lock()

    def set(self, val):
        with self._lock:
            old_val = self._value
            self._value = val
            return old_val

    def get(self):
        with self._lock:
            return self._value


def terminate_process(pid: int):
    """
    Kills the specified process and its subprocesses.

    :param pid: PID
    :type pid: int
    """
    proc = psutil.Process(pid)

    terminate_processes(proc.children(True) + [proc])


def terminate_processes(processes: list):
    log.message(f'Terminating {len(processes)} processes...')

    for p in processes:
        try:
            p.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    gone, alive = psutil.wait_procs(processes, timeout=4)

    if alive:
        log.warn(f'{len(alive)} are still alive')

        for p in alive:
            try:
                p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass


class PipelineStep:
    class _Sentinel:
        pass

    _sentinel = _Sentinel()

    def __init__(self, fn, size=1, name='PipelineStep'):
        self.name = name
        self.next = None
        self._size = size
        self._fn = fn
        self._workers = []
        self._input = mp.Queue()
        self._output = mp.Queue()

    def running(self) -> bool:
        return bool(self._workers)

    def run(self):
        if self._workers:
            raise DarwinError(f"{self.name} is already running")

        # for current purposes is good enough, for computation intensive problem need to utilize multiprocessing.Process
        self._workers = [threading.Thread(target=self._thread_fun, args=(i,)) for i in range(self._size)]

        for w in self._workers:
            w.start()

    def join(self):
        if not self._workers:
            raise DarwinError(f"{self.name} is not running")

        for w in self._workers:
            w.join()

        self._workers = []

        if self.next:
            self.next.close()
            self.next.join()
        else:
            self._output.put(self._sentinel)

    def _set_input(self, in_q):
        self._input = in_q

    def put(self, items: list):
        for item in items:
            self._input.put(item)

    def close(self):
        self.put([self._sentinel] * self._size)

    def link(self, step: 'PipelineStep'):
        self.next = step

        step._set_input(self._output)
        step.run()

    def _thread_fun(self, i):
        while True:
            val = self._input.get()

            if isinstance(val, self._Sentinel):
                break

            try:
                res = self._fn(val)

                if self._output:
                    self._output.put(res)
            except:
                traceback.print_exc()

    def results(self):
        while True:
            val = self._output.get()

            if isinstance(val, self._Sentinel):
                break

            yield val


class TankStep(PipelineStep):
    class _TimerEvent:
        pass

    _event = _TimerEvent()

    def __init__(self, fn, pump_interval, pipe_size=1, name='TankStep'):
        super(TankStep, self).__init__(fn, pipe_size, name)
        self.pump_interval = pump_interval
        self.timer = None
        self._reset_timer(self._set_ready)

    def _set_ready(self):
        self._input.put(self._event)

    def _reset_timer(self, fun):
        self.timer = threading.Timer(self.pump_interval, fun)
        self.timer.start()

    def _pump(self, tank: list):
        rest = tank

        try:
            pumped, rest = self._fn(tank)

            if self._output:
                for val in pumped:
                    self._output.put(val)
        except:
            traceback.print_exc()

        return rest

    def _thread_fun(self, i):
        tank = []

        while True:
            val = self._input.get()

            if isinstance(val, self._Sentinel):
                break

            if isinstance(val, self._TimerEvent):
                self.timer.cancel()

                tank = self._pump(tank)

                self._reset_timer(self._set_ready)

                continue

            tank.append(val)

        self.timer.cancel()

        ready_to_poll = threading.Event()
        ready_to_poll.set()

        def set_ready():
            ready_to_poll.set()

        while tank:
            ready_to_poll.wait()
            self.timer.cancel()

            tank = self._pump(tank)

            ready_to_poll.clear()
            self._reset_timer(set_ready)

        self.timer.cancel()


class Pipeline:
    def __init__(self, first: PipelineStep):
        self.first = self.last = first

    def link(self, step: PipelineStep):
        self.last.link(step)

        self.last = step

        return self

    def put(self, items: list):
        self.first.put(items)

    def start(self):
        if not self.first or self.first.running():
            return

        self.first.close()
        self.first.run()

    def join(self):
        self.first.join()
        self.first = None

    def results(self):
        self.start()

        if self.first and self.first.running():
            self.join()

        return self.last.results()


def apply_aliases(option, aliases: dict):
    if not option:
        return option

    res = str(option)

    for alias, text in aliases.items():
        res = res.replace('{' + alias + '}', str(text))

    return res


def format_time(t: float, fuzzy_eta: bool = False) -> str:
    if not fuzzy_eta:
        if t > 10:
            t = int(t)
            return f"{t} min."

        return f"{t:.1f} min."

    h = int(t / 60)
    d = int(h / 24)

    if d > 6:
        res = f"{d} d."
    elif d > 2:
        h %= 24
        res = f"{d} d. {h:02d} h."
    elif h > 23:
        res = f"{h} h."
    elif h > 1:
        m = int(t) % 60
        res = f"{h} h. {m:02d} min."
    else:
        if t > 10:
            t = int(t)
            return f"{t} min."

        return f"{t:.1f} min."

    return res
