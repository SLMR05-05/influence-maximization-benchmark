"""
Improved Genetic Algorithm (IGA) for Influence Maximization.

Key Contributions / Novel Mechanisms:
1. Degree-Biased / Community-Aware Initialization (Guided Initialization):
   Avoids purely random initialization by biasing seed selection towards
   high-degree, well-distributed nodes while maintaining population diversity.
2. Adaptive Mutation Rate based on Jaccard Population Diversity:
   Dynamically increases mutation probability when population diversity drops below
   a critical threshold (escaping premature convergence / local optima).
3. Degree-Guided Mutation Replacement:
   Biases mutated node selection towards promising influential candidates.
4. Ablation Study Flags:
   Allows toggling each improvement independently to evaluate individual contributions.
"""

from __future__ import annotations
import time
import random
from typing import List, Dict, Any, Tuple

import numpy as np

from im_research.core.interfaces import BaseAlgorithm, AlgorithmResult
from im_research.core.problem import IMProblem
from im_research.core.solution import Solution, Population


class IGA(BaseAlgorithm):
    """
    Improved Genetic Algorithm (IGA) for Influence Maximization (Central Proposed Method).

    Parameters:
    -----------
    pop_size : int
        Number of individuals in the population (default: 50).
    max_generations : int
        Maximum number of evolutionary generations (default: 100).
    crossover_rate : float
        Probability of performing set crossover (default: 0.85).
    mutation_rate_base : float
        Base mutation probability per gene (default: 0.10).
    mutation_rate_max : float
        Upper bound on adaptive mutation rate during stagnation (default: 0.35).
    diversity_threshold : float
        Mean pairwise Jaccard diversity threshold triggering adaptive mutation (default: 0.30).
    tournament_size : int
        Number of candidates in tournament selection (default: 3).
    elitism : int
        Number of elite solutions preserved across generations (default: 2).

    Ablation Study Controls:
    ------------------------
    enable_guided_init : bool
        If True, use degree-biased hybrid initialization; if False, uniform random.
    enable_adaptive_mutation : bool
        If True, dynamically scale mutation rate based on diversity; if False, constant rate.
    enable_degree_guided_mutation : bool
        If True, mutate with degree-weighted candidate selection; if False, uniform random.
    """

    def __init__(
        self,
        pop_size: int = 50,
        max_generations: int = 100,
        crossover_rate: float = 0.85,
        mutation_rate_base: float = 0.10,
        mutation_rate_max: float = 0.35,
        diversity_threshold: float = 0.30,
        tournament_size: int = 3,
        elitism: int = 2,
        enable_guided_init: bool = True,
        enable_adaptive_mutation: bool = True,
        enable_degree_guided_mutation: bool = True,
    ):
        super().__init__(name="IGA")
        self.pop_size = pop_size
        self.max_generations = max_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate_base = mutation_rate_base
        self.mutation_rate_max = mutation_rate_max
        self.diversity_threshold = diversity_threshold
        self.tournament_size = tournament_size
        self.elitism = elitism

        # Ablation study toggles
        self.enable_guided_init = enable_guided_init
        self.enable_adaptive_mutation = enable_adaptive_mutation
        self.enable_degree_guided_mutation = enable_degree_guided_mutation

    # ------------------------------------------------------------------ #
    #  Initialization Operator                                           #
    # ------------------------------------------------------------------ #

    def _get_node_degrees(self, graph: Any, n: int) -> np.ndarray:
        """Retrieves degrees robustly for C++ CSR Graph or standard graph interface."""
        if hasattr(graph, "row_ptr"):
            row_ptr = graph.row_ptr()
            return np.array([row_ptr[u + 1] - row_ptr[u] for u in range(n)], dtype=np.float64)
        elif hasattr(graph, "out_degree"):
            return np.array([graph.out_degree(u) for u in range(n)], dtype=np.float64)
        elif hasattr(graph, "degree"):
            return np.array([graph.degree(u) for u in range(n)], dtype=np.float64)
        else:
            return np.ones(n, dtype=np.float64)

    def _create_initial_population(
        self, problem: IMProblem, np_rng: np.random.Generator
    ) -> Population:
        """
        Creates the initial population.
        If enable_guided_init is True:
          - 70% individuals: degree-biased sampling without replacement
          - 30% individuals: pure uniform random (ensures global exploration)
        If False:
          - 100% uniform random (baseline GA style).
        """
        n = problem.num_nodes
        k = problem.k

        if not self.enable_guided_init:
            return problem.create_random_population(self.pop_size, np_rng)

        # Precompute degree weights
        degrees = self._get_node_degrees(problem.graph, n)
        degrees += 1.0  # Laplace smoothing
        degree_probs = degrees / degrees.sum()

        individuals: List[Solution] = []
        num_guided = int(0.70 * self.pop_size)
        num_random = self.pop_size - num_guided

        # Guided individuals (degree-biased sampling)
        for _ in range(num_guided):
            seeds = np_rng.choice(n, size=k, replace=False, p=degree_probs)
            individuals.append(Solution(sorted(int(x) for x in seeds)))

        # Random individuals
        for _ in range(num_random):
            seeds = np_rng.choice(n, size=k, replace=False)
            individuals.append(Solution(sorted(int(x) for x in seeds)))

        return Population(individuals)

    # ------------------------------------------------------------------ #
    #  Selection & Crossover Operators                                   #
    # ------------------------------------------------------------------ #

    def _tournament_select(self, pop: Population, rng: random.Random) -> Solution:
        """Tournament selection: sample tournament_size, return highest fitness."""
        candidates = rng.sample(pop.individuals, min(self.tournament_size, len(pop)))
        return max(candidates, key=lambda s: s.fitness or 0.0)

    def _crossover(
        self,
        parent_a: Solution,
        parent_b: Solution,
        k: int,
        n: int,
        rng: random.Random,
    ) -> Tuple[Solution, Solution]:
        """
        Set-based crossover:
        Children are sampled from union of parents (S_a ∪ S_b).
        Preserves good building blocks without positional gene ordering artifacts.
        """
        union = list(set(parent_a.seed_set) | set(parent_b.seed_set))
        if len(union) < k:
            all_nodes = set(range(n))
            extra = list(all_nodes - set(union))
            rng.shuffle(extra)
            union += extra[: k - len(union)]

        c1 = sorted(rng.sample(union, k))
        c2 = sorted(rng.sample(union, k))
        return Solution(c1), Solution(c2)

    # ------------------------------------------------------------------ #
    #  Adaptive Mutation Operator                                        #
    # ------------------------------------------------------------------ #

    def _calculate_mutation_rate(self, current_diversity: float) -> float:
        """
        Adaptive mutation rate:
        If diversity falls below diversity_threshold, linearly increases
        mutation rate up to mutation_rate_max to escape stagnation.
        """
        if not self.enable_adaptive_mutation:
            return self.mutation_rate_base

        if current_diversity < self.diversity_threshold:
            # Deficit ratio: 0.0 (at threshold) to 1.0 (zero diversity)
            deficit = (self.diversity_threshold - current_diversity) / self.diversity_threshold
            rate = self.mutation_rate_base + deficit * (
                self.mutation_rate_max - self.mutation_rate_base
            )
            return min(rate, self.mutation_rate_max)
        return self.mutation_rate_base

    def _mutate(
        self,
        sol: Solution,
        mutation_rate: float,
        n: int,
        rng: random.Random,
        top_candidates: List[int] | None,
    ) -> Solution:
        """
        Mutates a solution by replacing selected seeds with alternative nodes.
        Uses degree-guided candidate sampling if enabled.
        """
        seed_set = set(sol.seed_set)
        new_seeds = list(sol.seed_set)

        for i in range(len(new_seeds)):
            if rng.random() < mutation_rate:
                candidate_pool = None
                if self.enable_degree_guided_mutation and top_candidates:
                    valid_top = [x for x in top_candidates if x not in seed_set]
                    if valid_top and rng.random() < 0.70:
                        candidate_pool = valid_top

                if not candidate_pool:
                    # Fallback to random node outside current seed set
                    all_available = list(set(range(n)) - seed_set)
                    candidate_pool = all_available

                if candidate_pool:
                    replacement = rng.choice(candidate_pool)
                    seed_set.discard(new_seeds[i])
                    seed_set.add(replacement)
                    new_seeds[i] = replacement

        return Solution(sorted(seed_set))

    # ------------------------------------------------------------------ #
    #  Main Evolution Loop                                               #
    # ------------------------------------------------------------------ #

    def run(
        self,
        problem: IMProblem,
        seed: int = 42,
        max_evaluations: int | None = None,
        max_iterations: int | None = None,
    ) -> AlgorithmResult:

        rng = random.Random(seed)
        np_rng = np.random.default_rng(seed)

        n = problem.num_nodes
        k = problem.k
        max_gen = max_iterations or self.max_generations
        budget = max_evaluations or float("inf")

        t_start = time.perf_counter()
        total_evals = 0
        convergence_history: List[Dict[str, Any]] = []

        # Precompute top candidate nodes for degree-guided mutation
        top_candidates = None
        if self.enable_degree_guided_mutation:
            degrees = self._get_node_degrees(problem.graph, n)
            deg_pairs = [(degrees[u], u) for u in range(n)]
            deg_pairs.sort(reverse=True)
            top_limit = min(n, max(k * 5, 50))
            top_candidates = [u for _, u in deg_pairs[:top_limit]]

        # ---- Initial Population ---- #
        pop = self._create_initial_population(problem, np_rng)
        problem.batch_fitness(pop)
        total_evals += self.pop_size

        best_ever = pop.best
        current_diversity = pop.diversity_jaccard()

        convergence_history.append({
            "generation": 0,
            "best_fitness": best_ever.fitness,
            "mean_fitness": pop.mean_fitness,
            "diversity": current_diversity,
            "mutation_rate": self.mutation_rate_base,
            "evaluations": total_evals,
        })

        # ---- Evolution Loop ---- #
        for gen in range(1, max_gen + 1):
            if total_evals >= budget:
                break

            current_diversity = pop.diversity_jaccard()
            current_pm = self._calculate_mutation_rate(current_diversity)

            new_individuals: List[Solution] = []

            # 1. Elitism: preserve top `elitism` individuals untouched
            sorted_pop = sorted(
                pop.individuals, key=lambda s: s.fitness or 0.0, reverse=True
            )
            new_individuals.extend(sorted_pop[: self.elitism])

            # 2. Reproduction
            while len(new_individuals) < self.pop_size:
                p1 = self._tournament_select(pop, rng)
                p2 = self._tournament_select(pop, rng)

                if rng.random() < self.crossover_rate:
                    c1, c2 = self._crossover(p1, p2, k, n, rng)
                else:
                    c1 = Solution(p1.seed_set[:])
                    c2 = Solution(p2.seed_set[:])

                c1 = self._mutate(c1, current_pm, n, rng, top_candidates)
                c2 = self._mutate(c2, current_pm, n, rng, top_candidates)

                new_individuals.append(c1)
                if len(new_individuals) < self.pop_size:
                    new_individuals.append(c2)

            pop = Population(new_individuals)

            # 3. Batch Evaluation (OpenMP Parallel)
            unevaluated = [s for s in pop.individuals if s.fitness is None]
            if unevaluated:
                problem.batch_fitness(unevaluated)
                total_evals += len(unevaluated)

            gen_best = pop.best
            if (best_ever.fitness or 0.0) < (gen_best.fitness or 0.0):
                best_ever = gen_best

            convergence_history.append({
                "generation": gen,
                "best_fitness": best_ever.fitness,
                "mean_fitness": pop.mean_fitness,
                "diversity": current_diversity,
                "mutation_rate": current_pm,
                "evaluations": total_evals,
            })

        t_search_end = time.perf_counter()

        # Final evaluation with high Monte Carlo precision
        best_ever.fitness = problem.fitness(best_ever)
        total_evals += 1

        t_total_end = time.perf_counter()

        return AlgorithmResult(
            algorithm_name=self.name,
            best_solution=best_ever,
            search_time=t_search_end - t_start,
            total_evaluations=total_evals,
            convergence_history=convergence_history,
            metadata={
                "total_time": t_total_end - t_start,
                "pop_size": self.pop_size,
                "generations_completed": len(convergence_history) - 1,
                "crossover_rate": self.crossover_rate,
                "mutation_rate_base": self.mutation_rate_base,
                "mutation_rate_max": self.mutation_rate_max,
                "diversity_threshold": self.diversity_threshold,
                "elitism": self.elitism,
                "enable_guided_init": self.enable_guided_init,
                "enable_adaptive_mutation": self.enable_adaptive_mutation,
                "enable_degree_guided_mutation": self.enable_degree_guided_mutation,
                "random_seed": seed,
            },
        )
