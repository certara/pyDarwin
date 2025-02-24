import os
import shutil
import logging
import numpy as np
import warnings

from darwin import Population
from darwin.Log import log
from darwin.options import options
import darwin.utils as utils
from darwin.ExecutionManager import keep_going
from darwin.ModelCode import ModelCode
from darwin.Template import Template
from darwin.ModelRun import ModelRun
from darwin.Population import Population
from darwin.ModelCache import get_model_cache
from darwin.ModelRunManager import rerun_models
from darwin.algorithms.run_downhill import do_moga_downhill_step
from darwin.ModelEngineAdapter import get_model_phenotype

from .effect_limit import WeightedSampler

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.core.result import Result
from pymoo.core.population import pop_from_array_or_individual
from pymoo.operators.crossover.pntx import SinglePointCrossover, TwoPointCrossover
from pymoo.operators.mutation.bitflip import BitflipMutation
from pymoo.operators.sampling.rnd import BinaryRandomSampling
from pymoo.core.sampling import Sampling
from pymoo.core.problem import ElementwiseProblem
from pymoo.util.ref_dirs import get_reference_directions

warnings.filterwarnings('error', category=DeprecationWarning)
logger = logging.getLogger(__name__)


def _get_n_params(run: ModelRun) -> int:
    model = run.model

    return model.estimated_omega_num + model.estimated_theta_num + model.estimated_sigma_num


class MogaProblem(ElementwiseProblem):
    n_var = 0
    n_obj = 2
    n_constr = 0

    def __init__(self, run: ModelRun = None):
        super(MogaProblem, self).__init__(
            n_var=self.n_var,  # number of bits
            n_obj=self.n_obj,
            n_constr=self.n_constr,
            xl=np.zeros(self.n_var, dtype=int),
            xu=np.ones(self.n_var, dtype=int),
            # need this to send population and template to evaluate
            requires_kwargs=True
        )

        self.run = run
        self.three_obj = self.n_obj == 3

    def _evaluate(self, x, out, *args, **kwargs):
        f1 = self.run.result.ofv
        f2 = 999999 if f1 >= options.crash_value else _get_n_params(self.run)

        out["F"] = [f1, f2]

        if self.three_obj:
            f3 = self.run.result.post_run_r_penalty

            out["F"].append(f3)

            g1 = f1 - 999999
            g2 = 0.1-f2
            g3 = f3 - 999999

            out["G"] = [g1, g2, g3]


def _get_front_runs(res: Result, template: Template, model_cache) -> list:
    runs = []

    maxes = template.gene_max
    lengths = template.gene_length

    controls = {}

    for res_x in res.X:
        cur_x = [int(x) for x in res_x.astype(int)]
        mc = ModelCode.from_full_binary(cur_x, maxes, lengths)
        run = model_cache.find_model_run(genotype=str(mc.IntCode)) \
            or model_cache.find_model_run(phenotype=get_model_phenotype(template, mc))

        if run is None:
            log.warn(f"Missing a front model: {cur_x}")
            continue

        if run.control_file_name in controls:
            controls[run.control_file_name] += 1
            continue

        controls[run.control_file_name] = 1

        runs.append(run)

    runs = sorted(runs, key=lambda r: r.file_stem)

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


def _front_str(runs: list) -> str:
    lines = [f"OFV = {run.result.ofv}, NEP = {_get_n_params(run)}" for run in runs]
    return '\n'.join(sorted(lines))


class WeightedRandomSampling(Sampling):
    def __init__(self, template: Template):
        super(WeightedRandomSampling, self).__init__()

        self.sampler = WeightedSampler(template)

    def _do(self, problem, n_samples, **kwargs):
        val = np.array([self.sampler.create_individual() for _ in range(n_samples)])
        return val.astype(bool)


class _MOGARunner:
    def __init__(self, template: Template, pop_size: int):
        self.template = template
        self.model_cache = get_model_cache()
        self.pop = None

        opts = options.MOGA

        n_obj = opts['objectives']

        if n_obj != 3:
            n_obj = 2

        MogaProblem.n_var = sum(template.gene_length)
        MogaProblem.n_obj = n_obj
        MogaProblem.n_constr = opts['constraints']
        problem = MogaProblem()

        kwargs = {
            'pop_size': pop_size,
            'sampling': WeightedRandomSampling(template) if options.use_effect_limit else BinaryRandomSampling(),
            'crossover': SinglePointCrossover(prob=opts['crossover_rate']) if opts['crossover'] == 'single'
            else TwoPointCrossover(prob=opts['crossover_rate']),
            'mutation': BitflipMutation(prob=opts['mutation_rate'], prob_var=opts['attribute_mutation_probability']),
            'eliminate_duplicates': True
        }

        if n_obj == 3:
            kwargs['ref_dirs'] = get_reference_directions('das-dennis', 3, n_partitions=opts['partitions'])
            self.algorithm = NSGA3(**kwargs)
        else:
            self.algorithm = NSGA2(**kwargs)

        self.algorithm.setup(problem, seed=options.random_seed, verbose=False)

    def has_next(self) -> bool:
        return self.algorithm.has_next()

    def ask_population(self, n_gen: int, n_gens: int) -> Population:
        """
        Ask a population from the algorithm
        It saves the moo population in self.pop for subsequent tell

        :param n_gen: current generation number
        :param n_gens: max generation number
        :return: Population
        """
        self.pop = self.algorithm.ask()

        pop_full_bits = [[int(this_bit) for this_bit in this_ind.X] for this_ind in self.pop]

        return Population.from_codes(self.template, n_gen, pop_full_bits, ModelCode.from_full_binary,
                                     max_iteration=n_gens)

    def tell_runs(self, runs: list) -> list:
        """
        Tells the runs to the algorithm
        It uses self.pop which is only saved by ask_population
        The downhill step doesn't perform the _ask_, so pop is created from the runs

        :param runs: list of ModelRuns
        :return: the front as a list of non-duplicated ModelRuns
        """

        pop = self.pop

        if pop is None:
            infills = np.array([np.array(run.model.model_code.FullBinCode, dtype=bool) for run in runs])
            self.pop = pop = pop_from_array_or_individual(infills)

        for run, moo_ind in zip(runs, pop):
            problem = MogaProblem(run)

            self.algorithm.evaluator.eval(problem, moo_ind)

        self.algorithm.tell(infills=pop)

        res = self.algorithm.result()

        self.pop = None

        log.message('Current Non Dominated models:')

        return _get_front_runs(res, self.template, self.model_cache)

    def run_moga_downhill(self, front: list, generation) -> tuple:
        after = _front_str(front)

        changed = False

        for this_step in range(1, 100):  # up to 99 steps
            if not keep_going():
                break

            before = after

            downhill_runs = do_moga_downhill_step(self.template, front, generation, this_step)

            if not keep_going():
                break

            if not downhill_runs:
                log.warn(f"Downhill step {generation}/{this_step} has nothing to add to the search, done with downhill")
                break

            front = self.tell_runs(downhill_runs)

            after = _front_str(front)

            if before == after:
                break

            changed = True

        if changed:
            non_dominated_folder = os.path.join(options.non_dominated_models_dir, str(generation))

            _copy_front_files(front, non_dominated_folder)

        return front, after

    def dump_res(self):
        res = self.algorithm.result()

        log.message(f" MOGA best genome =\n{res.X.astype(int)},\n"
                    f" OFV and # of parameters =\n{res.F}")


def _copy_front_files(front: list, non_dominated_folder: str):
    utils.remove_dir(non_dominated_folder)
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
    generations_no_change = 0
    after = ''
    front = []

    runner = _MOGARunner(template, options.population_size)

    while keep_going() and n_gen < n_gens:
        if not runner.has_next():
            log.warn(f"MOGA finished before reaching generation {n_gens}")
            break

        n_gen += 1

        population = runner.ask_population(n_gen, n_gens)

        population.run()

        if not keep_going():
            break

        before = after

        front = runner.tell_runs(population.runs)

        after = _front_str(front)

        non_dominated_folder = os.path.join(options.non_dominated_models_dir, str(n_gen))

        _copy_front_files(front, non_dominated_folder)

        if downhill_period > 0 and n_gen % downhill_period == 0:
            log.message(f"Starting downhill generation {n_gen}")

            front, after = runner.run_moga_downhill(front, n_gen)

        if before == after:
            generations_no_change += 1
            log.message(f"No change in non dominated models for {generations_no_change} generations")
        else:
            generations_no_change = 0

    if options.final_downhill_search and keep_going():
        log.message(f"Starting final downhill step")
        front, after = runner.run_moga_downhill(front, 'FN')

    if not keep_going():
        return

    runner.dump_res()

    for run in front:
        run.run_dir = options.output_dir
        run.make_control_file(cleanup=False)
        run.output_results()
