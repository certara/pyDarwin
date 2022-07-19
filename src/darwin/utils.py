import os
import sys
import re
import shutil
import heapq
import threading
import multiprocessing as mp
import traceback
import psutil

from darwin.Log import log


def replace_tokens(tokens: dict, text: str, phenotype: dict, non_influential_tokens: list):
    """ 
    Loops over tokens in a single token set, replace any token stem in the control file with the assigned token. 
    Called once for each token group, until no more token stems are found. 
    Also determines whether a token set is "influential", that is does the choice of token set results in a change 
    in the resulting control file. A small penalty, is specified in the options file, e.g.,
    "non_influential_tokens_penalty": 0.00001,

    :param tokens: a dictionary of token sets

    :type tokens: dict

    :param text: current control file text

    :type text: string

    :param phenotype: integer array specifying which token set in the token group to substitute into the text

    :type phenotype: dict

    :param non_influential_tokens: Boolean list of whether the token group appears in the control file

    :type non_influential_tokens: list

    :return: boolean - were any tokens substituted (and we need to loop over again), current control file text

    :rtype: tuple
    
    """

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
                non_influential_tokens[current_token_set] = False  # is influential

            token_num = token_num + 1

        current_token_set += 1

    return any_found, text


def get_token_parts(token):
    match = re.search(r"{(.+?)\[(\d+)]", token)

    if match is None:
        return None, None

    return match.group(1), int(match.group(2))


def expand_tokens(tokens: dict, text_block: list, phenotype: dict) -> list:
    expanded_text_block = []

    for text_line in text_block:
        new_lines = _expand_line(tokens, text_line, phenotype, 0)

        expanded_text_block.extend(new_lines)

    return expanded_text_block


def _expand_line(tokens: dict, text_line: str, phenotype: dict, loop_num: int) -> list:
    # text_line should be simple string, not list
    # should return simple list (not list of lists)

    if loop_num > 4:
        log.error(f"Greater than 4 recursive calls to _expand_line with {text_line}, possibly circular nested tokens")
        sys.exit()

    new_expanded_text_block = []

    key, index = get_token_parts(text_line)

    if not key:
        return [text_line]

    token = tokens.get(key)[phenotype[key]][index - 1]  # problem here???
    token = remove_comments(token).splitlines()

    for token_line in token:  # for each line in the token
        if not token_line:
            continue

        # if there is no token ("{XXXX}"), this is terminal, just append
        if re.search("{.+}", token_line) is None:
            new_expanded_text_block.append(text_line)
        else:  # expand that line recursively
            new_lines = _expand_line(tokens, token_line, phenotype, loop_num + 1)

            new_expanded_text_block.extend(new_lines)

    return new_expanded_text_block


def remove_comments(code: str, comment_mark=';') -> str:
    """ remove any comments (";") from nonmem code

    :param code: input code
    :type code: str
    :param comment_mark:
    :return: code with comments removed
    :rtype: str
    """

    if type(code) != list:
        lines = code.splitlines()
    else:
        lines = code

    lines = [(line[:line.find(comment_mark)] if line.find(comment_mark) > -1 else line).strip() for line in lines]

    return '\n'.join(lines)


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
            raise RuntimeError(f"{self.name} is already running")

        # for current purposes is good enough, for computation intensive problem need to utilize multiprocessing.Process
        self._workers = [threading.Thread(target=self._thread_fun, args=(i,)) for i in range(self._size)]

        for w in self._workers:
            w.start()

    def join(self):
        if not self._workers:
            raise RuntimeError(f"{self.name} is not running")

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
