from __future__ import annotations
import time
from typing import List

from im_research.core.interfaces import BaseAlgorithm, AlgorithmResult
from im_research.core.problem import IMProblem
from im_research.core.solution import Solution


class DegreeCentrality(BaseAlgorithm):
    """
    Degree Centrality Heuristic for Influence Maximization.
    Selects top-k nodes with the highest out-degree in the graph.
    Deterministic: always produces the same seed set regardless of random seed.
    Time Complexity: O(|V| log k)
    """
    def __init__(self):
        super().__init__(name="Degree")

    def run(self,
            problem: IMProblem,
            seed: int = 42,
            max_evaluations: int | None = None,
            max_iterations: int | None = None) -> AlgorithmResult:

        t_start = time.perf_counter()

        graph = problem.graph
        n = graph.num_nodes()
        k = problem.k

        # Compute out-degree for each node directly from CSR row_ptr
        row_ptr = graph.row_ptr()
        degrees = [(row_ptr[u + 1] - row_ptr[u], u) for u in range(n)]
        degrees.sort(reverse=True)

        seed_set = sorted([u for _, u in degrees[:k]])
        solution = Solution(seed_set)

        t_search_end = time.perf_counter()

        # Evaluate the final seed set using the shared C++ Evaluator
        fitness = problem.fitness(solution)

        t_total_end = time.perf_counter()

        return AlgorithmResult(
            algorithm_name=self.name,
            best_solution=solution,
            search_time=t_search_end - t_start,
            total_evaluations=1,
            metadata={
                "total_time": t_total_end - t_start,
                "strategy": "top_k_by_out_degree"
            }
        )

