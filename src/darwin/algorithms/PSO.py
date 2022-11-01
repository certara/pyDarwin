# from https://pyswarms.readthedocs.io/en/development/examples/basic_optimization.html

r"""
Modified from
# modifed from https://pyswarms.readthedocs.io/en/latest/_modules/pyswarms/discrete/binary.html

A Binary Particle Swarm Optimization (binary PSO) algorithm.

It takes a set of candidate solutions, and tries to find the best
solution using a position-velocity update method. Unlike
:mod:`pyswarms.single.gb` and :mod:`pyswarms.single.lb`, this technique
is often applied to discrete binary problems such as job-shop scheduling,
sequencing, and the like.

The update rule for the velocity is still similar, as shown in the
proceeding equation:

.. math::

   v_{ij}(t + 1) = w * v_{ij}(t) + c_{1}r_{1j}(t)[y_{ij}(t) − x_{ij}(t)] + c_{2}r_{2j}(t)[\hat{y}_{j}(t) − x_{ij}(t)]

For the velocity update rule, a particle compares its current position
with respect to its neighbours. The nearest neighbours are being
determined by a kD-tree given a distance metric, similar to local-best
PSO. The neighbours are computed for every iteration. However, this whole
behavior can be modified into a global-best PSO by changing the nearest
neighbours equal to the number of particles in the swarm. In this case,
all particles see each other, and thus a global best particle can be established.

In addition, one notable change for binary PSO is that the position
update rule is now decided upon by the following case expression:

.. math::

   X_{ij}(t+1) = \left\{\begin{array}{lr}
        0, & \text{if } \text{rand() } \geq S(v_{ij}(t+1))\\
        1, & \text{if } \text{rand() } < S(v_{ij}(t+1))
        \end{array}\right\}

Where the function :math:`S(x)` is the sigmoid function defined as:

.. math::

   S(x) = \dfrac{1}{1 + e^{-x}}

This enables the algorithm to output binary positions rather than
a stream of continuous values as seen in global-best or local-best PSO.

This algorithm was adapted from the standard Binary PSO work of J. Kennedy and
R.C. Eberhart in Particle Swarm Optimization [SMC1997]_.

.. [SMC1997] J. Kennedy and R.C. Eberhart, "A discrete binary version of
    particle swarm algorithm," Proceedings of the IEEE International
    Conference on Systems, Man, and Cybernetics, 1997.
"""

import darwin.GlobalVars as GlobalVars
from pyswarms.backend.operators import compute_pbest, compute_objective_function
from pyswarms.backend.topology import Star
from pyswarms.backend.handlers import VelocityHandler
from pyswarms.base import DiscreteSwarmOptimizer
from pyswarms.utils.reporter import Reporter
# Import standard library
import logging
import shutil
import os
import darwin.algorithms.run_downhill as rundown
# Import modules
import numpy as np
import multiprocessing as mp

from collections import deque

from darwin.Log import log
from darwin.options import options

from darwin.Template import Template
from darwin.ModelRun import ModelRun
from darwin.Population import Population
from darwin.ModelCode import ModelCode


class _PSORunner(DiscreteSwarmOptimizer):
    """
    Run a binary Particle Swarm optimization (binary so it can use same full binary representation of the model that GA uses)
    Only the star topology is supported.
    :param model_template: Template object for the search
    :type model_template: Template
    :return: The single best model from the search
    :rtype: Model
    """

    def __init__(
            self,
            template,
            n_particles,
            dimensions,
            pso_options,
            darwin_options,
            init_pos=None,
            velocity_clamp=None,
            vh_strategy="unmodified",
            ftol=-np.inf,
            ftol_iter=1,
            num_generations=1
    ):
        """Initialize the swarm

        Attributes
        ----------
        n_particles : int
            number of particles in the swarm.
        dimensions : int
            number of dimensions in the space.
        options : dict with keys :code:`{'c1', 'c2', 'w', 'k', 'p'}`
            a dictionary containing the parameters for the specific
            optimization technique
                * c1 : float
                    cognitive parameter
                * c2 : float
                    social parameter
                * w : float
                    inertia parameter
                * k : int
                    number of neighbors to be considered. Must be a
                    positive integer less than :code:`n_particles`
                * p: int {1,2}
                    the Minkowski p-norm to use. 1 is the
                    sum-of-absolute values (or L1 distance) while 2 is
                    the Euclidean (or L2) distance.
        init_pos : numpy.ndarray, optional
            option to explicitly set the particles' initial positions. Set to
            :code:`None` if you wish to generate the particles randomly.
        velocity_clamp : tuple, optional
            a tuple of size 2 where the first entry is the minimum velocity
            and the second entry is the maximum velocity. It
            sets the limits for velocity clamping.
        vh_strategy : String
            a strategy for the handling of the velocity of out-of-bounds particles.
            Only the "unmodified" and the "adjust" strategies are allowed.
        ftol : float
            relative error in objective_func(best_pos) acceptable for
            convergence
        ftol_iter : int
            number of iterations over which the relative error in
            objective_func(best_pos) is acceptable for convergence.
            Default is :code:`1`
        """
        self.darwin_options = darwin_options
        self.pso_options = pso_options
        self.generation = 0
        self.template = template
        self.init_pos = init_pos
        # self.pop_full_bits is the binary
        self.population = Population.from_codes(self.template, self.generation, self.init_pos,
                                                ModelCode.from_full_binary,
                                                max_iteration=self.darwin_options.num_generations)
        # Initialize logger
        self.rep = Reporter(logger=logging.getLogger(__name__))


        # Initialize parent class, this creates the swarm, can set intitial position if needed
        super(_PSORunner, self).__init__(
            n_particles=n_particles,
            dimensions=dimensions,
            binary=True,
            options=pso_options,
            init_pos=init_pos,
            velocity_clamp=velocity_clamp,  # doesn't use velocity_clamp for binary (unmodified)
            ftol=ftol,
            ftol_iter=ftol_iter,
        )
        # Initialize the resettable attributes
        self.reset()
        # Initialize the topology
        self.top = Star(static=False)
        self.vh = VelocityHandler(strategy=vh_strategy)
        self.name = __name__

    def optimize(self, objective_func):  # , best_cost_yet_found, iters, model_template):
        """Optimize the swarm for a number of iterations

        Performs the optimization to evaluate the objective
        function :code:`f` for a number of iterations :code:`iter.`

        objective_func : function
            objective function to be evaluated
        iters : int
            number of iterations
        n_processes : int, optional
            number of processes to use for parallel particle evaluation
            Defaut is None with no parallelization.
        verbose : bool
            enable or disable the logs and progress bar (default: True = enable logs)
        kwargs : dict
            arguments for objective function

        tuple
            the local best cost and the local best position among the
            swarm.
        """
        # Apply verbosity
        n_processes = None
        verbose = False

        if verbose:
            log_level = logging.INFO
        else:
            log_level = logging.NOTSET

        # self.rep.log("Obj. func. args: {}".format(kwargs), lvl=logging.DEBUG)
        self.rep.log("Optimize for {} iterations with {}".format(self.darwin_options.num_generations, self.options),
                     lvl=log_level, )

        # Populate memory of the handlers
        # not sure this is needed, as we aren't doing velocity handler for binary, but will update for elitism and downhill
        self.vh.memory = self.swarm.position

        # Setup Pool of processes for parallel evaluation
        pool = None if n_processes is None else mp.Pool(n_processes)
        best_cost_yet_found = self.darwin_options['crash_value']
        self.swarm.pbest_cost = np.full(self.swarm_size[0], self.darwin_options['crash_value'])
        ftol_history = deque(maxlen=self.ftol_iter)


        last_best_cost = self.darwin_options['crash_value']
        last_best_poss = np.zeros([self.swarm.dimensions])
        found_better = False
        iterations_without_improvement = 0
        # elitism
        if self.darwin_options.PSO['elitist_num'] > 0:
            use_elitism = True
            elitism_num = self.darwin_options.PSO['elitist_num']
            best_costs_for_elitism = np.ones(elitism_num) * self.darwin_options['crash_value']

        else:
            use_elitism = False
        for this_iter in range(self.darwin_options.num_generations):
            self.generation = this_iter

            self.swarm.current_cost, self.population.runs = compute_objective_function(
                self.swarm, objective_func, pool, model_template=self.template, iteration=this_iter)
            # only have fitness in swarm .current_cost at this point (not in results)
            # current position seems to be in swarm.best_pos, while swarm.best_cost is just the best
            # fitness in swarm.current_cost
            # pbest is personal best, best position ever for each particle
            # for elitism and downhill, need to update swarm.vh.memory with new position
            self.swarm.pbest_pos, self.swarm.pbest_cost = compute_pbest(
                self.swarm
            )
            # downhill??
            have_downhill_results = False
            if self.darwin_options['downhill_period'] > 0:
                if (this_iter > 0) & (this_iter % self.darwin_options['downhill_period'] == 0):
                    have_downhill_results = True
                    log.message("Starting downhill for iteration " + str(this_iter))
                    self.population.name = this_iter
                    all_run = rundown.run_downhill(self.template, self.population)
                    best_downhill_models = self.population.get_best_runs(self.darwin_options['num_niches'])
                    # copy position and vh_memory
                    best_downhill_model = self.population.get_best_run()
                    downhill_best_cost = best_downhill_model.result.fitness
                    best_poss = []  # probably a better way to do this than a loop?
                    best_vh_memory = []
                    for x in best_downhill_models:
                            best_poss.append(x.model.model_code.FullBinCode)
                            best_vh_memory.append(x.model.model_code.FullBinCode)


            if not have_downhill_results: # only use elitism if no downhill
                elitism_models = self.population.get_best_runs(elitism_num)
                best_indices = sorted(range(len(self.swarm.current_cost)), # save for position and vh
                                    key=lambda sub: self.swarm.current_cost[sub])[:elitism_num]
                best_poss = self.swarm.position[best_indices]  # best_poss (plural)
                best_vh_memory = self.vh.memory[best_indices]
            best_index = sorted(range(len(self.swarm.current_cost)),
                                key=lambda sub: self.swarm.current_cost[sub])[:1]
            best_cost = self.swarm.current_cost[best_index][0]
            best_pos = self.swarm.pbest_pos[best_index]  # best positions
            if have_downhill_results:
                best_cost = np.min([best_cost, downhill_best_cost])
            if best_cost < last_best_cost:
                log.message(
                    "Better model found by PSO, cost = " + str(best_cost) + ", iteration = " + str(this_iter))

                iterations_without_improvement = 0
                last_best_cost = best_cost
                best_model = self.population.get_best_run()
                # write best to intermediate
                output_control = open(os.path.join(self.darwin_options.output_dir, "intermediate_control_file.mod"), "w")
                output_control.write(best_model.model.control)
                output_control.close()
                shutil.copyfile(os.path.join(best_model.run_dir, best_model.output_file_name),
                                os.path.join(self.darwin_options.output_dir, "intermediate_output_file.lst"))
            else:
                found_better = False
                iterations_without_improvement += 1
                log.message(
                    "Iterations without improvement = " + str(iterations_without_improvement) + ", iteration = " + str(
                        this_iter))


            best_cost_this_iter = np.min(self.swarm.current_cost)
            best_cost_yet_found = np.min([best_cost_yet_found, best_cost_this_iter])
            # Update gbest from neighborhood, global best
            self.swarm.best_pos, self.swarm.best_cost = self.top.compute_gbest(
                self.swarm, p=self.pso_options['p'], k=self.pso_options['k']
            )

            # Save to history
            hist = self.ToHistory(
                best_cost=self.swarm.best_cost,
                mean_pbest_cost=np.mean(self.swarm.pbest_cost),
                mean_neighbor_cost=np.mean(self.swarm.best_cost),
                position=self.swarm.position,
                velocity=self.swarm.velocity,
            )
            self._populate_history(hist)
            # Verify stop criteria based on the relative acceptable cost ftol
            relative_measure = self.ftol * (1 + np.abs(best_cost_yet_found))
            delta = (
                    np.abs(self.swarm.best_cost - best_cost_yet_found) <= relative_measure
            )
            if this_iter < self.ftol_iter:
                ftol_history.append(delta)
            else:
                ftol_history.append(delta)
                if all(ftol_history) and iterations_without_improvement >= options.PSO['break_on_no_change']:
                    break

            self.swarm.velocity = self._compute_velocity()
            # don't need velocity clamp for binary, can't large or small velocity
            # and position can be < 0 or > 1 due to sigmoid
            self.swarm.position = self._compute_position()
            if use_elitism or have_downhill_results:  # put best back randomly
                if have_downhill_results:
                    num_new = self.darwin_options['num_niches']
                else:
                    num_new = elitism_num
                indices = np.random.randint(0, self.darwin_options['population_size'], num_new)
                self.swarm.position[indices] = best_poss
                self.vh.memory[indices] = best_vh_memory # not sure we need this, seems to be the same as position
        if self.darwin_options['final_downhill_search']:
            log.message("Starting final downhill")

            self.population.name = this_iter
            all_run = rundown.run_downhill(self.template, self.population)
            final_best = self.population.get_best_run()
            final_best_cost = final_best.result.fitness
            final_best_pos = final_best.model.model_code.FullBinCode

        # Obtain the final best_cost and the final best_position
        else:  # no final downhill
            final_best_cost = self.swarm.best_cost.copy()
            final_best_pos = self.swarm.pbest_pos[
                self.swarm.pbest_cost.argmin()
            ].copy()

            # Close Pool of Processes
        if n_processes is not None:
            pool.close()
        # need all costs/positions for downhill
        # make final best here

        return final_best_cost, final_best_pos

    def _compute_velocity(self):  # swarm, clamp, vh, bounds=None):
        """Update the velocity matrix
        modifed from https://pyswarms.readthedocs.io/en/latest/_modules/pyswarms/discrete/binary.html
        This method updates the velocity matrix using the best and current
        positions of the swarm. The velocity matrix is computed using the
        cognitive and social terms of the swarm. The velocity is handled
        by a :code:`VelocityHandler`.

        A sample usage can be seen with the following:

        .. code-block :: python

            import pyswarms.backend as P
            from pyswarms.swarms.backend import Swarm, VelocityHandler

            my_swarm = P.create_swarm(n_particles, dimensions)
            my_vh = VelocityHandler(strategy="invert")

            for i in range(iters):
                # Inside the for-loop
                my_swarm.velocity = compute_velocity(my_swarm, clamp, my_vh, bounds)

        Parameters
        ----------
        swarm : pyswarms.backend.swarms.Swarm
            a Swarm instance
        clamp : tuple of floats, optional
            a tuple of size 2 where the first entry is the minimum velocity
            and the second entry is the maximum velocity. It
            sets the limits for velocity clamping.
        vh : pyswarms.backend.handlers.VelocityHandler
            a VelocityHandler object with a specified handling strategy.
            For further information see :mod:`pyswarms.backend.handlers`.
        bounds : tuple of numpy.ndarray or list, optional
            a tuple of size 2 where the first entry is the minimum bound while
            the second entry is the maximum bound. Each array must be of shape
            :code:`(dimensions,)`.

        Returns
        -------
        numpy.ndarray
            Updated velocity matrix
        """
        try:
            # Prepare parameters
            swarm_size = self.swarm.position.shape
            c1 = self.swarm.options["c1"]
            c2 = self.swarm.options["c2"]
            w = self.swarm.options["w"]
            # Compute for cognitive and social terms, moves "downhill" best, if pbest > current, will be +ive,

            cognitive = ( # moves in direction toward best from this particles last  position
                    c1
                    * np.random.uniform(0, 1, swarm_size)
                    * (self.swarm.pbest_pos - self.swarm.position)
            )
            social = (  # moves in direction of global best
                    c2
                    * np.random.uniform(0, 1, swarm_size)
                    * (self.swarm.best_pos - self.swarm.position)
            )
            # Compute temp velocity (subject to clamping if possible)
            temp_velocity = (w * self.swarm.velocity) + cognitive + social

            updated_velocity = temp_velocity # np.max(np.append(np.min(np.append(temp_velocity, 1)), -1))  # do need velocity clamp for binary vh(

            return updated_velocity
        except AttributeError:
            log.message(
                "Please pass a Swarm class. You passed {}".format(type(self.swarm))
            )
            raise
        except KeyError:
            log.message("Missing keyword in swarm.options")
            raise
        else:
            return updated_velocity

    def _compute_position(self):
        """Update the position matrix of the swarm

        This computes the next position in a binary swarm. It compares the
        sigmoid output of the velocity-matrix and compares it with a randomly
        generated matrix.

        Parameters
        ----------
        swarm: pyswarms.backend.swarms.Swarm
            a Swarm class
        """
        return (
                   #  np.random.random_sample(size=self.swarm.dimensions)
                   #  < self._sigmoid(self.swarm.velocity), if (untransformed) velocity is -ive, this will likley b 0,
                   #  if +ive, will likely be 1
               # modifed from https://pyswarms.readthedocs.io/en/latest/_modules/pyswarms/discrete/binary.html, need both n_particles and self.swarm.dimensions
                       np.random.random_sample(size=[self.n_particles, self.swarm.dimensions])
                       <  self._sigmoid(self.swarm.velocity)
               ) * 1

    def _sigmoid(self, x):
        """Helper method for the sigmoid function

        Parameters
        ----------
        x : numpy.ndarray
            Input vector for sigmoid computation

        Returns
        -------
        numpy.ndarray
            Output sigmoid computation
        """
        return 1 / (1 + np.exp(-x))


def f(x, model_template, iteration):
    n_particles = x.shape[0]
    # create models
    pop_full_bits = [x[i].tolist() for i in range(n_particles)]

    pop = Population.from_codes(model_template, iteration, pop_full_bits, ModelCode.from_full_binary)

    pop.run()

    j = [r.result.fitness for r in pop.runs]

    return np.array(j), pop.runs


# Initialize swarm, arbitrary


def run_pso(model_template: Template) -> ModelRun:
    """
    Runs Particle Swarm Optimization (PSO), based on PySwarm (https://github.com/ljvmiranda921/pyswarms)
    Called from Darwin.run_search, _run_template

    :param model_template: Model Template
    :type model_template: Template
    :return: Final/Best Model
    :rtype: Model
    """
    pop_size = options.population_size
    num_bits = int(np.sum(model_template.gene_length))
    # k is the number of positions to consider in the search
    # can be up to all, but can't be > pop size

    pso_options = {'c1': options.PSO['cognitive'],
                   'c2': options.PSO['social'],
                   'w': options.PSO['inertia'],
                   'k': options.PSO['neighbor_num'],
                   'p': options.PSO['p_norm']}
    if pso_options['k'] > options['population_size']:
        pso_options['k'] = options['population_size']
        log.message("k (neighbor_num) was > population_size, value set to population_size")

    if options.random_seed is not None:
        np.random.seed(options.random_seed)

    init_pos = np.random.randint(2, size=(pop_size, num_bits))  # looks like array is pop_size x numBits?

    runner = _PSORunner(model_template, pop_size, dimensions=num_bits, pso_options=pso_options, darwin_options=options,
                        ftol=0, ftol_iter=5, init_pos=init_pos, num_generations=0)


    # Perform optimization
    # doc for local vs global search at
    # https://pyswarms.readthedocs.io/en/development/_modules/pyswarms/discrete/binary.html?highlight=local#
    # like deap, need to break up the optimizaer so we can run in parallel, and do
    current_generation = 0
    best_cost_yet_found = options.crash_value
    cost, pos = runner.optimize(f)
    log.message(f"best fitness {str(cost)}, model {str(pos)}")
    return GlobalVars.BestRun
