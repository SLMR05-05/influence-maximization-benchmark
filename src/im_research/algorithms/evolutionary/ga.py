from __future__ import annotations
import time
import random
from typing import List, Dict, Any

import numpy as np

from im_research.core.interfaces import BaseAlgorithm, AlgorithmResult
from im_research.core.problem import IMProblem
from im_research.core.solution import Solution, Population


class BaselineGA(BaseAlgorithm):
    """
    Baseline Genetic Algorithm for Influence Maximization.
    Standard GA with:
    - Random uniform initialization
    - Tournament selection
    - One-point crossover with a repair operator
    - Uniform mutation (replace random gene with unseen node)
    - Elitism (best individual always survives)

    This is the UNIMPROVED baseline that IGA is directly compared against.
    Uses the SAME representation, SAME evaluator, and SAME budget as IGA
    to ensure any performance gap is due to algorithmic improvements only.
    """
    def __init__(self,
                 pop_size: int = 50,
                 max_generations: int = 100,
                 crossover_rate: float = 0.8,
                 mutation_rate: float = 0.1,
                 tournament_size: int = 3,
                 elitism: int = 1,
                 record_history: bool = True):
        super().__init__(name="BaselineGA")
        self.pop_size = pop_size
        self.max_generations = max_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.elitism = elitism
        self.record_history = record_history

    # ------------------------------------------------------------------ #
    #  Operators                                                           #
    # ------------------------------------------------------------------ #

    def _tournament_select(self, pop: Population, rng: random.Random) -> Solution:
        """Tournament selection: pick tournament_size candidates, return fittest."""
        candidates = rng.sample(pop.individuals, min(self.tournament_size, len(pop)))
        return max(candidates, key=lambda s: s.fitness or 0.0)

    def _crossover(self, parent_a: Solution, parent_b: Solution,
                   k: int, n: int, rng: random.Random) -> tuple[Solution, Solution]:
        """
        One-point crossover for ordered seed chromosomes.

        Duplicate and missing genes are repaired so every child contains
        exactly k valid, distinct nodes.
        """
        if k <= 1:
            return Solution(parent_a.seed_set[:]), Solution(parent_b.seed_set[:])

        cut = rng.randint(1, k - 1)
        genes_a = list(parent_a.seed_set)
        genes_b = list(parent_b.seed_set)

        def repair(genes: List[int], fallback: List[int]) -> Solution:
            repaired: List[int] = []
            seen = set()
            for gene in genes + fallback:
                if 0 <= gene < n and gene not in seen:
                    repaired.append(gene)
                    seen.add(gene)
                if len(repaired) == k:
                    break
            if len(repaired) < k:
                remaining = list(set(range(n)) - seen)
                rng.shuffle(remaining)
                repaired.extend(remaining[: k - len(repaired)])
            return Solution(sorted(repaired[:k]))

        child_1 = repair(genes_a[:cut] + genes_b[cut:], genes_b + genes_a)
        child_2 = repair(genes_b[:cut] + genes_a[cut:], genes_a + genes_b)
        return child_1, child_2

    def _mutate(self, sol: Solution, n: int, rng: random.Random) -> Solution:
        """
        Uniform mutation: each gene independently replaced
        with a uniformly random node not already in the seed set.
        """
        seed_set = set(sol.seed_set)
        new_seeds = list(sol.seed_set)

        for i in range(len(new_seeds)):
            if rng.random() < self.mutation_rate:
                all_nodes = list(set(range(n)) - seed_set)
                if all_nodes:
                    new_node = rng.choice(all_nodes)
                    seed_set.discard(new_seeds[i])
                    seed_set.add(new_node)
                    new_seeds[i] = new_node

        return Solution(sorted(seed_set))

    # ------------------------------------------------------------------ #
    #  Main run                                                            #
    # ------------------------------------------------------------------ #

    def run(self,
            problem: IMProblem,
            seed: int = 42,
            max_evaluations: int | None = None,
            max_iterations: int | None = None) -> AlgorithmResult:

        rng = random.Random(seed)
        np_rng = np.random.default_rng(seed)

        n = problem.num_nodes
        k = problem.k
        max_gen = max_iterations or self.max_generations
        budget = max_evaluations or float("inf")

        t_start = time.perf_counter()
        total_evals = 0
        convergence_history = []
        fitness_evaluation_history: List[Dict[str, Any]] = []
        population_history: List[Dict[str, Any]] = []

        # ---- Initial Population (Random) ---- #
        print(f"      [BaselineGA] Khởi tạo ngẫu nhiên quần thể N={self.pop_size}...", flush=True)
        pop = problem.create_random_population(self.pop_size, np_rng)
        scores = problem.batch_fitness(pop)
        total_evals += self.pop_size
        if self.record_history:
            fitness_evaluation_history.append({
                "generation": 0,
                "batch_size": self.pop_size,
                "fitness": [float(score) for score in scores],
                "evaluation_type": "monte_carlo",
            })
            population_history.append({
                "generation": 0,
                "individuals": [
                    {"seed_set": list(ind.seed_set), "fitness": float(ind.fitness or 0.0)}
                    for ind in pop.individuals
                ],
            })

        best_ever = pop.best
        print(f"      [BaselineGA] Hoàn tất t=0 | Best Spread = {best_ever.fitness:.2f} | Đa dạng Jaccard = {pop.diversity_jaccard():.3f}", flush=True)

        convergence_history.append({
            "generation": 0,
            "best_fitness": best_ever.fitness,
            "mean_fitness": pop.mean_fitness,
            "diversity": pop.diversity_jaccard(),
            "evaluations": total_evals
        })

        # ---- Evolution Loop ---- #
        log_interval = max(1, max_gen // 10)
        for gen in range(1, max_gen + 1):
            if total_evals >= budget:
                print(f"      [BaselineGA] [Gen {gen}] Đạt giới hạn budget={budget}. Dừng sớm.", flush=True)
                break

            new_individuals: List[Solution] = []

            # Elitism: keep best elitism individuals unchanged
            sorted_pop = sorted(pop.individuals, key=lambda s: s.fitness or 0.0, reverse=True)
            new_individuals.extend(sorted_pop[:self.elitism])

            # Fill rest of new population
            while len(new_individuals) < self.pop_size:
                p1 = self._tournament_select(pop, rng)
                p2 = self._tournament_select(pop, rng)

                if rng.random() < self.crossover_rate:
                    c1, c2 = self._crossover(p1, p2, k, n, rng)
                else:
                    c1, c2 = Solution(p1.seed_set[:]), Solution(p2.seed_set[:])

                c1 = self._mutate(c1, n, rng)
                c2 = self._mutate(c2, n, rng)

                new_individuals.append(c1)
                if len(new_individuals) < self.pop_size:
                    new_individuals.append(c2)

            pop = Population(new_individuals)

            # Evaluate new individuals (those without fitness = elites already have it)
            unevaluated = [i for i, s in enumerate(pop.individuals) if s.fitness is None]
            if unevaluated:
                batch = [pop.individuals[i] for i in unevaluated]
                scores = problem.batch_fitness(batch)
                total_evals += len(batch)
                if self.record_history:
                    fitness_evaluation_history.append({
                        "generation": gen,
                        "batch_size": len(batch),
                        "fitness": [float(score) for score in scores],
                        "evaluation_type": "monte_carlo",
                    })

            gen_best = pop.best
            if (best_ever.fitness or 0.0) < (gen_best.fitness or 0.0):
                best_ever = gen_best

            if gen == 1 or gen % log_interval == 0 or gen == max_gen:
                print(
                    f"      [BaselineGA] Thế hệ {gen:3d}/{max_gen} | Best Spread: {best_ever.fitness:6.2f} | Mean: {pop.mean_fitness:6.2f} | Đa dạng: {pop.diversity_jaccard():.3f}",
                    flush=True,
                )

            convergence_history.append({
                "generation": gen,
                "best_fitness": best_ever.fitness,
                "mean_fitness": pop.mean_fitness,
                "diversity": pop.diversity_jaccard(),
                "evaluations": total_evals
            })
            if self.record_history:
                population_history.append({
                    "generation": gen,
                    "individuals": [
                        {"seed_set": list(ind.seed_set), "fitness": float(ind.fitness or 0.0)}
                        for ind in pop.individuals
                    ],
                })

        t_search_end = time.perf_counter()

        # Final validation
        print(f"      [BaselineGA] Hoàn tất tiến hóa! Đánh giá nghiệm cuối cùng...", flush=True)
        best_ever.fitness = problem.fitness(best_ever)
        total_evals += 1

        t_total_end = time.perf_counter()

        result = AlgorithmResult(
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
                "mutation_rate": self.mutation_rate,
                "elitism": self.elitism,
                "random_seed": seed
            }
        )
        result.metadata["operator"] = "one_point_crossover_with_repair"
        result.metadata["final_search_fitness"] = float(best_ever.fitness or 0.0)
        result.metadata["final_evaluation_type"] = "monte_carlo"
        if self.record_history:
            result.metadata["fitness_evaluation_history"] = fitness_evaluation_history
            result.metadata["population_history"] = population_history
        return result

