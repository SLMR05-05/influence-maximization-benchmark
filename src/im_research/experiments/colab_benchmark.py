"""Reproducible backend benchmark for Google Colab experiments.

This module intentionally does not depend on the desktop GUI.  It coordinates
the existing CELF, BaselineGA, and IGA implementations, writes a versioned
JSON schema, and can write directly to a mounted Google Drive directory.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import os
import platform
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import networkx as nx
import numpy as np
from scipy import stats

from im_research import _im_core
from im_research.algorithms.evolutionary.ga import BaselineGA
from im_research.algorithms.evolutionary.iga import IGA
from im_research.algorithms.greedy.celf import CELF
from im_research.core.problem import IMProblem
from im_research.data.loader import build_cpp_graph, load_networkx_graph

SCHEMA_VERSION = "1.0.0"
SUPPORTED_ALGORITHMS = ("CELF", "GA", "IGA")


class _TeeStream:
    def __init__(self, original: Any, log_file: Any):
        self.original = original
        self.log_file = log_file

    def write(self, text: str) -> int:
        encoding = getattr(self.original, "encoding", None) or "utf-8"
        if encoding.lower().replace("-", "") != "utf8":
            text = text.encode(encoding, errors="replace").decode(encoding)
        self.original.write(text)
        self.log_file.write(text)
        self.log_file.flush()
        return len(text)

    def flush(self) -> None:
        self.original.flush()
        self.log_file.flush()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return str(value)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(
            _json_safe(payload), handle, indent=2, ensure_ascii=False, allow_nan=False
        )
        handle.write("\n")
    temporary.replace(path)


def _config_hash(config: Dict[str, Any]) -> str:
    encoded = json.dumps(_json_safe(config), sort_keys=True, ensure_ascii=False).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _graph_information(graph: nx.Graph, dataset_meta: Dict[str, Any]) -> Dict[str, Any]:
    degrees = [degree for _, degree in graph.degree()]
    try:
        communities = nx.community.louvain_communities(graph.to_undirected(), seed=42)
        community_count = len(communities)
    except nx.NetworkXException:
        community_count = None
    return {
        "number_of_nodes": int(graph.number_of_nodes()),
        "number_of_edges": int(graph.number_of_edges()),
        "directed": bool(graph.is_directed()),
        "density": float(nx.density(graph)),
        "average_degree": float(np.mean(degrees)) if degrees else 0.0,
        "minimum_degree": int(min(degrees)) if degrees else 0,
        "maximum_degree": int(max(degrees)) if degrees else 0,
        "number_of_communities": community_count,
        "dataset_metadata": dataset_meta,
    }


def _edge_probability(
    graph: nx.Graph, u: int, v: int, probability_model: str, p: float
) -> float:
    if probability_model.lower() in {"uniform", "constant", "fixed"}:
        return float(p)
    if graph.is_directed():
        return 1.0 / max(1, graph.in_degree(v))
    return 1.0 / max(1, graph.degree(v))


def _simulate_diffusion(
    graph: nx.Graph,
    seed_set: Sequence[int],
    diffusion_model: str,
    probability_model: str,
    p: float,
    seed: int,
    include_failed_edges: bool,
) -> Dict[str, Any]:
    if diffusion_model.upper() != "IC":
        raise ValueError(
            "The Colab backend currently supports only diffusion_model='IC'."
        )

    rng = random.Random(seed)
    activated = set(int(node) for node in seed_set)
    frontier = list(activated)
    history: Dict[str, Any] = {
        "random_seed": int(seed),
        "diffusion_model": diffusion_model.upper(),
        "probability_model": probability_model.upper(),
        "seed_set": sorted(activated),
    }
    step = 0
    history[f"step_{step}"] = {
        "newly_activated": sorted(activated),
        "all_activated": sorted(activated),
        "successful_edges": [],
        "failed_edges": [],
    }

    while frontier:
        next_frontier: List[int] = []
        successful_edges: List[List[int]] = []
        failed_edges: List[List[int]] = []
        for u in frontier:
            neighbors = (
                graph.successors(u) if graph.is_directed() else graph.neighbors(u)
            )
            for v in neighbors:
                if v in activated:
                    continue
                probability = _edge_probability(graph, u, v, probability_model, p)
                if rng.random() <= probability:
                    activated.add(v)
                    next_frontier.append(v)
                    successful_edges.append([int(u), int(v)])
                elif include_failed_edges:
                    failed_edges.append([int(u), int(v)])
        step += 1
        history[f"step_{step}"] = {
            "newly_activated": sorted(set(next_frontier)),
            "all_activated": sorted(activated),
            "successful_edges": successful_edges,
            "failed_edges": failed_edges,
        }
        frontier = list(dict.fromkeys(next_frontier))

    history["final_spread"] = len(activated)
    history["steps"] = step
    return history


def _algorithm_instance(name: str, config: Dict[str, Any], final_mc_runs: int) -> Any:
    if name == "CELF":
        return CELF()
    if name == "GA":
        return BaselineGA(
            pop_size=config["population_size"],
            max_generations=config["generations"],
            crossover_rate=config["crossover_rate"],
            mutation_rate=config["mutation_rate"],
            tournament_size=config["tournament_size"],
            elitism=config["elite_size"],
            record_history=config["record_population_history"],
        )
    if name == "IGA":
        return IGA(
            pop_size=config["population_size"],
            max_generations=config["generations"],
            p_c_min=config["iga"]["p_c_min"],
            p_c_max=config["iga"]["p_c_max"],
            p_m_min=config["iga"]["p_m_min"],
            p_m_max=config["iga"]["p_m_max"],
            tournament_size=config["tournament_size"],
            elitism=config["elite_size"],
            epsilon_div=config["iga"]["epsilon_div"],
            tau_overlap=config["iga"]["tau_overlap"],
            lambda_tour=config["iga"]["lambda_tour"],
            local_search_steps=config["iga"]["local_search_steps"],
            r_final=final_mc_runs,
            enable_guided_init=config["iga"]["enable_guided_init"],
            enable_adaptive_mutation=config["iga"]["enable_adaptive_mutation"],
            enable_degree_guided_mutation=config["iga"][
                "enable_degree_guided_mutation"
            ],
            enable_local_search=config["iga"]["enable_local_search"],
            enable_overlap_filtering=config["iga"]["enable_overlap_filtering"],
        )
    raise ValueError(f"Unsupported algorithm: {name}")


def _summary(values: Iterable[float]) -> Dict[str, Any]:
    values = [float(value) for value in values]
    if not values:
        return {
            "count": 0,
            "mean": None,
            "std": None,
            "minimum": None,
            "maximum": None,
            "median": None,
            "confidence_interval_95": None,
        }
    array = np.asarray(values, dtype=float)
    mean = float(np.mean(array))
    std = float(np.std(array, ddof=1)) if len(array) > 1 else 0.0
    if len(array) > 1:
        margin = float(stats.t.ppf(0.975, len(array) - 1) * std / math.sqrt(len(array)))
    else:
        margin = 0.0
    return {
        "count": len(values),
        "mean": mean,
        "std": std,
        "minimum": float(np.min(array)),
        "maximum": float(np.max(array)),
        "median": float(np.median(array)),
        "confidence_interval_95": [mean - margin, mean + margin],
    }


def _seed_set_consistency(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Describe whether independent runs selected the same final seed set."""
    if not records:
        return {
            "count": 0,
            "unique_seed_sets": 0,
            "all_runs_same": None,
            "most_frequent_seed_set": None,
            "most_frequent_count": 0,
            "best_run_id": None,
            "best_run_seed_set": None,
            "best_run_spread": None,
        }

    seed_sets = [
        tuple(int(node) for node in record["seed_set"])
        for record in records
    ]
    frequencies: Dict[tuple[int, ...], int] = {}
    for seed_set in seed_sets:
        frequencies[seed_set] = frequencies.get(seed_set, 0) + 1
    most_frequent = max(frequencies, key=frequencies.get)
    best_index, best_record = max(
        enumerate(records, start=1), key=lambda item: item[1]["final_spread"]
    )
    return {
        "count": len(records),
        "unique_seed_sets": len(frequencies),
        "all_runs_same": len(frequencies) == 1,
        "most_frequent_seed_set": list(most_frequent),
        "most_frequent_count": frequencies[most_frequent],
        "best_run_id": int(best_record.get("run_id", best_index)),
        "best_run_seed_set": list(best_record["seed_set"]),
        "best_run_spread": float(best_record["final_spread"]),
    }


def _statistical_tests(run_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    algorithms = sorted(
        {algorithm for record in run_records for algorithm in record["algorithms"]}
    )
    spreads = {
        algorithm: [
            record["algorithms"][algorithm]["final_spread"]
            for record in run_records
            if algorithm in record["algorithms"]
        ]
        for algorithm in algorithms
    }
    result: Dict[str, Any] = {
        "alpha": 0.05,
        "method": "Wilcoxon signed-rank",
        "pairwise": [],
    }
    for index, left in enumerate(algorithms):
        for right in algorithms[index + 1 :]:
            paired = min(len(spreads[left]), len(spreads[right]))
            test = {
                "left": left,
                "right": right,
                "n": paired,
                "statistic": None,
                "p_value": None,
                "conclusion": "insufficient paired runs",
            }
            if paired >= 2:
                left_values = spreads[left][:paired]
                right_values = spreads[right][:paired]
                if np.allclose(np.asarray(left_values), np.asarray(right_values)):
                    test["conclusion"] = "all paired differences are zero"
                else:
                    statistic, p_value = stats.wilcoxon(left_values, right_values)
                    test["statistic"] = float(statistic)
                    test["p_value"] = float(p_value)
                    test["conclusion"] = (
                        "statistically significant difference"
                        if p_value < result["alpha"]
                        else "no statistically significant difference"
                    )
            result["pairwise"].append(test)
    return result


def _default_config(
    dataset_name: str,
    dataset_path: str | Path | None,
    directed: bool,
    diffusion_model: str,
    probability_model: str,
    p: float,
    k: int,
    mc_runs: int,
    independent_runs: int,
    algorithms: Sequence[str],
    population_size: int,
    generations: int,
    elite_size: int,
    crossover_rate: float,
    mutation_rate: float,
    tournament_size: int,
    random_seed: int,
    celf_random_seed: int,
    validation_mc_runs: int,
    record_population_history: bool,
    record_mc_details: bool,
    record_failed_edges: bool,
) -> Dict[str, Any]:
    normalized_algorithms = [str(name).upper() for name in algorithms]
    unknown = sorted(set(normalized_algorithms) - set(SUPPORTED_ALGORITHMS))
    if unknown:
        raise ValueError(f"Unsupported algorithms: {', '.join(unknown)}")
    if diffusion_model.upper() != "IC":
        raise ValueError("Only diffusion_model='IC' is currently implemented.")
    if probability_model.lower() not in {
        "wc",
        "weighted",
        "weighted_cascade",
        "uniform",
        "constant",
        "fixed",
    }:
        raise ValueError(f"Unsupported probability_model: {probability_model}")
    if k <= 0 or mc_runs <= 0 or independent_runs <= 0 or validation_mc_runs <= 0:
        raise ValueError(
            "k, mc_runs, validation_mc_runs, and independent_runs must be positive."
        )
    if not 0.0 <= crossover_rate <= 1.0 or not 0.0 <= mutation_rate <= 1.0:
        raise ValueError("crossover_rate and mutation_rate must be in [0, 1].")
    return {
        "dataset": {
            "name": dataset_name,
            "path": str(dataset_path) if dataset_path is not None else None,
            "directed": bool(directed),
        },
        "diffusion": {
            "diffusion_model": diffusion_model.upper(),
            "probability_model": probability_model.upper(),
            "uniform_probability": float(p),
        },
        "problem": {"k": int(k)},
        "monte_carlo": {
            "search_runs": int(mc_runs),
            "validation_runs": int(validation_mc_runs),
            "save_replications": bool(record_mc_details),
        },
        "independent_runs": int(independent_runs),
        "algorithms": normalized_algorithms,
        "population_size": int(population_size),
        "generations": int(generations),
        "elite_size": int(elite_size),
        "crossover_rate": float(crossover_rate),
        "mutation_rate": float(mutation_rate),
        "tournament_size": int(tournament_size),
        "random_seed": int(random_seed),
        "celf_random_seed": int(celf_random_seed),
        "record_population_history": bool(record_population_history),
        "record_failed_edges": bool(record_failed_edges),
        "iga": {
            "p_c_min": 0.60,
            "p_c_max": 0.90,
            "p_m_min": 0.05,
            "p_m_max": 0.35,
            "epsilon_div": 0.30,
            "tau_overlap": 0.50,
            "lambda_tour": 0.25,
            "local_search_steps": 10,
            "enable_guided_init": True,
            "enable_adaptive_mutation": True,
            "enable_degree_guided_mutation": True,
            "enable_local_search": True,
            "enable_overlap_filtering": True,
        },
    }


def run_benchmark(
    dataset_path: str | Path | None = None,
    dataset_name: str = "Karate Club",
    directed: bool = False,
    diffusion_model: str = "IC",
    probability_model: str = "WC",
    p: float = 0.1,
    k: int = 10,
    mc_runs: int = 100,
    independent_runs: int = 3,
    algorithms: Sequence[str] = SUPPORTED_ALGORITHMS,
    population_size: int = 50,
    generations: int = 100,
    elite_size: int = 2,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.1,
    tournament_size: int = 3,
    random_seed: int = 42,
    celf_random_seed: int = 42,
    validation_mc_runs: int | None = None,
    output_dir: str | Path = "runs/colab_experiment",
    record_population_history: bool = True,
    record_mc_details: bool = False,
    record_failed_edges: bool = False,
    resume: bool = True,
) -> Dict[str, Any]:
    """Run CELF, GA, and IGA under a common IC probability configuration."""
    validation_mc_runs = validation_mc_runs or mc_runs
    config = _default_config(
        dataset_name,
        dataset_path,
        directed,
        diffusion_model,
        probability_model,
        p,
        k,
        mc_runs,
        independent_runs,
        algorithms,
        population_size,
        generations,
        elite_size,
        crossover_rate,
        mutation_rate,
        tournament_size,
        random_seed,
        celf_random_seed,
        validation_mc_runs,
        record_population_history,
        record_mc_details,
        record_failed_edges,
    )
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    config_digest = _config_hash(config)
    checkpoint_path = output_path / "checkpoint.json"
    run_records: List[Dict[str, Any]] = []

    if resume and checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("config_hash") != config_digest:
            raise ValueError(
                "Existing checkpoint configuration does not match this benchmark."
            )
        run_records = checkpoint.get("runs", [])

    graph, dataset_meta = load_networkx_graph(
        dataset_name,
        dataset_path=dataset_path,
        directed=directed,
    )
    if k > graph.number_of_nodes():
        raise ValueError(f"k={k} exceeds the graph size {graph.number_of_nodes()}.")
    probability_mode = (
        "wc"
        if probability_model.lower() in {"wc", "weighted", "weighted_cascade"}
        else "uniform"
    )
    cpp_graph = build_cpp_graph(graph, probability_mode=probability_mode, p=p)
    graph_info = _graph_information(graph, dataset_meta)
    start_timestamp = datetime.now(timezone.utc).isoformat()

    _write_json(
        output_path / "config.json",
        {
            "schema_version": SCHEMA_VERSION,
            "config_hash": config_digest,
            "configuration": config,
        },
    )
    _write_json(output_path / "graph_info.json", graph_info)

    log_path = output_path / "logs.txt"
    completed_indices = {int(record["run_id"]) for record in run_records}
    with (
        log_path.open("a", encoding="utf-8") as log_handle,
        contextlib.redirect_stdout(_TeeStream(sys.stdout, log_handle)),
        contextlib.redirect_stderr(_TeeStream(sys.stderr, log_handle)),
    ):
        print(f"[INFO] Dataset: {dataset_name}")
        print(
            f"[INFO] Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges"
        )
        print(
            f"[INFO] Diffusion: {diffusion_model.upper()} / {probability_mode.upper()}"
        )
        print(f"[INFO] Algorithms: {', '.join(config['algorithms'])}")

        for run_number in range(1, independent_runs + 1):
            if run_number in completed_indices:
                print(
                    f"[INFO] Skipping completed independent run {run_number}/{independent_runs}"
                )
                continue
            run_seed = random_seed + (run_number - 1) * 1009
            run_record: Dict[str, Any] = {
                "run_id": run_number,
                "random_seed": run_seed,
                "celf_random_seed": celf_random_seed,
                "algorithms": {},
            }
            print(
                f"[INFO] Starting independent run {run_number}/{independent_runs} (seed={run_seed})"
            )

            for algorithm_name in config["algorithms"]:
                search_seed = (
                    celf_random_seed if algorithm_name == "CELF" else run_seed
                )
                validation_seed = (
                    celf_random_seed + 100000
                    if algorithm_name == "CELF"
                    else random_seed + 100000 + (run_number - 1) * 1009
                )
                algorithm = _algorithm_instance(
                    algorithm_name, config, validation_mc_runs
                )
                evaluator = _im_core.Evaluator(
                    cpp_graph,
                    _im_core.DiffusionModel.IndependentCascade,
                    num_mc_simulations=mc_runs,
                    seed=search_seed,
                )
                problem = IMProblem(cpp_graph, k, evaluator)
                started = time.perf_counter()
                print(f"[{algorithm_name}] Starting search")
                result = algorithm.run(problem, seed=search_seed)
                search_finished = time.perf_counter()

                validation_evaluator = _im_core.Evaluator(
                    cpp_graph,
                    _im_core.DiffusionModel.IndependentCascade,
                    num_mc_simulations=validation_mc_runs,
                    seed=validation_seed,
                )
                validation_problem = IMProblem(cpp_graph, k, validation_evaluator)
                validation_started = time.perf_counter()
                replications = validation_evaluator.evaluate_replications(
                    list(result.best_solution.seed_set), validation_mc_runs
                )
                final_spread = float(np.mean(replications)) if replications else 0.0
                validation_finished = time.perf_counter()
                final_seed_set = sorted(result.best_solution.seed_set)
                diffusion_history = _simulate_diffusion(
                    graph,
                    final_seed_set,
                    diffusion_model,
                    probability_mode,
                    p,
                    validation_seed,
                    record_failed_edges,
                )
                algorithm_record = {
                    "parameters": {
                        "search_mc_runs": mc_runs,
                        "validation_mc_runs": validation_mc_runs,
                        "population_size": population_size,
                        "generations": generations,
                        "elite_size": elite_size,
                        "crossover_rate": crossover_rate,
                        "mutation_rate": mutation_rate,
                        "tournament_size": tournament_size,
                        "algorithm_metadata": result.metadata,
                    },
                    "random_seeds": {
                        "search": search_seed,
                        "validation": validation_seed,
                        "diffusion_history": validation_seed,
                    },
                    "timing": {
                        "search_seconds": float(
                            getattr(result, "search_time", search_finished - started)
                        ),
                        "validation_seconds": float(
                            validation_finished - validation_started
                        ),
                        "total_seconds": float(validation_finished - started),
                    },
                    "seed_set": final_seed_set,
                    "fitness": float(result.best_solution.fitness or 0.0),
                    "fitness_type": result.metadata.get(
                        "final_fitness_type", "monte_carlo"
                    ),
                    "final_spread": final_spread,
                    "spread_ratio": final_spread / graph.number_of_nodes(),
                    "convergence_history": result.convergence_history,
                    "evaluations": {
                        "search_evaluations": int(evaluator.total_evaluations()),
                        "search_mc_simulations": int(evaluator.total_mc_simulations()),
                        "validation_evaluations": int(
                            validation_evaluator.total_evaluations()
                        ),
                        "validation_mc_simulations": int(
                            validation_evaluator.total_mc_simulations()
                        ),
                    },
                    "diffusion_history": diffusion_history,
                }
                if "termination_reason" in result.metadata:
                    algorithm_record["termination"] = {
                        "reason": result.metadata["termination_reason"],
                        "generations_completed": result.metadata.get(
                            "generations_completed"
                        ),
                        "best_solution_at_termination": result.metadata.get(
                            "best_solution_at_termination"
                        ),
                    }
                if record_mc_details:
                    algorithm_record["validation_mc_details"] = {
                        "random_seed": validation_seed,
                        "spreads": [int(value) for value in replications],
                    }
                run_record["algorithms"][algorithm_name] = algorithm_record
                print(
                    f"[{algorithm_name}] Completed: spread={final_spread:.4f}, "
                    f"time={validation_finished - started:.3f}s"
                )

            run_records.append(run_record)
            _write_json(
                checkpoint_path,
                {
                    "schema_version": SCHEMA_VERSION,
                    "config_hash": config_digest,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "runs": run_records,
                },
            )
            print(f"[INFO] Checkpoint saved after independent run {run_number}")

    summary: Dict[str, Any] = {}
    for algorithm_name in config["algorithms"]:
        records = [
            record["algorithms"][algorithm_name]
            for record in run_records
            if algorithm_name in record["algorithms"]
        ]
        summary[algorithm_name] = {
            "final_spread": _summary(item["final_spread"] for item in records),
            "spread_ratio": _summary(item["spread_ratio"] for item in records),
            "execution_time": _summary(
                item["timing"]["total_seconds"] for item in records
            ),
            "fitness": _summary(item["fitness"] for item in records),
            "evaluations": _summary(
                item["evaluations"]["search_evaluations"] for item in records
            ),
            "mc_simulations": _summary(
                item["evaluations"]["search_mc_simulations"] for item in records
            ),
            "seed_set_consistency": _seed_set_consistency(records),
        }

    comparison = {
        "spread_comparison": {
            name: summary[name]["final_spread"] for name in config["algorithms"]
        },
        "runtime_comparison": {
            name: summary[name]["execution_time"] for name in config["algorithms"]
        },
        "stability_comparison": {
            name: summary[name]["final_spread"]["std"] for name in config["algorithms"]
        },
    }
    statistical_tests = _statistical_tests(run_records)
    experiment = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": output_path.name,
        "created_at": start_timestamp,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "numpy_version": np.__version__,
            "networkx_version": nx.__version__,
            "cwd": os.getcwd(),
        },
        "configuration": config,
        "config_hash": config_digest,
        "graph_information": graph_info,
        "runs": run_records,
        "summary": summary,
        "comparison": comparison,
        "statistical_tests": statistical_tests,
    }
    _write_json(output_path / "runs.json", run_records)
    _write_json(output_path / "summary.json", summary)
    _write_json(output_path / "comparison.json", comparison)
    _write_json(output_path / "statistical_tests.json", statistical_tests)
    _write_json(output_path / "experiment.json", experiment)
    _write_json(
        output_path / "manifest.json",
        {
            "schema_version": SCHEMA_VERSION,
            "files": [
                "config.json",
                "graph_info.json",
                "runs.json",
                "summary.json",
                "comparison.json",
                "statistical_tests.json",
                "experiment.json",
                "logs.txt",
                "checkpoint.json",
            ],
        },
    )
    return experiment
