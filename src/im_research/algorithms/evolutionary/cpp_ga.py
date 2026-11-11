from __future__ import annotations

import time

from im_research.core.interfaces import AlgorithmResult, BaseAlgorithm
from im_research.core.problem import IMProblem
from im_research.core.solution import Solution

try:
    from im_research import _im_core
except ImportError:
    _im_core = None


class CppBaselineGA(BaseAlgorithm):
    def __init__(self,
                 pop_size: int = 50,
                 max_generations: int = 100,
                 crossover_rate: float = 0.9,
                 mutation_rate: float = 0.1,
                 tournament_size: int = 5,
                 elitism: int = 2,
                 num_mc: int | None = None):
        super().__init__(name="BaselineGA")
        self.pop_size = int(pop_size)
        self.max_generations = int(max_generations)
        self.crossover_rate = float(crossover_rate)
        self.mutation_rate = float(mutation_rate)
        self.tournament_size = int(tournament_size)
        self.elitism = int(elitism)
        self.num_mc = None if num_mc is None else int(num_mc)

    def run(self,
            problem: IMProblem,
            seed: int = 42,
            max_evaluations: int | None = None,
            max_iterations: int | None = None) -> AlgorithmResult:
        if _im_core is None:
            raise RuntimeError(
                "C++ core (_im_core) is not built. Build the pybind11 extension first."
            )

        config = _im_core.GAConfig()
        config.k = int(problem.k)
        config.population_size = self.pop_size
        config.max_generations = int(max_iterations or self.max_generations)
        config.tournament_size = self.tournament_size
        config.crossover_rate = self.crossover_rate
        config.mutation_rate = self.mutation_rate
        config.elitism = self.elitism
        config.seed = int(seed)
        config.max_evaluations = int(max_evaluations or 0)

        if self.num_mc is not None:
            config.num_mc_simulations = max(1, self.num_mc)
        elif hasattr(problem.evaluator, "num_mc_simulations"):
            config.num_mc_simulations = max(
                1, int(problem.evaluator.num_mc_simulations())
            )
        else:
            config.num_mc_simulations = 100

        if hasattr(problem.evaluator, "model"):
            model = problem.evaluator.model()
        else:
            model = _im_core.DiffusionModel.IndependentCascade

        started = time.perf_counter()
        algorithm = _im_core.GeneticAlgorithm(problem.graph, model, config)
        result = algorithm.run()
        elapsed = time.perf_counter() - started

        history = []
        for generation, (best, mean, diversity) in enumerate(zip(
            result.best_fitness_history,
            result.mean_fitness_history,
            result.diversity_history,
        )):
            history.append({
                "generation": generation,
                "best_fitness": float(best),
                "mean_fitness": float(mean),
                "diversity": float(diversity),
            })

        top_individuals = []
        for rank, individual in enumerate(result.top_individuals, start=1):
            seeds = [int(node) for node in individual.seeds]
            fitness = float(individual.fitness)
            top_individuals.append({
                "rank": rank,
                "seeds": seeds,
                "fitness": fitness,
                "spread": fitness,
            })

        best_solution = Solution(
            [int(node) for node in result.best_seeds],
            fitness=float(result.best_fitness),
        )

        return AlgorithmResult(
            algorithm_name=self.name,
            best_solution=best_solution,
            search_time=float(result.search_time_seconds),
            total_evaluations=int(result.total_evaluations),
            convergence_history=history,
            metadata={
                "total_time": elapsed,
                "pop_size": config.population_size,
                "generations_completed": int(result.generations_completed),
                "crossover_rate": config.crossover_rate,
                "mutation_rate": config.mutation_rate,
                "tournament_size": config.tournament_size,
                "elitism": config.elitism,
                "num_mc_simulations": config.num_mc_simulations,
                "total_mc_simulations": int(result.total_mc_simulations),
                "random_seed": int(seed),
                "top_individuals": top_individuals,
                "backend": "cpp",
            },
        )
