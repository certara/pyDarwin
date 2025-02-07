import os
import shutil
import logging
import numpy as np
import warnings

from darwin import Population
from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import keep_going
from darwin.ModelCode import ModelCode
from darwin.Template import Template
from darwin.ModelRun import ModelRun
from darwin.Population import Population
from darwin.ModelCache import get_model_cache
from darwin.ModelRunManager import rerun_models
from darwin.algorithms.run_downhill import do_downhill_step

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.result import Result
from pymoo.core.population import pop_from_array_or_individual
from pymoo.operators.crossover.pntx import TwoPointCrossover
from pymoo.operators.mutation.bitflip import BitflipMutation
from pymoo.operators.sampling.rnd import BinaryRandomSampling
from pymoo.core.problem import ElementwiseProblem

warnings.filterwarnings('error', category=DeprecationWarning)
logger = logging.getLogger(__name__)


def _get_n_params(run: ModelRun) -> int:
    model = run.model

    return model.estimated_omega_num + model.estimated_theta_num + model.estimated_sigma_num


class MogaProblem(ElementwiseProblem):
    def __init__(self, n_var, run: ModelRun = None):
        super().__init__(n_var=n_var,  # number of bits
                         n_obj=2,
                         n_ieq_constr=0,
                         xl=np.zeros(n_var, dtype=int),
                         xu=np.ones(n_var, dtype=int),
                         # need this to send population and template to evaluate
                         requires_kwargs=True
                         )
        self.run = run

    def _evaluate(self, x, out, *args, **kwargs):
        f1 = self.run.result.ofv
        f2 = 999999 if f1 >= options.crash_value else _get_n_params(self.run)

        out["F"] = [f1, f2]


def _get_front_runs(res: Result, template: Template, model_cache) -> list:
    runs = []

    maxes = template.gene_max
    lengths = template.gene_length

    controls = {}

    for res_x in res.X:
        cur_x = [int(x) for x in res_x.astype(int)]
        mc = ModelCode.from_full_binary(cur_x, maxes, lengths)
        run = model_cache.find_model_run(genotype=str(mc.IntCode))

        if run.control_file_name in controls:
            controls[run.control_file_name] += 1
            continue

        controls[run.control_file_name] = 1

        if run is None:
            log.warn(f"Missing a front model: {cur_x}")
            continue

        runs.append(run)

    for run in runs:
        x = controls[run.control_file_name]
        x = f"(x{x})" if x > 1 else ''
        log.message(f"Model {run.control_file_name}, OFV = {run.result.ofv:.4f}, NEP = {_get_n_params(run)} {x}")

    reruns = [run for run in runs if not os.path.isdir(run.run_dir)]

    if reruns:
        if options.rerun_front_models:
            log.message('Re-running front models...')

            rerun_models(reruns)
        else:
            for run in reruns:
                run.make_control_file()
                run.output_results()

    return runs


def _front_cast(runs: list) -> str:
    lines = [f"OFV = {run.result.ofv:.4f}, NEP = {_get_n_params(run)}" for run in runs]
    return '\n'.join(sorted(lines))


class _MOGARunner:
    def __init__(self, template: Template, pop_size: int):
        self.n_var = sum(template.gene_length)
        self.template = template
        self.model_cache = get_model_cache()
        self.pop = None

        problem = MogaProblem(n_var=self.n_var)

        self.algorithm = NSGA2(
            pop_size=pop_size,
            sampling=BinaryRandomSampling(),
            crossover=TwoPointCrossover(prob=options.MOGA['crossover_rate']),
            mutation=BitflipMutation(prob=options.MOGA['mutation_rate']),
            eliminate_duplicates=True
        )

        self.algorithm.setup(problem, seed=options.random_seed, verbose=False)

    def has_next(self) -> bool:
        return self.algorithm.has_next()

    def ask_population(self, n_gen: int) -> Population:
        self.pop = self.algorithm.ask()

        pop_full_bits = [[int(this_bit) for this_bit in this_ind.X] for this_ind in self.pop]

        return Population.from_codes(self.template, n_gen, pop_full_bits, ModelCode.from_full_binary)

    def tell_runs(self, runs: list) -> list:
        pop = self.pop

        if pop is None:
            infills = np.array([np.array(run.model.model_code.FullBinCode, dtype=bool) for run in runs])
            self.pop = pop = pop_from_array_or_individual(infills)

        for run, moo_ind in zip(runs, pop):
            problem = MogaProblem(n_var=self.n_var, run=run)

            self.algorithm.evaluator.eval(problem, moo_ind)

        self.algorithm.tell(infills=pop)

        res = self.algorithm.result()

        self.pop = None

        log.message('Current Non Dominated models:')

        return _get_front_runs(res, self.template, self.model_cache)

    def dump_res(self):
        res = self.algorithm.result()

        log.message(f" MOGA best genome =\n{res.X.astype(int)},\n"
                    f" OFV and # of parameters =\n{res.F}")


def _copy_front_files(front: list, non_dominated_folder: str, n_gen: int):
    os.mkdir(non_dominated_folder)

    for run in front:
        if not os.path.isdir(run.run_dir):
            log.warn('is not copied')
            continue

        shutil.copytree(run.run_dir, os.path.join(non_dominated_folder, run.file_stem), dirs_exist_ok=True)


def run_moga(template: Template):
    n_gens = options.num_generations
    downhill_period = options.downhill_period

    n_gen = 0

    front = []

    runner = _MOGARunner(template, options.population_size)

    while keep_going() and n_gen < n_gens:
        if not runner.has_next():
            log.warn(f"MOGA finished before reaching generation {n_gens}")
            break

        n_gen += 1

        population = runner.ask_population(n_gen)

        population.run()

        if not keep_going():
            break

        front = runner.tell_runs(population.runs)

        non_dominated_folder = os.path.join(options.non_dominated_models_dir, str(n_gen))

        _copy_front_files(front, non_dominated_folder, n_gen)

        if downhill_period > 0 and n_gen % downhill_period == 0:
            log.message(f"Starting downhill generation {n_gen}")

            for this_step in range(1, 100):  # up to 99 steps
                if not keep_going():
                    break

                before = _front_cast(front)

                downhill_runs = do_downhill_step(template, front, population.name, this_step)

                front = runner.tell_runs(downhill_runs)

                after = _front_cast(front)

                if before == after:
                    break

            shutil.rmtree(non_dominated_folder)

            _copy_front_files(front, non_dominated_folder, n_gen)

    if not keep_going():
        return

    runner.dump_res()

    for run in front:
        run.run_dir = options.output_dir
        run.make_control_file(cleanup=False)
        run.output_results()
