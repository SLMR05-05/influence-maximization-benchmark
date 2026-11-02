from __future__ import annotations
import random
from typing import List, Set, Iterable
import numpy as np

class Solution:
    """
    Represents a discrete candidate solution for Influence Maximization:
    A seed set S containing exactly k distinct node IDs.
    """
    def __init__(self, seed_set: Iterable[int], fitness: float | None = None):
        self.seed_set: List[int] = sorted(list(set(seed_set)))
        self.fitness: float | None = fitness
        self.metadata: dict = {}

    @property
    def k(self) -> int:
        return len(self.seed_set)

    def is_valid(self, expected_k: int, max_node_id: int) -> bool:
        if len(self.seed_set) != expected_k:
            return False
        return all(0 <= node < max_node_id for node in self.seed_set)

    def repair(self, target_k: int, num_nodes: int, rng: random.Random | None = None) -> Solution:
        """
        Repairs a candidate solution if it contains duplicate or missing nodes
        to ensure strictly target_k unique nodes.
        """
        r = rng or random
        unique_nodes = set(n for n in self.seed_set if 0 <= n < num_nodes)
        
        while len(unique_nodes) < target_k:
            candidate = r.randint(0, num_nodes - 1)
            unique_nodes.add(candidate)
            
        if len(unique_nodes) > target_k:
            unique_nodes = set(r.sample(list(unique_nodes), target_k))
            
        self.seed_set = sorted(list(unique_nodes))
        return self

    def __repr__(self) -> str:
        fit_str = f"{self.fitness:.4f}" if self.fitness is not None else "None"
        return f"Solution(k={len(self.seed_set)}, fitness={fit_str}, seeds={self.seed_set[:5]}{'...' if len(self.seed_set) > 5 else ''})"


class Population:
    """
    Pygmo-inspired Population container of Solutions.
    Provides tracking of best individual, mean fitness, and population diversity.
    """
    def __init__(self, solutions: List[Solution] | None = None):
        self.individuals: List[Solution] = solutions or []

    def __len__(self) -> int:
        return len(self.individuals)

    def __getitem__(self, idx: int) -> Solution:
        return self.individuals[idx]

    def append(self, sol: Solution):
        self.individuals.append(sol)

    @property
    def best(self) -> Solution | None:
        evaluated = [s for s in self.individuals if s.fitness is not None]
        if not evaluated:
            return None
        return max(evaluated, key=lambda s: s.fitness)

    @property
    def mean_fitness(self) -> float:
        evaluated = [s.fitness for s in self.individuals if s.fitness is not None]
        if not evaluated:
            return 0.0
        return float(np.mean(evaluated))

    def diversity_jaccard(self) -> float:
        """
        Computes pairwise mean Jaccard distance between individuals to measure population diversity:
        Distance(S1, S2) = 1 - |S1 ∩ S2| / |S1 ∪ S2|.
        """
        n = len(self.individuals)
        if n < 2:
            return 0.0
        
        total_dist = 0.0
        count = 0
        sets = [set(s.seed_set) for s in self.individuals]
        for i in range(n):
            for j in range(i + 1, n):
                inter = len(sets[i] & sets[j])
                union = len(sets[i] | sets[j])
                dist = 1.0 - (inter / union if union > 0 else 0.0)
                total_dist += dist
                count += 1
        return total_dist / count if count > 0 else 0.0

