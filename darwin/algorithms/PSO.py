# from https://pyswarms.readthedocs.io/en/development/examples/basic_optimization.html

r"""
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

from pyswarms.backend.operators import compute_pbest, compute_objective_function
from pyswarms.backend.topology import Ring
from pyswarms.backend.handlers import VelocityHandler
from pyswarms.base import DiscreteSwarmOptimizer
from pyswarms.utils.reporter import Reporter
# Import standard library
import logging

# Import modules
import numpy as np
import multiprocessing as mp

from collections import deque

import time

import darwin.GlobalVars as GlobalVars

from darwin.Log import log
from darwin.options import options

from darwin.Template import Template
from darwin.Model import Model
from darwin.runAllModels import init_model_list, run_all
from darwin.ModelCode import ModelCode


class BinaryPSO(DiscreteSwarmOptimizer):
    def __init__(
        self,
        n_particles,
        dimensions,
        options,
        init_pos=None,
        velocity_clamp=None,
        vh_strategy="unmodified",
        ftol=-np.inf,
        ftol_iter=1,
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
        # Initialize logger
        self.rep = Reporter(logger=logging.getLogger(__name__))
        # Assign k-neighbors and p-value as attributes
        self.k, self.p = options["k"], options["p"]
        # Initialize parent class, this creates the swarm, can set intitial position if needed
        super(BinaryPSO, self).__init__(
            n_particles=n_particles,
            dimensions=dimensions,
            binary=True,
            options=options,
            init_pos=init_pos,
            velocity_clamp=velocity_clamp,
            ftol=ftol,
            ftol_iter=ftol_iter,
        )
        # Initialize the resettable attributes
        self.reset()
        # Initialize the topology
        self.top = Ring(static=False)
        self.vh = VelocityHandler(strategy=vh_strategy)
        self.name = __name__

    def optimize(self,  objective_func, iters, model_template ):
        """Optimize the swarm for a number of iterations

        Performs the optimization to evaluate the objective
        function :code:`f` for a number of iterations :code:`iter.`

        Parameters
        ----------
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

        Returns
        -------
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
        self.rep.log("Optimize for {} iterations with {}".format(iters, self.options), lvl=log_level,)

        # Populate memory of the handlers
        self.vh.memory = self.swarm.position

        # Setup Pool of processes for parallel evaluation
        pool = None if n_processes is None else mp.Pool(n_processes)

        self.swarm.pbest_cost = np.full(self.swarm_size[0], np.inf)
        ftol_history = deque(maxlen=self.ftol_iter)
         
        for i in self.rep.pbar(iters, self.name) if verbose else range(iters):
            # Compute cost for current position and personal best
            self.swarm.current_cost = compute_objective_function(
               # self.swarm, objective_func, pool, **kwargs
                self.swarm, objective_func, pool, model_template = model_template, iteration=i
            )
            self.swarm.pbest_pos, self.swarm.pbest_cost = compute_pbest(
                self.swarm
            )
            best_cost_yet_found = np.min(self.swarm.best_cost)
            # Update gbest from neighborhood
            self.swarm.best_pos, self.swarm.best_cost = self.top.compute_gbest(
                self.swarm, p=self.p, k=self.k
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
            if i < self.ftol_iter:
                ftol_history.append(delta)
            else:
                ftol_history.append(delta)
                if all(ftol_history):
                    break
            # Perform position velocity update
            self.swarm.velocity = self.top.compute_velocity(
                self.swarm, self.velocity_clamp, self.vh
            )
            self.swarm.position = self._compute_position(self.swarm)
        # Obtain the final best_cost and the final best_position
        final_best_cost = self.swarm.best_cost.copy()
        final_best_pos = self.swarm.pbest_pos[
            self.swarm.pbest_cost.argmin()
        ].copy()
        self.rep.log(
            "Optimization finished | best cost: {}, best pos: {}".format(final_best_cost, final_best_pos),
            lvl=log_level,
        )
        # Close Pool of Processes
        if n_processes is not None:
            pool.close()

        return final_best_cost, final_best_pos

    def _compute_position(self, swarm):
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
            np.random.random_sample(size=swarm.dimensions)
            < self._sigmoid(swarm.velocity)
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
 
# size = 6
# solution = np.random.randint(0, high=2, size=size) 
 

def f(x, model_template, iteration):
    n_particles = x.shape[0]
    # create models
    models = []
    maxes = model_template.gene_max
    lengths = model_template.gene_length
    pop_full_bits = []

    for i in range(n_particles):
        pop_full_bits.append(x[i].tolist()) # needs to be list, not numpy array

    for thisFullBits,model_num in zip(pop_full_bits,range(len(pop_full_bits))):
        code = ModelCode(thisFullBits, "FullBinary", maxes, lengths)
        models.append(Model(model_template, code, model_num, iteration))

    run_all(models)  # popFullBits,model_template,0)  # argument 1 is a full GA/DEAP individual

    j = []

    for i in range(n_particles):
        j.append(models[i].fitness)

    return np.array(j)

# Initialize swarm, arbitrary 
  

def run_pso(model_template: Template) -> Model:
    """ Runs PSO, 
    Argument is model_template, which has all the needed information """
    GlobalVars.StartTime = time.time()    
    init_model_list(model_template)
    pop_size = options.population_size
    numBits = int(np.sum(model_template.gene_length))

    pso_options = {'c1': 0.5, 'c2': 0.5, 'w':0.9, 'k': numBits, 'p':2}
    # k determines how local the search is - how many neighbors does the algorithm evaluate?

    # * c1 : float
    #     cognitive parameter
    # * c2 : float
    #     social parameter
    # * w : float
    #     inertia parameter
    # * k : int
    #     number of neighbors to be considered. Must be a
    #     positive integer less than :code:`n_particles`
    # * p: int {1,2}
    #     the Minkowski p-norm to use. 1 is the
    #     sum-of-absolute values (or L1 distance) while 2 is
    #     the Euclidean (or L2) distance.
    
    optimizer = BinaryPSO(n_particles=pop_size, dimensions=numBits, options=pso_options, ftol=0, ftol_iter=5)
    # n_particles must be > k (# of neighbors evaluated)    
    # no improvement for 5 iterations

    # Perform optimization
    # doc for local vs global search at
    # https://pyswarms.readthedocs.io/en/development/_modules/pyswarms/discrete/binary.html?highlight=local#
    cost, pos = optimizer.optimize(f, iters=options['num_generations'], model_template=model_template)

    log.message(f"best fitness {str(cost)}, model {str(pos)}")
