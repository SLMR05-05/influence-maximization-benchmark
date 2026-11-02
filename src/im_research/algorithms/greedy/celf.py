from __future__ import annotations
import time
import heapq
from typing import List, Tuple, Dict

from im_research.core.interfaces import BaseAlgorithm, AlgorithmResult
from im_research.core.problem import IMProblem
from im_research.core.solution import Solution


class CELF(BaseAlgorithm):
    """
    Cost-Effective Lazy Forward (CELF) Greedy Algorithm for Influence Maximization.
    Leskovec et al. (2007) — "Cost-effective Outbreak Detection in Networks."

    Key optimization over vanilla Greedy:
    - Exploits submodularity of the influence spread function σ(S).
    - Maintains a priority queue of marginal gains.
    - Recomputes a node's marginal gain lazily only when it reaches the top.
    - Typically reduces evaluations by 700x compared to vanilla Greedy.

    Correctness: CELF produces exactly the same seed set as vanilla Greedy
    due to the submodularity property of σ(S).

    Time Complexity: O(k * R * |E|) with significant constant reduction vs Greedy.
    """
    def __init__(self):
        super().__init__(name="CELF")

    def run(self,
            problem: IMProblem,
            seed: int = 42,
            max_evaluations: int | None = None,
            max_iterations: int | None = None) -> AlgorithmResult:

        t_start = time.perf_counter()

        n = problem.num_nodes
        k = problem.k
        total_evals = 0

        # Step 1: Compute initial marginal gain for each node
        # Marginal gain of v w.r.t. empty set = σ({v})
        # Use batch_evaluate for parallel computation via OpenMP
        all_single_seeds = [[u] for u in range(n)]
        initial_spreads = problem.evaluator.batch_evaluate(all_single_seeds)
        total_evals += n

        # Priority queue: (-marginal_gain, node_id, iteration_last_computed)
        heap: List[Tuple[float, int, int]] = []
        for u in range(n):
            heapq.heappush(heap, (-initial_spreads[u], u, 0))

        selected: List[int] = []
        selected_set = set()
        current_spread = 0.0
        convergence_history = []
        lazy_recomputes = 0

        for iteration in range(k):
            best_u = None
            best_gain = -1.0

            while heap:
                neg_gain, u, last_iter = heapq.heappop(heap)

                if u in selected_set:
                    continue

                # Lazy evaluation: recompute only if this gain was computed
                # before the last seed was added (potentially stale)
                if last_iter < iteration:
                    # Recompute marginal gain: σ(S ∪ {u}) - σ(S)
                    new_spread = problem.evaluator.evaluate(selected + [u])
                    total_evals += 1
                    lazy_recomputes += 1
                    marginal = new_spread - current_spread
                    heapq.heappush(heap, (-marginal, u, iteration))
                else:
                    # Gain is still fresh — this is our best node
                    best_u = u
                    best_gain = -neg_gain
                    break

            if best_u is None:
                break

            selected.append(best_u)
            selected_set.add(best_u)
            current_spread += best_gain

            convergence_history.append({
                "iteration": iteration + 1,
                "node_added": best_u,
                "marginal_gain": best_gain,
                "cumulative_spread": current_spread,
                "evaluations_so_far": total_evals
            })

        seed_set = sorted(selected)
        solution = Solution(seed_set, fitness=current_spread)

        t_search_end = time.perf_counter()

        # Final validation with the shared evaluator's configured MC replications
        final_fitness = problem.fitness(solution)
        total_evals += 1

        t_total_end = time.perf_counter()

        return AlgorithmResult(
            algorithm_name=self.name,
            best_solution=solution,
            search_time=t_search_end - t_start,
            total_evaluations=total_evals,
            convergence_history=convergence_history,
            metadata={
                "total_time": t_total_end - t_start,
                "lazy_recomputes": lazy_recomputes,
                "total_evaluations": total_evals,
                "final_validated_fitness": final_fitness,
                "strategy": "leskovec2007_celf"
            }
        )

