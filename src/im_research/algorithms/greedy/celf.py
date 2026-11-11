"""CELF with lazy evaluation (UC + CB) and an online influence bound.

Implements the Cost-Effective Lazy Forward (CELF) greedy algorithm of
Leskovec, Krause, Guestrin, Faloutsos, VanBriesen and Glance (KDD 2007),
together with the online upper bound on the optimal solution.

The implementation follows the interfaces already used by the project:
    * ``BaseAlgorithm`` / ``AlgorithmResult``
    * ``IMProblem`` (``problem.num_nodes``, ``problem.k``, ``problem.evaluator``)
    * the C++/Python ``Evaluator`` (``evaluate``, ``batch_evaluate``)
so it can be dropped in place of the previous ``CELF`` without touching the
GUI or the runner.
"""

from __future__ import annotations

import heapq
import math
import time
from typing import Any, Dict, List, Optional, Tuple

from im_research.core.interfaces import BaseAlgorithm, AlgorithmResult
from im_research.core.problem import IMProblem
from im_research.core.solution import Solution


class CELF(BaseAlgorithm):
    """Cost-Effective Lazy Forward (Leskovec et al., KDD 2007).

    Two lazy-forward variants are executed:
        * ``UC``  - Unit-Cost:  heap ordered by marginal gain  delta_s
        * ``CB``  - Cost-Benefit: heap ordered by ratio  delta_s / c(s)

    The variant with the larger final spread is returned.  An online upper
    bound on the optimal solution (with the configured budget) is computed
    and stored in ``result.metadata["online_bound"]``.
    """

    def __init__(
        self,
        costs: Optional[List[float]] = None,
        budget: Optional[float] = None,
        online_bound: bool = True,
    ):
        super().__init__(name="CELF")
        self.costs = costs
        self.budget = budget
        self.online_bound = online_bound

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #
    def _resolve_costs_and_budget(self, problem: IMProblem):
        n = problem.num_nodes
        if self.costs is None:
            costs = [1.0] * n
        else:
            if len(self.costs) != n:
                raise ValueError(
                    f"costs must have length {n}, got {len(self.costs)}"
                )
            costs = [float(c) for c in self.costs]

        if self.budget is None:
            # Default budget = k seeds under unit cost.  For non-unit costs the
            # caller is expected to pass an explicit budget.
            if all(abs(c - 1.0) < 1e-12 for c in costs):
                budget = float(problem.k)
            else:
                budget = float(problem.k)
        else:
            budget = float(self.budget)

        # Guard against non-positive costs.
        costs = [c if c > 0.0 else 1.0 for c in costs]
        if budget <= 0.0:
            budget = float(problem.k)
        return costs, budget

    def _push(self, heap: List, key: float, node: int, delta: float, flag: int):
        # heapq is a min-heap; negate the key to obtain a max-heap.
        heapq.heappush(heap, (-key, node, float(delta), int(flag)))

    # ------------------------------------------------------------------ #
    #  Lazy Forward                                                       #
    # ------------------------------------------------------------------ #
    def _lazy_forward(
        self,
        problem: IMProblem,
        costs: List[float],
        budget: float,
        mode: str,
        max_evaluations: Optional[int],
    ) -> Dict[str, Any]:
        """Run one lazy-forward pass.

        ``mode`` is either ``"UC"`` (unit-cost, heap by delta) or ``"CB"``
        (cost-benefit, heap by delta / cost).
        """
        if mode not in ("UC", "CB"):
            raise ValueError(f"Unknown lazy-forward mode: {mode}")

        evaluator = problem.evaluator
        n = problem.num_nodes
        total_evals = 0
        lazy_recomputes = 0

        # Initial marginal gains w.r.t. the empty set: delta_s = R({s}).
        # R(empty set) is 0 by convention.
        if max_evaluations is not None and total_evals + n > max_evaluations:
            # Evaluate as many as the budget allows, the rest stay at 0.0.
            initial = [0.0] * n
            affordable = max(0, max_evaluations - total_evals)
            for u in range(min(n, affordable)):
                initial[u] = float(evaluator.evaluate([u]))
                total_evals += 1
        else:
            initial = [float(v) for v in evaluator.batch_evaluate([[u] for u in range(n)])]
            total_evals += n

        heap: List[Tuple[float, int, float, int]] = []
        for u in range(n):
            delta = float(initial[u])
            cost_u = float(costs[u])
            ratio = delta / cost_u if cost_u > 0.0 else (float("inf") if delta >= 0 else float("-inf"))
            key = delta if mode == "UC" else ratio
            self._push(heap, key, u, delta, 0)

        selected: List[int] = []
        selected_set = set()
        total_cost = 0.0
        current_spread = 0.0
        current_step = 0
        history: List[Dict[str, Any]] = []

        while heap and total_cost < budget + 1e-12:
            if max_evaluations is not None and total_evals >= max_evaluations:
                break

            neg_key, u, delta, flag = heapq.heappop(heap)
            if u in selected_set:
                continue

            cost_u = float(costs[u])
            if cost_u <= 0.0:
                cost_u = 1.0

            # Does this node still fit the remaining budget?
            if total_cost + cost_u > budget + 1e-12:
                continue

            if flag == current_step:
                # Fresh gain -> select.
                selected.append(u)
                selected_set.add(u)
                total_cost += cost_u
                current_spread += float(delta)
                current_step += 1
                history.append(
                    {
                        "iteration": current_step,
                        "node_added": u,
                        "marginal_gain": float(delta),
                        "cumulative_spread": float(current_spread),
                        "total_cost": float(total_cost),
                        "evaluations_so_far": total_evals,
                    }
                )
            else:
                # Stale gain -> recompute lazily.
                if max_evaluations is not None and total_evals + 1 > max_evaluations:
                    # Put it back and stop; cannot afford another evaluation.
                    self._push(heap, -neg_key, u, delta, flag)
                    break

                new_spread = float(evaluator.evaluate(selected + [u]))
                total_evals += 1
                lazy_recomputes += 1
                marginal = new_spread - current_spread
                ratio = marginal / cost_u if cost_u > 0.0 else (
                    float("inf") if marginal >= 0 else float("-inf")
                )
                key = marginal if mode == "UC" else ratio
                self._push(heap, key, u, marginal, current_step)

        return {
            "mode": mode,
            "seeds": sorted(selected),
            "spread": float(current_spread),
            "total_cost": float(total_cost),
            "evaluations": int(total_evals),
            "lazy_recomputes": int(lazy_recomputes),
            "history": history,
        }

    # ------------------------------------------------------------------ #
    #  Online upper bound                                                #
    # ------------------------------------------------------------------ #
    def _get_online_bound(
        self,
        problem: IMProblem,
        selected: List[int],
        costs: List[float],
        budget: float,
    ) -> Tuple[float, Dict[str, Any]]:
        """Compute the online upper bound (Leskovec et al., Eq. for OPT).

        OPT <= R(A) + sum_{i=1}^{k-1} delta_{s_i} + lambda * delta_{s_k}
        where the s_i are the (not-yet-selected) nodes sorted by
        delta_s / c(s) in decreasing order, k is the cut point satisfying
        sum_{i=1}^{k-1} c(s_i) <= B < sum_{i=1}^{k} c(s_i), and
        lambda = (B - sum_{i=1}^{k-1} c(s_i)) / c(s_k).
        """
        evaluator = problem.evaluator
        n = problem.num_nodes
        selected_set = set(selected)

        remaining = [s for s in range(n) if s not in selected_set]
        if not remaining:
            r_a = float(evaluator.evaluate(list(selected))) if selected else 0.0
            return r_a, {"cut_node": None, "lambda": 0.0, "remaining": 0}

        # Marginal gain of adding each remaining node to A.
        seed_sets = [list(selected) + [s] for s in remaining]
        spreads = [float(v) for v in evaluator.batch_evaluate(seed_sets)]
        r_a = float(evaluator.evaluate(list(selected))) if selected else 0.0
        deltas = [sp - r_a for sp in spreads]

        # Sort remaining nodes by ratio delta / cost, decreasing.
        def ratio_of(idx: int) -> float:
            c = costs[remaining[idx]]
            if c <= 0.0:
                c = 1.0
            d = deltas[idx]
            if c == 0.0:
                return float("inf") if d >= 0 else float("-inf")
            return d / c

        order = sorted(range(len(remaining)), key=ratio_of, reverse=True)
        sorted_nodes = [remaining[i] for i in order]
        sorted_deltas = [deltas[i] for i in order]
        sorted_costs = [float(costs[s]) for s in sorted_nodes]

        cumulative = 0.0
        cut = None
        for i, c in enumerate(sorted_costs):
            if cumulative + c > budget + 1e-12:
                cut = i
                break
            cumulative += c

        if cut is None:
            # Everything fits inside the budget.
            bound = r_a + sum(sorted_deltas)
            lambda_val = 0.0
            cut_node = None
        else:
            cut_node = sorted_nodes[cut]
            delta_k = sorted_deltas[cut]
            cost_k = sorted_costs[cut]
            lambda_val = (budget - cumulative) / cost_k if cost_k > 0.0 else 0.0
            lambda_val = max(0.0, min(1.0, lambda_val))
            bound = r_a + sum(sorted_deltas[:cut]) + lambda_val * delta_k

        # Guard against MC noise producing a bound below R(A).
        bound = max(r_a, bound)

        details = {
            "R_A": float(r_a),
            "budget": float(budget),
            "cut_node": cut_node,
            "lambda": float(lambda_val),
            "cumulative_cost_before_cut": float(cumulative),
            "sum_deltas_before_cut": float(sum(sorted_deltas[:cut])) if cut is not None else float(sum(sorted_deltas)),
            "num_remaining": len(remaining),
        }
        return float(bound), details

    # ------------------------------------------------------------------ #
    #  Main entry                                                        #
    # ------------------------------------------------------------------ #
    def run(
        self,
        problem: IMProblem,
        seed: int = 42,
        max_evaluations: Optional[int] = None,
        max_iterations: Optional[int] = None,
    ) -> AlgorithmResult:
        t_start = time.perf_counter()

        costs, budget = self._resolve_costs_and_budget(problem)
        eval_budget = max_evaluations

        uc_result = self._lazy_forward(problem, costs, budget, "UC", eval_budget)
        cb_result = self._lazy_forward(problem, costs, budget, "CB", eval_budget)

        if uc_result["spread"] >= cb_result["spread"]:
            chosen = uc_result
            chosen_mode = "UC"
        else:
            chosen = cb_result
            chosen_mode = "CB"

        total_evals = uc_result["evaluations"] + cb_result["evaluations"]

        online_bound_value = None
        bound_details: Dict[str, Any] = {}
        if self.online_bound:
            online_bound_value, bound_details = self._get_online_bound(
                problem, chosen["seeds"], costs, budget
            )
            total_evals += len([s for s in range(problem.num_nodes) if s not in set(chosen["seeds"])]) + (1 if chosen["seeds"] else 0)

        t_search_end = time.perf_counter()

        seed_set = sorted(chosen["seeds"])
        solution = Solution(seed_set, fitness=chosen["spread"])

        # Final validation with the shared evaluator (matches prior CELF behaviour).
        try:
            final_fitness = float(problem.fitness(solution))
            total_evals += 1
        except Exception:
            final_fitness = float(chosen["spread"])

        t_total_end = time.perf_counter()

        convergence_history = chosen["history"]

        metadata: Dict[str, Any] = {
            "total_time": t_total_end - t_start,
            "lazy_recomputes": chosen["lazy_recomputes"],
            "total_evaluations": total_evals,
            "final_validated_fitness": final_fitness,
            "strategy": "leskovec2007_celf_uc_cb_online_bound",
            "mode_selected": chosen_mode,
            "budget": float(budget),
            "cost_model": "unit" if all(abs(c - 1.0) < 1e-12 for c in costs) else "custom",
            "uc": {
                "seeds": uc_result["seeds"],
                "spread": uc_result["spread"],
                "total_cost": uc_result["total_cost"],
                "evaluations": uc_result["evaluations"],
                "lazy_recomputes": uc_result["lazy_recomputes"],
            },
            "cb": {
                "seeds": cb_result["seeds"],
                "spread": cb_result["spread"],
                "total_cost": cb_result["total_cost"],
                "evaluations": cb_result["evaluations"],
                "lazy_recomputes": cb_result["lazy_recomputes"],
            },
        }
        if online_bound_value is not None:
            metadata["online_bound"] = float(online_bound_value)
            metadata["online_bound_details"] = bound_details

        return AlgorithmResult(
            algorithm_name=self.name,
            best_solution=solution,
            search_time=t_search_end - t_start,
            total_evaluations=total_evals,
            convergence_history=convergence_history,
            metadata=metadata,
        )
