from copy import copy
import time
import logging
import numpy as np
import warnings

import darwin.GlobalVars as GlobalVars

from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import keep_going
from darwin.ModelCode import ModelCode
from darwin.algorithms.run_downhill import run_downhill
from darwin.Population import Population
from darwin.Template import Template
from darwin.Model import Model
from darwin.ModelRun import ModelRun

from .DeapToolbox import DeapToolbox, model_run_to_deap_ind

from pymoo.algorithms.moo.nsga2 import NSGA2
import matplotlib
from pymoo.problems import get_problem
from pymoo.operators.crossover.pntx import TwoPointCrossover
from pymoo.operators.mutation.bitflip import BitflipMutation
from pymoo.operators.sampling.rnd import BinaryRandomSampling
from pymoo.optimize import minimize
from pymoo.visualization.scatter import Scatter
from pymoo.core.problem import ElementwiseProblem

import numpy as np
warnings.filterwarnings('error', category=DeprecationWarning)
logger = logging.getLogger(__name__)


class MogaProblem(ElementwiseProblem):
    def __init__(self, n_var, modeltemplate):
        super().__init__(n_var=n_var,   # number of bits
                         n_obj=2,
                         n_ieq_constr=0,
                         xl=np.zeros(n_var, dtype=int),
                         xu=np.ones(n_var, dtype=int),
                         # need this to send population and template to evaluate
                         requires_kwargs=True,
                         ModelTemplate=modeltemplate
                         )
        self.num_generations = 1
        self.generation = 1
        self.pop_size = 10
        self.toolbox = DeapToolbox(modeltemplate)
        # create an initial population of pop_size individuals (where
        # each individual is a list of bits [0|1])
        self.pop_full_bits = self.toolbox.new_population(self.pop_size)


    def _evaluate(self, x, out, *args, **kwargs):
        # will replace the code below with code to run a single generation of models
        # then population f1 and f2
        # model template in self.data['ModelTemplate']
        a = self.data['ModelTemplate']
        x_arr = [x.astype(int)]
        self.population = Population.from_codes(a, self.generation, x_arr,
                                                ModelCode.from_full_binary, max_iteration=self.num_generations)
        run = self.population.runs[0]
        model = self.population.models[0]
        self.population.run()
        # run a generation here, with current x
        # copy x to self
        #self.
        f1 =  run.result.fitness
        f2 =  model.estimated_theta_num + model.estimated_sigma_num + model.estimated_omega_num
        out["F"] = [f1, f2]


class _MOGARunner:
    def __init__(self, template: Template, pop_size, elitist_num, num_generations):
        self.generation = 0
        self.template = template
        self.elitist_num = elitist_num
        self.population = None
        self.num_generations = num_generations
        self.toolbox = DeapToolbox(template)
        self.pop_size = 10
        # create an initial population of pop_size individuals (where
        # each individual is a list of bits [0|1])
        self.pop_full_bits = self.toolbox.new_population(self.pop_size)

        # create an initial population of pop_size individuals (where
        # each individual is a list of bits [0|1])
        self.pop_full_bits = self.toolbox.new_population(pop_size)
        self.best_for_elitism = self.toolbox.new_population(elitist_num)

    def run_generation(self):
        log.message(f"pop_full_bits{self.pop_full_bits}")
        self.generation += 1

        if self.generation > self.num_generations or not keep_going():
            return False

        log.message(f"Starting generation {self.generation}")

        if self.generation > 1:
            self.pop_full_bits = self.toolbox.get_offspring(self.pop_full_bits)

            # replace first elitist_num individuals
            for i in range(self.elitist_num):
                self.pop_full_bits[i] = copy(self.best_for_elitism[i])

        self.population = Population.from_codes(self.template, self.generation, self.pop_full_bits,
                                                ModelCode.from_full_binary, max_iteration=self.num_generations)

        self.population.run()

        if not keep_going():
            return False

        for ind, run in zip(self.pop_full_bits, self.population.runs):
            ind.fitness.values = (run.result.fitness,)

        best_runs = self.population.get_best_runs(self.elitist_num)

        self.best_for_elitism = [model_run_to_deap_ind(run) for run in best_runs]

        return True

    def run_downhill(self, population: Population):

        log.message(f"Starting downhill generation = {self.generation}  at {time.asctime()}")

        best_runs = population.get_best_runs(options.num_niches)

        log.message(f"current best model(s) =")

        for run in best_runs:
            log.message(f"generation {self.generation}, ind {run.model_num}, fitness = {run.result.fitness}")

        run_downhill(self.template, population)

        best_runs = population.get_best_runs(self.elitist_num)

        log.message(f"Done with downhill step, {self.generation}. best fitness = {best_runs[0].result.fitness}")

        # redo best_for_elitism, after downhill
        self.best_for_elitism = [model_run_to_deap_ind(run) for run in best_runs]


def run_moga(model_template: Template) -> ModelRun:
    """
    Run the Genetic Algorithm (GA) search, using the DEAP (https://github.com/deap/deap) packages.
    The template object includes the control file template and all the token groups.

    :param model_template: Template object for the search
    :type model_template: Template
    :return: The single best model from the search
    :rtype: Model
    """


    pop_size = options.population_size
    elitist_num = options.MOGA['elitist_num']
    downhill_period = options.downhill_period
    runner = _MOGARunner(model_template, pop_size, elitist_num, options.num_generations)
    runner.problem = MogaProblem(n_var=100, modeltemplate=model_template) #n_var = num of genome bits
    # send everything needed for search to algorithms as **kwargs
    # does not (yet) minimiza on the pyDarwin problem, just runs the standard GA
    # staring below
    # plan is to move the run_generation code into
    #
    runner.algorithm = NSGA2(pop_size=30,
                      sampling=BinaryRandomSampling(),
                      crossover=TwoPointCrossover(),
                      mutation=BitflipMutation(),
                      eliminate_duplicates=True )
  # just to be sure that the minimzation runs, this is the simple problem, not the pyDarwin problem minimization
    res = minimize(runner.problem,
                   runner.algorithm,
                   ('n_gen', 10),
                   seed=1,
                   verbose=True)
    generations_no_change = 0

    log.message(f"MOGA best genome = {res.X},"
                f" OFV and # of parameters = {res.F}")
    # Begin evolution
    # can skip
    while runner.run_generation():
        population = runner.population

        if downhill_period > 0 and runner.generation % downhill_period == 0:
            runner.run_downhill(population)

        best_run = population.get_best_run()
        best_fitness = best_run.result.fitness

        log.message(f"Current generation best genome = {best_run.model.model_code.FullBinCode},"
                    f" best fitness = {best_fitness:.4f}")

        best_run_overall = GlobalVars.best_run or best_run
        overall_best_fitness = best_run_overall.result.fitness

        log.message(f"Best overall fitness = {best_run_overall.result.fitness:4f},"
                    f" iteration {best_run_overall.generation}, model {best_run_overall.model_num}")

        if best_fitness < overall_best_fitness:
            generations_no_change = 0
            log.message(f"Better fitness found, generation = {runner.generation},"
                        f" new best fitness = {best_fitness:.4f}")
        else:
            generations_no_change += 1
            log.message(f"No change in fitness for {generations_no_change} generations,"
                        f" best fitness = {overall_best_fitness:.4f}")

    log.message(f"-- End of MOGA component at {time.asctime()} --")

    population = runner.population

    final_moga_run = population.get_best_run()

    log.message(f'N non dominated solutions = MOGA is {str(final_moga_run.model.model_code.FullBinCode)}'
                f'OFVs are:')

    if options.final_downhill_search and keep_going():
        population.name = 'FN'

        run_downhill(model_template, population)

        best = population.get_best_run()

        log.message(f"Done with final downhill step. best fitness = {best.result.fitness}")

    return GlobalVars.best_run
