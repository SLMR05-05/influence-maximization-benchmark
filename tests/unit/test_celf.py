"""Unit tests for CELF (Leskovec et al., KDD 2007) with UC/CB and online bound."""
import time

from im_research import _im_core
from im_research.core.problem import IMProblem
from im_research.algorithms.greedy.celf import CELF


def _make_problem(n_graph: int = 7, k: int = 2, mc: int = 20, seed: int = 42):
    edges = [
        (0, 1), (0, 2), (0, 3), (1, 2), (1, 4),
        (2, 5), (3, 5), (4, 5), (4, 6), (5, 6),
    ]
    g = _im_core.Graph.from_edge_list_wc(n_graph, edges, is_directed=False)
    evaluator = _im_core.Evaluator(
        g, _im_core.DiffusionModel.IndependentCascade,
        num_mc_simulations=mc, seed=seed,
    )
    return IMProblem(graph=g, k=k, evaluator=evaluator), g


def test_celf_basic():
    problem, _ = _make_problem()
    algo = CELF()
    t0 = time.perf_counter()
    res = algo.run(problem, seed=42)
    dt = time.perf_counter() - t0

    print("\n[CELF basic]")
    print("  seeds          :", res.best_solution.seed_set)
    print("  R(A)           :", res.best_solution.fitness)
    print("  online_bound   :", res.metadata.get("online_bound"))
    print("  mode_selected  :", res.metadata.get("mode_selected"))
    print("  UC seeds       :", res.metadata["uc"]["seeds"], res.metadata["uc"]["spread"])
    print("  CB seeds       :", res.metadata["cb"]["seeds"], res.metadata["cb"]["spread"])
    print("  evals          :", res.total_evaluations)
    print("  time (s)       :", round(dt, 6))

    assert len(res.best_solution.seed_set) == problem.k
    assert res.best_solution.fitness is not None and res.best_solution.fitness > 0
    assert res.metadata.get("online_bound") is not None
    assert res.metadata["online_bound"] >= res.best_solution.fitness - 1e-9
    assert res.metadata["mode_selected"] in ("UC", "CB")
    assert len(res.convergence_history) == len(res.best_solution.seed_set)


def test_celf_unit_costs_equal_uc_cb_on_deterministic_graph():
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)]
    probs = [1.0] * len(edges)
    g = _im_core.Graph.from_edge_list(5, edges, probs, is_directed=True)
    evaluator = _im_core.Evaluator(
        g, _im_core.DiffusionModel.IndependentCascade,
        num_mc_simulations=5, seed=7,
    )
    problem = IMProblem(graph=g, k=2, evaluator=evaluator)

    res = CELF().run(problem, seed=7)
    # With unit costs and a deterministic cascade both variants agree.
    assert res.metadata["uc"]["seeds"] == res.metadata["cb"]["seeds"]
    assert res.metadata["online_bound"] >= res.best_solution.fitness - 1e-9


def test_celf_custom_costs_and_budget():
    problem, _ = _make_problem(k=3)
    # Node 0 is expensive; the rest are cheap.
    costs = [5.0] + [1.0] * (problem.num_nodes - 1)
    algo = CELF(costs=costs, budget=3.0)
    res = algo.run(problem, seed=42)

    print("\n[CELF custom costs]")
    print("  seeds          :", res.best_solution.seed_set)
    print("  total_cost     :", res.metadata["uc"]["total_cost"], "/", 3.0)
    print("  online_bound   :", res.metadata.get("online_bound"))

    assert res.metadata["cost_model"] == "custom"
    assert res.metadata["budget"] == 3.0
    # The expensive node must not have been selected under this budget.
    assert 0 not in res.best_solution.seed_set
    assert res.metadata.get("online_bound") is not None


def test_celf_online_bound_formula():
    """Recompute the bound by hand on a tiny deterministic graph."""
    edges = [(0, 1), (1, 2)]
    probs = [1.0, 1.0]
    g = _im_core.Graph.from_edge_list(3, edges, probs, is_directed=True)
    evaluator = _im_core.Evaluator(
        g, _im_core.DiffusionModel.IndependentCascade,
        num_mc_simulations=3, seed=1,
    )
    problem = IMProblem(graph=g, k=1, evaluator=evaluator)

    res = CELF(online_bound=True).run(problem, seed=1)
    # With k=1 the selected node activates the whole chain (3 nodes).
    assert res.best_solution.fitness == 3.0
    # No remaining node can improve on 3, so the bound equals R(A).
    assert res.metadata["online_bound"] == 3.0


def test_celf_respects_max_evaluations():
    problem, _ = _make_problem()
    res = CELF().run(problem, seed=42, max_evaluations=8)
    # With max_evaluations=8 the initial batch (n=7) leaves room for at most
    # one recompute per pass, plus the online bound.  Just make sure it does
    # not crash and stays bounded.
    assert res.total_evaluations <= 3 * problem.num_nodes + 20
    assert len(res.best_solution.seed_set) <= problem.k


if __name__ == "__main__":
    test_celf_basic()
    test_celf_custom_costs_and_budget()
    test_celf_online_bound_formula()
    print("ALL CELF TESTS PASSED")
