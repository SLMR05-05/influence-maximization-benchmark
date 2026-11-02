from __future__ import annotations
from typing import List, Any
import numpy as np
from .solution import Solution, Population

class IMProblem:
    """
    Pygmo-inspired Problem encapsulation for Influence Maximization.
    Decouples the objective function and diffusion evaluation from optimization algorithms.
    """
    def __init__(self,
                 graph: Any,
                 k: int,
                 evaluator: Any,
                 name: str = "InfluenceMaximization"):
        self.graph = graph
        self.k = k
        self.evaluator = evaluator
        self.name = name

    @property
    def num_nodes(self) -> int:
        return self.graph.num_nodes()

    def fitness(self, sol_or_seeds: Solution | List[int]) -> float:
        """
        Evaluates a single seed set and returns its influence spread.
        """
        seeds = sol_or_seeds.seed_set if isinstance(sol_or_seeds, Solution) else sol_or_seeds
        score = self.evaluator.evaluate(seeds)
        if isinstance(sol_or_seeds, Solution):
            sol_or_seeds.fitness = score
        return score

    def batch_fitness(self, population: Population | List[Solution]) -> List[float]:
        """
        Pygmo-style batch fitness evaluation.
        Transfers candidate seed sets to C++ Core to evaluate concurrently across all CPU threads.
        """
        individuals = population.individuals if isinstance(population, Population) else population
        seed_sets = [ind.seed_set for ind in individuals]
        
        scores = self.evaluator.batch_evaluate(seed_sets)
        for ind, score in zip(individuals, scores):
            ind.fitness = score
            
        return scores

    def create_random_solution(self, rng: np.random.Generator | None = None) -> Solution:
        """Generates a random valid seed set with strictly k distinct nodes."""
        if rng is not None:
            chosen = rng.choice(self.num_nodes, size=self.k, replace=False)
        else:
            chosen = np.random.choice(self.num_nodes, size=self.k, replace=False)
        return Solution(sorted(chosen.tolist()))

    def create_random_population(self, pop_size: int, rng: np.random.Generator | None = None) -> Population:
        """Generates an initial random population."""
        solutions = [self.create_random_solution(rng) for _ in range(pop_size)]
        return Population(solutions)

