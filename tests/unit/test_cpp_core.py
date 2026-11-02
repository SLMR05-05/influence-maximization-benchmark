import sys
import os

try:
    import pytest
except ImportError:
    pytest = None

# Ensure src is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from im_research import _im_core
from im_research.core.solution import Solution, Population
from im_research.core.problem import IMProblem

def test_cpp_core_bindings():
    assert _im_core is not None
    assert hasattr(_im_core, "Graph")
    assert hasattr(_im_core, "Evaluator")
    assert hasattr(_im_core, "DiffusionModel")

def test_graph_construction():
    edges = [(0, 1), (0, 2), (1, 3), (2, 4)]
    probs = [0.5, 0.5, 0.8, 0.8]
    g = _im_core.Graph.from_edge_list(5, edges, probs, is_directed=True)
    assert g.num_nodes() == 5
    assert g.num_edges() == 4
    assert g.out_degree(0) == 2
    assert g.out_degree(1) == 1

def test_single_and_batch_evaluation():
    edges = [(0, 1), (0, 2), (1, 3), (2, 4)]
    probs = [0.5, 0.5, 0.8, 0.8]
    g = _im_core.Graph.from_edge_list(5, edges, probs, is_directed=True)
    evaluator = _im_core.Evaluator(g, _im_core.DiffusionModel.IndependentCascade, num_mc_simulations=500, seed=42)

    # Evaluating node 0 must yield >= 1.0 (at least itself activated)
    spread_0 = evaluator.evaluate([0])
    assert spread_0 >= 1.0
    assert spread_0 <= 5.0

    # Batch evaluate
    batch_seeds = [[0], [1], [2], [3], [4], [0, 1]]
    batch_results = evaluator.batch_evaluate(batch_seeds)
    assert len(batch_results) == len(batch_seeds)
    for res in batch_results:
        assert 1.0 <= res <= 5.0

def test_problem_and_population_integration():
    edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
    probs = [1.0, 1.0, 1.0, 1.0] # Deterministic cascade
    g = _im_core.Graph.from_edge_list(5, edges, probs, is_directed=True)
    evaluator = _im_core.Evaluator(g, _im_core.DiffusionModel.IndependentCascade, num_mc_simulations=10, seed=42)
    
    problem = IMProblem(graph=g, k=2, evaluator=evaluator)
    pop = problem.create_random_population(pop_size=6)
    assert len(pop) == 6
    
    # Test pygmo-style batch evaluation across population
    scores = problem.batch_fitness(pop)
    assert len(scores) == 6
    assert pop.best is not None
    assert pop.best.fitness is not None
    assert pop.best.fitness >= 2.0 # k=2 seeds activate at least themselves

if __name__ == "__main__":
    test_cpp_core_bindings()
    test_graph_construction()
    test_single_and_batch_evaluation()
    test_problem_and_population_integration()
    print("ALL TESTS PASSED SUCCESSFULLY!")
