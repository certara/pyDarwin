from copy import copy
import time
import logging 
import numpy as np 
import random
import warnings

import csv
import os

from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga3 import NSGA3


from pymoo.optimize import minimize
from pymoo.util.ref_dirs import get_reference_directions
from pymoo.operators.crossover.pntx import SinglePointCrossover
from pymoo.operators.mutation.bitflip import BitflipMutation
from pymoo.operators.sampling.rnd import BinaryRandomSampling
from pymoo.indicators.hv import HV
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

import darwin.GlobalVars as GlobalVars

from darwin.Log import log
from darwin.options import options
from darwin.ExecutionManager import keep_going
from darwin.ModelCode import ModelCode
from darwin.Population import Population
from darwin.Template import Template
from darwin.Model import Model
from darwin.ModelRun import ModelRun


warnings.filterwarnings('ignore', category=DeprecationWarning)

logger = logging.getLogger(__name__)

def _get_n_params(run: ModelRun) -> int:
    model = run.model

    return model.estimated_omega_num + model.estimated_theta_num + model.estimated_sigma_num



class MOGAProblem(Problem):
    def __init__(self, n_var, genres, **kwargs):
        super().__init__(n_var=n_var,
                         n_obj=3,
                         n_constr=3,
                         xl=np.zeros(n_var, dtype=int),
                         xu=np.ones(n_var, dtype=int),
                         requires_kwargs=True
                         )
        self.genres=genres



    def _evaluate(self, x, out, *args, **kwargs):

        f1 = self.genres[:,0]
        f2 = self.genres[:,1]
        f3 = self.genres[:,2]

        g1 = f1 - 999999
        g2 = 0.1-f2
        g3 = f3 - 999999



        out["F"] = np.column_stack([f1, f2, f3])
        out["G"] = np.column_stack([g1, g2, g3])




class _MOGARunner:
    def __init__(self, template: Template, pop_size, num_generations):
        self.generation = 0
        self.template = template
        self.population = None
        self.num_generations = num_generations



def run_moga(model_template: Template) -> ModelRun:
    # Determine the number of variables based on the model template's gene lengths.
    n_var = int(np.sum(model_template.gene_length))
    # Retrieve genetic algorithm options.
    ga_options = options.GA
    crossover_probability = ga_options['crossover_rate']
    mutation_probability = ga_options['mutation_rate']
    attribute_mutation_probability = ga_options['attribute_mutation_probability']
    pop_size = options.population_size
    n_gens = options.num_generations
    # Create reference directions for the NSGA-III algorithm.
    ref_dirs = get_reference_directions("das-dennis", 3, n_partitions=12)
    # Initialize the NSGA-III runner.
    runner = _MOGARunner(model_template, pop_size, options.num_generations)
    runner.problem = MOGAProblem(n_var=n_var, genres=None)
    # Configure the NSGA-III algorithm.
    runner.algorithm = NSGA3(ref_dirs=ref_dirs,
                             pop_size=pop_size,
                             sampling=BinaryRandomSampling(),
                             crossover=SinglePointCrossover(prob=crossover_probability),
                             mutation=BitflipMutation(prob=mutation_probability,prob_var=attribute_mutation_probability),
                             eliminate_duplicates=True)
    # Set up the algorithm with termination criteria and history tracking.
    runner.algorithm.setup(runner.problem, termination=('n_gen', n_gens), seed=1, save_history=True, verbose=False)
    # Initialize variables for tracking progress.
    n_gen = 0
    pres = np.empty((0, 4))
    hvres = np.empty((0, 2))
    ref_point = np.array([100000000, 26, 100000000])
    # Main optimization loop.
    while runner.algorithm.has_next():

        pop = runner.algorithm.ask()
        bitstrings = [ind.X.astype(int) for ind in pop]
        n_gen += 1
        population = Population.from_codes(model_template,n_gen, bitstrings,
                                                ModelCode.from_full_binary,
                                                max_iteration=n_gens)
        population.run()
        run=population.runs
        f1 = [r.result.ofv for r in population.runs]
        f2 = [_get_n_params(r) for r in
              population.runs]
        f3 = [r.result.post_run_r_penalty for r in population.runs]

        genres = np.array([f1, f2, f3]).T



        n_gen = runner.algorithm.n_gen
        n_eval = runner.algorithm.evaluator.n_eval
        runner.problem = MOGAProblem(n_var=n_var, genres=genres)
        runner.algorithm.evaluator.eval(runner.problem, pop)
        runner.algorithm.tell(infills=pop)
        parents_objectives = runner.algorithm.pop.get("F")
        hv = HV(ref_point=ref_point).do(parents_objectives)
        hv_values = np.array([hv, n_gen]).T
        iteration_col = np.full((parents_objectives.shape[0], 1), n_gen)
        parents_objectives2 = np.hstack((parents_objectives,iteration_col))
        pres = np.vstack((pres, parents_objectives2))
        hvres = np.vstack((hvres, hv_values))

    # Extract the final results.
    res = runner.algorithm.result()
    all_X = []
    all_F = []
    for entry in res.history:
        all_X.append(entry.pop.get("X"))
        all_F.append(entry.pop.get("F"))
    all_X = np.vstack(all_X)
    all_X = all_X.astype(int)
    all_F = np.vstack(all_F)
    nds = NonDominatedSorting().do(all_F, only_non_dominated_front=True)
    pareto_X = all_X[nds]
    pareto_X = np.array([[int("".join(map(str, row)))] for row in pareto_X])
    pareto_F = all_F[nds]
    allpareto = np.hstack([pareto_X, pareto_F])
    # Save Pareto fronts
    pareto_dir = options.output_dir + '\\' + 'PARETO'
    os.makedirs(pareto_dir, exist_ok=True)
    output_path = os.path.join(pareto_dir, "allpareto.csv")
    np.savetxt(output_path, allpareto, delimiter=",", header="Model,OFV,np,rp", comments="")

    # Save each generation's parents
    genres_dir = options.output_dir + '\\' + 'GENRES'
    os.makedirs(genres_dir, exist_ok=True)
    output_path = os.path.join(genres_dir, "output.csv")
    np.savetxt(output_path, pres, delimiter=",", header="f1,f2,f3,G", comments="")
    # Save hyper volume
    output_path = os.path.join(genres_dir, "hv.csv")
    np.savetxt(output_path, hvres, delimiter=",", header="hv,G", comments="")

    log.message(f" NSGA3 ideal Pareto-front genome = {res.X.astype(int)},\n"
                f" OFV, # of P, and R Penalty = {res.F}")

    for i in range(len(res.X)):
        cur_x = [res.X[i].astype(int)]
        cur_population = Population.from_codes(model_template, n_gen + 1, cur_x,
                                               ModelCode.from_full_binary)
        cur_run = cur_population.runs[0]
        cur_run.run_dir = options.output_dir + '\\' + str(i)
        cur_run.make_control_file()
        cur_run.output_results()