"""Unit tests for all Influence Maximization algorithms (Heuristics, Greedy, GA)."""
import pytest
from im_research import _im_core
from im_research.core.problem import IMProblem
from im_research.algorithms.heuristics.degree import DegreeCentrality
from im_research.algorithms.heuristics.degree_discount import DegreeDiscount
from im_research.algorithms.heuristics.pagerank import PageRankHeuristic
from im_research.algorithms.greedy.celf import CELF
from im_research.algorithms.evolutionary.ga import BaselineGA


@pytest.fixture
def karate_problem():
    # Build standard karate graph with 34 nodes
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8),
        (0, 10), (0, 11), (0, 12), (0, 13), (0, 17), (0, 19), (0, 21), (0, 31),
        (1, 2), (1, 3), (1, 7), (1, 13), (1, 17), (1, 19), (1, 21), (1, 30),
        (33, 8), (33, 9), (33, 13), (33, 14), (33, 15), (33, 18), (33, 20),
        (33, 22), (33, 23), (33, 26), (33, 27), (33, 28), (33, 29), (33, 30),
        (33, 31), (33, 32)
    ]
    probs = [0.1] * len(edges)
    # Undirected graph
    g = _im_core.Graph.from_edge_list(34, edges, probs, is_directed=False)
    evaluator = _im_core.Evaluator(g, _im_core.DiffusionModel.IndependentCascade, num_mc_simulations=100, seed=42)
    return IMProblem(graph=g, evaluator=evaluator, k=3)


def test_degree_centrality(karate_problem):
    algo = DegreeCentrality()
    res = algo.run(karate_problem, seed=42)
    assert len(res.best_solution.seed_set) == 3
    assert 0 in res.best_solution.seed_set or 33 in res.best_solution.seed_set
    assert res.best_solution.fitness > 0


def test_degree_discount(karate_problem):
    algo = DegreeDiscount(edge_probability=0.1)
    res = algo.run(karate_problem, seed=42)
    assert len(res.best_solution.seed_set) == 3
    assert res.best_solution.fitness > 0


def test_pagerank(karate_problem):
    algo = PageRankHeuristic(damping=0.85, max_iter=20)
    res = algo.run(karate_problem, seed=42)
    assert len(res.best_solution.seed_set) == 3
    assert res.best_solution.fitness > 0


def test_celf(karate_problem):
    algo = CELF()
    res = algo.run(karate_problem, seed=42)
    assert len(res.best_solution.seed_set) == 3
    assert res.best_solution.fitness > 0


def test_baseline_ga(karate_problem):
    algo = BaselineGA(pop_size=10, max_generations=5, elitism=1)
    res = algo.run(karate_problem, seed=42)
    assert len(res.best_solution.seed_set) == 3
    assert res.best_solution.fitness > 0
    assert len(res.convergence_history) == 6


