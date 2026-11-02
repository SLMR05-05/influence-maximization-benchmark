#!/usr/bin/env python3
"""
Influence Maximization Experiment Runner.
Executes algorithms under identical conditions with the C++ Core Evaluator.
Saves reproducible logs, convergence histories, and summary tables.
"""

from __future__ import annotations
import sys
import os
import argparse
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Ensure project src is in Python path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import numpy as np

from im_research import _im_core
from im_research.data.loader import load_graph
from im_research.core.problem import IMProblem
from im_research.algorithms.heuristics.degree import DegreeCentrality
from im_research.algorithms.heuristics.degree_discount import DegreeDiscount
from im_research.algorithms.heuristics.pagerank import PageRankHeuristic
from im_research.algorithms.greedy.celf import CELF
from im_research.algorithms.evolutionary.ga import BaselineGA
from im_research.algorithms.evolutionary.iga import IGA

ALGORITHM_REGISTRY = {
    "degree": lambda **kw: DegreeCentrality(),
    "degree_discount": lambda **kw: DegreeDiscount(edge_probability=0.1),
    "pagerank": lambda **kw: PageRankHeuristic(damping=0.85, max_iter=30),
    "celf": lambda **kw: CELF(),
    "ga": lambda **kw: BaselineGA(pop_size=kw.get("pop_size", 50), max_generations=kw.get("max_gen", 100)),
    "baseline_ga": lambda **kw: BaselineGA(pop_size=kw.get("pop_size", 50), max_generations=kw.get("max_gen", 100)),
    "iga": lambda **kw: IGA(pop_size=kw.get("pop_size", 50), max_generations=kw.get("max_gen", 100),
                            enable_guided_init=True, enable_adaptive_mutation=True),
}


def parse_args():
    parser = argparse.ArgumentParser(description="IM Experiment Runner")
    parser.add_argument("--dataset", type=str, default="Karate Club", help="Dataset name")
    parser.add_argument("--model", type=str, default="IC", choices=["IC", "LT"], help="Diffusion model")
    parser.add_argument("--k", type=int, default=10, help="Seed set size k")
    parser.add_argument("--mc", type=int, default=200, help="Monte Carlo simulations for search")
    parser.add_argument("--mc_val", type=int, default=1000, help="Monte Carlo simulations for final validation")
    parser.add_argument("--runs", type=int, default=1, help="Number of independent repetitions")
    parser.add_argument("--algo", action="append", dest="algos", help="Algorithms to run (can be repeated)")
    parser.add_argument("--out_dir", type=str, default=None, help="Directory to save run results")
    return parser.parse_args()


def run_experiments():
    args = parse_args()
    selected_algos = args.algos or ["iga", "celf", "ga", "degree_discount", "pagerank", "degree"]

    print("=" * 70)
    print("      IM-Benchmark-Lab — INFLUENCE MAXIMIZATION EXPERIMENT RUNNER")
    print("=" * 70)
    print(f"Dataset      : {args.dataset}")
    print(f"Model        : {args.model}")
    print(f"Budget k     : {args.k}")
    print(f"MC Search (R): {args.mc}")
    print(f"MC Val (R)   : {args.mc_val}")
    print(f"Repetitions  : {args.runs}")
    print(f"Algorithms   : {', '.join(selected_algos)}")
    print("-" * 70)

    # 1. Load Dataset
    print(f"[1/4] Loading graph dataset '{args.dataset}'...")
    cpp_graph, meta = load_graph(args.dataset, p=0.1)
    print(f"      Graph loaded: {cpp_graph.num_nodes()} nodes, {cpp_graph.num_edges()} edges")

    # 2. Setup C++ Shared Evaluator
    diff_model = (
        _im_core.DiffusionModel.IndependentCascade
        if args.model.upper() == "IC"
        else _im_core.DiffusionModel.LinearThreshold
    )
    evaluator = _im_core.Evaluator(cpp_graph, diff_model, num_mc_simulations=args.mc, seed=42)
    val_evaluator = _im_core.Evaluator(cpp_graph, diff_model, num_mc_simulations=args.mc_val, seed=12345)

    problem = IMProblem(graph=cpp_graph, k=args.k, evaluator=evaluator)
    val_problem = IMProblem(graph=cpp_graph, k=args.k, evaluator=val_evaluator)

    # 3. Output directory setup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir) if args.out_dir else PROJECT_ROOT / "runs" / f"EXP_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    results_table = []
    detailed_results = {}

    # 4. Execute Algorithms
    print(f"\n[2/4] Running {len(selected_algos)} algorithms across {args.runs} repetition(s)...")

    for algo_key in selected_algos:
        if algo_key not in ALGORITHM_REGISTRY:
            print(f"  [WARN] Unknown algorithm '{algo_key}', skipping.")
            continue

        algo_builder = ALGORITHM_REGISTRY[algo_key]
        algo_instance = algo_builder()
        algo_name = algo_instance.name

        print(f"\n>> Executing: {algo_name}")
        run_spreads = []
        run_times = []
        run_solutions = []

        for r in range(args.runs):
            seed = 42 + r * 7
            t0 = time.perf_counter()
            res = algo_instance.run(problem, seed=seed)
            t_elapsed = time.perf_counter() - t0

            # Validate solution with high-precision validation evaluator
            val_spread = val_problem.fitness(res.best_solution)

            run_spreads.append(val_spread)
            run_times.append(t_elapsed)
            run_solutions.append(res.best_solution.seed_set)

            print(f"   [Run {r+1}/{args.runs}] Spread: {val_spread:.2f} | Time: {t_elapsed:.3f}s | Seeds: {res.best_solution.seed_set[:5]}...")

        mean_spread = float(np.mean(run_spreads))
        std_spread = float(np.std(run_spreads))
        mean_time = float(np.mean(run_times))

        results_table.append({
            "algorithm": algo_name,
            "code": algo_key,
            "mean_spread": round(mean_spread, 2),
            "std_spread": round(std_spread, 2),
            "mean_time": round(mean_time, 3),
            "best_spread": round(float(np.max(run_spreads)), 2),
        })

        detailed_results[algo_name] = {
            "spreads": run_spreads,
            "times": run_times,
            "seeds": run_solutions,
        }

    # Sort results table by mean_spread descending
    results_table.sort(key=lambda x: x["mean_spread"], reverse=True)
    for idx, row in enumerate(results_table, start=1):
        row["rank"] = f"#{idx}"

    # 5. Display & Save Results
    print("\n" + "=" * 70)
    print("                    EXPERIMENT RESULTS SUMMARY")
    print("=" * 70)
    print(f"{'Rank':<6}{'Algorithm':<22}{'Mean Spread':<16}{'Std Dev':<12}{'Avg Time':<10}")
    print("-" * 70)
    for row in results_table:
        print(f"{row['rank']:<6}{row['algorithm']:<22}{row['mean_spread']:<16}{row['std_spread']:<12}{row['mean_time']:<8.3f}s")
    print("=" * 70)

    # Save to JSON
    summary_path = out_dir / "summary.json"
    latest_path = PROJECT_ROOT / "runs" / "latest_results.json"
    latest_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "dataset": args.dataset,
        "k": args.k,
        "model": args.model,
        "mc": args.mc,
        "mc_val": args.mc_val,
        "runs": args.runs,
        "timestamp": timestamp,
        "summary": results_table,
        "details": detailed_results,
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n[3/4] Saved results to:\n      - {summary_path}\n      - {latest_path}")
    print("[4/4] Experiment run completed successfully! ✓\n")


if __name__ == "__main__":
    run_experiments()

