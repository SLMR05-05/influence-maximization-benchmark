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

def test_weighted_cascade_graph_and_replications():
    edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 4), (2, 5), (3, 5), (4, 5), (4, 6), (5, 6)]
    g = _im_core.Graph.from_edge_list_wc(7, edges, is_directed=False)
    assert g.num_nodes() == 7
    assert g.num_edges() == 20
    assert abs(g.edge_prob(0, 1) - 1.0 / 3.0) < 1e-6
    assert abs(g.edge_prob(0, 3) - 0.5) < 1e-6

    evaluator = _im_core.Evaluator(
        g, _im_core.DiffusionModel.IndependentCascade,
        num_mc_simulations=20, seed=42,
    )
    spreads = evaluator.evaluate_replications([0, 1], 20)
    assert len(spreads) == 20
    assert all(2 <= spread <= 7 for spread in spreads)


def test_cpp_genetic_algorithm():
    edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 4), (2, 5), (3, 5), (4, 5), (4, 6), (5, 6)]
    g = _im_core.Graph.from_edge_list_wc(7, edges, is_directed=False)
    config = _im_core.GAConfig()
    config.k = 2
    config.population_size = 10
    config.max_generations = 3
    config.tournament_size = 3
    config.crossover_rate = 0.9
    config.mutation_rate = 0.1
    config.elitism = 1
    config.num_mc_simulations = 20
    config.seed = 42

    algorithm = _im_core.GeneticAlgorithm(
        g, _im_core.DiffusionModel.IndependentCascade, config,
    )
    result = algorithm.run()
    assert len(result.best_seeds) == 2
    assert result.best_fitness >= 2.0
    assert result.generations_completed == 3
    assert result.total_evaluations > 0
    assert len(result.best_fitness_history) == 4
    assert len(result.top_individuals) <= 5


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
    test_weighted_cascade_graph_and_replications()
    test_cpp_genetic_algorithm()
    test_problem_and_population_integration()
    print("ALL TESTS PASSED SUCCESSFULLY!")
