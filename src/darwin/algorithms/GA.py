from copy import copy
from datetime import timedelta
import time
import logging 
import numpy as np 

import darwin.GlobalVars as GlobalVars

from darwin.Log import log
from darwin.options import options
from darwin.execution_man import keep_going
from darwin.ModelCode import ModelCode
from darwin.run_downhill import run_downhill
from darwin.Population import Population
from darwin.Template import Template
from darwin.Model import Model, write_best_model_files
from darwin.ModelRun import ModelRun

from .DeapToolbox import DeapToolbox, model_run_to_deap_ind

np.warnings.filterwarnings('error', category=np.VisibleDeprecationWarning)
logger = logging.getLogger(__name__) 


class _GARunner:
    def __init__(self, template: Template, pop_size, elitist_num):
        self.generation = -1
        self.template = template
        self.elitist_num = elitist_num

        self.toolbox = DeapToolbox(template)

        # create an initial population of pop_size individuals (where
        # each individual is a list of bits [0|1])
        self.pop_full_bits = self.toolbox.new_population(pop_size)
        self.best_for_elitism = self.toolbox.new_population(elitist_num)

    def run_generation(self):
        self.generation += 1

        log.message("-- Starting Generation %i --" % self.generation)

        if self.generation > 0:
            self.pop_full_bits = self.toolbox.get_offspring(self.pop_full_bits)

            # replace first elitist_num individuals
            for i in range(self.elitist_num):
                self.pop_full_bits[i] = copy(self.best_for_elitism[i])

        population = Population.from_codes(self.template, self.generation, self.pop_full_bits,
                                           ModelCode.from_full_binary)

        population.run()

        if not keep_going():
            return population, False

        for ind, run in zip(self.pop_full_bits, population.runs):
            ind.fitness.values = (run.result.fitness,)

        best_runs = population.get_best_runs(self.elitist_num)

        self.best_for_elitism = [model_run_to_deap_ind(run) for run in best_runs]

        return population, True

    def run_downhill(self, population: Population):
        # pop will have the fitnesses without the niche penalty here
        # add local exhaustive search here??
        # temp_fitnesses = copy(fitnesses)
        # downhill with NumNiches best models
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


def run_ga(model_template: Template) -> ModelRun:
    """
    Run the Genetic Algorithm (GA) search, using the DEAP (https://github.com/deap/deap) packages.
    All the required information is contained in the Template objects, plus the options module
    The template objects includes the control file template, and all the token groups.

    Called from Darwin.run_search, _run_template

    :param model_template: Template object for the search

    :type model_template: Template

    :return: The single best model from the search

    :rtype: Model
    """    
    downhill_q = options.downhill_q
    pop_size = options.population_size
    elitist_num = options['elitist_num']

    runner = _GARunner(model_template, pop_size, elitist_num)

    # run generation 0
    population, cont = runner.run_generation()

    if not cont:
        return GlobalVars.BestRun

    generations_no_change = 0
    overall_best_fitness = options.crash_value
    num_generations = options['num_generations']

    # Begin evolution

    while runner.generation < num_generations:
        population, cont = runner.run_generation()

        if not cont:
            break

        if runner.generation % downhill_q == 0:
            runner.run_downhill(population)

        best_run = population.get_best_run()

        best_fitness = best_run.result.fitness

        log.message(f"Current generation best genome = {best_run.model.model_code.FullBinCode},"
                    f" best fitness = {best_fitness:.4f}")

        best_run_overall = GlobalVars.BestRun

        log.message(f"Best overall fitness = {best_run_overall.result.fitness:4f},"
                    f" iteration {best_run_overall.generation}, model {best_run_overall.model_num}")

        if best_fitness < overall_best_fitness:
            log.message(f"Better fitness found, generation = {runner.generation},"
                        f" new best fitness = {best_fitness:.4f}")
            overall_best_fitness = best_fitness
            generations_no_change = 0
        else:
            generations_no_change += 1
            log.message(f"No change in fitness for {generations_no_change} generations,"
                        f" best fitness = {overall_best_fitness:.4f}")

    log.message(f"-- End of GA component at {time.asctime()} --")

    final_ga_run = population.get_best_run()

    if options["final_fullExhaustiveSearch"] and keep_going():
        population.name = 'FN'

        run_downhill(model_template, population)

        best = population.get_best_run()

        log.message(f"Done with final downhill step. best fitness = {best.result.fitness}")

    log.message(f"-- End of Optimization at {time.asctime()} --")

    best_run = GlobalVars.BestRun

    elapsed = time.time() - GlobalVars.StartTime

    log.message(f"Elapse time = " + str(timedelta(seconds=elapsed)) + "\n")
    log.message(f'Best individual GA is {str(final_ga_run.model.model_code.FullBinCode)}'
                f' with fitness of {final_ga_run.result.fitness:4f}')
    log.message(f"Best overall fitness = {best_run.result.fitness:4f},"
                f" iteration {best_run.generation}, model {best_run.model_num}")

    write_best_model_files(GlobalVars.FinalControlFile, GlobalVars.FinalResultFile)

    log.message(f"Final out from best model is in {GlobalVars.FinalResultFile}")

    return best_run
