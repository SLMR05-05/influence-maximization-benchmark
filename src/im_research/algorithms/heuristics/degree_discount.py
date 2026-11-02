from __future__ import annotations
import time
from typing import List, Set

from im_research.core.interfaces import BaseAlgorithm, AlgorithmResult
from im_research.core.problem import IMProblem
from im_research.core.solution import Solution


class DegreeDiscount(BaseAlgorithm):
    """
    Degree Discount Heuristic for Influence Maximization under IC model.
    Chen et al. (2009) — Efficient Influence Maximization in Social Networks.

    Key idea: after selecting node u as a seed, discount the effective degree
    of its neighbors by the number of already-selected neighbors to avoid
    redundant coverage.

    For IC model with uniform probability p, the discounted degree of v is:
        dd(v) = d(v) - 2*t(v) - (d(v) - t(v)) * t(v) * p
    where t(v) = number of already-selected neighbors of v.

    Time Complexity: O(k * |V|) — much faster than CELF while remaining
    competitive in influence quality.
    """
    def __init__(self, edge_probability: float = 0.01):
        super().__init__(name="DegreeDiscount")
        self.p = edge_probability

    def run(self,
            problem: IMProblem,
            seed: int = 42,
            max_evaluations: int | None = None,
            max_iterations: int | None = None) -> AlgorithmResult:

        t_start = time.perf_counter()

        graph = problem.graph
        n = graph.num_nodes()
        k = problem.k
        p = self.p

        row_ptr = graph.row_ptr()
        col_indices = graph.col_indices()

        # Compute out-degree for each node
        degree = [row_ptr[u + 1] - row_ptr[u] for u in range(n)]

        # t[v] = number of selected neighbors of v
        t = [0] * n
        # discounted degree score
        dd = [float(degree[u]) for u in range(n)]

        selected: List[int] = []
        selected_set: Set[int] = set()

        for _ in range(k):
            # Pick node with max discounted degree not yet selected
            best_u = max(
                (u for u in range(n) if u not in selected_set),
                key=lambda u: dd[u]
            )
            selected.append(best_u)
            selected_set.add(best_u)

            # Update discount scores for neighbors of best_u
            start, end = row_ptr[best_u], row_ptr[best_u + 1]
            for idx in range(start, end):
                v = col_indices[idx]
                if v not in selected_set:
                    t[v] += 1
                    dv = degree[v]
                    tv = t[v]
                    dd[v] = dv - 2 * tv - (dv - tv) * tv * p

        seed_set = sorted(selected)
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
                "edge_probability_p": self.p,
                "strategy": "chen2009_degree_discount"
            }
        )

