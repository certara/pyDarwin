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

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.result import Result
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

    for res_x in res.X:
        cur_x = [int(x) for x in res_x.astype(int)]
        mc = ModelCode.from_full_binary(cur_x, maxes, lengths)
        run = model_cache.find_model_run(genotype=str(mc.IntCode))

        if run is None:
            log.warn(f"Missing a front model: {cur_x}")
            continue

        runs.append(run)

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


def run_moga(template: Template):
    n_var = sum(template.gene_length)
    pop_size = options.population_size
    n_gens = options.num_generations

    model_cache = get_model_cache()

    problem = MogaProblem(n_var=n_var)

    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=BinaryRandomSampling(),
        crossover=TwoPointCrossover(prob=options.MOGA['crossover_rate']),
        mutation=BitflipMutation(prob=options.MOGA['mutation_rate']),
        eliminate_duplicates=True
    )

    algorithm.setup(problem, termination=('n_gen', n_gens), seed=options.random_seed, verbose=False)

    n_gen = 0

    front = []
    res = Result()

    while algorithm.has_next() and keep_going():
        n_gen += 1

        # ask the algorithm for the next solution to be evaluated
        pop = algorithm.ask()

        # construct genome
        pop_full_bits = [[int(this_bit) for this_bit in this_ind.X] for this_ind in pop]

        population = Population.from_codes(template, algorithm.n_gen, pop_full_bits, ModelCode.from_full_binary)

        population.run()

        if not keep_going():
            break

        for run, moo_ind in zip(population.runs, pop):
            problem = MogaProblem(n_var=n_var, run=run)

            algorithm.evaluator.eval(problem, moo_ind)

        algorithm.tell(infills=pop)

        res = algorithm.result()
        front = _get_front_runs(res, template, model_cache)

        log.message('Current Non Dominated models:')

        non_dominated_folder = os.path.join(options.non_dominated_models_dir, str(n_gen))
        os.mkdir(non_dominated_folder)

        for run in front:
            log.message(f"Generation {n_gen} Pareto Front: Model {run.control_file_name}, " +
                        f"OFV = {run.result.ofv:.4f}, NEP = {_get_n_params(run)}")

            if not os.path.isdir(run.run_dir):
                log.warn('is not copied')
                continue

            shutil.copytree(run.run_dir, os.path.join(non_dominated_folder, run.file_stem), dirs_exist_ok=True)

    if not keep_going():
        return

    log.message(f" MOGA best genome = {res.X.astype(int)},\n"
                f" OFV and # of parameters = {res.F}")

    for run in front:
        run.run_dir = options.output_dir
        run.make_control_file(cleanup=False)
        run.output_results()
