import os
import shutil
from copy import copy
import time
import logging
import numpy as np
import warnings

import darwin.GlobalVars as GlobalVars
from darwin import Population
from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import keep_going
from darwin.ModelCode import ModelCode
from darwin.algorithms.run_downhill import run_downhill
from darwin.Population import Population
from darwin.Template import Template
from darwin.Model import Model
from darwin.ModelRun import ModelRun
from grapheme import length
from darwin.Population import Population
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

from pymoo.core.callback import Callback
import numpy as np

warnings.filterwarnings('error', category=DeprecationWarning)
logger = logging.getLogger(__name__)


class MogaProblem(ElementwiseProblem):
    def __init__(self, n_var, modeltemplate, generation, n_eval):
        super().__init__(n_var=n_var,  # number of bits
                         n_obj=2,
                         n_ieq_constr=0,
                         xl=np.zeros(n_var, dtype=int),
                         xu=np.ones(n_var, dtype=int),
                         # need this to send population and template to evaluate
                         requires_kwargs=True,
                         ModelTemplate=modeltemplate
                         )
        self.num_generations = options.num_generations
        self.generation = generation
        self.n_eval = n_eval

    # class MyCallback(Callback):
    #
    #     def __init__(self) -> None:
    #         super().__init__()
    #         self.data["front"] = []
    #
    #     def notify(self, algorithm):
    #         # self.data["front"].append(algorithm.pop.get("F").min())
    #         self.data["front"].append(algorithm.pop.get("data"))

    def _evaluate(self, x, out, *args, **kwargs):
        # will replace the code below with code to run a single generation of models
        # then population f1 and f2
        # model template in self.data['ModelTemplate']
        a = self.data['ModelTemplate']
        x_arr = [x.astype(int)]
        self.population = Population.from_codes(a, self.generation, x_arr,
                                                ModelCode.from_full_binary,
                                                start_number=self.n_eval,
                                                max_iteration=self.num_generations)
        self.population.run()
        run = self.population.runs[0]  # append run, run is Modelrun
        model = run.model

        f1 = run.result.ofv
        f2 = model.estimated_omega_num + model.estimated_theta_num + model.estimated_sigma_num
        out["F"] = [f1, f2]


class _MOGARunner:
    def __init__(self, template: Template, pop_size, num_generations):
        self.generation = 0
        self.template = template
        self.population = None
        self.num_generations = num_generations


def run_moga(model_template: Template) -> ModelRun:
    n_var = int(np.sum(model_template.gene_length))
    pop_size = options.population_size  # connect with options file
    n_gens = options.num_generations  # connect with options file

    runner = _MOGARunner(model_template, pop_size, options.num_generations)
    runner.problem = MogaProblem(n_var=n_var, modeltemplate=model_template, generation=1,
                                 n_eval=0)  # n_var = num of genome bits
    runner.algorithm = NSGA2(pop_size=pop_size,
                             sampling=BinaryRandomSampling(),
                             crossover=TwoPointCrossover(),
                             mutation=BitflipMutation(),
                             eliminate_duplicates=True)

    # prepare the algorithm to solve the specific problem (same arguments as for the minimize function)
    runner.algorithm.setup(runner.problem, termination=('n_gen', n_gens), seed=1, verbose=False)
    all_population = None  # all models ever run
    while runner.algorithm.has_next():
        # ask the algorithm for the next solution to be evaluated
        # all evaluations are in pop
        pop = runner.algorithm.ask()
        # construct genome
        pop_full_bits = []
        for this_ind in pop:
            this_genome = []
            for this_bit in this_ind.X:
                this_genome.append(int(this_bit))
            pop_full_bits.append(this_genome)
        # this is a standard GA/pydarwin population (not a moo population), just to record pareto front and get temp dir
        full_populaton = Population.from_codes(model_template, runner.algorithm.n_gen, pop_full_bits,
                                               code_converter=ModelCode.from_full_binary)
        for ii in range(len(pop)):
            n_gen = runner.algorithm.n_gen
            n_eval = runner.algorithm.evaluator.n_eval
            runner.problem = MogaProblem(n_var=n_var, modeltemplate=model_template, generation=n_gen, n_eval=n_eval)

            runner.algorithm.evaluator.eval(runner.problem, pop[ii])
            full_populaton.runs[ii].result.ofv = pop[ii].F  # both OFV and Nparms
            full_populaton.runs[ii].run_dir = runner.problem.population.runs[0].run_dir
            full_populaton.runs[ii].control_file_name = runner.problem.population.runs[0].control_file_name
            full_populaton.runs[ii].output_file_name = runner.problem.population.runs[0].output_file_name
            # note, this print (log.message) after each individual because each individual gets defined as a population
            # when in elementwise mode, should be fixed when run parallel??
            # note there is no fitness, should not be on console output

        # append full population models to all_population
        if n_gen == 1:
            all_population = full_populaton
        else:
            for this_run in full_populaton.runs:
                all_population.runs.append(this_run)
        runner.algorithm.tell(infills=pop)
        # below will need to be refactored/otherwise improved
        # extra files in folders are deleted before they can be copied to non_dominated folder,
        # probably will be fixed when run parallel??
        # note that model numbering is different, numnbers are sequenctial, do not reset to 1 with each generation
        # therefore, model number in FullPopulation is incorrect. set to copy temp folder from pop object to FullPopulation
        # front_results = runner.algorithm.callback.data['front'][0]
        non_dominated_folder = os.path.join(options.working_dir, "non_dominated_models", str(n_gen))
        os.mkdir(non_dominated_folder)
        log.message("Current Non Dominated models:")
        n_front_models = 0
        # this resorts the models and accoding to their rank
        res = runner.algorithm.result()

        for ii in range(len(res.X)):
            cur_x = [res.X[ii].astype(int)]
            n_front_models += 1
            # find model in original population by genome
            for model in all_population.runs:
                if all(model.model.model_code.FullBinCode == cur_x[0]):
                    os.mkdir(os.path.join(non_dominated_folder, str(n_front_models)))
                    # find source directory by matching genome of FullPopulation and res
                    src_dir = model.run_dir
                    for filename in os.listdir(src_dir):
                        src_file = os.path.join(src_dir, filename)
                        dst_file = os.path.join(non_dominated_folder, str(n_front_models), filename)
                        if os.path.isfile(src_file):
                            shutil.copy2(src_file, dst_file)  # MODEL NUMBER IS WRONG ON CONSOLE OUTPUT
                    log.message(
                        "Generation " + str(n_gen) + " Pareto Front, Model " + model.control_file_name + ", OFV = " + \
                        str(round(model.result.ofv[0], 4)) + ", NParms = " + \
                        str(int(model.result.ofv[1])))
                    break

    res = runner.algorithm.result()
    log.message(f" MOGA best genome = {res.X.astype(int)},\n"
                f" OFV and # of parameters = {res.F}")
    for ii in range(len(res.X)):
        cur_x = [res.X[ii].astype(int)]
        cur_population = Population.from_codes(model_template, n_gen + 1, cur_x,
                                               ModelCode.from_full_binary)
        # cur_population.run()
        cur_run = cur_population.runs[0]
        # cur_model = cur_run.model
        cur_run.run_dir = options.output_dir + '\\' + str(ii)
        cur_run.make_control_file()
        cur_run.output_results()
