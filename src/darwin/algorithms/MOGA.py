import os
import shutil
import logging
import numpy as np
import warnings

from darwin import Population
from darwin.Log import log
from darwin.options import options
from darwin.ModelCode import ModelCode
from darwin.Template import Template
from darwin.ModelRun import ModelRun
from darwin.Population import Population
from darwin.ModelCache import get_model_cache

from pymoo.algorithms.moo.nsga2 import NSGA2
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


def _get_front_runs(res_xx: list, model_cache) -> list:
    runs = []

    for res_x in res_xx:
        cur_x = [int(x) for x in res_x.astype(int)]
        run = model_cache.find_model_run(genotype=str(cur_x))

        if run is None:
            log.warn(f"Missing a front model: {cur_x}")
            continue

        runs.append(run)

    return runs


def run_moga(model_template: Template):
    n_var = sum(model_template.gene_length)
    pop_size = options.population_size  # connect with options file
    n_gens = options.num_generations  # connect with options file

    model_cache = get_model_cache()

    problem = MogaProblem(n_var=n_var)

    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=BinaryRandomSampling(),
        crossover=TwoPointCrossover(prob=options['MOGA']['crossover_rate']),
        mutation=BitflipMutation(prob=options['MOGA']['mutation_rate']),
        eliminate_duplicates=True
    )

    algorithm.setup(problem, termination=('n_gen', n_gens), seed=options.random_seed, verbose=False)

    n_gen = 0

    while algorithm.has_next():
        n_gen += 1

        # ask the algorithm for the next solution to be evaluated
        pop = algorithm.ask()

        # construct genome
        pop_full_bits = [[int(this_bit) for this_bit in this_ind.X] for this_ind in pop]

        population = Population.from_codes(model_template, algorithm.n_gen, pop_full_bits, ModelCode.from_full_binary)

        population.run()

        for run, moo_ind in zip(population.runs, pop):
            problem = MogaProblem(n_var=n_var, run=run)

            algorithm.evaluator.eval(problem, moo_ind)

        algorithm.tell(infills=pop)

        non_dominated_folder = os.path.join(options.working_dir, 'non_dominated_models', str(n_gen))

        os.mkdir(non_dominated_folder)

        res = algorithm.result()

        log.message('Current Non Dominated models:')

        for run in _get_front_runs(res.X, model_cache):
            log.message(f"Generation {n_gen} Pareto Front: Model {run.control_file_name}, " +
                        f"OFV = {run.result.ofv:.4f}, NEP = {_get_n_params(run)}")

            if not os.path.isdir(run.run_dir):
                continue

            shutil.copytree(run.run_dir, os.path.join(non_dominated_folder, run.file_stem), dirs_exist_ok=True)

    res = algorithm.result()

    log.message(f" MOGA best genome = {res.X.astype(int)},\n"
                f" OFV and # of parameters = {res.F}")

    for run in _get_front_runs(res.X, model_cache):
        run.run_dir = options.output_dir
        run.make_control_file(cleanup=False)
        run.output_results()
