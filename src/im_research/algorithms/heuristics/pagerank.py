from __future__ import annotations
import time
from typing import List, Dict

from im_research.core.interfaces import BaseAlgorithm, AlgorithmResult
from im_research.core.problem import IMProblem
from im_research.core.solution import Solution


class PageRankHeuristic(BaseAlgorithm):
    """
    PageRank-based Heuristic for Influence Maximization.
    Selects top-k nodes by PageRank score computed directly from the CSR graph.

    PageRank models the probability that a random surfer lands on a node,
    capturing both direct and indirect influence potential in the network.

    Algorithm: Power Iteration
        PR(v) = (1 - d) / N  +  d * Σ_{u ∈ In(v)} PR(u) / out_degree(u)
    where d = damping factor (typically 0.85), N = number of nodes.

    Time Complexity: O(iterations * |E|)
    """
    def __init__(self, damping: float = 0.85, max_iter: int = 100, tol: float = 1e-6):
        super().__init__(name="PageRank")
        self.damping = damping
        self.max_iter = max_iter
        self.tol = tol

    def run(self,
            problem: IMProblem,
            seed: int = 42,
            max_evaluations: int | None = None,
            max_iterations: int | None = None) -> AlgorithmResult:

        t_start = time.perf_counter()

        graph = problem.graph
        n = graph.num_nodes()
        k = problem.k
        d = self.damping

        row_ptr = graph.row_ptr()
        col_indices = graph.col_indices()

        # Out-degree for dangling node handling
        out_degree = [row_ptr[u + 1] - row_ptr[u] for u in range(n)]

        # Build reverse adjacency (in-neighbors) for PageRank computation
        # in_neighbors[v] = list of (u, out_degree_u) for edges u -> v
        in_neighbors: List[List[tuple]] = [[] for _ in range(n)]
        for u in range(n):
            if out_degree[u] > 0:
                for idx in range(row_ptr[u], row_ptr[u + 1]):
                    v = col_indices[idx]
                    in_neighbors[v].append((u, out_degree[u]))

        # Power Iteration
        pr = [1.0 / n] * n
        base_score = (1.0 - d) / n

        for iteration in range(self.max_iter):
            new_pr = [base_score] * n

            for v in range(n):
                for (u, deg_u) in in_neighbors[v]:
                    new_pr[v] += d * pr[u] / deg_u

            # Convergence check (L1 norm)
            delta = sum(abs(new_pr[v] - pr[v]) for v in range(n))
            pr = new_pr
            if delta < self.tol:
                break

        # Select top-k by PageRank score
        ranked = sorted(range(n), key=lambda u: pr[u], reverse=True)
        seed_set = sorted(ranked[:k])
        solution = Solution(seed_set)

        t_search_end = time.perf_counter()
        fitness = problem.fitness(solution)
        t_total_end = time.perf_counter()

        return AlgorithmResult(
            algorithm_name=self.name,
            best_solution=solution,
            search_time=t_search_end - t_start,
            total_evaluations=1,
            metadata={
                "total_time": t_total_end - t_start,
                "damping": self.damping,
                "converged_iterations": iteration + 1,
                "strategy": "pagerank_power_iteration"
            }
        )

