import os
import re

import subprocess

from darwin.Log import log
from darwin.options import options

import darwin.utils as utils

from .ModelRun import ModelRun, run_to_json, json_to_run
from .GridManager import GridManager, register_grid_man


def _get_job_name(run: ModelRun) -> str:
    return f"{options.project_stem}-{run.file_stem}"


class GridJob:
    def __init__(self, run: ModelRun, runs_dir, results_dir):
        json_file = run.file_stem + '.json'

        self.run = run
        self.name = _get_job_name(run)
        self.input_path = os.path.join(runs_dir, json_file)
        self.output_path = os.path.join(results_dir, json_file)
        self.id = ''


class GenericGridManager(GridManager):
    def __init__(self):
        runs_dir = os.path.join(options.temp_dir, 'runs')
        results_dir = os.path.join(options.output_dir, 'run_results')

        utils.remove_dir(runs_dir)
        os.makedirs(runs_dir)

        utils.remove_dir(results_dir)
        os.makedirs(results_dir)

        self.jobs = {}
        self.runs_dir = runs_dir
        self.results_dir = results_dir

        opts = options.get('grid_manager', {})

        self.submit_command = [options.apply_aliases(arg) for arg in opts['submit_command'].split(' ')]
        self.poll_command = [options.apply_aliases(arg) for arg in opts['poll_command'].split(' ')]
        self.delete_command = [options.apply_aliases(arg) for arg in opts.get('delete_command', '').split(' ')]
        self.submit_job_id_re = re.compile(opts['submit_job_id_re'])
        self.poll_job_id_re = re.compile(opts['poll_job_id_re'])
        self.python_path = opts['python_path']

    def add_model_run(self, run: ModelRun):
        job = GridJob(run, self.runs_dir, self.results_dir)

        run_to_json(run, job.input_path)

        if self.submit(job):
            self.jobs[job.id] = job

    def submit(self, job: GridJob) -> bool:
        aliases = {
            'results_dir': self.results_dir,
            'job_name': job.name,
            'run_name': job.run.file_stem,
            'run_number': job.run.model_num,
            'run_dir': job.run.run_dir,
            'generation': job.run.generation,
        }

        command = [utils.apply_aliases(arg, aliases) for arg in self.submit_command]

        command += [self.python_path, '-m', 'darwin.run_model', job.input_path, job.output_path, options.options_file]

        out = _run_process(command, f'Failed to submit a job: {job.name}')

        if out is None:
            return False

        job.id = self._parse_submit_output(out)

        if not job.id:
            log.error(f'Failed to parse job id: {out}')
            return False

        return True

    def poll_model_runs(self, runs: list):
        if not runs:
            return [], []

        out = _run_process(self._alias_command_with_ids(self.poll_command), 'Failed to poll jobs') or ''

        remaining = {_get_job_name(r): r for r in runs}
        finished = []

        for line in out.split('\\n'):
            job_id = self._parse_poll_line(line)

            if not job_id:
                continue

            # if job was submitter with this GridMan
            job = self.jobs.get(job_id)

            # and it was requested by this poll
            if job and job.name in remaining:
                del self.jobs[job_id]
                del remaining[job.name]
                finished.append(json_to_run(job.output_path))

        return finished, list(remaining.values())

    def remove_all(self) -> bool:
        log.message('Removing all submitted jobs...')

        if not self.jobs:
            log.message('None left')
            return True

        if not self.delete_command:
            log.message('Delete command is not set')
            return True

        out = _run_process(self._alias_command_with_ids(self.delete_command), 'Failed to remove jobs')

        if out is not None:
            log.message('Done')

            return True

        return False

    def _parse_submit_output(self, output: str) -> str:
        return _parse_id(self.submit_job_id_re, output)

    def _parse_poll_line(self, line) -> str:
        return _parse_id(self.poll_job_id_re, line)

    def _alias_command_with_ids(self, command) -> list:
        complete_command = []

        for arg in command:
            if arg == '{job_ids}':
                complete_command.extend(list(self.jobs.keys()))
            else:
                complete_command.append(arg)

        return complete_command


def _parse_id(regex, output) -> str:
    m = regex.search(output)

    if not m:
        return ''

    return m.group(1)


def _run_process(command: list, error_message: str):
    process = None

    try:
        process = subprocess.run(command, capture_output=True)
    except:
        pass

    if process is None or process.returncode != 0:
        log.error(error_message)

        if process:
            log.error(str(process.stderr))

        return None

    return str(process.stdout)


def register():
    register_grid_man('darwin.GenericGridManager', GenericGridManager)
