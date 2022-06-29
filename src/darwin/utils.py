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


def _get_token_parts(token):
    match = re.search(r"{.+\[", token).span()
    stem = token[match[0] + 1:match[1] - 1]
    rest_part = token[match[1]:]
    match = re.search("[0-9]+]", rest_part).span()

    try:
        index = int(rest_part[match[0]:match[1] - 1])  # should be integer
    except:
        return "none integer found in " + stem + ", " + token
        # json.load seems to return its own error and exit immediately
        # this try/except doesn't do anything

    return stem, index


def _expand_tokens(tokens: dict, text_block: list, phenotype: dict) -> list:
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

    key, index = _get_token_parts(text_line)
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


def remove_comments(code: str) -> str:
    """ remove any comments (";") from nonmem code

    :param code: input code
    :type code: str
    :return: code with comments removed
    :rtype: str
    """
    new_code = ""

    if type(code) != list:
        lines = code.splitlines()
    else:
        lines = code[0]

    for line in lines:
        if line.find(";") > -1:
            line = line[:line.find(";")]
        new_code += line.strip() + '\n'

    return new_code


def match_thetas(control: str, tokens: dict, var_theta_block: list, phenotype: dict, last_fixed_theta: int) -> str:
    """
    Parses current control file text, looking for THETA(*) and calculates the appropriate index for that THETA
    (starting with the last_fixed_theta - the largest value used for THETA() in the fixed code)

    :param control: control file text
    :type control: str

    :param tokens: token groups
    :type tokens: dict

    :param var_theta_block: variable theta block
    :type var_theta_block: str

    :param phenotype: phenotype for model
    :type phenotype: dict

    :param last_fixed_theta: highest value used for THETA in fixed code. Fixed values for THETA must start with 1
        and be continuous until the last fixed THETA
    :type last_fixed_theta: int

    :return: new control file
    :rtype: str
    """
    # EXAMPLED_THETA_BLOCK IS THE FINAL $THETA BLOCK FOR THIS MODEL, WITH THE TOKEN TEXT SUBSTITUTED IN
    # EXPANDED TO ONE LINE PER THETA
    # token ({'ADVAN[3]}) will be present on if there is a THETA(???) in it
    # one instance of token for each theta present, so they can be counted
    # may be empty list ([]), but each element must contain '{??[N]}
    expanded_theta_block = _expand_tokens(tokens, var_theta_block, phenotype)
    # then look at each  token, get THETA(alpha) from non-THETA block tokens
    theta_indices = _get_theta_matches(expanded_theta_block, tokens, phenotype)

    # add last fixed theta value to all
    for k, v in theta_indices.items():
        # add last fixed theta value to all
        # and put into control file
        control = control.replace(f"THETA({k})", "THETA(" + str(v + last_fixed_theta) + ")")

    return control


def _get_theta_matches(expanded_theta_block: list, tokens: dict, full_phenotype: dict) -> dict:
    # shouldn't be any THETA(alpha) in expandedTHETABlock, should  be trimmed out
    # get stem and index, look in other tokens in this token set (phenotype)
    # tokens can be ignored here, they are already expanded, just list the alpha indices of each THETA(alpha) in order
    # and match the row in the expandedTHETAblock
    # note that commonly a stem will have more than one THETA, e.g, THETA(ADVANA)
    # and THETA(ADVANB) for ADVAN4, K23 and K32
    # however, an alpha index MAY NOT appear more than once, e.g.,
    # e.g. TVCL = THETA()**THETA(CL~WT)
    #      TVQ  = THETA()**THETA(CL~WT)
    # is NOT PERMITTED, need to do:
    # CLPWR = THETA(CL~WT)
    # TVCL = THETA()**CLPWR
    # TVQ  = THETA()**CLPWR

    theta_matches = {}
    cur_theta = 1
    # keep track of added/check token, don't want to repeat them, otherwise sequence of THETA indices will be wrong
    all_checked_tokens = []

    for theta_row in expanded_theta_block:
        # get all THETA(alpha) indices in other tokens in this token set
        stem, index = _get_token_parts(theta_row)
        phenotype = full_phenotype[stem]
        full_token = ""  # assemble full token, except the one in $THETA, to search for THETA(alpha)

        if not (any(stem in s for s in all_checked_tokens)):  # add if not already in list
            for token in range(len(tokens[stem][phenotype])):
                if token != index - 1:
                    # only include text is it ends up in the model
                    new_string = tokens[stem][phenotype][token].replace(" ", "")
                    new_string = remove_comments(new_string).strip()
                    full_token = full_token + new_string + "\n"

            # get THETA(alphas)
            full_indices = re.findall(r"THETA\(.+\)", full_token)
            # get unique THETA(INDEX)
            full_indices = list(dict.fromkeys(full_indices))

            for line in full_indices:
                # have to get only part between THETA( and )
                start_theta = line.find("THETA(") + 6
                last_parens = line.find(")", (start_theta - 2))
                theta_index = line[start_theta:last_parens]

                theta_matches[theta_index] = cur_theta

                cur_theta += 1

            all_checked_tokens.append(stem)

        # number should match #of rows with stem in expandedTHETABlock

    return theta_matches


def _get_rand_var_matches(expanded_block, tokens, full_phenotype, which_rand):
    rand_matches = {}
    cur_rand = 1

    # keep track of added/check token, don't want to repeat them, otherwise sequence of THETA indices will be wrong
    all_checked_tokens = []

    for rand_row in expanded_block:
        # get all THETA(alpha) indices in other tokens in this token set
        stem, index = _get_token_parts(rand_row)
        phenotype = full_phenotype[stem]
        full_token = ""  # assemble full token, except the one in $THETA, to search for THETA(alpha)

        if not (any(stem in s for s in all_checked_tokens)):  # add if not already in list
            for thisToken in range(len(tokens[stem][phenotype])):
                if thisToken != index - 1:
                    new_string = tokens[stem][phenotype][thisToken]  # can't always replace spaces, sometimes needed
                    new_string = remove_comments(new_string).strip()
                    full_token = full_token + new_string + "\n"

                    # replace THETA with XXXXXX, so it doesn't conflict with ETA
                    if which_rand == "ETA":
                        full_token = full_token.replace("THETA", "XXXXX")

            # get ETA/EPS(alphas)
            full_indices = re.findall(which_rand + r"\(.+?\)", full_token)  # non-greedy with ?

            for i in range(len(full_indices)):
                start = full_indices[i].find((which_rand + "(")) + 4
                last_parens = full_indices[i].find(")", (start - 2))
                rand_index = full_indices[i][start:last_parens]
                rand_matches[rand_index] = cur_rand
                cur_rand += 1
            all_checked_tokens.append(stem)

        # number should match #of rows with stem in expandedTHETABlock

    return rand_matches


def match_rands(control: str, tokens: dict, var_rand_block: list, phenotype: dict, last_fixed_rand, stem: str) -> str:

    expanded_rand_block = _expand_tokens(tokens, var_rand_block, phenotype)

    # then look at each  token, get THETA(alpha) from non-THETA block tokens
    rand_indices = _get_rand_var_matches(expanded_rand_block, tokens, phenotype, stem)

    # add last fixed theta value to all
    for i, (k, v) in enumerate(rand_indices.items()):
        # add last fixed random parm value to all
        # and put into control file
        control = control.replace(stem + "(" + k + ")", stem + "(" + str(v + last_fixed_rand) + ")")

    return control


def remove_file(file_path: str):
    if os.path.isfile(file_path) or os.path.islink(file_path):
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

    for p in proc.children(True):
        p.terminate()

    proc.terminate()


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
        self._output = None

    def run(self):
        if self._workers:
            raise RuntimeError(f"{self.name} is already running")

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

    def _set_input(self, in_q):
        self._input = in_q

    def put(self, items: list):
        for item in items:
            self._input.put(item)

    def close(self):
        self.put([self._sentinel] * self._size)

    def link(self, step: 'PipelineStep'):
        self.next = step
        self._output = mp.Queue()

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


class TankStep(PipelineStep):
    def __init__(self, fn, tank_size, pipe_size=1, name='TankStep'):
        super(TankStep, self).__init__(fn, pipe_size, name)
        self._tank_size = tank_size

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

            tank.append(val)

            if len(tank) < self._tank_size:
                continue

            tank = self._pump(tank)

        while tank:
            tank = self._pump(tank)


class Pipeline:
    def __init__(self, first: PipelineStep):
        self.first = first

    def link(self, step: PipelineStep):
        s = self.first

        while s.next is not None:
            s = s.next

        s.link(step)

        return self

    def put(self, items: list):
        self.first.put(items)

    def start(self):
        self.first.close()
        self.first.run()

    def join(self):
        self.first.join()
