import os
import time


def post_process(run_dir: str):
    with open(os.path.join(run_dir, "python_output"), "a") as f:
        f.write(run_dir)

    time.sleep(1)

    return([4.0, 'test test test'])