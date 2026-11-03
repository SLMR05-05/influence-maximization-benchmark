from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import time
from .problem import IMProblem
from .solution import Solution

class AlgorithmResult:
    """
    Standardized result object returned by all algorithms.
    Ensures identical tracking of solution quality, runtime, and convergence metrics.
    """
    def __init__(self,
                 algorithm_name: str,
                 best_solution: Solution,
                 search_time: float,
                 total_evaluations: int,
                 convergence_history: List[Dict[str, Any]] | None = None,
                 metadata: Dict[str, Any] | None = None):
        self.algorithm_name = algorithm_name
        self.best_solution = best_solution
        self.search_time = search_time
        self.total_evaluations = total_evaluations
        self.convergence_history = convergence_history or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm_name,
            "seed_set": self.best_solution.seed_set,
            "best_fitness": self.best_solution.fitness,
            "k": len(self.best_solution.seed_set),
            "search_time_sec": self.search_time,
            "total_evaluations": self.total_evaluations,
            "metadata": self.metadata
        }


class BaseAlgorithm(ABC):
    """
    Pygmo-inspired Abstract Base Class for all Influence Maximization algorithms
    (Heuristics, Greedy, GA, PSO, ACO).
    """
    def __init__(self, name: str, config: Dict[str, Any] | None = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    def run(self,
            problem: IMProblem,
            seed: int = 42,
            max_evaluations: int | None = None,
            max_iterations: int | None = None) -> AlgorithmResult:
        """
        Executes the algorithm on the given problem within the standardized budget.
        """
        pass

