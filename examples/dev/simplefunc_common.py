import os
import time


def post_process():
    cwd = os.getcwd()

    with open("python_output", "a") as f:  # just to check we're in the right directory
        f.write(cwd)

    time.sleep(1)

    return([4.0, 'test test test'])