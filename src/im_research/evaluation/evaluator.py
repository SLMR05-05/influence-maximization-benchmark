from __future__ import annotations
from typing import List, Set, Any
import random
import time

try:
    from im_research import _im_core
    CPP_CORE_AVAILABLE = True
except ImportError:
    CPP_CORE_AVAILABLE = False
    _im_core = None


class PythonReferenceEvaluator:
    """
    Pure Python Reference Evaluator for Independent Cascade diffusion.
    STRICTLY used for unit testing and verifying the correctness of C++ Core.
    NEVER used for performance benchmarking.
    """
    def __init__(self, num_nodes: int, adj_list: List[List[tuple[int, float]]], num_mc_simulations: int = 1000, seed: int = 42):
        self.num_nodes = num_nodes
        self.adj_list = adj_list
        self.num_mc_simulations = num_mc_simulations
        self.seed = seed
        self.rng = random.Random(seed)
        self.total_evaluations = 0

    def evaluate(self, seed_set: List[int]) -> float:
        self.total_evaluations += 1
        if not seed_set or self.num_mc_simulations <= 0:
            return 0.0

        total_activated = 0
        for _ in range(self.num_mc_simulations):
            visited: Set[int] = set(seed_set)
            queue = list(seed_set)
            
            while queue:
                u = queue.pop(0)
                if u < len(self.adj_list):
                    for v, p in self.adj_list[u]:
                        if v not in visited:
                            if self.rng.random() <= p:
                                visited.add(v)
                                queue.append(v)
            total_activated += len(visited)

        return total_activated / self.num_mc_simulations

    def batch_evaluate(self, seed_sets: List[List[int]]) -> List[float]:
        return [self.evaluate(s) for s in seed_sets]


def create_evaluator(graph: Any,
                     model: str = "IC",
                     num_mc: int = 1000,
                     seed: int = 42,
                     force_python: bool = False):
    """
    Factory function to instantiate the standard Evaluator.
    Defaults to high-performance C++ Evaluator if compiled.
    """
    if CPP_CORE_AVAILABLE and not force_python:
        cpp_model = _im_core.DiffusionModel.IndependentCascade if model.upper() == "IC" else _im_core.DiffusionModel.LinearThreshold
        return _im_core.Evaluator(graph, cpp_model, num_mc, seed)
    else:
        # Fallback to pure python reference
        # Extract adjacency from graph object
        adj: List[List[tuple[int, float]]] = [[] for _ in range(graph.num_nodes())]
        row_ptr = graph.row_ptr()
        col_indices = graph.col_indices()
        edge_probs = graph.edge_probs()
        for u in range(graph.num_nodes()):
            start = row_ptr[u]
            end = row_ptr[u + 1]
            for idx in range(start, end):
                adj[u].append((col_indices[idx], edge_probs[idx]))
        return PythonReferenceEvaluator(graph.num_nodes(), adj, num_mc, seed)

