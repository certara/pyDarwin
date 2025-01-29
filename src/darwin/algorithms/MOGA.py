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
from grapheme import length

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
        super().__init__(n_var=n_var,   # number of bits
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

    class MyCallback(Callback):

        def __init__(self) -> None:
            super().__init__()
            self.data["best"] = []

        def notify(self, algorithm):
            self.data["best"].append(algorithm.pop.get("F").min())

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
        run = self.population.runs[0]  #append run, run is Modelrun
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
    """
     Need to edit below, change from trival MOGA problem to run NONMEM
    """


    n_var = int(np.sum(model_template.gene_length))
    pop_size = options.population_size #connect with options file
    n_gens = options.num_generations    #connect with options file

    runner = _MOGARunner(model_template, pop_size, options.num_generations)
    runner.problem = MogaProblem(n_var=n_var, modeltemplate=model_template, generation=1, n_eval=0) #n_var = num of genome bits
    runner.algorithm = NSGA2(pop_size=pop_size,
                      sampling=BinaryRandomSampling(),
                      crossover=TwoPointCrossover(),
                      mutation=BitflipMutation(),
                      eliminate_duplicates=True)

    # prepare the algorithm to solve the specific problem (same arguments as for the minimize function)
    runner.algorithm.setup(runner.problem, termination=('n_gen', n_gens), seed=1, verbose=False)
    # n_gen = 0
    runner.algorithm.callback = runner.problem.MyCallback()
    # until the algorithm has no terminated
    while runner.algorithm.has_next():
        # ask the algorithm for the next solution to be evaluated
        # all evaluations are in pop
        pop = runner.algorithm.ask()
        for ii in range(len(pop)):
            n_gen = runner.algorithm.n_gen
            n_eval = runner.algorithm.evaluator.n_eval
            runner.problem = MogaProblem(n_var=n_var, modeltemplate=model_template, generation=n_gen, n_eval=n_eval)

            runner.algorithm.evaluator.eval(runner.problem, pop[ii])
            # note, this print (log.message) after each individual because each individual gets defined as a population
            # when in elementwise mode, should be fixed when run parallel??
            # note there is no fitness, should not be on console output
        # returned the evaluated individuals which have been evaluated or even modified
        runner.algorithm.tell(infills=pop)
        # can't find a way to get fronts out of the problem object, call back doesn't seem to have access
        # the fronts object in classes.py in C:\Users\msale\AppData\Local\Programs\Python\Python310\Lib\site-packages\pymoo\operators\survival\rank_and_crowding
        # may need to manually recalculate fronts for output to console and plotting
        # callback below just returns best model
        # and runner.algorithm.result() doesn't include the model source, only the genome (X) and the objectives (F) and
        # other MOO related objects
        vals = runner.algorithm.callback.data["best"]
        front = runner.algorithm.result()
       # log.message(str(runner.algorithm.n_gen) + ", " + str(runner.algorithm.evaluator.n_eval))8
    res = runner.algorithm.result()
    log.message(f" MOGA best genome = {res.X.astype(int)},\n"
                f" OFV and # of parameters = {res.F}")
    for ii in range(len(res.X)):
        cur_x = [res.X[ii].astype(int)]
        cur_population = Population.from_codes(model_template, n_gen+1, cur_x,
                                                ModelCode.from_full_binary)
        # cur_population.run()
        cur_run = cur_population.runs[0]
        # cur_model = cur_run.model
        cur_run.run_dir = options.output_dir + '\\' + str(ii)
        cur_run.make_control_file()
        cur_run.output_results()